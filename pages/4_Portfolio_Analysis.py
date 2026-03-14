import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io
from scipy.stats import norm
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image,
)
from datetime import datetime

st.set_page_config(page_title="Portfolio Analysis · Finance Tools", page_icon="📦", layout="wide")

PRIMARY = "#003f88"
ACCENT  = "#0066cc"
CLRS    = ["#003f88", "#0066cc", "#3399ff", "#00B4AE", "#1A936F", "#C0392B", "#F39C12"]

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

st.title("📦 Portfolio Analysis")
st.markdown(
    '<p class="ev-caption">Select global indices · Set weights · '
    'Expected return · Sharpe ratio · Value at Risk</p>',
    unsafe_allow_html=True,
)

INDICES = {
    "^GSPC":    "S&P 500",
    "^STOXX50E":"EURO STOXX 50",
    "^FTSE":    "FTSE 100",
    "^N225":    "Nikkei 225",
    "^HSI":     "Hang Seng",
    "^DJI":     "Dow Jones",
    "^IXIC":    "NASDAQ",
    "^RUT":     "Russell 2000",
    "^GDAXI":   "DAX (Germany)",
    "^IBEX":    "IBEX 35 (Spain)",
}

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Portfolio Settings")
    selected = st.multiselect(
        "Select indices (2–5)",
        list(INDICES.keys()),
        default=["^GSPC", "^STOXX50E", "^FTSE", "^IBEX"],
        format_func=lambda x: INDICES[x],
    )
    period = st.selectbox("Time period", ["1y", "2y", "5y", "10y", "ytd"], index=2)
    risk_free = st.slider("Risk-free rate (%)", 0.0, 10.0, 2.0, 0.1,
                          help="Annualised risk-free rate (e.g. US 10Y Treasury yield)")

    if 2 <= len(selected) <= 5:
        st.markdown("---")
        st.subheader("Weights")
        st.caption("Automatically normalised to 100%")
        default_w = round(1 / len(selected), 2)
        weights_raw = []
        for ticker in selected:
            w = st.number_input(INDICES[ticker], min_value=0.0, max_value=1.0,
                                value=default_w, step=0.01, key=f"w_{ticker}")
            weights_raw.append(w)
        total_w = sum(weights_raw)
        if total_w > 0:
            st.caption(f"Sum: {total_w:.2f} → normalised to 1.0")

if len(selected) < 2 or len(selected) > 5:
    st.warning("Please select between 2 and 5 indices in the sidebar.")
    st.stop()

total_w = sum(weights_raw)
if total_w == 0:
    st.error("All weights are zero. Set at least one weight above 0.")
    st.stop()

weights = np.array(weights_raw) / total_w  # auto-normalise

# ── Data ───────────────────────────────────────────────────────────────────────
try:
    import yfinance as yf
    with st.spinner("Fetching market data..."):
        raw = yf.download(selected, period=period, progress=False, auto_adjust=True)
        if isinstance(raw.columns, pd.MultiIndex):
            prices = raw["Close"]
        else:
            prices = raw[["Close"]] if "Close" in raw.columns else raw
        prices = prices.dropna()
except Exception as e:
    st.error(f"Could not fetch data: {e}")
    st.stop()

if prices.empty or len(prices) < 10:
    st.error("Not enough data returned. Try a different period or indices.")
    st.stop()

# ── Calculations ───────────────────────────────────────────────────────────────
returns        = prices.pct_change().dropna()
port_returns   = returns.dot(weights)

ann_return     = float(port_returns.mean() * 252)
ann_vol        = float(port_returns.std() * np.sqrt(252))
rf_daily       = risk_free / 100 / 252
sharpe         = (port_returns.mean() - rf_daily) / port_returns.std()
ann_sharpe     = float(sharpe * np.sqrt(252))

conf           = 0.95
daily_var      = float(norm.ppf(1 - conf) * port_returns.std() - port_returns.mean())
annual_var     = float(daily_var * np.sqrt(252))

# Individual asset returns
ind_returns    = returns.mean() * 252
ind_vols       = returns.std() * np.sqrt(252)

