import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
from datetime import datetime, date, timedelta

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image,
    Table, TableStyle, HRFlowable,
)

PRIMARY = "#003f88"
ACCENT  = "#0066cc"
GREEN   = "#1A936F"
RED     = "#C0392B"
PDF_HDR = colors.HexColor("#003f88")
PDF_ACC = colors.HexColor("#0066cc")
PDF_ALT = colors.HexColor("#EAF1FB")

st.set_page_config(page_title="Cash Flow Forecast · Finance Tools", page_icon="💧", layout="wide")

st.markdown("""
    <style>
        .block-container { padding-top: 1.5rem; }
        h2 { font-size: 1.25rem !important; color: #333;
             border-bottom: 2px solid #eee; padding-bottom: 6px; margin-top: 1.5rem; }
        .ev-caption { color: #888; font-size: 0.88rem; margin-top: -6px; margin-bottom: 1rem; }
        .kpi-card { background: #f7f9fc; border-left: 4px solid #0066cc;
                    border-radius: 6px; padding: 0.9rem 1rem; height: 100%; }
        .kpi-green{ border-left-color: #1A936F !important; }
        .kpi-red  { border-left-color: #C0392B !important; }
        .kpi-label{ font-size: 0.78rem; color: #888; font-weight: 600; text-transform: uppercase; }
        .kpi-value{ font-size: 1.6rem; font-weight: 800; color: #003f88; line-height: 1.2; }
        .kpi-sub  { font-size: 0.78rem; color: #999; margin-top: 2px; }
    </style>
""", unsafe_allow_html=True)

st.title("💧 13-Week Cash Flow Forecast")
st.markdown(
    '<p class="ev-caption">Rolling weekly cash forecast · Inflows · Outflows · Closing balance · PDF export</p>',
    unsafe_allow_html=True,
)

# ── Settings ──────────────────────────────────────────────────────────────────
st.header("Settings")
c1, c2, c3 = st.columns(3)
with c1:
    company = st.text_input("Company name", value="My Company")
with c2:
    start_date = st.date_input("Forecast start date", value=date.today())
with c3:
    opening_balance = st.number_input("Opening cash balance ($)", value=50000, step=1000)

# ── Inflow categories ─────────────────────────────────────────────────────────
st.header("Weekly Inflows")
st.caption("Enter expected cash receipts per week. Leave 0 if none.")

INFLOW_CATS = ["Customer Receipts", "Loan Proceeds", "Asset Sales", "Other Income"]
inflow_data = {}
for cat in INFLOW_CATS:
    with st.expander(f"📥 {cat}", expanded=(cat == "Customer Receipts")):
        cols = st.columns(13)
        vals = []
        for w in range(13):
            with cols[w]:
                v = st.number_input(f"W{w+1}", min_value=0.0, value=0.0,
                                    step=100.0, key=f"in_{cat}_{w}", label_visibility="visible")
                vals.append(v)
        inflow_data[cat] = vals

# ── Outflow categories ────────────────────────────────────────────────────────
st.header("Weekly Outflows")
st.caption("Enter expected cash payments per week.")

OUTFLOW_CATS = ["Payroll", "Suppliers / COGS", "Rent & Utilities", "Loan Repayments",
                "Tax Payments", "Capex", "Other Payments"]
outflow_data = {}
for cat in OUTFLOW_CATS:
    with st.expander(f"📤 {cat}", expanded=(cat == "Payroll")):
        cols = st.columns(13)
        vals = []
        for w in range(13):
            with cols[w]:
                v = st.number_input(f"W{w+1}", min_value=0.0, value=0.0,
                                    step=100.0, key=f"out_{cat}_{w}", label_visibility="visible")
                vals.append(v)
        outflow_data[cat] = vals

# ── Build forecast table ───────────────────────────────────────────────────────
weeks = [f"W{i+1}\n{(start_date + timedelta(weeks=i)).strftime('%d %b')}" for i in range(13)]
week_labels = [f"W{i+1} {(start_date + timedelta(weeks=i)).strftime('%d %b')}" for i in range(13)]

total_inflows  = [sum(inflow_data[c][w] for c in INFLOW_CATS) for w in range(13)]
total_outflows = [sum(outflow_data[c][w] for c in OUTFLOW_CATS) for w in range(13)]
net_flow       = [total_inflows[w] - total_outflows[w] for w in range(13)]

