import os, base64, json, gspread, re
from oauth2client.service_account import ServiceAccountCredentials

def main():
    encoded_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not encoded_json:
        print("Error: GOOGLE_SERVICE_ACCOUNT_JSON is empty.")
        return

    try:
        # 1. Base64デコード（余計な改行やゴミを掃除して解凍）
        clean_b64 = re.sub(r'[^A-Za-z0-9+/=]', '', encoded_json)
        creds_dict = json.loads(base64.b64decode(clean_b64).decode('utf-8'))
        
        # 2. 秘密鍵の改行補正
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

        # 3. 認証と接続確認
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key("1wSfyGreLH_lb7vR_vpmuJ3rAndtMNvMDQbv2ZlPVxUE").sheet1
        print("Successfully connected to the sheet!")
        
    except Exception as e:
        print(f"Authentication Error: {e}")

if __name__ == "__main__":
    main()
