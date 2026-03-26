import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
from datetime import datetime, date, timedelta

PRIMARY = "#003f88"
ACCENT  = "#0066cc"
GREEN   = "#1A936F"
RED     = "#C0392B"

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

from share_utils import share_pdf_button
from mobile_css import inject_mobile_css
inject_mobile_css()
st.page_link("app.py", label="← All Tools")

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
        _week_labels = [f"W{w+1} ({(start_date + timedelta(weeks=w)).strftime('%d %b')})" for w in range(13)]
        _df = pd.DataFrame({"Week": _week_labels, "Amount ($)": [0.0] * 13})
        _edited = st.data_editor(
            _df,
            key=f"in_{cat}",
            hide_index=True,
            use_container_width=True,
            column_config={
                "Week": st.column_config.TextColumn("Week", disabled=True, width="medium"),
                "Amount ($)": st.column_config.NumberColumn("Amount ($)", min_value=0.0, step=100.0, format="$%.0f"),
            },
        )
        inflow_data[cat] = _edited["Amount ($)"].tolist()

# ── Outflow categories ────────────────────────────────────────────────────────
st.header("Weekly Outflows")
st.caption("Enter expected cash payments per week.")

OUTFLOW_CATS = ["Payroll", "Suppliers / COGS", "Rent & Utilities", "Loan Repayments",
                "Tax Payments", "Capex", "Other Payments"]
outflow_data = {}
for cat in OUTFLOW_CATS:
    with st.expander(f"📤 {cat}", expanded=(cat == "Payroll")):
        _week_labels = [f"W{w+1} ({(start_date + timedelta(weeks=w)).strftime('%d %b')})" for w in range(13)]
        _df = pd.DataFrame({"Week": _week_labels, "Amount ($)": [0.0] * 13})
        _edited = st.data_editor(
            _df,
            key=f"out_{cat}",
            hide_index=True,
            use_container_width=True,
            column_config={
                "Week": st.column_config.TextColumn("Week", disabled=True, width="medium"),
                "Amount ($)": st.column_config.NumberColumn("Amount ($)", min_value=0.0, step=100.0, format="$%.0f"),
            },
        )
        outflow_data[cat] = _edited["Amount ($)"].tolist()

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
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pdf_utils import (
    new_doc, build_header, section_heading, kpi_row,
    data_table, chart_image, spacer, NumberedCanvas, CONTENT_W,
)
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors as rl_colors

st.subheader("Export")
logo_file = st.file_uploader("Upload company logo (optional)", type=["png", "jpg", "jpeg"], key="logo")
logo_bytes = logo_file.read() if logo_file else None

def build_pdf():
    buf = io.BytesIO()
    doc = new_doc(buf)
    story = []

    story.append(build_header("13-Week Cash Flow Forecast", company, logo_bytes=logo_bytes))
    story.append(spacer(0.4))

    story.append(kpi_row([
        ("Opening Balance",      f"${opening_balance:,.0f}", f"Start of forecast"),
        ("Total Inflows",        f"${total_in:,.0f}",        "13-week total"),
        ("Total Outflows",       f"${total_out:,.0f}",       "13-week total"),
        ("Closing Balance W13",  f"${closing[-1]:,.0f}",     f"Net {closing[-1]-opening_balance:+,.0f}"),
    ]))
    story.append(spacer(0.4))

    story.append(section_heading("Weekly Cash Flow Chart"))
    story.append(spacer(0.2))
    story.append(chart_image(fig, height_ratio=0.50))
    story.append(spacer(0.4))

    story.append(section_heading("Weekly Forecast Summary"))
    story.append(spacer(0.2))

    key_row_keys = ["Opening Balance", "Total Inflows", "Total Outflows", "Net Cash Flow", "Closing Balance"]
    tbl_headers  = [""] + [f"W{i+1}" for i in range(13)]
    tbl_rows     = [[lbl] + [f"${v:,.0f}" for v in rows[lbl]] for lbl in key_row_keys]
    cw = CONTENT_W / 14
    story.append(data_table(tbl_headers, tbl_rows, col_widths=[cw * 1.8] + [cw * 0.94] * 13))

    doc.build(story, canvasmaker=NumberedCanvas)
    buf.seek(0)
    return buf

if st.button("📄 Export PDF Report", type="primary"):
    try:
        pdf = build_pdf()
        st.download_button("⬇️ Download PDF", pdf,
                           file_name=f"cashflow_{company.replace(' ','_')}.pdf",
                           mime="application/pdf", use_container_width=True)
        share_pdf_button(pdf, f"cashflow_{company.replace(' ','_')}.pdf")
    except Exception as e:
        st.error(f"PDF generation error: {e}")
