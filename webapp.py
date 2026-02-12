"""Web更新チェッカー — Flask版"""
import os
import json
import base64
import re
import gspread
from google.oauth2.service_account import Credentials
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

SHEET_KEY = "1wSfyGreLH_lb7vR_vpmuJ3rAndtMNvMDQbv2ZlPVxUE"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# GCP鍵ファイルのパス (PythonAnywhere用)
KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gcp_key.json")


def get_sheet():
    """GCP認証してGoogle Sheetsに接続"""
    raw = None
    # 1. ファイルから読む (PythonAnywhere)
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE) as f:
            raw = f.read()
    # 2. 環境変数から読む (Render等)
    if not raw:
        raw = os.environ.get("GCP_JSON", "")
    if not raw:
        return None

    raw_stripped = raw.strip()
    if raw_stripped.startswith("{"):
        creds_dict = json.loads(raw_stripped)
    else:
        cleaned = re.sub(r'[\s\n]', '', raw)
        pad = len(cleaned) % 4
        if pad:
            cleaned += '=' * (4 - pad)
        creds_dict = json.loads(base64.b64decode(cleaned).decode("utf-8"))

    if "private_key" in creds_dict:
        pk = creds_dict["private_key"]
        if "\\n" in pk:
            pk = pk.replace("\\n", "\n")
        if not pk.endswith("\n"):
            pk += "\n"
        creds_dict["private_key"] = pk

    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_KEY).sheet1


@app.route("/")
def index():
    sheet = get_sheet()
    rows = []
    error = None
    if sheet:
        try:
            rows = sheet.get_all_records()
        except Exception as e:
            error = str(e)
    else:
        error = "Google Sheetsに接続できません"
    return render_template("index.html", rows=rows, error=error)


@app.route("/add", methods=["POST"])
def add():
    sheet = get_sheet()
    if not sheet:
        return redirect(url_for("index"))

    mode = request.form.get("mode", "kw")
    if mode == "url":
        url = request.form.get("url", "").strip()
        freq = request.form.get("freq", "12")
        if url:
            sheet.append_row(["update", url, "HP更新", int(freq), "", ""])
    else:
        keyword = request.form.get("keyword", "").strip()
        source_type = request.form.get("source_type", "preset")
        if source_type == "custom":
            source = request.form.get("custom_source", "").strip()
        else:
            source = request.form.get("preset_source", "x")
        freq = request.form.get("freq", "12")
        if keyword and source:
            sheet.append_row([keyword, "", source, int(freq), "", ""])

    return redirect(url_for("index"))


@app.route("/edit", methods=["POST"])
def edit():
    sheet = get_sheet()
    if not sheet:
        return redirect(url_for("index"))

    row_index = int(request.form.get("row_index", 0))
    edit_mode = request.form.get("edit_mode", "")
    freq = int(request.form.get("edit_freq", "12"))

    if row_index < 2:
        return redirect(url_for("index"))

    try:
        if edit_mode == "url":
            new_url = request.form.get("edit_url", "").strip()
            if new_url:
                sheet.update_cell(row_index, 2, new_url)  # url列
            sheet.update_cell(row_index, 4, freq)  # freq列
        else:
            new_word = request.form.get("edit_word", "").strip()
            new_memo = request.form.get("edit_memo", "").strip()
            if new_word:
                sheet.update_cell(row_index, 1, new_word)  # word列
            if new_memo:
                sheet.update_cell(row_index, 3, new_memo)  # memo列
                # memoが変わったらURLをリセット（Geminiに再生成させる）
                sheet.update_cell(row_index, 2, "")
            sheet.update_cell(row_index, 4, freq)  # freq列
    except Exception:
        pass

    return redirect(url_for("index"))


@app.route("/delete/<int:row_index>", methods=["POST"])
def delete(row_index):
    sheet = get_sheet()
    if sheet:
        try:
            sheet.delete_rows(row_index)
        except Exception:
            pass
    return redirect(url_for("index"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
