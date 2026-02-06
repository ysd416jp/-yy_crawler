import os, json, base64, re
import gspread
import google.generativeai as genai
from google.oauth2.service_account import Credentials

def main():
    print("--- 処理開始 ---")
    
    # 1. GitHub Secret を取得
    raw_val = os.environ.get("GCP_JSON") or os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    gemini_key = os.environ.get("GEMINI_API_KEY")

    if not raw_val or not gemini_key:
        print("エラー: 必要なキーが見つかりません。")
        return

    try:
        # 2. キーの判別と解凍 (ここがループの原因でした)
        # 余計な空白や改行を削除
        cleaned_val = re.sub(r'[\s\n]', '', raw_val)

        if cleaned_val.startswith('{'):
            # そのままのJSONの場合
            creds_info = json.loads(cleaned_val)
        else:
            # Base64の場合 (現在の設定はこれです)
            # 復号時にエラーが出ないようパディングを補正
            missing_padding = len(cleaned_val) % 4
            if missing_padding:
                cleaned_val += '=' * (4 - missing_padding)
            decoded_bytes = base64.b64decode(cleaned_val)
            creds_info = json.loads(decoded_bytes.decode('utf-8'))

        # 3. 秘密鍵の改行コード問題の最終処理
        # JSONの中の \\n を 本物の改行 \n に直す
        if 'private_key' in creds_info:
            creds_info['private_key'] = creds_info['private_key'].replace('\\n', '\n')

        # 4. Google Sheets 認証 (google-auth使用)
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        client = gspread.authorize(creds)
        
        sheet = client.open_by_key("1wSfyGreLH_lb7vR_vpmuJ3rAndtMNvMDQbv2ZlPVxUE").sheet1
        print("認証成功: スプレッドシートに接続しました。")

        # 5. URL生成処理
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        rows = sheet.get_all_records()
        for i, row in enumerate(rows, start=2):
            url_cell = str(row.get('url', '')).strip()
            # URLが空、または http で始まらない場合のみ生成
            if not url_cell.startswith('http'):
                word = row.get('word')
                memo = row.get('memo')
                print(f"Generating URL for: {word}")
                
                try:
                    prompt = f"「{word}」を「{memo}」で検索するURLを1つ出力(URLのみ)。"
                    res = model.generate_content(prompt)
                    new_url = res.text.strip()
                    sheet.update_cell(i, 2, new_url)
                    print(f" -> 書き込み完了: {new_url}")
                except Exception as e:
                    print(f" -> Gemini生成エラー: {e}")

        print("--- 全処理完了 ---")

    except Exception as e:
        print(f"致命的なエラー: {e}")
        # デバッグ用: キーの中身がどう見えているかの一部（秘密鍵本体は出さない）
        if 'creds_info' in locals():
            pk = creds_info.get('private_key', '')
            print(f"Private Key start: {pk[:30]}...") 

if __name__ == "__main__":
    main()
