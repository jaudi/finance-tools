import streamlit as st
import pandas as pd
import numpy as np
import io
import plotly.graph_objects as go
from datetime import datetime

from reportlab.lib import colors

import sys as _sys_fm, os as _os_fm
_sys_fm.path.insert(0, _os_fm.join(_os_fm.dirname(__file__), ".."))
from pdf_utils import (
    new_doc, build_header, section_heading, kpi_row,
    data_table, chart_image, spacer, NumberedCanvas, CONTENT_W,
)

# ── Theme ──────────────────────────────────────────────────────────────────────
PRIMARY = "#003f88"
ACCENT  = "#0066cc"
CLRS    = ["#003f88", "#0066cc", "#3399ff", "#00B4AE", "#1A936F", "#C0392B"]
PDF_HDR = colors.HexColor("#003f88")
PDF_ACC = colors.HexColor("#0066cc")
PDF_ALT = colors.HexColor("#EAF1FB")

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="5-Year Financial Model · FinancePlots",
    page_icon="📈",
    layout="wide",
)

st.markdown("""
    <style>
        .block-container { padding-top: 1.5rem; }
        h2 { font-size: 1.25rem !important; color: #333;
             border-bottom: 2px solid #eee; padding-bottom: 6px; margin-top: 1.5rem; }
        .ev-caption { color: #888; font-size: 0.88rem; margin-top: -6px; margin-bottom: 1rem; }
        .kpi-card {
            background: #f7f9fc;
            border-left: 4px solid #0066cc;
            border-radius: 6px;
            padding: 0.9rem 1rem;
            height: 100%;
        }
        .kpi-label { font-size: 0.78rem; color: #888; font-weight: 600; text-transform: uppercase; }
        .kpi-value { font-size: 1.6rem; font-weight: 800; color: #003f88; line-height: 1.2; }
        .kpi-sub   { font-size: 0.78rem; color: #999; margin-top: 2px; }
    </style>
""", unsafe_allow_html=True)

st.title("📈 5-Year Financial Model")
st.markdown(
    '<p class="ev-caption">Income statement · Cash flow · Balance sheet · '
    'Key ratios — adjust assumptions and export to PDF</p>',
    unsafe_allow_html=True,
)

# ── Sidebar inputs ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Assumptions")

    company_name = st.text_input("Company / report name", value="My Company")

    st.subheader("Revenue")
    initial_revenue = st.number_input("Initial Revenue ($)", min_value=0, value=100_000, step=5_000)
    revenue_growth  = st.slider("Annual Growth Rate (%)", 0, 100, 10)

    st.subheader("P&L")
    cogs_pct = st.slider("COGS (% of Revenue)", 0, 100, 40)
    opex_pct = st.slider("Operating Expenses (% of Revenue)", 0, 100, 20)
    tax_rate = st.slider("Tax Rate (%)", 0, 100, 25)

    st.subheader("Cash Flow")
    capex          = st.number_input("Annual CapEx ($)", min_value=0, value=5_000, step=500)
    dep_amort      = st.number_input("Annual D&A ($)", min_value=0, value=5_000, step=500)
    change_in_nwc  = st.number_input("Annual Change in NWC ($)", value=500, step=100)

# ── Calculations ───────────────────────────────────────────────────────────────
YEARS      = 5
years_list = [f"Year {i+1}" for i in range(YEARS)]

revenue = [initial_revenue]
cogs_v, gross_profit_v, opex_v, ebit_v, tax_v, net_income_v = [], [], [], [], [], []
op_cf_v, inv_cf_v, net_cf_v = [], [], []
assets_v, liab_v, equity_v = [], [], []

