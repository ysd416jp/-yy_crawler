import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# UI設定
st.set_page_config(page_title="webwatch", layout="centered")

def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # Secretsから文字列を取得
    raw_json = st.secrets["GOOGLE_SERVICE_ACCOUNT_JSON"]
    # JSONとして読み込む
    creds_dict = json.loads(raw_json)
    
    # 【最重要】秘密鍵の改行コードを「本物の改行」に強制変換し、余計な空白を削除
    if "private_key" in creds_dict:
        fixed_key = creds_dict["private_key"].replace("\\n", "\n").strip()
        creds_dict["private_key"] = fixed_key
    
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open_by_key("1wSfyGreLH_lb7vR_vpmuJ3rAndtMNvMDQbv2ZlPVxUE").sheet1

# --- テーマ定義 (CSS) ---
THEMES = {
    "Minimal Monochrome": "<style>.stApp { background-color: #ffffff; color: #000000; } .stButton>button { background-color: #000000; color: #ffffff; }</style>",
    "Dark Cyber": "<style>.stApp { background-color: #0e1117; color: #00ffcc; } .stButton>button { border: 1px solid #00ffcc; box-shadow: 0 0 10px #00ffcc; }</style>",
    "Clean Modern": "<style>.stApp { background-color: #f8f9fa; color: #333333; } .stButton>button { background-color: #4a90e2; color: #ffffff; border-radius: 8px; }</style>",
    "Industrial": "<style>.stApp { background-color: #4b5563; color: #fbbf24; } .stButton>button { background-color: #374151; border: 3px outset #6b7280; }</style>"
}

st.title("webwatch")

# 設定セクション
with st.expander("Settings / Theme"):
    selected_theme = st.selectbox("Select Theme", list(THEMES.keys()), index=0)
st.markdown(THEMES[selected_theme], unsafe_allow_html=True)

# メインモード選択
mode = st.radio("Check Type", ["Website Update", "Keyword Tracking"], horizontal=True)
st.divider()

# フォーム
with st.form("main_form", clear_on_submit=True):
    if mode == "Website Update":
        target_url = st.text_input("Target URL", placeholder="https://example.com")
        freq = st.select_slider("Frequency (Times/Day)", options=[1, 4, 12, 24], value=24)
        memo, word = "HP更新", "update"
    else:
        word = st.text_input("Search Keyword", placeholder="sushi-yukichi, etc.")
        site_alias = st.selectbox("Source", ["x", "indeed", "townwork", "jalan"])
        freq = st.select_slider("Frequency (Times/Day)", options=[1, 4, 12, 24], value=24)
        memo, target_url = site_alias, ""

    if st.form_submit_button("Start Monitoring"):
        try:
            sheet = get_sheet()
            sheet.append_row([word, target_url, memo, freq])
            st.success("Registration Complete")
        except Exception as e:
            st.error(f"System Error: {e}")

st.caption("Settings will be processed by GitHub Actions within 1 hour.")