closing = []
bal = opening_balance
for w in range(13):
    bal += net_flow[w]
    closing.append(bal)

opening = [opening_balance] + closing[:-1]

# ── KPI cards ─────────────────────────────────────────────────────────────────
st.header("Summary")
k1, k2, k3, k4 = st.columns(4)
min_bal    = min(closing)
max_bal    = max(closing)
total_in   = sum(total_inflows)
total_out  = sum(total_outflows)
min_week   = week_labels[closing.index(min_bal)]
max_week   = week_labels[closing.index(max_bal)]
color_min  = "kpi-red" if min_bal < 0 else "kpi-green"

for col, label, value, sub, extra_cls in [
    (k1, "Total Inflows",  f"${total_in:,.0f}",  "13-week total", ""),
    (k2, "Total Outflows", f"${total_out:,.0f}", "13-week total", "kpi-red"),
    (k3, "Closing Balance (W13)", f"${closing[-1]:,.0f}", f"Net {closing[-1]-opening_balance:+,.0f}", "kpi-green" if closing[-1] >= 0 else "kpi-red"),
    (k4, "Lowest Balance", f"${min_bal:,.0f}", min_week, color_min),
]:
    with col:
        st.markdown(
            f'<div class="kpi-card {extra_cls}">'
            f'<div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div>'
            f'<div class="kpi-sub">{sub}</div>'
            f'</div>', unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

# ── Chart ─────────────────────────────────────────────────────────────────────
fig = go.Figure()
fig.add_bar(x=week_labels, y=total_inflows,  name="Total Inflows",
            marker_color=ACCENT, opacity=0.85)
fig.add_bar(x=week_labels, y=[-v for v in total_outflows], name="Total Outflows",
            marker_color=RED, opacity=0.85)
fig.add_scatter(x=week_labels, y=closing, name="Closing Balance",
                mode="lines+markers",
                line=dict(color=GREEN, width=3),
                marker=dict(size=7, color=GREEN))
fig.add_hline(y=0, line_dash="dash", line_color="rgba(0,0,0,0.2)")

fig.update_layout(
    barmode="relative",
    title="Weekly Cash Flow & Running Balance",
    title_font=dict(size=18, color=PRIMARY),
    height=460,
    font=dict(family="Inter, Arial, sans-serif", size=12),
    paper_bgcolor="white", plot_bgcolor="rgba(248,249,252,1)",
    margin=dict(t=60, b=50, l=60, r=20),
    legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="rgba(0,0,0,0.08)", borderwidth=1),
    bargap=0.25,
)
fig.update_xaxes(showgrid=False, showline=True, linecolor="rgba(0,0,0,0.12)")
fig.update_yaxes(gridcolor="rgba(0,0,0,0.06)", zeroline=True, zerolinecolor="rgba(0,0,0,0.15)")
st.plotly_chart(fig, use_container_width=True)

# ── Forecast table ─────────────────────────────────────────────────────────────
st.header("Detailed Forecast Table")
rows = {"Opening Balance": opening}
for cat in INFLOW_CATS:
    rows[f"  ↳ {cat}"] = inflow_data[cat]
rows["Total Inflows"] = total_inflows
for cat in OUTFLOW_CATS:
    rows[f"  ↳ {cat}"] = outflow_data[cat]
rows["Total Outflows"] = total_outflows
rows["Net Cash Flow"]  = net_flow
rows["Closing Balance"] = closing

df = pd.DataFrame(rows, index=week_labels).T
df_display = df.map(lambda x: f"${x:,.0f}")
st.dataframe(df_display, use_container_width=True)

# ── PDF export ────────────────────────────────────────────────────────────────
st.subheader("Export")

