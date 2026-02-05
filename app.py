import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

st.set_page_config(page_title="吉田監視所", page_icon="🍣")

def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # クラウド上の設定から鍵を読み込む
    creds_dict = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT_JSON"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open_by_key("1wSfyGreLH_lb7vR_vpmuJ3rAndtMNvMDQbv2ZlPVxUE").sheet1

st.title("🍣 吉田監視所")
st.write("「お気に入り」からポチポチするだけの簡単監視設定。")

# 1) モード選択
mode = st.radio(
    "1) 何をしたいですか？",
    ["i) HPの更新をチェックしたい", "ii) 注目ワードを追跡したい"],
    index=0
)

st.divider()

# 2) 詳細入力
with st.form("main_form"):
    if "i)" in mode:
        st.subheader("🌐 HP更新チェック")
        target_url = st.text_input("チェックしたいURL", placeholder="https://example.com")
        freq = st.select_slider("チェック頻度（1日に何回？）", options=[1, 4, 12, 24], value=24)
        memo = "HP更新"
        word = "update"
    else:
        st.subheader("🔍 注目ワード追跡")
        word = st.text_input("追跡ワード", placeholder="鮨ゆきち、求人、パチンコなど")
        site_alias = st.selectbox("どこで探す？", ["x", "インディード", "タウンワーク", "じゃらん"])
        freq = st.select_slider("チェック頻度", options=[1, 4, 12, 24], value=24)
        memo = site_alias
        target_url = ""

    if st.form_submit_button("🚀 監視を開始する"):
        try:
            sheet = get_sheet()
            sheet.append_row([word, target_url, memo, freq])
            st.success("✅ 登録完了！AIが監視網を広げました。")
            st.balloons()
        except Exception as e:
            st.error(f"エラー: {e}")

st.info("※登録した内容は、1時間以内に GitHub Actions が自動で処理を開始します。")
