import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
from datetime import datetime

PRIMARY = "#003f88"
ACCENT  = "#0066cc"
GREEN   = "#1A936F"
RED     = "#C0392B"

st.set_page_config(page_title="Valuation Calculator · Finance Tools", page_icon="🏢", layout="wide")

st.markdown("""
    <style>
        .block-container { padding-top: 1.5rem; }
        h2 { font-size: 1.25rem !important; color: #333;
             border-bottom: 2px solid #eee; padding-bottom: 6px; margin-top: 1.5rem; }
        .ev-caption { color: #888; font-size: 0.88rem; margin-top: -6px; margin-bottom: 1rem; }
        .kpi-card  { background: #f7f9fc; border-left: 4px solid #0066cc;
                     border-radius: 6px; padding: 0.9rem 1rem; height: 100%; }
        .kpi-green { border-left-color: #1A936F !important; }
        .kpi-label { font-size: 0.78rem; color: #888; font-weight: 600; text-transform: uppercase; }
        .kpi-value { font-size: 1.6rem; font-weight: 800; color: #003f88; line-height: 1.2; }
        .kpi-sub   { font-size: 0.78rem; color: #999; margin-top: 2px; }
        .method-header { font-size: 1rem; font-weight: 700; color: #003f88; margin-bottom: 0.3rem; }
    </style>
""", unsafe_allow_html=True)

from mobile_css import inject_mobile_css
inject_mobile_css()
st.page_link("app.py", label="← All Tools")

st.title("🏢 Business Valuation Calculator")
st.markdown(
    '<p class="ev-caption">DCF · EBITDA Multiple · Revenue Multiple · Comparable analysis · PDF export</p>',
    unsafe_allow_html=True,
)

# ── Company info ───────────────────────────────────────────────────────────────
st.header("Company Information")
ci1, ci2, ci3 = st.columns(3)
with ci1:
    company  = st.text_input("Company name", value="My Company")
with ci2:
    industry = st.selectbox("Industry", [
        "SaaS / Software", "E-commerce", "Manufacturing", "Services / Consulting",
        "Healthcare", "Finance", "Retail", "Real Estate", "Other",
    ])
with ci3:
    currency = st.selectbox("Currency", ["USD ($)", "EUR (€)", "GBP (£)"])
sym = currency.split("(")[1].replace(")", "")

# ── Method 1: DCF ──────────────────────────────────────────────────────────────
st.header("Method 1 — Discounted Cash Flow (DCF)")

d1, d2, d3 = st.columns(3)
with d1:
    fcf_base    = st.number_input(f"Current Free Cash Flow ({sym})", value=500000, step=10000)
    fcf_growth  = st.slider("FCF growth rate (years 1-5, %)", 0.0, 50.0, 15.0, 0.5)
with d2:
    terminal_growth = st.slider("Terminal growth rate (%)", 0.0, 5.0, 2.5, 0.1)
    wacc            = st.slider("Discount rate / WACC (%)", 1.0, 30.0, 12.0, 0.5)
with d3:
    debt       = st.number_input(f"Net Debt ({sym})", value=0, step=10000)
    cash_equiv = st.number_input(f"Cash & Equivalents ({sym})", value=100000, step=10000)

fcf_list = []
pv_list  = []
fcf = fcf_base
for yr in range(1, 6):
    fcf *= (1 + fcf_growth / 100)
    pv   = fcf / ((1 + wacc / 100) ** yr)
    fcf_list.append(fcf)
    pv_list.append(pv)

if wacc <= terminal_growth:
    st.error(
        f"⚠️ WACC ({wacc}%) must be greater than the terminal growth rate ({terminal_growth}%) "
        "for the DCF formula to work. Please adjust the sliders."
    )
    st.stop()

terminal_value    = fcf_list[-1] * (1 + terminal_growth / 100) / ((wacc - terminal_growth) / 100)
pv_terminal       = terminal_value / ((1 + wacc / 100) ** 5)
enterprise_dcf    = sum(pv_list) + pv_terminal
equity_dcf        = enterprise_dcf - debt + cash_equiv

# ── Method 2: EBITDA Multiple ─────────────────────────────────────────────────
st.header("Method 2 — EBITDA Multiple")

e1, e2, e3 = st.columns(3)
EBITDA_DEFAULTS = {
    "SaaS / Software": (12.0, 18.0), "E-commerce": (8.0, 14.0),
    "Manufacturing": (6.0, 10.0), "Services / Consulting": (7.0, 12.0),
    "Healthcare": (10.0, 16.0), "Finance": (8.0, 14.0),
    "Retail": (5.0, 9.0), "Real Estate": (12.0, 20.0), "Other": (7.0, 12.0),
}
def_lo, def_hi = EBITDA_DEFAULTS[industry]

