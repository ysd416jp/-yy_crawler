import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import base64
import re

st.set_page_config(page_title="webwatch", layout="centered")

def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # 1. Secretsから文字列を取得
    encoded_raw = st.secrets["ENCODED_JSON"]
    
    # 2. 【最強補正】Base64以外の文字（スペース、引用符など）を完全に除去
    # A-Z, a-z, 0-9, +, / 以外をすべて捨てる
    clean_b64 = re.sub(r'[^A-Za-z0-9+/]', '', encoded_raw)
    
    # 3. 【長さ補正】4の倍数になるように '=' を付け足す
    missing_padding = len(clean_b64) % 4
    if missing_padding:
        clean_b64 += '=' * (4 - missing_padding)
    
    # 4. デコードして JSON 復元
    decoded_creds = base64.b64decode(clean_b64).decode("utf-8")
    creds_dict = json.loads(decoded_creds)
    
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open_by_key("1wSfyGreLH_lb7vR_vpmuJ3rAndtMNvMDQbv2ZlPVxUE").sheet1

# --- デザインとUI (変更なし) ---
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
        freq = st.select_slider("Frequency", options=[1, 4, 12, 24], value=24)
        memo, word = "HP更新", "update"
    else:
        word = st.text_input("Search Keyword")
        site_alias = st.selectbox("Source", ["x", "indeed", "townwork", "jalan"])
        freq = st.select_slider("Frequency", options=[1, 4, 12, 24], value=24)
        memo, target_url = site_alias, ""

    if st.form_submit_button("Start Monitoring"):
        try:
            sheet = get_sheet()
            sheet.append_row([word, target_url, memo, freq])
            st.success("Registration Complete")
            st.balloons()
        except Exception as e:
            st.error(f"System Error: {e}")
