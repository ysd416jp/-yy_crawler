import os
from google import genai

def get_api_key():
    """api_keys.txt から GEMINI_API_KEY を抽出する"""
    try:
        with open("api_keys.txt", "r") as f:
            for line in f:
                if line.startswith("GEMINI_API_KEY="):
                    return line.split("=")[1].strip()
    except FileNotFoundError:
        print("エラー: api_keys.txt が見つかりません。")
    return None

def test_generation(memo, word):
    api_key = get_api_key()
    if not api_key:
        print("エラー: APIキーを取得できませんでした。")
        return

    client = genai.Client(api_key=api_key)
    
    # 汎用性を重視したプロンプト
    prompt = (
        f"タスク：サービス名『{memo}』からドメインを特定し、"
        f"キーワード『{word}』を24時間以内の新着に絞って検索するGoogle検索URLを1つ生成せよ。\n"
        f"制約：\n"
        f"1. 『{memo}』が日本語の場合、適切なドメイン（indeed.com, x.com, jalan.net 等）に自力で変換すること。\n"
        f"2. 回答はURLのみ（https://...）とし、余計な説明や装飾（`等）は一切省くこと。"
    )
    
    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )
        url = response.text.strip().replace("`", "")
        print(f"\n[入力] サイト名: {memo} / 検索語: {word}")
        print(f"[出力] 生成URL: {url}")
    except Exception as e:
        print(f"エラー: {e}")

# 検証：吉田さんが気になっていた「インディード」や「x」でテスト
print("--- Gemini 3.0 推論テスト開始 ---")
test_generation("インディード", "鮨ゆきち")
test_generation("x", "鮨ゆきち")
test_generation("タウンワーク", "鮨ゆきち")
