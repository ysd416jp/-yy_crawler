"""Web更新チェッカー — Flask版"""
import os
import json
import base64
import re
import asyncio
import tempfile
import gspread
from google.oauth2.service_account import Credentials
from flask import Flask, render_template, request, redirect, url_for, Response, send_file
from urllib.parse import quote
import edge_tts

app = Flask(__name__)

SHEET_KEY = "1wSfyGreLH_lb7vR_vpmuJ3rAndtMNvMDQbv2ZlPVxUE"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# GCP鍵ファイルのパス (PythonAnywhere用)
KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gcp_key.json")


def get_sheet():
    """GCP認証してGoogle Sheetsに接続"""
    raw = None
    # 1. ファイルから読む (PythonAnywhere)
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE) as f:
            raw = f.read()
    # 2. 環境変数から読む (Render等)
    if not raw:
        raw = os.environ.get("GCP_JSON", "")
    if not raw:
        return None

    raw_stripped = raw.strip()
    if raw_stripped.startswith("{"):
        creds_dict = json.loads(raw_stripped)
    else:
        cleaned = re.sub(r'[\s\n]', '', raw)
        pad = len(cleaned) % 4
        if pad:
            cleaned += '=' * (4 - pad)
        creds_dict = json.loads(base64.b64decode(cleaned).decode("utf-8"))

    if "private_key" in creds_dict:
        pk = creds_dict["private_key"]
        if "\\n" in pk:
            pk = pk.replace("\\n", "\n")
        if not pk.endswith("\n"):
            pk += "\n"
        creds_dict["private_key"] = pk

    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_KEY).sheet1


# --- サイト名→ドメイン名の対応表 ---
# ユーザーがカスタムサイト名として入力しうる日本語名からドメインを引く
# ここに無いサイト名でも汎用フォールバックで「Google検索 + サイト名 + キーワード」になる
SITE_DOMAINS = {
    # SNS（サイト内検索URLが確実に動くもの）
    "x":         None,   # 専用テンプレートあり
    "twitter":   None,
    "youtube":   None,
    "google":    None,
    # グルメ
    "食べログ":           "tabelog.com",
    "tabelog":            "tabelog.com",
    "ホットペッパーグルメ": "hotpepper.jp",
    "ホットペッパー":      "hotpepper.jp",
    "hotpepper":          "hotpepper.jp",
    "ぐるなび":           "gnavi.co.jp",
    "gnavi":              "gnavi.co.jp",
    "retty":              "retty.me",
    # 旅行
    "jalan":              "jalan.net",
    "じゃらん":           "jalan.net",
    "楽天トラベル":        "travel.rakuten.co.jp",
    "booking.com":        "booking.com",
    "booking":            "booking.com",
    # 求人
    "indeed":             "indeed.com",
    "townwork":           "townwork.net",
    "タウンワーク":        "townwork.net",
    "リクナビnext":       "next.rikunabi.com",
    "マイナビ転職":        "tenshoku.mynavi.jp",
    "doda":               "doda.jp",
    # ショッピング
    "amazon":             "amazon.co.jp",
    "アマゾン":           "amazon.co.jp",
    "楽天市場":           "rakuten.co.jp",
    "rakuten":            "rakuten.co.jp",
    "メルカリ":           "mercari.com",
    "mercari":            "mercari.com",
    "yahoo!ショッピング":  "shopping.yahoo.co.jp",
    "yahooショッピング":   "shopping.yahoo.co.jp",
    # 不動産
    "suumo":              "suumo.jp",
    "スーモ":             "suumo.jp",
    "homes":              "homes.co.jp",
    # ニュース
    "yahoo!ニュース":      "news.yahoo.co.jp",
    "yahooニュース":       "news.yahoo.co.jp",
    "nhk":                "www3.nhk.or.jp",
}

