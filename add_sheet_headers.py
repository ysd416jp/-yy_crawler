"""Google Sheetsにprev_hash, prev_len列を追加するワンショットスクリプト"""
import os, json, base64, re
import gspread
from google.oauth2.service_account import Credentials


def get_credentials():
    raw_val = os.environ.get("GCP_JSON")
    if not raw_val:
        raise RuntimeError("GCP_JSON が未設定")

    cleaned_val = re.sub(r'[\s\n]', '', raw_val)

    if cleaned_val.startswith('{'):
        creds_info = json.loads(cleaned_val)
    else:
        missing_padding = len(cleaned_val) % 4
        if missing_padding:
            cleaned_val += '=' * (4 - missing_padding)
        creds_info = json.loads(base64.b64decode(cleaned_val).decode('utf-8'))

    if 'private_key' in creds_info:
        creds_info['private_key'] = creds_info['private_key'].replace('\\n', '\n')

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    return Credentials.from_service_account_info(creds_info, scopes=scopes)


def main():
    creds = get_credentials()
    client = gspread.authorize(creds)
    sheet = client.open_by_key("1wSfyGreLH_lb7vR_vpmuJ3rAndtMNvMDQbv2ZlPVxUE").sheet1

    headers = sheet.row_values(1)
    print(f"現在のヘッダー: {headers}")

    if "prev_hash" not in headers:
        col = len(headers) + 1
        sheet.update_cell(1, col, "prev_hash")
        headers.append("prev_hash")
        print(f"prev_hash を {col}列目に追加")

    if "prev_len" not in headers:
        col = len(headers) + 1
        sheet.update_cell(1, col, "prev_len")
        headers.append("prev_len")
        print(f"prev_len を {col}列目に追加")

    print(f"最終ヘッダー: {sheet.row_values(1)}")


if __name__ == "__main__":
    main()
