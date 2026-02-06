import os, base64, json, re
import gspread
import google.generativeai as genai
from google.oauth2.service_account import Credentials

def main():
    encoded = os.environ.get("GCP_JSON")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    
    if not encoded or not gemini_key:
        print("Error: Missing environment variables.")
        return

    try:
        # --- 認証処理 (最新ライブラリ版) ---
        # 1. Base64のゴミを除去してデコード
        clean_b64 = re.sub(r'[^A-Za-z0-9+/=]', '', encoded)
        creds_json = base64.b64decode(clean_b64).decode('utf-8')
        creds_dict = json.loads(creds_json)

        # 2. 秘密鍵の改行コードを正規化
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

        # 3. モダンな認証クラスで接続
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        # スプレッドシートを開く
        sheet = client.open_by_key("1wSfyGreLH_lb7vR_vpmuJ3rAndtMNvMDQbv2ZlPVxUE").sheet1
        print("Successfully connected via google-auth!")
        
        # --- URL生成処理 ---
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        data = sheet.get_all_records()
        for i, row in enumerate(data, start=2):
            current_url = str(row.get('url', '')).strip()
            # URLが空、または http で始まらない場合に生成
            if not current_url.startswith('http'):
                word, memo = row.get('word'), row.get('memo')
                print(f"Generating URL for: {word}")
                
                prompt = f"「{word}」を「{memo}」で検索するためのURLを1つ出力してください。URLのみを返してください。"
                try:
                    response = model.generate_content(prompt)
                    new_url = response.text.strip()
                    sheet.update_cell(i, 2, new_url)
                    print(f" -> Updated row {i}: {new_url}")
                except Exception as e:
                    print(f" -> Gemini Error on row {i}: {e}")

        print("All Done.")
        
    except Exception as e:
        print(f"Fatal Error: {e}")

if __name__ == "__main__":
    main()
