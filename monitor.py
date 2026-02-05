import os, base64, json, gspread, re
from oauth2client.service_account import ServiceAccountCredentials

def main():
    encoded = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not encoded:
        print("Error: GOOGLE_SERVICE_ACCOUNT_JSON is empty.")
        return

    try:
        # 1. Base64デコード（非ASCII文字を完全除去して解凍）
        clean_b64 = re.sub(r'[^A-Za-z0-9+/=]', '', encoded)
        creds_dict = json.loads(base64.b64decode(clean_b64).decode('utf-8'))
        
        # 2. 秘密鍵の「文字としての\n」を「実際の改行」へ厳密に置換
        if "private_key" in creds_dict:
            pk = creds_dict["private_key"]
            # 既存の改行を削除し、エスケープされた\nを本物の改行に戻す
            pk = pk.replace("\n", "").replace("\\n", "\n")
            creds_dict["private_key"] = pk

        # 3. 認証実行
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # 4. 接続テスト
        sheet = client.open_by_key("1wSfyGreLH_lb7vR_vpmuJ3rAndtMNvMDQbv2ZlPVxUE").sheet1
        print("Successfully connected to the sheet!")
        
    except Exception as e:
        print(f"Authentication Error: {e}")

if __name__ == "__main__":
    main()
