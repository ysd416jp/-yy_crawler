import os
import base64
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def main():
    # 1. GitHub Secrets から真空パックされた鍵を取得
    encoded_json = os.environ.get("GCP_SA_KEY")
    if not encoded_json:
        print("Error: GCP_SA_KEY not found in environment variables.")
        return

    # 2. 解凍（Base64デコード）
    try:
        decoded_bytes = base64.b64decode(encoded_json)
        creds_dict = json.loads(decoded_bytes.decode("utf-8"))
        
        # 3. 秘密鍵の改行を強制補正（念のため）
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # スプレッドシート操作（SHEET_IDは既存のものを使用）
        sheet = client.open_by_key("1wSfyGreLH_lb7vR_vpmuJ3rAndtMNvMDQbv2ZlPVxUE").sheet1
        print("Successfully connected to the sheet!")
        
        # ここにURL作成ロジックが続く...（既存の処理を維持）
        
    except Exception as e:
        print(f"Authentication Error: {e}")

if __name__ == "__main__":
    main()
