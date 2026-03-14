import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Stock Comparison · Finance Tools", page_icon="📉", layout="wide")

PRIMARY = "#003f88"
CLRS    = ["#003f88", "#C0392B", "#0066cc", "#1A936F"]

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

st.title("📉 Stock Comparison")
st.markdown(
    '<p class="ev-caption">Compare two stocks side by side — '
    'price, returns, correlation and key ratios</p>',
    unsafe_allow_html=True,
)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Stocks")
    ticker1 = st.text_input("Stock 1 (e.g. AAPL)", value="AAPL").upper().strip()
    ticker2 = st.text_input("Stock 2 (e.g. MSFT)", value="MSFT").upper().strip()
    period  = st.selectbox("Time period", ["1y", "2y", "5y", "10y"], index=2)

# ── Data fetch ────────────────────────────────────────────────────────────────
import yfinance as yf

@st.cache_data(ttl=3600)
def fetch_prices(t1, t2, per):
    raw = yf.download([t1, t2], period=per, progress=False, auto_adjust=True)
    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw["Close"]
    else:
        prices = raw[["Close"]]
    return prices.dropna()

@st.cache_data(ttl=3600)
def fetch_info(ticker):
    try:
        info = yf.Ticker(ticker).info
        return {
            "name":           info.get("longName", ticker),
            "sector":         info.get("sector", "—"),
            "forward_pe":     info.get("forwardPE"),
            "trailing_pe":    info.get("trailingPE"),
            "payout_ratio":   info.get("payoutRatio"),
            "earnings_growth":info.get("earningsQuarterlyGrowth"),
            "market_cap":     info.get("marketCap"),
            "dividend_yield": info.get("dividendYield"),
            "52w_high":       info.get("fiftyTwoWeekHigh"),
            "52w_low":        info.get("fiftyTwoWeekLow"),
        }
    except Exception:
        return {}

with st.spinner("Fetching data..."):
    try:
        prices = fetch_prices(ticker1, ticker2, period)
        info1  = fetch_info(ticker1)
        info2  = fetch_info(ticker2)
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        st.stop()

if prices.empty or len(prices.columns) < 2:
    st.error("Could not load data for one or both tickers. Check the symbols and try again.")
    st.stop()

p1 = prices[ticker1] if ticker1 in prices.columns else prices.iloc[:, 0]
p2 = prices[ticker2] if ticker2 in prices.columns else prices.iloc[:, 1]

# ── Calculations ───────────────────────────────────────────────────────────────
ret1     = p1.pct_change().dropna()
ret2     = p2.pct_change().dropna()
cum1     = (1 + ret1).cumprod() - 1
cum2     = (1 + ret2).cumprod() - 1
corr     = float(ret1.corr(ret2))

ann_ret1 = float(ret1.mean() * 252)
ann_ret2 = float(ret2.mean() * 252)
ann_vol1 = float(ret1.std() * np.sqrt(252))
ann_vol2 = float(ret2.std() * np.sqrt(252))
total1   = float(cum1.iloc[-1])
total2   = float(cum2.iloc[-1])

# ── KPI cards ─────────────────────────────────────────────────────────────────
st.header(f"{info1.get('name', ticker1)}  vs  {info2.get('name', ticker2)}")

def _kpi(col, label, v1, v2, fmt=None, pct=False):
    with col:
        def _f(v):
            if v is None: return "—"
            if pct:       return f"{v:.1%}"
            if fmt:       return fmt(v)
            return f"{v:.2f}"
        cls1 = "kpi-green" if (v1 or 0) > (v2 or 0) else "kpi-red"
        cls2 = "kpi-green" if (v2 or 0) > (v1 or 0) else "kpi-red"
        st.markdown(
            f'<div class="kpi-card {cls1}">'
            f'<div class="kpi-label">{label} — {ticker1}</div>'
            f'<div class="kpi-value">{_f(v1)}</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        st.markdown(
            f'<div class="kpi-card {cls2}">'
            f'<div class="kpi-label">{label} — {ticker2}</div>'
            f'<div class="kpi-value">{_f(v2)}</div></div>',
            unsafe_allow_html=True,
        )

c1, c2, c3, c4, c5 = st.columns(5)
_kpi(c1, "Total Return",   total1,   total2,   pct=True)
_kpi(c2, "Ann. Return",    ann_ret1, ann_ret2, pct=True)
_kpi(c3, "Volatility",     ann_vol1, ann_vol2, pct=True)
_kpi(c4, "Forward P/E",    info1.get("forward_pe"), info2.get("forward_pe"),
     fmt=lambda v: f"{v:.1f}x")
_kpi(c5, "Payout Ratio",   info1.get("payout_ratio"), info2.get("payout_ratio"), pct=True)

# Correlation
corr_cls = "kpi-green" if abs(corr) < 0.5 else ("" if abs(corr) < 0.8 else "kpi-red")
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    f'<div class="kpi-card {corr_cls}" style="max-width:300px">'
    f'<div class="kpi-label">Correlation ({period})</div>'
    f'<div class="kpi-value">{corr:.2f}</div>'
    f'<div class="kpi-sub">{"Low — good diversification" if abs(corr) < 0.5 else ("Moderate" if abs(corr) < 0.8 else "High — limited diversification benefit")}</div>'
    f'</div>',
    unsafe_allow_html=True,
)
st.markdown("<br>", unsafe_allow_html=True)

