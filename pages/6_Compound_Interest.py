import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io

PRIMARY = "#003f88"
ACCENT  = "#0066cc"
GREEN   = "#1A936F"
GOLD    = "#F39C12"

st.set_page_config(page_title="Compound Interest · Finance Tools", page_icon="📈", layout="wide")

st.markdown("""
    <style>
        .block-container { padding-top: 1.5rem; }
        h2 { font-size: 1.25rem !important; color: #333;
             border-bottom: 2px solid #eee; padding-bottom: 6px; margin-top: 1.5rem; }
        .ev-caption { color: #888; font-size: 0.88rem; margin-top: -6px; margin-bottom: 1rem; }
        .kpi-card  { background: #f7f9fc; border-left: 4px solid #0066cc;
                     border-radius: 6px; padding: 0.9rem 1rem; height: 100%; }
        .kpi-green { border-left-color: #1A936F !important; }
        .kpi-gold  { border-left-color: #F39C12 !important; }
        .kpi-label { font-size: 0.78rem; color: #888; font-weight: 600; text-transform: uppercase; }
        .kpi-value { font-size: 1.6rem; font-weight: 800; color: #003f88; line-height: 1.2; }
        .kpi-sub   { font-size: 0.78rem; color: #999; margin-top: 2px; }
        .bench-box { background: #f0f5ff; border: 1px solid #ccd9f0; border-radius: 8px;
                     padding: 0.8rem 1rem; font-size: 0.82rem; color: #444; line-height: 1.8; }
        .bench-box b { color: #003f88; }
    </style>
""", unsafe_allow_html=True)

from mobile_css import inject_mobile_css
inject_mobile_css()
st.page_link("app.py", label="← All Tools")

st.title("📈 Compound Interest Calculator")
st.markdown(
    '<p class="ev-caption">Initial capital · Regular contributions · Annual return · Investment horizon</p>',
    unsafe_allow_html=True,
)

# ── Inputs ─────────────────────────────────────────────────────────────────────
st.header("Assumptions")
c1, c2 = st.columns(2)

with c1:
    st.subheader("Capital & Contributions")
    initial_capital = st.number_input(
        "Initial capital (€)", min_value=0.0, value=10_000.0, step=500.0, format="%.2f"
    )
    monthly_contribution = st.number_input(
        "Monthly contribution (€)", min_value=0.0, value=500.0, step=50.0, format="%.2f"
    )
    years = st.slider("Investment horizon (years)", min_value=1, max_value=50, value=20)

with c2:
    st.subheader("Return Rate")

    # Preset shortcuts
    preset = st.radio(
        "Use a historical benchmark:",
        options=["S&P 500 (~10%)", "Global equities (~8%)", "Bonds (~4%)", "Savings (~2%)", "Custom"],
        index=1,
        horizontal=True,
    )
    preset_map = {
        "S&P 500 (~10%)":       10.0,
        "Global equities (~8%)": 8.0,
        "Bonds (~4%)":           4.0,
        "Savings (~2%)":         2.0,
    }
    default_rate = preset_map.get(preset, 8.0)
    annual_rate_pct = st.number_input(
        "Annual return (%)",
        min_value=0.0, max_value=50.0,
        value=default_rate,
        step=0.5, format="%.1f",
        disabled=(preset != "Custom"),
    )
    if preset != "Custom":
        annual_rate_pct = default_rate

    st.markdown("""
        <div class="bench-box">
            📊 <b>Historical benchmarks (nominal, long-run averages)</b><br>
            🇺🇸 S&P 500 (1928–2024): ~<b>10%</b>/yr · ~7% after inflation<br>
            🌍 Global equities (MSCI World): ~<b>8%</b>/yr<br>
            🏦 Government bonds: ~<b>4%</b>/yr<br>
            💶 Savings / deposit accounts: ~<b>2%</b>/yr<br>
            <span style="color:#999;font-size:0.78rem;">Past performance does not guarantee future results.</span>
        </div>
    """, unsafe_allow_html=True)

# ── Calculations ───────────────────────────────────────────────────────────────
r_monthly = annual_rate_pct / 100 / 12
months    = years * 12

balance         = initial_capital
total_contrib   = initial_capital
total_interest  = 0.0

rows = []
for m in range(1, months + 1):
    interest      = balance * r_monthly
    balance       = balance + interest + monthly_contribution
    total_interest += interest
    total_contrib  += monthly_contribution

    if m % 12 == 0:
        yr = m // 12
        rows.append({
            "Year":                yr,
            "Portfolio Value":     round(balance, 2),
            "Total Contributed":   round(total_contrib, 2),
            "Interest Earned":     round(total_interest, 2),
        })

final_value       = balance
total_invested    = initial_capital + monthly_contribution * months
return_multiple   = final_value / total_invested if total_invested > 0 else 1.0

df = pd.DataFrame(rows)

# ── KPI cards ──────────────────────────────────────────────────────────────────
st.header("Results")
k1, k2, k3, k4 = st.columns(4)

