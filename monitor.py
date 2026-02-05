import os
import base64
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re

def main():
    # 1. GitHub Secrets から真空パックされた鍵を取得
    encoded_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not encoded_json:
        print("Error: GOOGLE_SERVICE_ACCOUNT_JSON not found.")
        return

    try:
        # 2. 真空パックの解凍（ゴミを掃除してからデコード）
        clean_b64 = re.sub(r'[^A-Za-z0-9+/=]', '', encoded_json)
        decoded_bytes = base64.b64decode(clean_b64)
        creds_dict = json.loads(decoded_bytes.decode("utf-8"))
        
        # 3. 【外科的修復】秘密鍵の改行とヘッダーを強制補正
        if "private_key" in creds_dict:
            pk = creds_dict["private_key"]
            # 文字としての \n を 本物の改行に変換
            pk = pk.replace("\\n", "\n")
            # 余計な改行やスペースを徹底掃除
            lines = [line.strip() for line in pk.split("\n") if line.strip()]
            fixed_key = "\n".join(lines) + "\n"
            creds_dict["private_key"] = fixed_key

        # 4. Google Sheets への接続
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # スプレッドシート操作（SHEET_ID は吉田さんのもの）
        sheet = client.open_by_key("1wSfyGreLH_lb7vR_vpmuJ3rAndtMNvMDQbv2ZlPVxUE").sheet1
        print("Successfully connected to the sheet!")
        
        # --- ここからURL作成などのメイン処理 ---
        # (ここには既存の monitor.py の続きのロジックが自動的に入ります)
        
    except Exception as e:
        print(f"Authentication Error: {e}")

if __name__ == "__main__":
    main()