with e1:
    ebitda = st.number_input(f"EBITDA ({sym})", value=800000, step=10000)
with e2:
    ebitda_mult_lo = st.number_input("Multiple — Low", value=def_lo, step=0.5)
    ebitda_mult_hi = st.number_input("Multiple — High", value=def_hi, step=0.5)
with e3:
    ebitda_mult_mid = (ebitda_mult_lo + ebitda_mult_hi) / 2
    st.metric("Suggested mid multiple", f"{ebitda_mult_mid:.1f}x",
              help=f"Based on {industry} sector benchmarks")

ev_ebitda_lo  = ebitda * ebitda_mult_lo
ev_ebitda_mid = ebitda * ebitda_mult_mid
ev_ebitda_hi  = ebitda * ebitda_mult_hi
eq_ebitda_lo  = ev_ebitda_lo  - debt + cash_equiv
eq_ebitda_mid = ev_ebitda_mid - debt + cash_equiv
eq_ebitda_hi  = ev_ebitda_hi  - debt + cash_equiv

# ── Method 3: Revenue Multiple ────────────────────────────────────────────────
st.header("Method 3 — Revenue Multiple")

r1, r2, r3 = st.columns(3)
REV_DEFAULTS = {
    "SaaS / Software": (4.0, 10.0), "E-commerce": (1.0, 3.0),
    "Manufacturing": (0.5, 1.5), "Services / Consulting": (1.0, 2.5),
    "Healthcare": (2.0, 5.0), "Finance": (1.5, 4.0),
    "Retail": (0.3, 0.8), "Real Estate": (1.0, 3.0), "Other": (1.0, 3.0),
}
rev_lo, rev_hi = REV_DEFAULTS[industry]

with r1:
    revenue = st.number_input(f"Annual Revenue ({sym})", value=2000000, step=50000)
with r2:
    rev_mult_lo = st.number_input("Revenue Multiple — Low", value=rev_lo, step=0.1)
    rev_mult_hi = st.number_input("Revenue Multiple — High", value=rev_hi, step=0.1)
with r3:
    rev_mult_mid = (rev_mult_lo + rev_mult_hi) / 2
    st.metric("Suggested mid multiple", f"{rev_mult_mid:.1f}x",
              help=f"Based on {industry} sector benchmarks")

ev_rev_lo  = revenue * rev_mult_lo
ev_rev_mid = revenue * rev_mult_mid
ev_rev_hi  = revenue * rev_mult_hi
eq_rev_lo  = ev_rev_lo  - debt + cash_equiv
eq_rev_mid = ev_rev_mid - debt + cash_equiv
eq_rev_hi  = ev_rev_hi  - debt + cash_equiv

# ── Summary ────────────────────────────────────────────────────────────────────
st.header("Valuation Summary")

k1, k2, k3, k4 = st.columns(4)
avg_low  = (equity_dcf * 0.5 + eq_ebitda_lo * 0.3 + eq_rev_lo * 0.2)
avg_high = (equity_dcf * 0.5 + eq_ebitda_hi * 0.3 + eq_rev_hi * 0.2)