for yr in range(YEARS):
    if yr > 0:
        revenue.append(revenue[-1] * (1 + revenue_growth / 100))

    cogs_v.append(revenue[yr] * cogs_pct / 100)
    gross_profit_v.append(revenue[yr] - cogs_v[yr])
    opex_v.append(revenue[yr] * opex_pct / 100)
    ebit_v.append(gross_profit_v[yr] - opex_v[yr])
    tax_v.append(max(ebit_v[yr], 0) * tax_rate / 100)
    net_income_v.append(ebit_v[yr] - tax_v[yr])

    op_cf_v.append(net_income_v[yr] + dep_amort - change_in_nwc)
    inv_cf_v.append(-capex)
    net_cf_v.append(op_cf_v[yr] + inv_cf_v[yr])

    if yr == 0:
        assets_v.append(net_cf_v[yr] + dep_amort + capex)
    else:
        assets_v.append(assets_v[-1] + net_cf_v[yr] + dep_amort + capex)
    liab_v.append(revenue[yr] * 0.4)
    equity_v.append(assets_v[yr] - liab_v[yr])


def growth_rates(series):
    return [0.0] + [
        (series[i] / series[i - 1] - 1) * 100 if series[i - 1] != 0 else 0.0
        for i in range(1, YEARS)
    ]


gross_margin = [gp / rev * 100 for gp, rev in zip(gross_profit_v, revenue)]
op_margin    = [eb / rev * 100 for eb, rev in zip(ebit_v, revenue)]
net_margin   = [ni / rev * 100 for ni, rev in zip(net_income_v, revenue)]
roa          = [ni / a * 100 if a != 0 else 0 for ni, a in zip(net_income_v, assets_v)]
roe          = [ni / eq * 100 if eq != 0 else 0 for ni, eq in zip(net_income_v, equity_v)]

income_df = pd.DataFrame({
    "Year": years_list,
    "Revenue ($)": revenue,
    "Revenue Growth (%)": growth_rates(revenue),
    "COGS ($)": cogs_v,
    "Gross Profit ($)": gross_profit_v,
    "Gross Margin (%)": gross_margin,
    "OpEx ($)": opex_v,
    "EBIT ($)": ebit_v,
    "Tax ($)": tax_v,
    "Net Income ($)": net_income_v,
    "Net Margin (%)": net_margin,
}).round(2)

cf_df = pd.DataFrame({
    "Year": years_list,
    "Operating CF ($)": op_cf_v,
    "Investing CF ($)": inv_cf_v,
    "Net Cash Flow ($)": net_cf_v,
}).round(2)

bs_df = pd.DataFrame({
    "Year": years_list,
    "Assets ($)": assets_v,
    "Liabilities ($)": liab_v,
    "Equity ($)": equity_v,
}).round(2)

ratios_df = pd.DataFrame({
    "Year": years_list,
    "Gross Margin (%)": gross_margin,
    "Operating Margin (%)": op_margin,
    "Net Margin (%)": net_margin,
    "ROA (%)": roa,
    "ROE (%)": roe,
}).round(2)

# ── KPI cards (Year 5) ─────────────────────────────────────────────────────────
st.header("Key Metrics — Year 5")

