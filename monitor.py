import os, json, hashlib, requests, gspread
from google import genai
from oauth2client.service_account import ServiceAccountCredentials
from linebot import LineBotApi
from linebot.models import TextSendMessage

# 鍵の読み込み（GitHub Secrets からの注入を想定）
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
LINE_TOKEN = os.environ.get("LINE_ACCESS_TOKEN")
USER_ID = os.environ.get("LINE_USER_ID")
SERVICE_ACCOUNT_JSON = json.loads(os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON"))
SHEET_ID = "1wSfyGreLH_lb7vR_vpmuJ3rAndtMNvMDQbv2ZlPVxUE"

def main():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(SERVICE_ACCOUNT_JSON, scope)
    client_gs = gspread.authorize(creds)
    sheet = client_gs.open_by_key(SHEET_ID).sheet1
    data = sheet.get_all_values()
    client_ai = genai.Client(api_key=GEMINI_API_KEY)
    line_bot_api = LineBotApi(LINE_TOKEN)
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

    for i, row in enumerate(data[1:], start=2):
        word, current_url, memo = row[0], row[1], row[2]
        old_hash = row[4] if len(row) > 4 else ""
        if not word: continue

        # --- 検証済み：AIによる自律的ドメイン推論 ---
        if not current_url and memo and memo != "HP更新":
            try:
                prompt = (
                    f"タスク：サービス名『{memo}』からドメインを特定し、"
                    f"キーワード『{word}』を24時間以内の新着に絞って検索するGoogle検索URLを1つ生成せよ。\n"
                    f"制約：適切なドメイン（indeed.com等）に自力で変換し、回答はURLのみとすること。"
                )
                response = client_ai.models.generate_content(
                    model="gemini-3-flash-preview", 
                    contents=prompt
                )
                url = response.text.strip().replace("`", "")
                if "http" in url:
                    current_url = url
                    sheet.update_cell(i, 2, current_url)
                    print(f"Row {i}: URL Evolved -> {current_url}")
            except Exception as e: print(f"Row {i} Gemini Error: {e}")

        if not current_url: continue

        # 巡回監視とLINE通知
        try:
            res = requests.get(current_url, headers=headers, timeout=20)
            res.encoding = res.apparent_encoding
            new_hash = hashlib.md5(res.text.encode()).hexdigest()
            exclude = ["一致する情報は見つかりませんでした", "0件", "見つかりませんでした"]
            if word in res.text and not any(ex in res.text for ex in exclude):
                if new_hash != old_hash:
                    msg = f"【発見】{word} ({memo})\n{current_url}"
                    line_bot_api.push_message(USER_ID, TextSendMessage(text=msg))
                    sheet.update_cell(i, 5, new_hash)
        except Exception as e: print(f"Row {i} Net Error: {e}")

if __name__ == "__main__": main()
