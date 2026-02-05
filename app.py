import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# --- ページ設定 ---
st.set_page_config(page_title="webwatch", layout="centered")

# --- テーマ定義 (CSS) ---
THEMES = {
    "Minimal Monochrome": """
        <style>
        .stApp { background-color: #ffffff; color: #000000; font-family: 'Helvetica', sans-serif; }
        .stButton>button { background-color: #000000; color: #ffffff; border-radius: 0px; border: 1px solid #000000; width: 100%; }
        input { border-radius: 0px !important; border: 1px solid #000000 !important; }
        </style>
    """,
    "Dark Cyber": """
        <style>
        .stApp { background-color: #0e1117; color: #00ffcc; font-family: 'Courier New', monospace; }
        .stButton>button { background-color: #0e1117; color: #00ffcc; border: 1px solid #00ffcc; box-shadow: 0 0 10px #00ffcc; width: 100%; }
        input { background-color: #1a1c24 !important; color: #00ffcc !important; border: 1px solid #00ffcc !important; }
        div[data-baseweb="select"] > div { background-color: #1a1c24 !important; color: #00ffcc !important; }
        </style>
    """,
    "Clean Modern": """
        <style>
        .stApp { background-color: #f8f9fa; color: #333333; }
        .stButton>button { background-color: #4a90e2; color: #ffffff; border-radius: 8px; border: none; width: 100%; }
        .stForm { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        input { border-radius: 8px !important; }
        </style>
    """,
    "Industrial": """
        <style>
        .stApp { background-color: #4b5563; color: #e5e7eb; font-family: 'Impact', sans-serif; }
        .stButton>button { background-color: #374151; color: #fbbf24; border: 3px outset #6b7280; font-weight: bold; width: 100%; }
        .stForm { border: 4px solid #1f2937; background-color: #374151; }
        input { background-color: #1f2937 !important; color: #ffffff !important; border: 2px inset #6b7280 !important; }
        </style>
    """
}

# --- 機能定義 ---
def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT_JSON"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open_by_key("1wSfyGreLH_lb7vR_vpmuJ3rAndtMNvMDQbv2ZlPVxUE").sheet1

# --- UI構築 ---
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
            st.error(f"Error: {e}")

st.caption("Settings will be processed by GitHub Actions within 1 hour.")
