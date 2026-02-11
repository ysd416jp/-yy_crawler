import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import base64
import re

st.set_page_config(page_title="webwatch", layout="centered")

def get_sheet():
    if "ENCODED_JSON" not in st.secrets:
        st.error("Secretsに 'ENCODED_JSON' が設定されていません。")
        return None

    try:
        # 1. Base64デコード
        encoded_raw = st.secrets["ENCODED_JSON"].strip().strip('"').strip("'")
        clean_b64 = re.sub(r'[^A-Za-z0-9+/=]', '', encoded_raw)
        decoded_bytes = base64.b64decode(clean_b64)
        creds_dict = json.loads(decoded_bytes.decode("utf-8"))
        
        # 2. 秘密鍵の改行修復
        if "private_key" in creds_dict:
            pk = creds_dict["private_key"]
            # エスケープされた \n を実際の改行に変換
            if "\\n" in pk:
                pk = pk.replace("\\n", "\n")
            # 末尾に改行がなければ追加
            if not pk.endswith("\n"):
                pk += "\n"
            creds_dict["private_key"] = pk

        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds).open_by_key("1wSfyGreLH_lb7vR_vpmuJ3rAndtMNvMDQbv2ZlPVxUE").sheet1
    except Exception as e:
        st.error(f"🔍 鍵の修復に失敗しました: {e}")
        return None

# --- UI デザイン ---
THEMES = {
    "Minimal Monochrome": "<style>.stApp { background-color: #ffffff; color: #000000; } .stButton>button { background-color: #000000; color: #ffffff; }</style>",
    "Dark Cyber": "<style>.stApp { background-color: #0e1117; color: #00ffcc; } .stButton>button { border: 1px solid #00ffcc; box-shadow: 0 0 10px #00ffcc; }</style>",
    "Clean Modern": "<style>.stApp { background-color: #f8f9fa; color: #333333; } .stButton>button { background-color: #4a90e2; color: #ffffff; border-radius: 8px; }</style>",
    "Industrial": "<style>.stApp { background-color: #4b5563; color: #fbbf24; } .stButton>button { background-color: #374151; border: 3px outset #6b7280; }</style>"
}

st.title("webwatch")
with st.expander("Settings / Theme"):
    selected_theme = st.selectbox("Select Theme", list(THEMES.keys()), index=0)
st.markdown(THEMES[selected_theme], unsafe_allow_html=True)

mode = st.radio("Check Type", ["Website Update", "Keyword Tracking"], horizontal=True)
st.divider()

with st.form("main_form", clear_on_submit=True):
    if mode == "Website Update":
        target_url = st.text_input("Target URL")
        word, memo = "update", "HP更新"
    else:
        word = st.text_input("Search Keyword")
        site_alias = st.selectbox("Source", ["x", "indeed", "townwork", "jalan", "hotpepper"])
        memo, target_url = site_alias, ""
    
    freq = st.select_slider("Frequency", options=[1, 4, 12, 24], value=24)

    if st.form_submit_button("Start Monitoring"):
        sheet = get_sheet()
        if sheet:
            try:
                sheet.append_row([word, target_url, memo, freq])
                st.success("Registration Complete")
                st.balloons()
            except Exception as e:
                st.error(f"Sheet Error: {e}")
