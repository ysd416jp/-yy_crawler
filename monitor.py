import os, json, base64, re, hashlib
import gspread
import google.generativeai as genai
from google.oauth2.service_account import Credentials
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

# --- 検索URLテンプレート（既知サイトはGemini不要） ---
SEARCH_TEMPLATES = {
    "jalan":     "https://www.jalan.net/uw/uwp3200/uww3201init.do?keyword={word}",
    "hotpepper": "https://www.hotpepper.jp/CSP/psh/rstLst/00/?keyword={word}",
    "indeed":    "https://jp.indeed.com/jobs?q={word}",
    "townwork":  "https://townwork.net/joSrchRsltList/?fw={word}",
    "x":         "https://x.com/search?q={word}",
}

# --- 軽微変更の閾値 ---
MIN_CHANGE_CHARS = 50
MIN_CHANGE_RATIO = 0.05


def get_credentials():
    """GitHub Secret / 環境変数からGCP認証情報を取得"""
    raw_val = os.environ.get("GCP_JSON") or os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw_val:
        raise RuntimeError("GCP_JSON が未設定")

    cleaned_val = re.sub(r'[\s\n]', '', raw_val)

    if cleaned_val.startswith('{'):
        creds_info = json.loads(cleaned_val)
    else:
        missing_padding = len(cleaned_val) % 4
        if missing_padding:
            cleaned_val += '=' * (4 - missing_padding)
        creds_info = json.loads(base64.b64decode(cleaned_val).decode('utf-8'))

    if 'private_key' in creds_info:
        creds_info['private_key'] = creds_info['private_key'].replace('\\n', '\n')

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


def check_site_update(sheet, row_index, row):
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

    if not prev_hash:
        # 初回: ハッシュだけ保存して終了
        sheet.update_cell(row_index, 5, current_hash)
        print(f"  行{row_index}: 初回チェック、ハッシュ保存")
        return

    if current_hash == prev_hash:
        print(f"  行{row_index}: 変更なし")
        return

    # --- 差分量を計算 ---
    change_chars = abs(len(current_text) - len(prev_hash))  # 大まかな差分
    # より正確にはdifflibを使うが、前回テキスト全文は保存していないので
    # テキスト長の差で簡易判定する
    total_chars = max(len(current_text), 1)

    # 前回テキスト長は保存していないので、ハッシュが変わった＝何か変わった
    # ここではテキスト長の変化だけでは不十分なので、常に通知する方針とし、
    # 代わりにノイズ除去（script/style/nav等の除外）で軽微変更を減らす
    # ただし初回以降は前回テキスト長を6列目に保存して比較する
    prev_len_str = str(row.get('prev_len', '')).strip()
    if prev_len_str and prev_len_str.isdigit():
        prev_len = int(prev_len_str)
        change_chars = abs(len(current_text) - prev_len)
        change_ratio = change_chars / max(prev_len, 1)

        if change_chars < MIN_CHANGE_CHARS and change_ratio < MIN_CHANGE_RATIO:
            print(f"  行{row_index}: 軽微変更（{change_chars}文字, {change_ratio:.1%}）スキップ")
            sheet.update_cell(row_index, 5, current_hash)
            sheet.update_cell(row_index, 6, str(len(current_text)))
            return

    # --- 通知 ---
    word = row.get('word', '')
    msg = f"🔔 サイト更新検知\n{word}\n変更量: 約{change_chars}文字\n{url}"
    send_line_notification(msg)
    print(f"  行{row_index}: 更新検知 → LINE通知")

    # ハッシュとテキスト長を更新
    sheet.update_cell(row_index, 5, current_hash)
    sheet.update_cell(row_index, 6, str(len(current_text)))


def generate_search_url(sheet, row_index, row, gemini_model):
    """キーワード検索URL生成（テンプレート優先、未知サイトはGemini）"""
    url_cell = str(row.get('url', '')).strip()
    if url_cell.startswith('http'):
        return  # 既にURLあり

    word = str(row.get('word', '')).strip()
    memo = str(row.get('memo', '')).strip().lower()

    if not word:
        return

    # テンプレートにあるサイトはそれを使う
    if memo in SEARCH_TEMPLATES:
        new_url = SEARCH_TEMPLATES[memo].format(word=quote(word))
        sheet.update_cell(row_index, 2, new_url)
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
        sheet.update_cell(row_index, 2, new_url)
        print(f"  行{row_index}: Gemini URL生成 → {new_url}")
    except Exception as e:
        print(f"  行{row_index}: Gemini生成エラー: {e}")


def main():
    print("--- 処理開始 ---")

    try:
        creds = get_credentials()
        client = gspread.authorize(creds)
        sheet = client.open_by_key("1wSfyGreLH_lb7vR_vpmuJ3rAndtMNvMDQbv2ZlPVxUE").sheet1
        print("認証成功")

        # Geminiモデル（キーがあれば）
        gemini_key = os.environ.get("GEMINI_API_KEY")
        gemini_model = None
        if gemini_key:
            genai.configure(api_key=gemini_key)
            gemini_model = genai.GenerativeModel('gemini-1.5-flash')

        rows = sheet.get_all_records()
        for i, row in enumerate(rows, start=2):
            memo = str(row.get('memo', '')).strip()

            if memo == "HP更新":
                # サイト更新チェック
                check_site_update(sheet, i, row)
            else:
                # キーワード検索URL生成
                generate_search_url(sheet, i, row, gemini_model)

        print("--- 全処理完了 ---")

    except Exception as e:
        print(f"致命的なエラー: {e}")


if __name__ == "__main__":
    main()
