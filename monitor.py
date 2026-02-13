import os, json, base64, re, hashlib
import gspread
import google.generativeai as genai
from google.oauth2.service_account import Credentials
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

# --- 検索URLテンプレート（既知サイトはGemini不要） ---
# キー: 日本語名・英語名・略称など複数登録して柔軟にマッチ
SEARCH_TEMPLATES = {
    # グルメ
    "食べログ":           "https://tabelog.com/keywords/{word}/kwdLst/",
    "tabelog":            "https://tabelog.com/keywords/{word}/kwdLst/",
    "ホットペッパーグルメ": "https://www.hotpepper.jp/CSP/psh/rstLst/00/?keyword={word}",
    "ホットペッパー":      "https://www.hotpepper.jp/CSP/psh/rstLst/00/?keyword={word}",
    "hotpepper":          "https://www.hotpepper.jp/CSP/psh/rstLst/00/?keyword={word}",
    "ぐるなび":           "https://r.gnavi.co.jp/eki/result/?freeword={word}",
    "gnavi":              "https://r.gnavi.co.jp/eki/result/?freeword={word}",
    "retty":              "https://retty.me/search/?keyword={word}",
    # 旅行・宿泊
    "jalan":              "https://www.jalan.net/uw/uwp3200/uww3201init.do?keyword={word}",
    "じゃらん":           "https://www.jalan.net/uw/uwp3200/uww3201init.do?keyword={word}",
    "楽天トラベル":        "https://search.travel.rakuten.co.jp/ds/hotellist/search?f_free_word={word}",
    "rakuten travel":     "https://search.travel.rakuten.co.jp/ds/hotellist/search?f_free_word={word}",
    "booking.com":        "https://www.booking.com/searchresults.html?ss={word}",
    "booking":            "https://www.booking.com/searchresults.html?ss={word}",
    # 求人
    "indeed":             "https://jp.indeed.com/jobs?q={word}",
    "townwork":           "https://townwork.net/joSrchRsltList/?fw={word}",
    "タウンワーク":        "https://townwork.net/joSrchRsltList/?fw={word}",
    "リクナビnext":       "https://next.rikunabi.com/search/?freeWordKey={word}",
    "マイナビ転職":        "https://tenshoku.mynavi.jp/list/kw{word}/",
    "doda":               "https://doda.jp/keyword/{word}/",
    # SNS・検索
    "x":                  "https://x.com/search?q={word}",
    "twitter":            "https://x.com/search?q={word}",
    "youtube":            "https://www.youtube.com/results?search_query={word}",
    "google":             "https://www.google.com/search?q={word}",
    "bing":               "https://www.bing.com/search?q={word}",
    # ショッピング
    "amazon":             "https://www.amazon.co.jp/s?k={word}",
    "アマゾン":           "https://www.amazon.co.jp/s?k={word}",
    "楽天市場":           "https://search.rakuten.co.jp/search/mall/{word}/",
    "rakuten":            "https://search.rakuten.co.jp/search/mall/{word}/",
    "メルカリ":           "https://jp.mercari.com/search?keyword={word}",
    "mercari":            "https://jp.mercari.com/search?keyword={word}",
    "yahoo!ショッピング":  "https://shopping.yahoo.co.jp/search?p={word}",
    "yahooショッピング":   "https://shopping.yahoo.co.jp/search?p={word}",
    # 不動産
    "suumo":              "https://suumo.jp/jj/common/ichiran/JJ010FJ001/?fw={word}",
    "スーモ":             "https://suumo.jp/jj/common/ichiran/JJ010FJ001/?fw={word}",
    "homes":              "https://www.homes.co.jp/chintai/theme/keyword={word}/",
    # ニュース
    "yahoo!ニュース":      "https://news.yahoo.co.jp/search?p={word}",
    "yahooニュース":       "https://news.yahoo.co.jp/search?p={word}",
    "nhk":                "https://www3.nhk.or.jp/news/json/search/2.0/search.json?q={word}",
}

# --- 軽微変更の閾値 (大規模サイトのみ適用) ---
MIN_CHANGE_CHARS = 50
MIN_CHANGE_RATIO = 0.05
# テキスト量がこの値以下なら軽微変更フィルタを無効にする
# (ニュースサイトのトップ等、テキスト量が少ないがコンテンツが入れ替わるもの)
SMALL_PAGE_THRESHOLD = 5000