# ── Charts ────────────────────────────────────────────────────────────────────
_layout = dict(
    template="plotly_white", height=400,
    font=dict(family="Inter, Segoe UI, sans-serif", size=12),
    paper_bgcolor="white", plot_bgcolor="rgba(248,249,252,1)",
    margin=dict(t=52, b=45, l=65, r=20),
    legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="rgba(0,0,0,0.08)",
                borderwidth=1, font=dict(size=11)),
    hoverlabel=dict(bgcolor="white", font_size=12),
)

col_l, col_r = st.columns(2)

with col_l:
    # Normalised price (base 100)
    norm1 = p1 / p1.iloc[0] * 100
    norm2 = p2 / p2.iloc[0] * 100
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=norm1.index, y=norm1.values, name=ticker1,
                              mode="lines", line=dict(width=2.5, color=CLRS[0])))
    fig1.add_trace(go.Scatter(x=norm2.index, y=norm2.values, name=ticker2,
                              mode="lines", line=dict(width=2.5, color=CLRS[1])))
    fig1.add_hline(y=100, line_dash="dot", line_color="rgba(0,0,0,0.2)")
    fig1.update_layout(title="Normalised Price (Base 100)",
                       title_font=dict(size=15, color=PRIMARY), **_layout)
    st.plotly_chart(fig1, use_container_width=True)

with col_r:
    # Cumulative returns
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=cum1.index, y=cum1.values * 100, name=ticker1,
                              mode="lines", line=dict(width=2.5, color=CLRS[0]),
                              fill="tozeroy", fillcolor="rgba(0,63,136,0.07)"))
    fig2.add_trace(go.Scatter(x=cum2.index, y=cum2.values * 100, name=ticker2,
                              mode="lines", line=dict(width=2.5, color=CLRS[1]),
                              fill="tozeroy", fillcolor="rgba(192,57,43,0.07)"))
    fig2.add_hline(y=0, line_width=1, line_color="rgba(0,0,0,0.2)")
    fig2.update_layout(title="Cumulative Return (%)",
                       title_font=dict(size=15, color=PRIMARY), **_layout)
    fig2.update_yaxes(ticksuffix="%")
    st.plotly_chart(fig2, use_container_width=True)

# Rolling 30-day volatility
roll_vol1 = ret1.rolling(30).std() * np.sqrt(252) * 100
roll_vol2 = ret2.rolling(30).std() * np.sqrt(252) * 100
fig3 = go.Figure()
fig3.add_trace(go.Scatter(x=roll_vol1.index, y=roll_vol1.values, name=ticker1,
                          mode="lines", line=dict(width=2, color=CLRS[0])))
fig3.add_trace(go.Scatter(x=roll_vol2.index, y=roll_vol2.values, name=ticker2,
                          mode="lines", line=dict(width=2, color=CLRS[1])))
fig3.update_layout(title="Rolling 30-Day Volatility (Annualised %)",
                   title_font=dict(size=15, color=PRIMARY), **_layout)
fig3.update_yaxes(ticksuffix="%")
st.plotly_chart(fig3, use_container_width=True)

# ── Key Ratios Table ──────────────────────────────────────────────────────────
st.header("Key Ratios")

def _safe(v, pct=False, suffix="x"):
    if v is None: return "—"
    if pct:       return f"{v:.1%}"
    return f"{v:.1f}{suffix}"

ratio_data = {
    "":                     [ticker1, ticker2],
    "Sector":               [info1.get("sector","—"), info2.get("sector","—")],
    "Forward P/E":          [_safe(info1.get("forward_pe")), _safe(info2.get("forward_pe"))],
    "Trailing P/E":         [_safe(info1.get("trailing_pe")), _safe(info2.get("trailing_pe"))],
    "Payout Ratio":         [_safe(info1.get("payout_ratio"), pct=True), _safe(info2.get("payout_ratio"), pct=True)],
    "Earnings Growth (QoQ)":[_safe(info1.get("earnings_growth"), pct=True), _safe(info2.get("earnings_growth"), pct=True)],
    "Dividend Yield":       [_safe(info1.get("dividend_yield"), pct=True), _safe(info2.get("dividend_yield"), pct=True)],
    "52W High":             [f"${info1.get('52w_high', 0):,.2f}" if info1.get('52w_high') else "—",
                             f"${info2.get('52w_high', 0):,.2f}" if info2.get('52w_high') else "—"],
    "52W Low":              [f"${info1.get('52w_low', 0):,.2f}" if info1.get('52w_low') else "—",
                             f"${info2.get('52w_low', 0):,.2f}" if info2.get('52w_low') else "—"],
}
st.dataframe(pd.DataFrame(ratio_data).set_index(""), use_container_width=True)

# ── Download ───────────────────────────────────────────────────────────────────
st.header("Download Data")
col_dl1, col_dl2 = st.columns(2)

with col_dl1:
    price_csv = prices[[ticker1, ticker2]].copy()
    price_csv.index.name = "Date"
    st.download_button(
        "📥 Download Price History (CSV)",
        data=price_csv.to_csv().encode("utf-8"),
        file_name=f"{ticker1}_vs_{ticker2}_prices_{period}.csv",
        mime="text/csv",
        use_container_width=True,
    )

with col_dl2:
    returns_csv = pd.DataFrame({
        f"{ticker1} Daily Return": ret1,
        f"{ticker2} Daily Return": ret2,
        f"{ticker1} Cumulative Return": cum1,
        f"{ticker2} Cumulative Return": cum2,
    })
    returns_csv.index.name = "Date"
    st.download_button(
        "📥 Download Returns (CSV)",
        data=returns_csv.to_csv().encode("utf-8"),
        file_name=f"{ticker1}_vs_{ticker2}_returns_{period}.csv",
        mime="text/csv",
        use_container_width=True,
    )

st.caption("Data from Yahoo Finance. Not financial advice.")
