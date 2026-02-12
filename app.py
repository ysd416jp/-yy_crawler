import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import base64
import re
from datetime import datetime

st.set_page_config(page_title="Web更新チェッカー", layout="centered", initial_sidebar_state="collapsed")

# ============================================================
# カスタムCSS — 元のダークUI再現
# ============================================================
st.markdown("""
<style>
/* --- 全体 --- */
.stApp {
    background-color: #0e1117;
    color: #e0e0e0;
}
header[data-testid="stHeader"] { background-color: #0e1117; }
/* --- タイトル --- */
h1 { color: #ffffff !important; font-size: 1.6rem !important; font-weight: 600 !important; }
/* --- ボタン共通 --- */
.stButton > button {
    border-radius: 8px; font-weight: 500; padding: 0.5rem 1.2rem;
    transition: all 0.2s ease;
}
.stButton > button:hover { transform: translateY(-1px); }
/* --- 追加ボタン（緑系） --- */
div[data-testid="column"]:nth-child(1) .stButton > button {
    background: linear-gradient(135deg, #1a5c3a 0%, #238b5e 100%);
    color: #fff; border: none; width: 100%;
}
div[data-testid="column"]:nth-child(2) .stButton > button {
    background: linear-gradient(135deg, #1a3d5c 0%, #2370a0 100%);
    color: #fff; border: none; width: 100%;
}
/* --- カード --- */
.monitor-card {
    background: #1a1d24; border-radius: 10px; padding: 14px 18px;
    margin-bottom: 8px; display: flex; align-items: center;
    border: 1px solid #2a2d35;
}
.monitor-card:hover { border-color: #3a3d45; }
.card-icon {
    width: 36px; height: 36px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; margin-right: 14px; flex-shrink: 0;
}
.card-icon-url { background: #1a3d2a; }
.card-icon-kw  { background: #1a2d4a; }
.card-title { font-size: 0.95rem; color: #fff; font-weight: 500; }
.card-sub   { font-size: 0.75rem; color: #888; margin-top: 2px; }
.card-body  { flex: 1; }
/* --- セクション見出し --- */
.section-title {
    color: #999; font-size: 0.8rem; font-weight: 600;
    letter-spacing: 0.04em; margin: 24px 0 10px 0;
}
/* --- 履歴行 --- */
.history-row {
    background: #14161c; border-radius: 6px; padding: 8px 14px;
    margin-bottom: 4px; font-size: 0.82rem; color: #aaa;
    border-left: 3px solid #2a2d35;
}
.history-row-change {
    border-left-color: #e6934a;
    color: #e6934a;
}
/* --- 入力フォーム --- */
input, select, .stSelectbox > div > div {
    background-color: #1a1d24 !important;
    color: #e0e0e0 !important;
    border-color: #2a2d35 !important;
}
.stTextInput label, .stSelectbox label, .stNumberInput label {
    color: #999 !important;
}
/* --- 区切り線 --- */
hr { border-color: #1e2028 !important; }
/* --- dialog --- */
div[data-testid="stExpander"] {
    background-color: #14161c; border: 1px solid #2a2d35; border-radius: 8px;
}
/* --- バージョン --- */
.version { text-align: right; color: #444; font-size: 0.7rem; margin-top: 40px; }
/* Streamlitデフォルト要素を非表示 */
#MainMenu, footer { display: none; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# Google Sheets 認証
# ============================================================
@st.cache_resource(ttl=300)
def get_client():
    # --- Secrets から鍵データを取得 ---
    # 方法1: [gcp] セクションに各フィールドを直書き
    if "gcp" in st.secrets and "private_key" in st.secrets["gcp"]:
        try:
            creds_dict = dict(st.secrets["gcp"])
            scope = ["https://spreadsheets.google.com/feeds",
                     "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            return gspread.authorize(creds)
        except Exception as e:
            st.error(f"認証エラー(gcp): {e}")
            return None

    # 方法2: ENCODED_JSON (Base64)
    if "ENCODED_JSON" not in st.secrets:
        st.error("Secretsに認証情報が設定されていません。")
        return None
    try:
        raw = st.secrets["ENCODED_JSON"]
        # TOMLのダブルクォートで \n が実改行になる場合があるので除去
        clean_b64 = re.sub(r'[^A-Za-z0-9+/=]', '', raw)
        # パディング補正
        pad = len(clean_b64) % 4
        if pad:
            clean_b64 += '=' * (4 - pad)
        decoded_bytes = base64.b64decode(clean_b64)
        creds_dict = json.loads(decoded_bytes.decode("utf-8"))
        # private_key 修復
        if "private_key" in creds_dict:
            pk = creds_dict["private_key"]
            if "\\n" in pk:
                pk = pk.replace("\\n", "\n")
            if not pk.endswith("\n"):
                pk += "\n"
            creds_dict["private_key"] = pk
        scope = ["https://spreadsheets.google.com/feeds",
                 "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"認証エラー: {e}")
        return None

SHEET_KEY = "1wSfyGreLH_lb7vR_vpmuJ3rAndtMNvMDQbv2ZlPVxUE"

def get_sheet():
    client = get_client()
    if client is None:
        return None
    try:
        return client.open_by_key(SHEET_KEY).sheet1
    except Exception as e:
        st.error(f"シートエラー: {e}")
        return None


# ============================================================
# タイトル
# ============================================================
col_t, col_r = st.columns([8, 1])
with col_t:
    st.markdown("# Web更新チェッカー")
with col_r:
    if st.button("🔄", help="データ再読込"):
        st.cache_resource.clear()
        st.rerun()

# ============================================================
# 追加ボタン
# ============================================================
col1, col2 = st.columns(2)
with col1:
    add_url = st.button("＋ 🌐 URL監視")
with col2:
    add_kw = st.button("＋ 🔍 検索監視")

# ============================================================
# 追加フォーム（ボタン押下時のみ表示）
# ============================================================
if add_url:
    st.session_state["show_form"] = "url"
if add_kw:
    st.session_state["show_form"] = "kw"

show_form = st.session_state.get("show_form", None)

if show_form == "url":
    with st.expander("🌐 URL監視を追加", expanded=True):
        with st.form("add_url_form"):
            target_url = st.text_input("監視するURL", placeholder="https://example.com")
            freq = st.selectbox("チェック間隔", [1, 4, 6, 12, 24], index=2,
                                format_func=lambda x: f"{x}時間ごと")
            submitted = st.form_submit_button("追加する")
            if submitted and target_url:
                sheet = get_sheet()
                if sheet:
                    sheet.append_row(["update", target_url, "HP更新", freq, "", ""])
                    st.success("URL監視を追加しました")
                    st.session_state["show_form"] = None
                    st.cache_resource.clear()
                    st.rerun()

elif show_form == "kw":
    with st.expander("🔍 検索監視を追加", expanded=True):
        with st.form("add_kw_form"):
            keyword = st.text_input("検索キーワード", placeholder="キーワードを入力")
            source = st.selectbox("検索先", ["x", "indeed", "townwork", "jalan", "hotpepper", "google"])
            freq = st.selectbox("チェック間隔", [1, 4, 6, 12, 24], index=2,
                                format_func=lambda x: f"{x}時間ごと")
            submitted = st.form_submit_button("追加する")
            if submitted and keyword:
                sheet = get_sheet()
                if sheet:
                    sheet.append_row([keyword, "", source, freq, "", ""])
                    st.success("検索監視を追加しました")
                    st.session_state["show_form"] = None
                    st.cache_resource.clear()
                    st.rerun()

# ============================================================
# 監視一覧を取得・表示
# ============================================================
sheet = get_sheet()
if sheet:
    try:
        rows = sheet.get_all_records()
    except Exception:
        rows = []

    if rows:
        st.markdown(f'<div class="section-title">監視中 ({len(rows)}件)</div>',
                    unsafe_allow_html=True)

        for i, row in enumerate(rows, start=2):
            word = str(row.get("word", ""))
            url = str(row.get("url", ""))
            memo = str(row.get("memo", ""))
            freq = str(row.get("freq", ""))

            is_url_watch = (memo == "HP更新")

            if is_url_watch:
                icon_cls = "card-icon-url"
                icon = "🌐"
                title = url if url else "(URL未設定)"
                sub = f"{freq}時間ごと"
            else:
                icon_cls = "card-icon-kw"
                icon = "🔍"
                title = word
                sub = f"{freq}時間ごと・{memo}"

            col_card, col_del = st.columns([10, 1])
            with col_card:
                st.markdown(f'''
                <div class="monitor-card">
                    <div class="card-icon {icon_cls}">{icon}</div>
                    <div class="card-body">
                        <div class="card-title">{title}</div>
                        <div class="card-sub">{sub}</div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            with col_del:
                if st.button("🗑", key=f"del_{i}", help="削除"):
                    sheet.delete_rows(i)
                    st.cache_resource.clear()
                    st.rerun()
    else:
        st.info("監視項目がありません。上のボタンから追加してください。")

    # ============================================================
    # 履歴セクション（直近の実行ログから作成）
    # ============================================================
    # Google Sheetsのデータから簡易的に状態を表示
    if rows:
        st.markdown('<div class="section-title">最新ステータス</div>',
                    unsafe_allow_html=True)
        for row in rows:
            word = str(row.get("word", ""))
            memo = str(row.get("memo", ""))
            prev_hash = str(row.get("prev_hash", "")).strip()
            url = str(row.get("url", "")).strip()
            is_url_watch = (memo == "HP更新")

            if is_url_watch:
                label = url[:40] if url else word
                if prev_hash:
                    status = "✅ 監視中"
                else:
                    status = "⏳ 初回チェック待ち"
            else:
                label = word
                if url:
                    status = f"✅ URL生成済"
                else:
                    status = "⏳ URL未生成"

            st.markdown(
                f'<div class="history-row">{label} — {status}</div>',
                unsafe_allow_html=True)

else:
    st.warning("Google Sheetsに接続できません。Secretsの設定を確認してください。")

# ============================================================
# フッター
# ============================================================
st.markdown('<div class="version">v4.0.0</div>', unsafe_allow_html=True)