def get_credentials():
    """GitHub Secret / 環境変数からGCP認証情報を取得"""
    raw_val = os.environ.get("GCP_JSON") or os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw_val:
        raise RuntimeError("GCP_JSON が未設定")

    raw_stripped = raw_val.strip()

    if raw_stripped.startswith('{'):
        # JSON形式の場合、そのままパース（空白を消さない）
        creds_info = json.loads(raw_stripped)
    else:
        # Base64形式の場合
        cleaned_val = re.sub(r'[\s\n]', '', raw_val)
        missing_padding = len(cleaned_val) % 4
        if missing_padding:
            cleaned_val += '=' * (4 - missing_padding)
        creds_info = json.loads(base64.b64decode(cleaned_val).decode('utf-8'))

    # private_keyの改行修復
    if 'private_key' in creds_info:
        pk = creds_info['private_key']
        # エスケープされた \n を実際の改行に変換
        if '\\n' in pk:
            pk = pk.replace('\\n', '\n')
        # 末尾に改行がなければ追加
        if not pk.endswith('\n'):
            pk += '\n'
        creds_info['private_key'] = pk

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    return Credentials.from_service_account_info(creds_info, scopes=scopes)


def send_line_notification(message):
    """LINE Messaging APIでプッシュ通知を送る"""
    token = os.environ.get("LINE_CHANNEL_TOKEN")
    user_id = os.environ.get("LINE_USER_ID")
    if not token or not user_id:
        print("LINE通知スキップ: TOKEN/USER_IDが未設定")
        return

    resp = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        json={
            "to": user_id,
            "messages": [{"type": "text", "text": message}],
        },
    )
    if resp.status_code == 200:
        print(f"LINE通知送信OK")
    else:
        print(f"LINE通知エラー: {resp.status_code} {resp.text}")


def extract_body_text(html):
    """HTMLから本文テキストだけ抽出（ノイズ除去）"""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "iframe"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


def get_col_index(headers, name):
    """ヘッダー名から1-based列番号を取得"""
    try:
        return headers.index(name) + 1
    except ValueError:
        return None


def check_site_update(sheet, row_index, row, col_map):
    """サイト更新チェック。軽微変更はスキップ、閾値超えたらLINE通知"""
    url = str(row.get('url', '')).strip()
    if not url.startswith('http'):
        print(f"  行{row_index}: URLが未設定、スキップ")
        return

    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "web-watcher/1.0"})
        resp.raise_for_status()
    except Exception as e:
        print(f"  行{row_index}: HTML取得失敗 ({e})")
        return

    current_text = extract_body_text(resp.text)
    current_hash = hashlib.sha256(current_text.encode()).hexdigest()

    prev_hash = str(row.get('prev_hash', '')).strip()

    col_prev_hash = col_map.get('prev_hash')
    col_prev_len = col_map.get('prev_len')

    if not prev_hash:
        if col_prev_hash:
            sheet.update_cell(row_index, col_prev_hash, current_hash)
        if col_prev_len:
            sheet.update_cell(row_index, col_prev_len, str(len(current_text)))
        print(f"  行{row_index}: 初回チェック、ハッシュ保存")
        return

    if current_hash == prev_hash:
        print(f"  行{row_index}: 変更なし")
        return

    # --- 差分量を計算 ---
    prev_len_str = str(row.get('prev_len', '')).strip()
    current_len = len(current_text)
    change_chars = abs(current_len - (int(prev_len_str) if prev_len_str.isdigit() else 0))

    # 大きいページのみ軽微変更フィルタを適用
    # 小さいページ（ニュースサイトトップ等）はハッシュ変化で即通知
    if prev_len_str and prev_len_str.isdigit():
        prev_len = int(prev_len_str)
        if prev_len > SMALL_PAGE_THRESHOLD:
            change_ratio = change_chars / max(prev_len, 1)
            if change_chars < MIN_CHANGE_CHARS and change_ratio < MIN_CHANGE_RATIO:
                print(f"  行{row_index}: 軽微変更（{change_chars}文字, {change_ratio:.1%}）スキップ")
                if col_prev_hash:
                    sheet.update_cell(row_index, col_prev_hash, current_hash)
                if col_prev_len:
                    sheet.update_cell(row_index, col_prev_len, str(current_len))
                return

    # --- 通知 ---
    word = str(row.get('word', ''))
    memo = str(row.get('memo', ''))
    if memo == "HP更新":
        label = url
    else:
        label = f"{word}（{memo}）"
    msg = f"🔔 サイト更新検知\n{label}\n{url}"
    send_line_notification(msg)
    print(f"  行{row_index}: 更新検知 → LINE通知")

    if col_prev_hash:
        sheet.update_cell(row_index, col_prev_hash, current_hash)
    if col_prev_len:
        sheet.update_cell(row_index, col_prev_len, str(current_len))