def build_pdf():
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=1.5*cm, bottomMargin=2*cm)
    W = A4[0] - 4*cm

    h_style  = ParagraphStyle("h",  fontName="Helvetica-Bold", fontSize=20,
                               textColor=colors.white, alignment=TA_LEFT)
    s_style  = ParagraphStyle("s",  fontName="Helvetica", fontSize=9,
                               textColor=colors.HexColor("#ccddee"), alignment=TA_LEFT)
    sec_style= ParagraphStyle("sc", fontName="Helvetica-Bold", fontSize=11,
                               textColor=colors.HexColor(PRIMARY), spaceBefore=12, spaceAfter=4)
    ft_style = ParagraphStyle("ft", fontName="Helvetica", fontSize=8,
                               textColor=colors.HexColor("#999999"), alignment=TA_CENTER)

    story = []

    hdr = Table([[Paragraph("FinancePlots", h_style),
                  Paragraph(f"13-Week Cash Flow<br/>{company}", h_style),
                  Paragraph(f"Generated\n{datetime.now().strftime('%B %d, %Y')}", s_style)]],
                colWidths=[W*0.22, W*0.50, W*0.28])
    hdr.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), PDF_HDR),
        ("TOPPADDING",    (0,0), (-1,-1), 14), ("BOTTOMPADDING", (0,0), (-1,-1), 14),
        ("LEFTPADDING",   (0,0), (-1,-1), 14), ("RIGHTPADDING",  (0,0), (-1,-1), 14),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"), ("ALIGN", (2,0), (2,0), "RIGHT"),
    ]))
    story.append(hdr)
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=3, color=PDF_ACC, spaceAfter=8))

    # KPI summary table
    kpi_data = [
        ["Opening Balance", "Total Inflows", "Total Outflows", "Closing Balance (W13)"],
        [f"${opening_balance:,.0f}", f"${total_in:,.0f}", f"${total_out:,.0f}", f"${closing[-1]:,.0f}"],
    ]
    kpi_tbl = Table(kpi_data, colWidths=[W/4]*4)
    kpi_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), PDF_ACC),
        ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 10),
        ("ALIGN",      (0,0), (-1,-1), "CENTER"),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 7), ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("BACKGROUND", (0,1), (-1,1), PDF_ALT),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#DDDDDD")),
    ]))
    story.append(kpi_tbl)
    story.append(Spacer(1, 0.4*cm))

    # Chart image
    img_bytes = fig.to_image(format="png", width=900, height=460, scale=2)
    story.append(Paragraph("Cash Flow Chart", sec_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#DDDDDD"), spaceAfter=4))
    story.append(Image(io.BytesIO(img_bytes), width=W, height=W*0.50))
    story.append(Spacer(1, 0.4*cm))

    # Forecast table (compact)
    story.append(Paragraph("Weekly Forecast", sec_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#DDDDDD"), spaceAfter=4))

    key_rows = ["Opening Balance", "Total Inflows", "Total Outflows", "Net Cash Flow", "Closing Balance"]
    tbl_header = [""] + [f"W{i+1}" for i in range(13)]
    tbl_data   = [tbl_header]
    for row_label in key_rows:
        row_vals = rows[row_label]
        tbl_data.append([row_label] + [f"${v:,.0f}" for v in row_vals])

    col_w = W / 14
    tbl = Table(tbl_data, colWidths=[col_w*1.8] + [col_w*0.94]*13, repeatRows=1)
    bold_rows = {0, 3, 5, 7, 9}
    tbl_styles = [
        ("BACKGROUND", (0,0), (-1,0), PDF_HDR),
        ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 7),
        ("ALIGN",      (1,0), (-1,-1), "RIGHT"),
        ("ALIGN",      (0,0), (0,-1), "LEFT"),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#DDDDDD")),
    ]
    for ri in range(1, len(tbl_data)):
        if ri % 2 == 0:
            tbl_styles.append(("BACKGROUND", (0,ri), (-1,ri), PDF_ALT))
    tbl.setStyle(TableStyle(tbl_styles))
    story.append(tbl)

    story.append(Spacer(1, 0.6*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#DDDDDD"), spaceAfter=4))
    story.append(Paragraph("Generated by FinancePlots · Confidential · For planning purposes only", ft_style))

    doc.build(story)
    buf.seek(0)
    return buf

if st.button("Generate PDF", type="primary"):
    try:
        pdf = build_pdf()
        st.download_button("📄 Download PDF Report", pdf,
                           file_name=f"cashflow_{company.replace(' ','_')}.pdf",
                           mime="application/pdf", use_container_width=True)
    except Exception as e:
        st.error(f"Error generating PDF: {e}")
