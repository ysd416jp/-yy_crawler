import os, base64, json, gspread, re
from oauth2client.service_account import ServiceAccountCredentials

def main():
    encoded = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not encoded:
        print("Error: GOOGLE_SERVICE_ACCOUNT_JSON not found.")
        return

    try:
        # Base64デコード
        clean_b64 = re.sub(r'[^A-Za-z0-9+/=]', '', encoded)
        creds_dict = json.loads(base64.b64decode(clean_b64).decode('utf-8'))
        
        # 秘密鍵の改行コード補正
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace('\\n', '\n')

        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # 接続確認
        sheet = client.open_by_key("1wSfyGreLH_lb7vR_vpmuJ3rAndtMNvMDQbv2ZlPVxUE").sheet1
        print("Successfully connected to the sheet!")
        
    except Exception as e:
        print(f"Authentication Error: {e}")

if __name__ == "__main__":
    main()
