import os, json, gspread
from oauth2client.service_account import ServiceAccountCredentials

def main():
    # 1. 環境変数からJSONを直接読み込む
    raw_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw_json:
        print("Error: GOOGLE_SERVICE_ACCOUNT_JSON is empty.")
        return

    try:
        # 2. JSONを解析し、秘密鍵の改行を補正
        creds_dict = json.loads(raw_json)
        if "private_key" in creds_dict:
            # 秘密鍵内の \n 文字を実際の改行に変換
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

        # 3. 認証
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # 4. 接続確認
        sheet = client.open_by_key("1wSfyGreLH_lb7vR_vpmuJ3rAndtMNvMDQbv2ZlPVxUE").sheet1
        print("Successfully connected to the sheet!")
        
    except Exception as e:
        print(f"Authentication Error: {e}")

if __name__ == "__main__":
    main()
