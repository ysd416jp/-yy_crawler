import os, base64, json, gspread, re
import google.generativeai as genai
from oauth2client.service_account import ServiceAccountCredentials

def main():
    # 診断ログで成功が確認できた「GCP_JSON」を使用
    encoded = os.environ.get("GCP_JSON")
    gemini_key = os.environ.get("GEMINI_API_KEY")

    if not encoded or not gemini_key:
        print("Error: Environment variables are missing.")
        return

    try:
        # 1. 認証（Base64デコードと改行補正）
        clean_b64 = re.sub(r'[^A-Za-z0-9+/=]', '', encoded)
        creds_dict = json.loads(base64.b64decode(clean_b64).decode('utf-8'))
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

        # 2. Google Sheet 接続
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        # 吉田さんのスプレッドシートIDを指定
        sheet = client.open_by_key("1wSfyGreLH_lb7vR_vpmuJ3rAndtMNvMDQbv2ZlPVxUE").sheet1
        
        # 3. AI (Gemini) 設定
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        # 4. 未処理の行（url列が空、またはhttpでない）を処理
        data = sheet.get_all_records()
        for i, row in enumerate(data, start=2):
            url_val = str(row.get('url', '')).strip()
            if not url_val.startswith('http'):
                word = row.get('word')
                memo = row.get('memo')
                print(f"Generating URL for: {word} ({memo})")
                
                prompt = f"「{word}」を「{memo}」で検索するためのGoogle検索URL、またはサイト内検索URLを1つだけ出力してください。URLのみを返し、説明は不要です。"
                response = model.generate_content(prompt)
                new_url = response.text.strip()
                
                # B列(2列目)を更新
                sheet.update_cell(i, 2, new_url)
                print(f"Updated row {i} with: {new_url}")

        print("Successfully processed all rows.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
