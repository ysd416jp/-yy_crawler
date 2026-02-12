"""Web更新チェッカー — Flask版"""
import os
import json
import base64
import re
import gspread
from google.oauth2.service_account import Credentials
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)

SHEET_KEY = "1wSfyGreLH_lb7vR_vpmuJ3rAndtMNvMDQbv2ZlPVxUE"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def get_sheet():
    """GCP認証してGoogle Sheetsに接続"""
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
    if sheet:
        try:
            rows = sheet.get_all_records()
        except Exception:
            rows = []
    return render_template("index.html", rows=rows)


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
        source = request.form.get("source", "x")
        freq = request.form.get("freq", "12")
        if keyword:
            sheet.append_row([keyword, "", source, int(freq), "", ""])

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
