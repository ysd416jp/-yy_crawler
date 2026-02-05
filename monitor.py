import os
import requests
from bs4 import BeautifulSoup
from linebot import LineBotApi
from linebot.models import TextSendMessage

# GitHub Secretsから読み込み
LINE_TOKEN = os.environ.get("LINE_ACCESS_TOKEN")
USER_ID = os.environ.get("LINE_USER_ID")

def main():
    url = "https://townwork.net/jozen/hokkaido/shisetsu_01204/kw0000000000/"
    word = "鮨ゆきち"
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        
        if word in res.text:
            line_bot_api = LineBotApi(LINE_TOKEN)
            message = f"【速報】「{word}」の情報を発見しました！\n{url}"
            line_bot_api.push_message(USER_ID, TextSendMessage(text=message))
            print("発見：LINEを送信しました。")
        else:
            print("未発見：まだ情報は出ていないようです。")
            
    except Exception as e:
        print(f"エラー発生: {e}")

if __name__ == "__main__":
    main()