def find_template(memo):
    """メモからテンプレートを検索（完全一致→部分一致）"""
    memo_clean = memo.strip().lower()
    # 完全一致
    if memo_clean in SEARCH_TEMPLATES:
        return SEARCH_TEMPLATES[memo_clean]
    # 部分一致（テンプレートキーがメモに含まれる or メモがキーに含まれる）
    for key, tmpl in SEARCH_TEMPLATES.items():
        if key in memo_clean or memo_clean in key:
            return tmpl
    return None


def generate_search_url(sheet, row_index, row, gemini_model, col_map):
    """キーワード検索URL生成（テンプレート優先、未知サイトはGemini）"""
    url_cell = str(row.get('url', '')).strip()
    if url_cell.startswith('http'):
        return  # 既にURLあり

    word = str(row.get('word', '')).strip()
    memo = str(row.get('memo', '')).strip()
    col_url = col_map.get('url', 2)

    if not word:
        return

    # テンプレートにあるサイトはそれを使う
    tmpl = find_template(memo)
    if tmpl:
        new_url = tmpl.format(word=quote(word))
        sheet.update_cell(row_index, col_url, new_url)
        print(f"  行{row_index}: テンプレートURL生成 → {new_url}")
        return

    # 未知サイトはGeminiにフォールバック
    if not gemini_model:
        print(f"  行{row_index}: Gemini未設定、スキップ")
        return

    try:
        prompt = (
            f"「{memo}」のサイト内検索で「{word}」を検索した結果ページのURLを"
            f"1つだけ出力してください。URLのみを出力し、説明は不要です。"
        )
        res = gemini_model.generate_content(prompt)
        new_url = res.text.strip()
        sheet.update_cell(row_index, col_url, new_url)
        print(f"  行{row_index}: Gemini URL生成 → {new_url}")
    except Exception as e:
        print(f"  行{row_index}: Gemini生成エラー: {e}")


def should_run_now(row, current_hour):
    """頻度設定に基づいて今実行すべきかを判定"""
    freq_key = 'count' if 'count' in row else 'freq'
    try:
        freq = int(row.get(freq_key, 1))
    except (ValueError, TypeError):
        freq = 1
    if freq <= 0:
        freq = 1
    return (current_hour % freq) == 0


def main():
    print("--- 処理開始 ---")

    try:
        creds = get_credentials()
        client = gspread.authorize(creds)
        sheet = client.open_by_key("1wSfyGreLH_lb7vR_vpmuJ3rAndtMNvMDQbv2ZlPVxUE").sheet1
        print("認証成功")

        # ヘッダー取得 & 列マップ作成
        headers = sheet.row_values(1)
        col_map = {h: i + 1 for i, h in enumerate(headers)}
        print(f"ヘッダー: {headers}")

        # prev_hash, prev_lenがなければ自動追加
        if "prev_hash" not in col_map:
            idx = len(headers) + 1
            sheet.update_cell(1, idx, "prev_hash")
            col_map["prev_hash"] = idx
            headers.append("prev_hash")
            print("ヘッダーに prev_hash を追加")
        if "prev_len" not in col_map:
            idx = len(headers) + 1
            sheet.update_cell(1, idx, "prev_len")
            col_map["prev_len"] = idx
            headers.append("prev_len")
            print("ヘッダーに prev_len を追加")

        # Geminiモデル（キーがあれば）
        gemini_key = os.environ.get("GEMINI_API_KEY")
        gemini_model = None
        if gemini_key:
            genai.configure(api_key=gemini_key)
            gemini_model = genai.GenerativeModel('gemini-2.5-flash')

        # 現在の時刻（UTC）
        from datetime import datetime, timezone
        current_hour = datetime.now(timezone.utc).hour

        rows = sheet.get_all_records()
        for i, row in enumerate(rows, start=2):
            memo = str(row.get('memo', '')).strip()

            # URL未生成の検索監視は頻度に関係なく常に生成を試みる
            if memo != "HP更新":
                url_cell = str(row.get('url', '')).strip()
                if not url_cell.startswith('http'):
                    generate_search_url(sheet, i, row, gemini_model, col_map)
                    continue

            # 頻度チェック（URL生成済みの監視・HP更新のみ）
            if not should_run_now(row, current_hour):
                print(f"  行{i}: 頻度スキップ")
                continue

            if memo == "HP更新":
                check_site_update(sheet, i, row, col_map)
            else:
                # URL生成済みなら更新チェック
                check_site_update(sheet, i, row, col_map)

        print("--- 全処理完了 ---")

    except Exception as e:
        print(f"致命的なエラー: {e}")


if __name__ == "__main__":
    main()
