import os
from google import genai

def get_api_key():
    try:
        with open("api_keys.txt", "r") as f:
            for line in f:
                if "GEMINI_API_KEY=" in line:
                    return line.split("=")[1].strip().strip("'").strip('"')
    except Exception: return None
    return None

def test_pachinko():
    key = get_api_key()
    if not key:
        print("エラー: api_keys.txt が正しく読み込めません。")
        return

    client = genai.Client(api_key=key)
    memo = "インディード"
    word = "パチンコ"
    
    prompt = (
        f"タスク：サービス名『{memo}』からドメインを特定し、"
        f"キーワード『{word}』を24時間以内の新着に絞って検索するGoogle検索URLを1つ生成せよ。\n"
        f"制約：適切なドメイン（indeed.com等）に自力で変換し、回答はURLのみとすること。"
    )
    
    try:
        response = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
        url = response.text.strip().replace("`", "")
        print(f"\n--- パチンコ検証結果 ---")
        print(f"入力: {memo} / {word}")
        print(f"出力: {url}")
        print(f"------------------------\n")
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    test_pachinko()
