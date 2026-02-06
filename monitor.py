import os, json, base64, re
import gspread
import google.generativeai as genai
from google.oauth2.service_account import Credentials

def main():
    print("--- Starting Monitor Script (Modern Auth) ---")
    raw_key = os.environ.get("GCP_JSON")
    gemini_key = os.environ.get("GEMINI_API_KEY")

    if not raw_key or not gemini_key:
        print("Error: Environment variables missing.")
        return

    try:
        # 鍵データのクリーニングと読み込み
        # Base64でも生JSONでも対応できるロジック
        cleaned_key = re.sub(r'[^A-Za-z0-9+/={}:",_\-\n]', '', raw_key)
        if cleaned_key.strip().startswith('{'):
            creds_info = json.loads(cleaned_key)
        else:
            # Base64の場合
            decoded_bytes = base64.b64decode(cleaned_key)
            creds_info = json.loads(decoded_bytes.decode('utf-8'))

        # 最新ライブラリで認証（改行コード問題は自動解決される）
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        client = gspread.authorize(creds)
        
        # スプレッドシート接続
        sheet = client.open_by_key("1wSfyGreLH_lb7vR_vpmuJ3rAndtMNvMDQbv2ZlPVxUE").sheet1
        print("Auth Success: Connected to Google Sheets via google-auth!")

        # URL生成ロジック
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        rows = sheet.get_all_records()
        for i, row in enumerate(rows, start=2):
            url_cell = str(row.get('url', '')).strip()
            if not url_cell.startswith('http'):
                word = row.get('word')
                print(f"Generating URL for: {word}")
                try:
                    prompt = f"「{word}」の検索URLを1つ出力してください(URLのみ)。"
                    res = model.generate_content(prompt)
                    new_url = res.text.strip()
                    sheet.update_cell(i, 2, new_url)
                    print(f" -> Updated: {new_url}")
                except Exception as e:
                    print(f" -> Gen Error: {e}")

        print("--- Process Completed Successfully ---")

    except Exception as e:
        # 新しいライブラリのエラー詳細を表示
        print(f"Fatal Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    main()
