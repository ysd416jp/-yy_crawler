import os, json, gspread
from oauth2client.service_account import ServiceAccountCredentials

def main():
    # 1. ワークフロー設定で指定した「GCP_JSON」を読み込む
    raw_json = os.environ.get("GCP_JSON")
    
    if not raw_json:
        print("Authentication Error: No key could be detected.")
        return

    try:
        # 2. JSONを解析し、秘密鍵の改行コードを正常化
        creds_dict = json.loads(raw_json)
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

        # 3. 認証
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