# サイト内検索URLが確実に動くもの（最小限）
DIRECT_TEMPLATES = {
    "x":       "https://x.com/search?q={word}",
    "twitter": "https://x.com/search?q={word}",
    "youtube": "https://www.youtube.com/results?search_query={word}",
    "google":  "https://www.google.com/search?q={word}",
}


def generate_url_now(word, memo):
    """検索URLを即時生成（汎用: Google検索+site:ドメイン）"""
    memo_lower = memo.strip().lower()

    # 1. 確実に動くサイト内検索（X, YouTube, Google）
    if memo_lower in DIRECT_TEMPLATES:
        return DIRECT_TEMPLATES[memo_lower].format(word=quote(word))

    # 2. ドメイン対応表にあるサイト → Google site:検索
    domain = None
    # 完全一致
    if memo_lower in SITE_DOMAINS:
        domain = SITE_DOMAINS[memo_lower]
    else:
        # 部分一致
        for key, d in SITE_DOMAINS.items():
            if key in memo_lower or memo_lower in key:
                domain = d
                break

    if domain:
        return f"https://www.google.com/search?q={quote(word)}+site%3A{domain}"

    # 3. 対応表にも無い未知のサイト → Google検索「キーワード サイト名」
    #    例: memo="食堂マップ", word="ラーメン" → Google検索「ラーメン 食堂マップ」
    return f"https://www.google.com/search?q={quote(word)}+{quote(memo)}"


# --- favicon / apple-touch-icon (空SVGで404を回避) ---
_FAVICON_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y="80" font-size="80">📡</text></svg>'

@app.route("/favicon.ico")
def favicon():
    return Response(_FAVICON_SVG, mimetype="image/svg+xml", content_type="image/svg+xml; charset=utf-8")

@app.route("/apple-touch-icon.png")
@app.route("/apple-touch-icon-precomposed.png")
def apple_touch_icon():
    return Response(status=204)


@app.route("/")
def index():
    sheet = get_sheet()
    rows = []
    error = None
    if sheet:
        try:
            headers = sheet.row_values(1)
            col = {h: i + 1 for i, h in enumerate(headers)}
            rows = sheet.get_all_records()
            # URL未生成の検索監視があれば自動生成
            for i, row in enumerate(rows, start=2):
                memo = str(row.get('memo', '')).strip()
                url = str(row.get('url', '')).strip()
                word = str(row.get('word', '')).strip()
                if memo != "HP更新" and not url.startswith('http') and word and memo:
                    generated = generate_url_now(word, memo)
                    if generated and 'url' in col:
                        sheet.update_cell(i, col['url'], generated)
                        row['url'] = generated
        except Exception as e:
            error = str(e)
    else:
        error = "Google Sheetsに接続できません"
    return render_template("index.html", rows=rows, error=error)


@app.route("/add", methods=["POST"])
def add():
    sheet = get_sheet()
    if not sheet:
        return redirect(url_for("index"))

    mode = request.form.get("mode", "kw")
    if mode == "url":
        url = request.form.get("url", "").strip()
        freq = request.form.get("freq", "12")
        if url:
            sheet.append_row(["update", url, "HP更新", int(freq), "", ""])
    else:
        keyword = request.form.get("keyword", "").strip()
        source_type = request.form.get("source_type", "preset")
        if source_type == "custom":
            source = request.form.get("custom_source", "").strip()
        else:
            source = request.form.get("preset_source", "x")
        freq = request.form.get("freq", "12")
        if keyword and source:
            # 即座にURL生成を試みる
            generated_url = generate_url_now(keyword, source)
            sheet.append_row([keyword, generated_url, source, int(freq), "", ""])

    return redirect(url_for("index"))