# ── KPI Cards ─────────────────────────────────────────────────────────────────
st.header("Portfolio Metrics")
k1, k2, k3, k4 = st.columns(4)
kpi_defs = [
    (k1, "Expected Return",  f"{ann_return:.2%}",  f"Period: {period}",
         "kpi-green" if ann_return > 0 else "kpi-red"),
    (k2, "Volatility (σ)",   f"{ann_vol:.2%}",     "Annualised std dev",         ""),
    (k3, "Sharpe Ratio",     f"{ann_sharpe:.2f}",  f"RF rate: {risk_free}%",
         "kpi-green" if ann_sharpe > 1 else ("" if ann_sharpe > 0 else "kpi-red")),
    (k4, "VaR (95%, Annual)",f"{annual_var:.2%}",  "Max expected annual loss",   "kpi-red"),
]
for col, label, val, sub, cls in kpi_defs:
    with col:
        st.markdown(
            f'<div class="kpi-card {cls}">'
            f'<div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{val}</div>'
            f'<div class="kpi-sub">{sub}</div></div>',
            unsafe_allow_html=True,
        )
st.markdown("<br>", unsafe_allow_html=True)

# ── Charts ────────────────────────────────────────────────────────────────────
_layout = dict(template="plotly_white", height=380,
               font=dict(family="Inter, Segoe UI, sans-serif", size=12),
               paper_bgcolor="white", plot_bgcolor="rgba(248,249,252,1)",
               margin=dict(t=52, b=45, l=65, r=20),
               legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="rgba(0,0,0,0.08)",
                           borderwidth=1, font=dict(size=11)),
               hoverlabel=dict(bgcolor="white", font_size=12))

col_l, col_r = st.columns(2)

# Chart 1: Cumulative portfolio return
with col_l:
    cum_port = (1 + port_returns).cumprod() - 1
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=cum_port.index, y=cum_port.values * 100,
        name="Portfolio", mode="lines",
        line=dict(width=3, color=CLRS[0]),
        fill="tozeroy",
        fillcolor="rgba(0,63,136,0.07)",
        hovertemplate="%{x|%b %Y}: %{y:.2f}%<extra></extra>",
    ))
    fig1.add_hline(y=0, line_width=1, line_color="rgba(0,0,0,0.2)")
    fig1.update_layout(title="Cumulative Portfolio Return",
                       title_font=dict(size=15, color=PRIMARY), **_layout)
    fig1.update_yaxes(ticksuffix="%", tickformat=".1f")
    st.plotly_chart(fig1, use_container_width=True)

# Chart 2: Allocation donut
with col_r:
    fig2 = go.Figure(go.Pie(
        labels=[INDICES[t] for t in selected],
        values=weights,
        hole=0.52,
        marker=dict(colors=CLRS[:len(selected)]),
        textfont=dict(size=11),
        hovertemplate="%{label}: %{percent}<extra></extra>",
    ))
    fig2.update_layout(title="Portfolio Allocation",
                       title_font=dict(size=15, color=PRIMARY),
                       **{k: v for k, v in _layout.items() if k != "bargap"})
    st.plotly_chart(fig2, use_container_width=True)

# Chart 3: Individual asset cumulative returns
fig3 = go.Figure()
for i, ticker in enumerate(selected):
    col_data = returns[ticker] if ticker in returns.columns else returns.iloc[:, i]
    cum = (1 + col_data).cumprod() - 1
    fig3.add_trace(go.Scatter(
        x=cum.index, y=cum.values * 100,
        name=INDICES[ticker], mode="lines",
        line=dict(width=2, color=CLRS[i % len(CLRS)]),
        hovertemplate=f"{INDICES[ticker]} %{{x|%b %Y}}: %{{y:.2f}}%<extra></extra>",
    ))
fig3.add_hline(y=0, line_width=1, line_color="rgba(0,0,0,0.2)")
fig3.update_layout(title="Individual Index Cumulative Returns",
                   title_font=dict(size=15, color=PRIMARY), **_layout)
