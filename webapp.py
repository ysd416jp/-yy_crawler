"""Web更新チェッカー — Flask版"""
import os
import json
import base64
import re
import gspread
from google.oauth2.service_account import Credentials
from flask import Flask, render_template, request, redirect, url_for, Response
from urllib.parse import quote

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


# --- 検索URLテンプレート（monitor.pyと共通） ---
SEARCH_TEMPLATES = {
    "jalan":     "https://www.jalan.net/uw/uwp3200/uww3201init.do?keyword={word}",
    "hotpepper": "https://www.hotpepper.jp/CSP/psh/rstLst/00/?keyword={word}",
    "indeed":    "https://jp.indeed.com/jobs?q={word}",
    "townwork":  "https://townwork.net/joSrchRsltList/?fw={word}",
    "x":         "https://x.com/search?q={word}",
}


def generate_url_now(word, memo):
    """検索URLを即時生成（テンプレート優先、未知サイトはGemini）"""
    memo_lower = memo.strip().lower()

    # テンプレートにあるサイト
    if memo_lower in SEARCH_TEMPLATES:
        return SEARCH_TEMPLATES[memo_lower].format(word=quote(word))

    # Geminiで生成
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        return ""

    try:
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = (
            f"「{memo}」のサイト内検索で「{word}」を検索した結果ページのURLを"
            f"1つだけ出力してください。URLのみを出力し、説明は不要です。"
        )
        res = model.generate_content(prompt)
        return res.text.strip()
    except Exception:
        return ""


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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
