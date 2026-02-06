import os, base64, json, gspread, re
import google.generativeai as genai
from oauth2client.service_account import ServiceAccountCredentials

def main():
    encoded = os.environ.get("GCP_JSON")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not encoded or not gemini_key: return

    try:
        # 認証処理
        clean_b64 = re.sub(r'[^A-Za-z0-9+/=]', '', encoded)
        creds_dict = json.loads(base64.b64decode(clean_b64).decode('utf-8'))
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key("1wSfyGreLH_lb7vR_vpmuJ3rAndtMNvMDQbv2ZlPVxUE").sheet1
        
        # URL生成処理
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        data = sheet.get_all_records()
        for i, row in enumerate(data, start=2):
            if not str(row.get('url', '')).startswith('http'):
                word, memo = row.get('word'), row.get('memo')
                prompt = f"「{word}」を「{memo}」で検索するためのURLを1つ出力してください。URLのみを返し、説明は不要です。"
                url = model.generate_content(prompt).text.strip()
                sheet.update_cell(i, 2, url)
                print(f"Updated row {i}: {url}")

        print("Successfully updated the sheet!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
