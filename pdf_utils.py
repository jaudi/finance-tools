"""
FinancePlots — Shared PDF utilities
Premium report styling used by all tools.
"""
from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image,
    Table, TableStyle, HRFlowable,
)
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.utils import ImageReader

# ── Brand colours ───────────────────────────────────────────────────────────
C_NAVY   = colors.HexColor("#0A1628")   # header / dark bg
C_BLUE   = colors.HexColor("#2563EB")   # accent / buttons
C_LBLUE  = colors.HexColor("#DBEAFE")   # table alt row
C_MID    = colors.HexColor("#1E3A5F")   # sub-header bg
C_WHITE  = colors.white
C_GRAY   = colors.HexColor("#6B7280")
C_LGRAY  = colors.HexColor("#F3F4F6")
C_GREEN  = colors.HexColor("#059669")
C_RED    = colors.HexColor("#DC2626")
C_BORDER = colors.HexColor("#E5E7EB")
C_LINE   = colors.HexColor("#2563EB")

PAGE_W = A4[0]
PAGE_H = A4[1]
MARGIN = 1.8 * cm
CONTENT_W = PAGE_W - 2 * MARGIN


# ── Text styles ──────────────────────────────────────────────────────────────
def styles():
    return {
        "title": ParagraphStyle(
            "title", fontName="Helvetica-Bold", fontSize=22,
            textColor=C_WHITE, alignment=TA_LEFT, leading=26,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", fontName="Helvetica", fontSize=10,
            textColor=colors.HexColor("#93C5FD"), alignment=TA_LEFT, leading=14,
        ),
        "date": ParagraphStyle(
            "date", fontName="Helvetica", fontSize=9,
            textColor=colors.HexColor("#93C5FD"), alignment=TA_RIGHT,
        ),
        "section": ParagraphStyle(
            "section", fontName="Helvetica-Bold", fontSize=11,
            textColor=C_WHITE, alignment=TA_LEFT, leading=14,
        ),
        "body": ParagraphStyle(
            "body", fontName="Helvetica", fontSize=9,
            textColor=colors.HexColor("#374151"), leading=14,
        ),
        "kpi_label": ParagraphStyle(
            "kpi_label", fontName="Helvetica-Bold", fontSize=8,
            textColor=C_GRAY, alignment=TA_CENTER,
        ),
        "kpi_value": ParagraphStyle(
            "kpi_value", fontName="Helvetica-Bold", fontSize=18,
            textColor=C_NAVY, alignment=TA_CENTER,
        ),
        "kpi_sub": ParagraphStyle(
            "kpi_sub", fontName="Helvetica", fontSize=8,
            textColor=C_GRAY, alignment=TA_CENTER,
        ),
        "footer": ParagraphStyle(
            "footer", fontName="Helvetica", fontSize=8,
            textColor=C_GRAY, alignment=TA_CENTER,
        ),
        "th": ParagraphStyle(
            "th", fontName="Helvetica-Bold", fontSize=9,
            textColor=C_WHITE, alignment=TA_CENTER,
        ),
        "td": ParagraphStyle(
            "td", fontName="Helvetica", fontSize=9,
            textColor=colors.HexColor("#1F2937"), alignment=TA_CENTER,
        ),
        "td_left": ParagraphStyle(
            "td_left", fontName="Helvetica", fontSize=9,
            textColor=colors.HexColor("#1F2937"), alignment=TA_LEFT,
        ),
    }


# ── Page numbering callback ──────────────────────────────────────────────────
class NumberedCanvas(pdf_canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pages = []

    def showPage(self):
        self._pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._pages)
        for page_dict in self._pages:
            self.__dict__.update(page_dict)
            self._draw_footer(total)
            super().showPage()
        super().save()

    def _draw_footer(self, total):
        page_num = self._pageNumber
        self.saveState()
        # thin blue line
        self.setStrokeColor(C_BLUE)
        self.setLineWidth(0.8)
        self.line(MARGIN, 1.4 * cm, PAGE_W - MARGIN, 1.4 * cm)
        # left: brand
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(C_NAVY)
        self.drawString(MARGIN, 1.0 * cm, "FinancePlots")
        self.setFont("Helvetica", 8)
        self.setFillColor(C_GRAY)
        self.drawString(MARGIN + 65, 1.0 * cm, "· financeplots.com · Not financial advice")
        # right: page number
        self.setFont("Helvetica", 8)
        text = f"Page {page_num} of {total}"
        self.drawRightString(PAGE_W - MARGIN, 1.0 * cm, text)
        self.restoreState()


