import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import base64

st.set_page_config(page_title="webwatch", layout="centered")

def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # 【最終処方】Base64をデコードしてJSONを復元（文字化けの余地なし）
    encoded_creds = st.secrets["ENCODED_JSON"]
    decoded_creds = base64.b64decode(encoded_creds).decode("utf-8")
    creds_dict = json.loads(decoded_creds)
    
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open_by_key("1wSfyGreLH_lb7vR_vpmuJ3rAndtMNvMDQbv2ZlPVxUE").sheet1

# --- 以下、デザインとUI部分は維持 ---
THEMES = {
    "Minimal Monochrome": "<style>.stApp { background-color: #ffffff; color: #000000; } .stButton>button { background-color: #000000; color: #ffffff; border: 1px solid #000000; }</style>",
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