@app.route("/edit", methods=["POST"])
def edit():
    sheet = get_sheet()
    if not sheet:
        return redirect(url_for("index"))

    row_index = int(request.form.get("row_index", 0))
    edit_mode = request.form.get("edit_mode", "")
    freq = int(request.form.get("edit_freq", "12"))

    if row_index < 2:
        return redirect(url_for("index"))

    # ヘッダーから列番号を動的取得
    headers = sheet.row_values(1)
    col = {h: i + 1 for i, h in enumerate(headers)}

    try:
        if edit_mode == "url":
            new_url = request.form.get("edit_url", "").strip()
            if new_url and 'url' in col:
                sheet.update_cell(row_index, col['url'], new_url)
        else:
            new_word = request.form.get("edit_word", "").strip()
            new_memo = request.form.get("edit_memo", "").strip()
            if new_word and 'word' in col:
                sheet.update_cell(row_index, col['word'], new_word)
            if new_memo and 'memo' in col:
                sheet.update_cell(row_index, col['memo'], new_memo)
            # キーワードかメモが変わったらURLを即時再生成
            if (new_word or new_memo) and 'url' in col:
                # 現在の値を取得（変更されていない方）
                current_row = sheet.row_values(row_index)
                word_val = new_word or (current_row[col['word'] - 1] if len(current_row) >= col['word'] else "")
                memo_val = new_memo or (current_row[col['memo'] - 1] if len(current_row) >= col['memo'] else "")
                if word_val and memo_val and memo_val != "HP更新":
                    generated_url = generate_url_now(word_val, memo_val)
                    sheet.update_cell(row_index, col['url'], generated_url)

        # 頻度列（countまたはfreq）
        freq_col = col.get('count') or col.get('freq')
        if freq_col:
            sheet.update_cell(row_index, freq_col, freq)
    except Exception:
        pass

    return redirect(url_for("index"))


@app.route("/delete/<int:row_index>", methods=["POST"])
def delete(row_index):
    sheet = get_sheet()
    if sheet:
        try:
            sheet.delete_rows(row_index)
        except Exception:
            pass
    return redirect(url_for("index"))


# ============================================================
# TTS (Text-to-Speech) 機能
# ============================================================

# 日本語音声の定義
TTS_VOICES = [
    {"id": "ja-JP-NanamiNeural",   "name": "Nanami (女性)", "gender": "Female"},
    {"id": "ja-JP-KeitaNeural",    "name": "Keita (男性)",  "gender": "Male"},
    {"id": "ja-JP-AoiNeural",      "name": "Aoi (女性)",    "gender": "Female"},
    {"id": "ja-JP-DaichiNeural",   "name": "Daichi (男性)", "gender": "Male"},
    {"id": "ja-JP-MayuNeural",     "name": "Mayu (女性)",   "gender": "Female"},
    {"id": "ja-JP-NaokiNeural",    "name": "Naoki (男性)",  "gender": "Male"},
    {"id": "ja-JP-ShioriNeural",   "name": "Shiori (女性)", "gender": "Female"},
]


@app.route("/tts")
def tts_page():
    return render_template("tts.html", voices=TTS_VOICES)


@app.route("/tts/generate", methods=["POST"])
def tts_generate():
    text = request.form.get("text", "").strip()
    voice = request.form.get("voice", "ja-JP-NanamiNeural")
    rate = request.form.get("rate", "+0%")
    pitch = request.form.get("pitch", "+0Hz")

    if not text:
        return Response("テキストが空です", status=400)

    # 最大文字数制限（無料サービスなので）
    if len(text) > 5000:
        return Response("テキストは5000文字以内にしてください", status=400)

    # voice IDのバリデーション
    valid_ids = {v["id"] for v in TTS_VOICES}
    if voice not in valid_ids:
        voice = "ja-JP-NanamiNeural"

    tmp_path = None
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tmp_path = tmp.name
        tmp.close()

        async def _generate():
            communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
            await communicate.save(tmp_path)

        asyncio.run(_generate())

        # ファイルをメモリに読み込んでから返す
        with open(tmp_path, "rb") as f:
            audio_data = f.read()

        return Response(
            audio_data,
            mimetype="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=tts_output.mp3"},
        )
    except Exception as e:
        return Response(f"音声生成エラー: {e}", status=500)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