for col, label, value, sub in [
    (k1, "DCF Equity Value",          f"{sym}{equity_dcf/1e6:.2f}M", f"EV: {sym}{enterprise_dcf/1e6:.2f}M"),
    (k2, "EBITDA Multiple (Mid)",     f"{sym}{eq_ebitda_mid/1e6:.2f}M", f"Range: {sym}{eq_ebitda_lo/1e6:.1f}M–{sym}{eq_ebitda_hi/1e6:.1f}M"),
    (k3, "Revenue Multiple (Mid)",    f"{sym}{eq_rev_mid/1e6:.2f}M",    f"Range: {sym}{eq_rev_lo/1e6:.1f}M–{sym}{eq_rev_hi/1e6:.1f}M"),
    (k4, "Blended Range",             f"{sym}{avg_low/1e6:.1f}M–{sym}{avg_high/1e6:.1f}M", "50% DCF / 30% EBITDA / 20% Rev"),
]:
    with col:
        st.markdown(
            f'<div class="kpi-card kpi-green">'
            f'<div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div>'
            f'<div class="kpi-sub">{sub}</div>'
            f'</div>', unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

# ── Valuation bridge chart ─────────────────────────────────────────────────────
methods  = ["DCF", "EBITDA Low", "EBITDA Mid", "EBITDA High", "Revenue Low", "Revenue Mid", "Revenue High"]
eq_vals  = [equity_dcf, eq_ebitda_lo, eq_ebitda_mid, eq_ebitda_hi, eq_rev_lo, eq_rev_mid, eq_rev_hi]
bar_clrs = [ACCENT, "#B0C4DE", RED, "#B0C4DE", "#B0C4DE", GREEN, "#B0C4DE"]

fig = go.Figure(go.Bar(
    x=methods, y=[v/1e6 for v in eq_vals],
    marker_color=bar_clrs, opacity=0.88,
    text=[f"{sym}{v/1e6:.2f}M" for v in eq_vals],
    textposition="outside",
))
fig.update_layout(
    title="Equity Valuation by Method",
    title_font=dict(size=18, color=PRIMARY),
    height=440,
    font=dict(family="Inter, Arial, sans-serif", size=12),
    paper_bgcolor="white", plot_bgcolor="rgba(248,249,252,1)",
    margin=dict(t=60, b=50, l=70, r=20),
    yaxis_title=f"Equity Value ({sym}M)",
    bargap=0.3,
)
fig.update_xaxes(showgrid=False, showline=True, linecolor="rgba(0,0,0,0.12)")
fig.update_yaxes(gridcolor="rgba(0,0,0,0.06)", zeroline=False)
st.plotly_chart(fig, use_container_width=True)

# ── DCF detail table ───────────────────────────────────────────────────────────
st.header("DCF Detail")
dcf_rows = []
fcf = fcf_base
for yr in range(1, 6):
    fcf *= (1 + fcf_growth / 100)
    pv   = fcf / ((1 + wacc / 100) ** yr)
    dcf_rows.append({
        "Year": f"Year {yr}",
        f"FCF ({sym})": f"{sym}{fcf:,.0f}",
        "Discount Factor": f"{1/((1+wacc/100)**yr):.4f}",
        f"PV of FCF ({sym})": f"{sym}{pv:,.0f}",
    })
dcf_rows.append({
    "Year": "Terminal Value",
    f"FCF ({sym})": f"{sym}{terminal_value:,.0f}",
    "Discount Factor": f"{1/((1+wacc/100)**5):.4f}",
    f"PV of FCF ({sym})": f"{sym}{pv_terminal:,.0f}",
})
st.dataframe(pd.DataFrame(dcf_rows), use_container_width=True, hide_index=True)

# ── PDF export ─────────────────────────────────────────────────────────────────
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pdf_utils import (
    new_doc, build_header, section_heading, kpi_row,
    data_table, chart_image, spacer, NumberedCanvas,
)

st.subheader("Export")
logo_file = st.file_uploader("Upload company logo (optional)", type=["png", "jpg", "jpeg"], key="logo")
logo_bytes = logo_file.read() if logo_file else None

def build_pdf():
    buf = io.BytesIO()
    doc = new_doc(buf)
    story = []

    story.append(build_header("Business Valuation (DCF)", f"{company} · {industry}", logo_bytes=logo_bytes))
    story.append(spacer(0.4))

    story.append(kpi_row([
        ("DCF Equity Value",   f"{sym}{equity_dcf/1e6:.2f}M",  f"EV: {sym}{enterprise_dcf/1e6:.2f}M"),
        ("EBITDA Multiple",    f"{sym}{eq_ebitda_mid/1e6:.2f}M", f"Range: {sym}{eq_ebitda_lo/1e6:.1f}M–{sym}{eq_ebitda_hi/1e6:.1f}M"),
        ("Revenue Multiple",   f"{sym}{eq_rev_mid/1e6:.2f}M",   f"Range: {sym}{eq_rev_lo/1e6:.1f}M–{sym}{eq_rev_hi/1e6:.1f}M"),
        ("Blended Range",      f"{sym}{avg_low/1e6:.1f}M–{sym}{avg_high/1e6:.1f}M", "50% DCF / 30% EBITDA / 20% Rev"),
    ]))
    story.append(spacer(0.4))

    story.append(section_heading("Valuation by Method"))
    story.append(spacer(0.2))
    story.append(chart_image(fig, height_ratio=0.46))
    story.append(spacer(0.4))

    story.append(section_heading("DCF Detail"))
    story.append(spacer(0.2))
    story.append(data_table(
        ["Year", f"FCF ({sym})", "Discount Factor", f"PV ({sym})"],
        [[r["Year"], r[f"FCF ({sym})"], r["Discount Factor"], r[f"PV of FCF ({sym})"]]
         for r in dcf_rows],
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    buf.seek(0)
    return buf

if st.button("📄 Export PDF Report", type="primary"):
    try:
        pdf = build_pdf()
        st.download_button("⬇️ Download PDF", pdf,
                           file_name=f"valuation_{company.replace(' ','_')}.pdf",
                           mime="application/pdf", use_container_width=True)
        st.caption("📧 To share by email: download above and attach the PDF.")
    except Exception as e:
        st.error(f"PDF generation error: {e}")