k1, k2, k3, k4 = st.columns(4)
kpis = [
    (k1, "Revenue",        revenue[-1],         f"Growth: {growth_rates(revenue)[-1]:+.1f}% YoY"),
    (k2, "Net Income",     net_income_v[-1],    f"Margin: {net_margin[-1]:.1f}%"),
    (k3, "Total Cash Flow", sum(net_cf_v),      f"Avg/yr: ${sum(net_cf_v)/YEARS:,.0f}"),
    (k4, "Equity",         equity_v[-1],        f"ROE: {roe[-1]:.1f}%"),
]
for widget, label, value, sub in kpis:
    with widget:
        sign = "$" if abs(value) < 1e15 else ""
        st.markdown(
            f'<div class="kpi-card">'
            f'<div class="kpi-label">{label} (Y5)</div>'
            f'<div class="kpi-value">${value:,.0f}</div>'
            f'<div class="kpi-sub">{sub}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

# ── Financial statements in tabs ───────────────────────────────────────────────
st.header("Financial Statements")

tab1, tab2, tab3, tab4 = st.tabs(
    ["📋 Income Statement", "💵 Cash Flow", "🏦 Balance Sheet", "📐 Ratios"]
)
with tab1:
    st.dataframe(income_df.set_index("Year"), use_container_width=True)
with tab2:
    st.dataframe(cf_df.set_index("Year"), use_container_width=True)
with tab3:
    st.dataframe(bs_df.set_index("Year"), use_container_width=True)
with tab4:
    st.dataframe(ratios_df.set_index("Year"), use_container_width=True)

# ── Charts ─────────────────────────────────────────────────────────────────────
st.header("Visualizations")

_layout = dict(
    template="plotly_white",
    height=380,
    font=dict(family="Inter, Segoe UI, Arial, sans-serif", size=12),
    paper_bgcolor="white",
    plot_bgcolor="rgba(248,249,252,1)",
    margin=dict(t=55, b=45, l=65, r=20),
    bargap=0.25,
    legend=dict(
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="rgba(0,0,0,0.08)",
        borderwidth=1,
        font=dict(size=11),
    ),
    hoverlabel=dict(bgcolor="white", bordercolor="rgba(0,0,0,0.1)", font_size=12),
)

def _ax(fig, money=True):
    fig.update_xaxes(showgrid=False, showline=True, linecolor="rgba(0,0,0,0.12)",
                     tickfont=dict(size=11), zeroline=False)
    fmt = dict(tickprefix="$", tickformat=",.0f") if money else dict(ticksuffix="%")
    fig.update_yaxes(gridcolor="rgba(0,0,0,0.06)", showline=False,
                     tickfont=dict(size=11), zeroline=False, **fmt)


# Chart 1: Revenue & Profitability
fig1 = go.Figure()
for name, vals, color in [
    ("Revenue",      revenue,        CLRS[0]),
    ("Gross Profit", gross_profit_v, CLRS[2]),
    ("Net Income",   net_income_v,   CLRS[3]),
]:
    fig1.add_trace(go.Scatter(
        x=years_list, y=vals, name=name, mode="lines+markers",
        line=dict(width=3, color=color),
        marker=dict(size=8, line=dict(width=2, color="white")),
    ))
fig1.update_layout(
    title="Revenue & Profitability",
    title_font=dict(size=16, color=PRIMARY),
    **_layout,
)
_ax(fig1, money=True)

# Chart 2: Profit margins
fig2 = go.Figure()
for name, vals, color in [
    ("Gross Margin %",     gross_margin, CLRS[0]),
    ("Operating Margin %", op_margin,    CLRS[1]),
    ("Net Margin %",       net_margin,   CLRS[3]),
]:
    fig2.add_trace(go.Scatter(
        x=years_list, y=vals, name=name, mode="lines+markers",
        line=dict(width=3, color=color),
        marker=dict(size=8, line=dict(width=2, color="white")),
    ))
fig2.update_layout(
    title="Profit Margins",
    title_font=dict(size=16, color=PRIMARY),
    **_layout,
)
_ax(fig2, money=False)

# Chart 3: Cash flows (grouped bar)
fig3 = go.Figure()
for name, vals, color in [
    ("Operating CF",  op_cf_v,  CLRS[1]),
    ("Investing CF",  inv_cf_v, CLRS[5]),
    ("Net Cash Flow", net_cf_v, CLRS[0]),
]:
    fig3.add_trace(go.Bar(x=years_list, y=vals, name=name,
                          marker_color=color, opacity=0.88))
fig3.update_layout(
    title="Cash Flow by Year",
    title_font=dict(size=16, color=PRIMARY),
    barmode="group",
    **_layout,
)
_ax(fig3, money=True)

# Chart 4: Balance sheet (grouped bar)
fig4 = go.Figure()
for name, vals, color in [
    ("Assets",      assets_v, CLRS[0]),
    ("Liabilities", liab_v,   CLRS[5]),
    ("Equity",      equity_v, CLRS[3]),
]:
    fig4.add_trace(go.Bar(x=years_list, y=vals, name=name,
                          marker_color=color, opacity=0.88))
fig4.update_layout(
    title="Balance Sheet",
    title_font=dict(size=16, color=PRIMARY),
    barmode="group",
    **_layout,
)
_ax(fig4, money=True)

col_l, col_r = st.columns(2)
with col_l:
    st.plotly_chart(fig1, use_container_width=True)
    st.plotly_chart(fig3, use_container_width=True)
with col_r:
    st.plotly_chart(fig2, use_container_width=True)
    st.plotly_chart(fig4, use_container_width=True)

# ── PDF export ─────────────────────────────────────────────────────────────────
st.header("Export")

# Excel export (always available)
excel_buf = io.BytesIO()
with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
    income_df.to_excel(writer, sheet_name="Income Statement", index=False)
    cf_df.to_excel(writer, sheet_name="Cash Flow", index=False)
    bs_df.to_excel(writer, sheet_name="Balance Sheet", index=False)
    ratios_df.to_excel(writer, sheet_name="Ratios", index=False)
excel_buf.seek(0)
st.download_button(
    "📊 Download Excel",
    excel_buf,
    file_name=f"financial_model_{company_name.replace(' ', '_')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
)

if st.button("📄 Export PDF Report", type="primary", use_container_width=True):
    try:
        buf = io.BytesIO()
        doc = new_doc(buf)
        story = []

        story.append(build_header("5-Year Financial Model", company_name))
        story.append(spacer(0.4))

        story.append(kpi_row([
            ("Revenue (Y5)",     f"${revenue[-1]:,.0f}",      "Year 5"),
            ("Net Income (Y5)",  f"${net_income_v[-1]:,.0f}", "Year 5"),
            ("Total Cash Flow",  f"${sum(net_cf_v):,.0f}",    "5-year total"),
            ("Equity (Y5)",      f"${equity_v[-1]:,.0f}",     "Year 5"),
        ]))
        story.append(spacer(0.4))

        story.append(section_heading("Model Assumptions"))
        story.append(spacer(0.2))
        story.append(data_table(
            ["Initial Revenue", "Growth Rate", "COGS %", "OpEx %", "Tax Rate", "CapEx", "D&A"],
            [[f"${initial_revenue:,}", f"{revenue_growth}%", f"{cogs_pct}%",
              f"{opex_pct}%", f"{tax_rate}%", f"${capex:,}", f"${dep_amort:,}"]],
        ))
        story.append(spacer(0.4))

        for fig_obj, title in [
            (fig1, "Revenue & Profitability"),
            (fig2, "Profit Margins"),
            (fig3, "Cash Flow by Year"),
            (fig4, "Balance Sheet"),
        ]:
            story.append(section_heading(title))
            story.append(spacer(0.2))
            story.append(chart_image(fig_obj, height_ratio=0.44))
            story.append(spacer(0.3))

        for df_obj, title in [
            (income_df, "Income Statement"),
            (cf_df,     "Cash Flow Statement"),
            (bs_df,     "Balance Sheet"),
            (ratios_df, "Financial Ratios"),
        ]:
            story.append(section_heading(title))
            story.append(spacer(0.2))
            story.append(data_table(list(df_obj.columns), df_obj.astype(str).values.tolist()))
            story.append(spacer(0.3))

        doc.build(story, canvasmaker=NumberedCanvas)
        buf.seek(0)

        st.download_button(
            "⬇️ Download PDF",
            buf,
            file_name=f"financial_model_{company_name.replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    except Exception as e:
        st.error(f"Error generating PDF: {e}")

# ── Disclaimer ─────────────────────────────────────────────────────────────────
with st.expander("Disclaimer & key assumptions"):
    st.markdown("""
    This model is for illustrative purposes only and should not be considered financial advice.

    **Key assumptions:**
    - Revenue grows at a constant annual rate
    - COGS and OpEx are fixed percentages of revenue each year
    - Tax is only applied when EBIT is positive
    - CapEx, D&A, and change in NWC are constant each year
    - Liabilities are modelled at 40% of annual revenue
    """)