fig3.update_yaxes(ticksuffix="%", tickformat=".1f")
st.plotly_chart(fig3, use_container_width=True)

# Chart 4: Risk/Return scatter
fig4 = go.Figure()
fig4.add_trace(go.Scatter(
    x=ind_vols.values * 100,
    y=ind_returns.values * 100,
    mode="markers+text",
    text=[INDICES[t] for t in selected],
    textposition="top center",
    marker=dict(size=14, color=CLRS[:len(selected)],
                line=dict(width=2, color="white")),
    hovertemplate="%{text}<br>Vol: %{x:.1f}%<br>Return: %{y:.1f}%<extra></extra>",
))
# Portfolio point
fig4.add_trace(go.Scatter(
    x=[ann_vol * 100], y=[ann_return * 100],
    mode="markers+text", text=["Portfolio"],
    textposition="top center",
    marker=dict(size=18, color="#F39C12", symbol="star",
                line=dict(width=2, color="white")),
    name="Portfolio",
))
fig4.update_layout(title="Risk / Return by Asset",
                   title_font=dict(size=15, color=PRIMARY),
                   showlegend=False, **_layout)
fig4.update_xaxes(title="Volatility (%)", ticksuffix="%")
fig4.update_yaxes(title="Expected Return (%)", ticksuffix="%")
st.plotly_chart(fig4, use_container_width=True)

# ── Export ─────────────────────────────────────────────────────────────────────
st.header("Export")

col_xl, col_pdf = st.columns(2)

