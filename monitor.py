import os, json, hashlib, requests, gspread
from google import genai
from oauth2client.service_account import ServiceAccountCredentials
from linebot import LineBotApi
from linebot.models import TextSendMessage

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
LINE_TOKEN = os.environ.get("LINE_ACCESS_TOKEN")
USER_ID = os.environ.get("LINE_USER_ID")
SERVICE_ACCOUNT_JSON = json.loads(os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON"))
SHEET_ID = "1wSfyGreLH_lb7vR_vpmuJ3rAndtMNvMDQbv2ZlPVxUE"

def main():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(SERVICE_ACCOUNT_JSON, scope)
    client_gs = gspread.authorize(creds)
    sheet = client_gs.open_by_key(SHEET_ID).sheet1
    data = sheet.get_all_values()
    client_ai = genai.Client(api_key=GEMINI_API_KEY)
    line_bot_api = LineBotApi(LINE_TOKEN)
    headers = {"User-Agent": "Mozilla/5.0"}

    for i, row in enumerate(data[1:], start=2):
        word, current_url, memo = row[0], row[1], row[2]
        old_hash = row[4] if len(row) > 4 else ""
        if not word: continue

        # --- AIによる高度な検索URL錬成 ---
        if not current_url and memo and memo != "HP更新":
            try:
                # プロンプトを進化：検索戦略をAIに考えさせる
                prompt = (
                    f"目的：キーワード『{word}』の新着情報をWebサイト『{memo}』からGoogle検索で見つけ出す。\n"
                    f"タスク：最もヒット率の高いGoogle検索URL（URL全体）を1つ生成せよ。\n"
                    f"制約：1. 『{memo}』という愛称をx.comやjalan.net等の適切なドメインに変換しsite:演算子を使うこと。"
                    f"2. 24時間以内の新着指定（&tbs=qdr:d）を必ずURLに含めること。回答はURLのみ。"
                )
                response = client_ai.models.generate_content(
                    model="gemini-3-flash-preview",
                    contents=prompt
                )
                # URL以外のノイズ（マークダウン等）を除去
                generated_url = response.text.strip().split('\n')[0].replace("`", "")
                
                if "http" in generated_url:
                    current_url = generated_url
                    sheet.update_cell(i, 2, current_url)
                    print(f"Row {i}: Evolved URL saved -> {current_url}")
            except Exception as e: print(f"Row {i} Gemini Error: {e}")

        if not current_url: continue

        # 監視・通知ロジック
        try:
            res = requests.get(current_url, headers=headers, timeout=20)
            new_hash = hashlib.md5(res.text.encode()).hexdigest()
            # ヒット判定（除外ワードを考慮）
            exclude = ["0件", "見つかりませんでした", "一致する情報はありません"]
            if word in res.text and not any(ex in res.text for ex in exclude):
                if new_hash != old_hash:
                    line_bot_api.push_message(USER_ID, TextSendMessage(text=f"【発見】{word} ({memo})\n{current_url}"))
                    sheet.update_cell(i, 5, new_hash)
        except Exception as e: print(f"Row {i} Net Error: {e}")

if __name__ == "__main__": main()