# ── Header builder ───────────────────────────────────────────────────────────
def build_header(report_title: str, subtitle: str, logo_bytes=None, st=styles()) -> Table:
    """Full-width branded header block. Pass logo_bytes (PNG/JPG) to show a company logo."""
    date_str = datetime.now().strftime("%B %d, %Y")

    if logo_bytes:
        reader = ImageReader(BytesIO(logo_bytes))
        img_w, img_h = reader.getSize()
        aspect = img_w / img_h
        max_w = CONTENT_W * 0.18
        max_h = 1.2 * cm
        if aspect > max_w / max_h:
            w, h = max_w, max_w / aspect
        else:
            h, w = max_h, max_h * aspect
        left_cell = Image(BytesIO(logo_bytes), width=w, height=h)
    else:
        left_cell = Table(
            [[
                Paragraph("<b>Finance</b>Plots", ParagraphStyle(
                    "brand", fontName="Helvetica-Bold", fontSize=13,
                    textColor=colors.HexColor("#93C5FD"), alignment=TA_LEFT,
                )),
            ]],
            colWidths=[CONTENT_W * 0.22],
        )
        left_cell.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))

    title_cell = [
        Paragraph(report_title, st["title"]),
        Paragraph(subtitle, st["subtitle"]),
    ]
    date_cell = Paragraph(f"Generated<br/>{date_str}", st["date"])

    hdr = Table(
        [[left_cell, title_cell, date_cell]],
        colWidths=[CONTENT_W * 0.22, CONTENT_W * 0.52, CONTENT_W * 0.26],
    )
    hdr.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (2, 0), (2, 0), "RIGHT"),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    return hdr


# ── Section heading ──────────────────────────────────────────────────────────
def section_heading(title: str, st=styles()) -> Table:
    """Coloured section label bar."""
    tbl = Table([[Paragraph(f"  {title}", st["section"])]], colWidths=[CONTENT_W])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_MID),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ROUNDEDCORNERS", [3, 3, 3, 3]),
    ]))
    return tbl


# ── KPI row ──────────────────────────────────────────────────────────────────
def kpi_row(items: list[tuple[str, str, str]], st=styles()) -> Table:
    """
    items: list of (label, value, sub_text)
    Returns a full-width table of KPI cards.
    """
    n = len(items)
    col_w = CONTENT_W / n
    cells = []
    for label, value, sub in items:
        cell = [
            Paragraph(label.upper(), st["kpi_label"]),
            Spacer(1, 3),
            Paragraph(value, st["kpi_value"]),
            Spacer(1, 2),
            Paragraph(sub, st["kpi_sub"]),
        ]
        cells.append(cell)

    tbl = Table([cells], colWidths=[col_w] * n)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_LGRAY),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LINEABOVE",     (0, 0), (-1, 0), 3, C_BLUE),
        ("LINEBEFORE",    (1, 0), (-1, 0), 0.5, C_BORDER),
        ("GRID",          (0, 0), (-1, -1), 0, colors.white),
        ("BOX",           (0, 0), (-1, -1), 0.5, C_BORDER),
    ]))
    return tbl


# ── Data table ───────────────────────────────────────────────────────────────
def data_table(headers: list[str], rows: list[list], col_widths=None) -> Table:
    """
    Styled data table with navy header and alternating rows.
    headers: list of column header strings
    rows: list of row lists (strings)
    """
    st = styles()
    if col_widths is None:
        n = len(headers)
        col_widths = [CONTENT_W / n] * n

    tbl_data = [[Paragraph(h, st["th"]) for h in headers]]
    for i, row in enumerate(rows):
        styled_row = []
        for j, cell in enumerate(row):
            p_style = st["td_left"] if j == 0 else st["td"]
            styled_row.append(Paragraph(str(cell), p_style))
        tbl_data.append(styled_row)

    tbl = Table(tbl_data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ("BACKGROUND",    (0, 0), (-1, 0), C_NAVY),
        ("TEXTCOLOR",     (0, 0), (-1, 0), C_WHITE),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",          (0, 0), (-1, -1), 0.4, C_BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_WHITE, C_LBLUE]),
    ]
    tbl.setStyle(TableStyle(style_cmds))
    return tbl


# ── Chart image ──────────────────────────────────────────────────────────────
def chart_image(fig, width=None, height_ratio=0.50) -> Image:
    """Convert a Plotly figure to a ReportLab Image."""
    if width is None:
        width = CONTENT_W
    img_bytes = fig.to_image(format="png", width=1100, height=int(1100 * height_ratio), scale=2)
    return Image(BytesIO(img_bytes), width=width, height=width * height_ratio)


# ── Document builder ─────────────────────────────────────────────────────────
def new_doc(buf: BytesIO) -> SimpleDocTemplate:
    return SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=1.4 * cm,
        bottomMargin=2.2 * cm,
    )


def spacer(h=0.3) -> Spacer:
    return Spacer(1, h * cm)


def divider() -> HRFlowable:
    return HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceAfter=4)