with col_xl:
    xl_buf = io.BytesIO()
    returns_export = returns.copy()
    returns_export.columns = [INDICES[t] for t in selected]
    cum_export = ((1 + returns_export).cumprod() - 1) * 100
    cum_export.columns = [f"{c} Cumulative (%)" for c in returns_export.columns]

    metrics_df = pd.DataFrame({
        "Metric": ["Expected Return", "Volatility (σ)", "Sharpe Ratio", "VaR (95% Annual)"],
        "Value": [f"{ann_return:.2%}", f"{ann_vol:.2%}", f"{ann_sharpe:.2f}", f"{annual_var:.2%}"],
    })
    alloc_df = pd.DataFrame({
        "Index": [INDICES[t] for t in selected],
        "Weight": [f"{w:.2%}" for w in weights],
    })

    with pd.ExcelWriter(xl_buf, engine="openpyxl") as writer:
        metrics_df.to_excel(writer, sheet_name="Portfolio Metrics", index=False)
        alloc_df.to_excel(writer, sheet_name="Allocation", index=False)
        returns_export.to_excel(writer, sheet_name="Daily Returns")
        cum_export.to_excel(writer, sheet_name="Cumulative Returns")
    xl_buf.seek(0)
    st.download_button(
        "📊 Download Excel",
        xl_buf,
        file_name="portfolio_analysis.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

with col_pdf:
    if st.button("Generate PDF Report", type="primary", use_container_width=True):
        try:
            PDF_HDR = colors.HexColor("#003f88")
            PDF_ACC = colors.HexColor("#0066cc")
            PDF_ALT = colors.HexColor("#EAF1FB")

            chart1_bytes = fig1.to_image(format="png", width=900, height=380, scale=2)
            chart2_bytes = fig2.to_image(format="png", width=900, height=380, scale=2)
            chart4_bytes = fig4.to_image(format="png", width=900, height=380, scale=2)

            buf = io.BytesIO()
            doc = SimpleDocTemplate(buf, pagesize=A4,
                                    leftMargin=2*cm, rightMargin=2*cm,
                                    topMargin=1.5*cm, bottomMargin=2*cm)
            W = A4[0] - 4*cm

            h_style   = ParagraphStyle("h",   fontName="Helvetica-Bold", fontSize=20,
                                       textColor=colors.white, alignment=TA_LEFT)
            s_style   = ParagraphStyle("s",   fontName="Helvetica", fontSize=9,
                                       textColor=colors.HexColor("#ccddee"), alignment=TA_LEFT)
            sec_style = ParagraphStyle("sec", fontName="Helvetica-Bold", fontSize=11,
                                       textColor=colors.HexColor("#003f88"), spaceBefore=12, spaceAfter=4)
            ft_style  = ParagraphStyle("ft",  fontName="Helvetica", fontSize=8,
                                       textColor=colors.HexColor("#999"), alignment=TA_CENTER)
            ct_style  = ParagraphStyle("ct",  fontName="Helvetica", fontSize=9,
                                       textColor=colors.HexColor("#666"), spaceBefore=4, spaceAfter=2)

            story = []

            hdr = Table(
                [[Paragraph("FinancePlots", h_style),
                  Paragraph("Portfolio Analysis", h_style),
                  Paragraph(f"Generated\n{datetime.now().strftime('%B %d, %Y')}", s_style)]],
                colWidths=[W * 0.22, W * 0.50, W * 0.28],
            )
            hdr.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), PDF_HDR),
                ("TOPPADDING", (0, 0), (-1, -1), 16),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (2, 0), (2, 0), "RIGHT"),
            ]))
            story.append(hdr)
            story.append(Spacer(1, 0.4*cm))
            story.append(HRFlowable(width="100%", thickness=3, color=PDF_ACC, spaceAfter=8))

            story.append(Paragraph("Portfolio Metrics", sec_style))
            kpi_data = [
                ["Expected Return", "Volatility (σ)", "Sharpe Ratio", "VaR (95% Annual)"],
                [f"{ann_return:.2%}", f"{ann_vol:.2%}", f"{ann_sharpe:.2f}", f"{annual_var:.2%}"],
            ]
            kt = Table(kpi_data, colWidths=[W / 4] * 4)
            kt.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), PDF_ACC),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 1), (-1, 1), PDF_ALT),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
            ]))
            story.append(kt)
            story.append(Spacer(1, 0.3*cm))

            story.append(Paragraph("Allocation", sec_style))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#DDDDDD"), spaceAfter=4))
            alloc_data = [["Index", "Weight"]] + [[INDICES[t], f"{w:.2%}"] for t, w in zip(selected, weights)]
            at = Table(alloc_data, colWidths=[W * 0.7, W * 0.3])
            at.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), PDF_HDR),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")),
            ]))
            for ri in range(1, len(alloc_data)):
                if ri % 2 == 0:
                    at.setStyle(TableStyle([("BACKGROUND", (0, ri), (-1, ri), PDF_ALT)]))
            story.append(at)
            story.append(Spacer(1, 0.3*cm))

            for chart_bytes, title in [
                (chart1_bytes, "Cumulative Portfolio Return"),
                (chart2_bytes, "Portfolio Allocation"),
                (chart4_bytes, "Risk / Return by Asset"),
            ]:
                story.append(Paragraph(title, ct_style))
                story.append(Image(io.BytesIO(chart_bytes), width=W, height=W * 0.42))
                story.append(Spacer(1, 0.2*cm))

            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#DDDDDD"), spaceAfter=4))
            story.append(Paragraph("Generated by FinancePlots · For informational purposes only", ft_style))

            doc.build(story)
            buf.seek(0)
            st.download_button(
                "📄 Download PDF Report",
                buf,
                file_name="portfolio_analysis.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Error generating PDF: {e}")

# ── Definitions ───────────────────────────────────────────────────────────────
with st.expander("Definitions & Methodology"):
    st.markdown(f"""
    - **Expected Return**: annualised mean daily return × 252 trading days
    - **Volatility**: annualised standard deviation of daily returns
    - **Sharpe Ratio**: (Portfolio Return − Risk-Free Rate) / Volatility.
      A ratio above **1.0** is generally considered good.
    - **Value at Risk (VaR, 95%)**: maximum expected loss at 95% confidence.
      Uses parametric (normal distribution) method.
    - **Risk-free rate used**: {risk_free}% per year (set in sidebar)
    - Data sourced from Yahoo Finance. Past performance is not indicative of future results.
    - This tool is for informational purposes only and does not constitute investment advice.
    """)
