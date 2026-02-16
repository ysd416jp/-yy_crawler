"""
QRコード付きトークンPDF生成
各従業員の受検URL+QRコードを一覧化し、印刷用PDFを生成する
"""

import io
import qrcode
from fpdf import FPDF


class TokenPDF(FPDF):
    """A4用紙に4名分のトークンカードを配置するPDF"""

    def __init__(self):
        super().__init__()
        # 日本語フォント（Noto Sans JPがなければデフォルト）
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 8, "Stress Check - Access Tokens", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def add_token_card(self, name, department, url, token, qr_img_path):
        """1名分のトークンカードを追加"""
        # カードの高さを確認、必要なら改ページ
        if self.get_y() > 240:
            self.add_page()

        start_y = self.get_y()

        # 枠線
        self.set_draw_color(200, 200, 200)
        self.rect(10, start_y, 190, 55)

        # QRコード画像
        self.image(qr_img_path, x=14, y=start_y + 3, w=48, h=48)

        # テキスト情報
        text_x = 68
        self.set_xy(text_x, start_y + 4)

        # 名前
        self.set_font("Helvetica", "B", 14)
        self.cell(120, 8, name, new_x="LMARGIN", new_y="NEXT")

        # 部署
        self.set_xy(text_x, start_y + 14)
        self.set_font("Helvetica", "", 10)
        self.cell(120, 6, department or "", new_x="LMARGIN", new_y="NEXT")

        # URL
        self.set_xy(text_x, start_y + 24)
        self.set_font("Courier", "", 7)
        self.cell(120, 5, url, new_x="LMARGIN", new_y="NEXT")

        # 案内文
        self.set_xy(text_x, start_y + 32)
        self.set_font("Helvetica", "", 8)
        self.multi_cell(120, 4, (
            "QR code or URL above to access your stress check.\n"
            "Your responses are confidential."
        ))

        self.set_y(start_y + 58)


def generate_token_pdf(tokens, base_url):
    """
    トークン一覧からPDFを生成

    Args:
        tokens: AccessTokenオブジェクトのリスト
        base_url: サーバーのベースURL

    Returns:
        PDFのバイト列
    """
    pdf = TokenPDF()
    pdf.add_page()

    for tk in tokens:
        url = f"{base_url}/survey/{tk.token}"
        dept_name = tk.employee.department.name if tk.employee.department else ""

        # QRコード生成
        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data(url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")

        # 一時的にバイトIOに保存
        qr_bytes = io.BytesIO()
        qr_img.save(qr_bytes, format="PNG")
        qr_bytes.seek(0)

        # PDFにカードを追加
        pdf.add_token_card(
            name=tk.employee.name,
            department=dept_name,
            url=url,
            token=tk.token,
            qr_img_path=qr_bytes,
        )

    return pdf.output()