for col, label, value, sub, cls in [
    (k1, "Final Portfolio Value",  f"€{final_value:,.0f}",     f"After {years} years",                ""),
    (k2, "Total Invested",         f"€{total_invested:,.0f}",  f"Initial + contributions",            ""),
    (k3, "Interest Earned",        f"€{total_interest:,.0f}",  f"{total_interest/final_value*100:.0f}% of final value", "kpi-green"),
    (k4, "Return Multiple",        f"{return_multiple:.1f}×",  f"Every €1 became €{return_multiple:.2f}", "kpi-gold"),
]:
    with col:
        st.markdown(
            f'<div class="kpi-card {cls}">'
            f'<div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div>'
            f'<div class="kpi-sub">{sub}</div>'
            f'</div>', unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

# ── Growth chart ───────────────────────────────────────────────────────────────
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df["Year"], y=df["Interest Earned"],
    name="Interest Earned",
    stackgroup="one",
    fillcolor="rgba(26,147,111,0.55)",
    line=dict(color=GREEN, width=0),
))
fig.add_trace(go.Scatter(
    x=df["Year"],
    y=df["Total Contributed"] - initial_capital,
    name="Monthly Contributions",
    stackgroup="one",
    fillcolor="rgba(0,102,204,0.45)",
    line=dict(color=ACCENT, width=0),
))
fig.add_trace(go.Scatter(
    x=df["Year"],
    y=[initial_capital] * len(df),
    name="Initial Capital",
    stackgroup="one",
    fillcolor="rgba(0,63,136,0.35)",
    line=dict(color=PRIMARY, width=0),
))

fig.update_layout(
    title="Portfolio Growth Over Time",
    title_font=dict(size=18, color=PRIMARY),
    height=460,
    font=dict(family="Inter, Arial, sans-serif", size=12),
    paper_bgcolor="white", plot_bgcolor="rgba(248,249,252,1)",
    margin=dict(t=60, b=50, l=80, r=20),
    xaxis_title="Year",
    yaxis_title="Portfolio Value (€)",
    yaxis_tickprefix="€",
    yaxis_tickformat=",.0f",
    legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="rgba(0,0,0,0.08)", borderwidth=1),
    hovermode="x unified",
)
fig.update_xaxes(showgrid=False, showline=True, linecolor="rgba(0,0,0,0.12)")
fig.update_yaxes(gridcolor="rgba(0,0,0,0.06)", zeroline=False)
st.plotly_chart(fig, use_container_width=True)

# ── Year-by-year table ─────────────────────────────────────────────────────────
st.header("Year-by-Year Breakdown")

display_df = df.copy()
display_df["Portfolio Value"]   = display_df["Portfolio Value"].apply(lambda x: f"€{x:,.0f}")
display_df["Total Contributed"] = display_df["Total Contributed"].apply(lambda x: f"€{x:,.0f}")
display_df["Interest Earned"]   = display_df["Interest Earned"].apply(lambda x: f"€{x:,.0f}")

st.dataframe(display_df, use_container_width=True, hide_index=True)

# ── PDF export ─────────────────────────────────────────────────────────────────
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pdf_utils import (
    new_doc, build_header, section_heading, kpi_row,
    data_table, chart_image, spacer, divider, NumberedCanvas,
)

st.subheader("Export")
logo_file = st.file_uploader("Upload company logo (optional)", type=["png", "jpg", "jpeg"], key="logo")
logo_bytes = logo_file.read() if logo_file else None

def build_pdf():
    buf = io.BytesIO()
    doc = new_doc(buf)
    story = []
    story.append(build_header("Compound Interest Calculator", "FinancePlots", logo_bytes=logo_bytes))
    story.append(spacer(0.4))
    story.append(kpi_row([
        ("Final Portfolio Value", f"€{final_value:,.0f}",    f"After {years} years"),
        ("Total Invested",        f"€{total_invested:,.0f}", "Initial + contributions"),
        ("Interest Earned",       f"€{total_interest:,.0f}", f"{total_interest/final_value*100:.0f}% of final value"),
        ("Return Multiple",       f"{return_multiple:.1f}×", f"€1 → €{return_multiple:.2f}"),
    ]))
    story.append(spacer(0.4))
    story.append(section_heading("Portfolio Growth Chart"))
    story.append(spacer(0.2))
    story.append(chart_image(fig, height_ratio=0.48))
    story.append(spacer(0.4))
    story.append(section_heading("Year-by-Year Breakdown"))
    story.append(spacer(0.2))
    story.append(data_table(
        ["Year", "Portfolio Value", "Total Contributed", "Interest Earned"],
        [[str(r["Year"]), r["Portfolio Value"], r["Total Contributed"], r["Interest Earned"]]
         for _, r in display_df.iterrows()],
    ))
    doc.build(story, canvasmaker=NumberedCanvas)
    buf.seek(0)
    return buf

if st.button("📄 Export PDF Report", type="primary"):
    try:
        pdf = build_pdf()
        st.download_button("⬇️ Download PDF", pdf,
                           file_name="compound_interest.pdf",
                           mime="application/pdf", use_container_width=True)
        st.caption("📧 To share by email: download above and attach the PDF.")
    except Exception as e:
        st.error(f"PDF generation error: {e}")
