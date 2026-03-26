import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Stock Analysis · Finance Tools", page_icon="📊", layout="wide")

PRIMARY = "#003f88"
CLRS    = ["#003f88", "#0066cc", "#C0392B", "#F39C12", "#1A936F"]

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

from mobile_css import inject_mobile_css
inject_mobile_css()

st.title("📊 Stock Analysis")
st.markdown(
    '<p class="ev-caption">Enter any ticker · Price history · '
    'Moving averages · Cumulative returns · Key ratios</p>',
    unsafe_allow_html=True,
)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Settings")
    ticker = st.text_input(
        "Ticker symbol",
        value="SAN.MC",
        help="Any Yahoo Finance ticker. Examples: AAPL, MSFT, SAN.MC, BBVA.MC, ^IBEX, BTC-USD",
    ).upper().strip()
    period = st.radio("Period", ["1y", "3y", "5y", "10y", "ytd"], index=2, horizontal=True)
    show_ma = st.multiselect(
        "Moving averages",
        ["50-day", "150-day", "200-day"],
        default=["50-day", "200-day"],
    )

if not ticker:
    st.info("Enter a ticker symbol in the sidebar to get started.")
    st.stop()

# ── Data ───────────────────────────────────────────────────────────────────────
import yfinance as yf

@st.cache_data(ttl=3600)
def fetch_stock(ticker, period):
    try:
        return yf.download(ticker, period=period, progress=False, auto_adjust=True)
    except Exception as e:
        st.error(f"Failed to fetch data for {ticker}: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def fetch_info(ticker):
    try:
        return yf.Ticker(ticker).info
    except Exception:
        return {}

with st.spinner(f"Fetching data for {ticker}..."):
    df   = fetch_stock(ticker, period)
    info = fetch_info(ticker)

if df.empty:
    st.error(f"No data found for **{ticker}**. Check the symbol and try again.")
    st.stop()

price   = df["Close"].squeeze().dropna()
returns = price.pct_change().dropna()
cum_ret = (1 + returns).cumprod() - 1

# Moving averages
ma_map = {"50-day": 50, "150-day": 150, "200-day": 200}
for ma_label in show_ma:
    price_series = price.copy()
    df[ma_label] = price_series.rolling(ma_map[ma_label]).mean()

# ── KPI Cards ─────────────────────────────────────────────────────────────────
last_price   = float(price.iloc[-1])
prev_price   = float(price.iloc[-2]) if len(price) > 1 else last_price
chg_1d       = (last_price - prev_price) / prev_price
total_return = float(cum_ret.iloc[-1])
ann_vol      = float(returns.std() * np.sqrt(252))
ann_ret      = float(returns.mean() * 252)

name     = info.get("longName", ticker)
currency = info.get("currency", "")
cur_sym  = {"USD": "$", "EUR": "€", "GBP": "£"}.get(currency, currency + " ")

st.header(f"{name}  ·  {ticker}")

k1, k2, k3, k4, k5 = st.columns(5)
kpi_data = [
    (k1, "Last Price",
     f"{cur_sym}{last_price:,.2f}",
     f"1D: {'▲' if chg_1d >= 0 else '▼'} {abs(chg_1d):.2f}%",
     "kpi-green" if chg_1d >= 0 else "kpi-red"),
    (k2, f"Return ({period})",
     f"{total_return:+.1%}", f"Period: {period}",
     "kpi-green" if total_return >= 0 else "kpi-red"),
    (k3, "Ann. Volatility",
     f"{ann_vol:.1%}", "Annualised std dev", ""),
    (k4, "Ann. Return",
     f"{ann_ret:+.1%}", "Based on selected period",
     "kpi-green" if ann_ret >= 0 else "kpi-red"),
    (k5, "Forward P/E",
     f"{info.get('forwardPE'):.1f}x" if info.get("forwardPE") else "—",
     info.get("sector", "—"), ""),
]
for col, label, val, sub, cls in kpi_data:
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
_layout = dict(
    template="plotly_white", height=420,
    font=dict(family="Inter, Segoe UI, sans-serif", size=12),
    paper_bgcolor="white", plot_bgcolor="rgba(248,249,252,1)",
    margin=dict(t=52, b=45, l=65, r=20),
    legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="rgba(0,0,0,0.08)",
                borderwidth=1, font=dict(size=11)),
    hoverlabel=dict(bgcolor="white", font_size=12),
)

# Chart 1: Price + Moving Averages
fig1 = go.Figure()
fig1.add_trace(go.Scatter(
    x=price.index, y=price.values, name="Price",
    mode="lines", line=dict(width=2, color=CLRS[0]),
    hovertemplate=f"{cur_sym}%{{y:,.2f}}<extra></extra>",
))
ma_colors = {"50-day": CLRS[2], "150-day": CLRS[3], "200-day": CLRS[4]}
for ma_label in show_ma:
    if ma_label in df.columns:
        ma_s = df[ma_label].squeeze().dropna()
        fig1.add_trace(go.Scatter(
            x=ma_s.index, y=ma_s.values, name=ma_label,
            mode="lines",
            line=dict(width=1.5, dash="dot", color=ma_colors[ma_label]),
            hovertemplate=f"{ma_label}: {cur_sym}%{{y:,.2f}}<extra></extra>",
        ))
fig1.update_layout(title=f"{name} — Price & Moving Averages",
                   title_font=dict(size=15, color=PRIMARY), **_layout)
fig1.update_yaxes(tickprefix=cur_sym, tickformat=",.2f")
st.plotly_chart(fig1, use_container_width=True)

col_l, col_r = st.columns(2)

# Chart 2: Cumulative return
with col_l:
    fill_color = "rgba(26,147,111,0.08)" if total_return >= 0 else "rgba(192,57,43,0.08)"
    line_color  = CLRS[4] if total_return >= 0 else CLRS[2]
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=cum_ret.index, y=cum_ret.values * 100,
        name="Cumulative Return", mode="lines",
        line=dict(width=2.5, color=line_color),
        fill="tozeroy", fillcolor=fill_color,
        hovertemplate="%{x|%b %Y}: %{y:.2f}%<extra></extra>",
    ))
    fig2.add_hline(y=0, line_width=1, line_color="rgba(0,0,0,0.2)")
    fig2.update_layout(title="Cumulative Return (%)",
                       title_font=dict(size=15, color=PRIMARY),
                       showlegend=False, **_layout)
    fig2.update_yaxes(ticksuffix="%")
    st.plotly_chart(fig2, use_container_width=True)

# Chart 3: Rolling 30-day volatility
with col_r:
    roll_vol = returns.rolling(30).std() * np.sqrt(252) * 100
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=roll_vol.index, y=roll_vol.values,
        name="30D Volatility", mode="lines",
        line=dict(width=2, color=CLRS[3]),
        fill="tozeroy", fillcolor="rgba(243,156,18,0.08)",
        hovertemplate="%{x|%b %Y}: %{y:.1f}%<extra></extra>",
    ))
    fig3.update_layout(title="Rolling 30-Day Volatility (Annualised %)",
                       title_font=dict(size=15, color=PRIMARY),
                       showlegend=False, **_layout)
    fig3.update_yaxes(ticksuffix="%")
    st.plotly_chart(fig3, use_container_width=True)

# ── Volume ────────────────────────────────────────────────────────────────────
if "Volume" in df.columns:
    vol_series = df["Volume"].squeeze().dropna()
    if not vol_series.empty and vol_series.sum() > 0:
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(
            x=vol_series.index, y=vol_series.values,
            name="Volume", marker_color=CLRS[1], opacity=0.7,
            hovertemplate="%{x|%b %Y}: %{y:,.0f}<extra></extra>",
        ))
        fig4.update_layout(title="Trading Volume",
                           title_font=dict(size=15, color=PRIMARY),
                           showlegend=False,
                           **{k: v for k, v in _layout.items() if k != "height"},
                           height=280)
        fig4.update_yaxes(tickformat=".2s")
        st.plotly_chart(fig4, use_container_width=True)

# ── Company Info & Ratios ─────────────────────────────────────────────────────
if info:
    with st.expander("Company Info & Key Ratios"):
        col_a, col_b = st.columns(2)

        def _s(key, pct=False, mult=1, suffix=""):
            v = info.get(key)
            if v is None: return "—"
            v = v * mult
            return f"{v:.2%}" if pct else f"{v:,.2f}{suffix}"

        with col_a:
            st.markdown(f"**Company**: {info.get('longName', ticker)}")
            st.markdown(f"**Sector**: {info.get('sector', '—')}")
            st.markdown(f"**Industry**: {info.get('industry', '—')}")
            mc = info.get("marketCap")
            st.markdown(f"**Market Cap**: {cur_sym}{mc/1e9:.1f}B" if mc else "**Market Cap**: —")
            st.markdown(f"**Exchange**: {info.get('exchange', '—')}")
            st.markdown(f"**Currency**: {currency}")
        with col_b:
            st.markdown(f"**Forward P/E**: {_s('forwardPE', suffix='x')}")
            st.markdown(f"**Trailing P/E**: {_s('trailingPE', suffix='x')}")
            st.markdown(f"**Price/Book**: {_s('priceToBook', suffix='x')}")
            st.markdown(f"**Dividend Yield**: {_s('dividendYield', pct=True)}")
            st.markdown(f"**Payout Ratio**: {_s('payoutRatio', pct=True)}")
            hi = info.get('fiftyTwoWeekHigh')
            lo = info.get('fiftyTwoWeekLow')
            st.markdown(f"**52W High / Low**: {cur_sym}{hi:,.2f} / {cur_sym}{lo:,.2f}" if hi and lo else "**52W High / Low**: —")

# ── Download ───────────────────────────────────────────────────────────────────
st.header("Download Data")
col_dl1, col_dl2 = st.columns(2)

with col_dl1:
    price_df = pd.DataFrame({"Date": price.index, "Close": price.values}).set_index("Date")
    price_df["Daily Return"] = returns.reindex(price.index)
    price_df["Cumulative Return"] = cum_ret.reindex(price.index)
    for ma_label in show_ma:
        if ma_label in df.columns:
            price_df[ma_label] = df[ma_label].squeeze().reindex(price.index)
    st.download_button(
        "📥 Download Price History (CSV)",
        data=price_df.to_csv().encode("utf-8"),
        file_name=f"{ticker}_{period}_history.csv",
        mime="text/csv",
        use_container_width=True,
    )

with col_dl2:
    roll_vol_series = returns.rolling(30).std() * np.sqrt(252) * 100
    vol_df = pd.DataFrame({
        "Date": roll_vol_series.index,
        "Rolling 30D Volatility (%)": roll_vol_series.values,
    }).set_index("Date")
    st.download_button(
        "📥 Download Volatility (CSV)",
        data=vol_df.to_csv().encode("utf-8"),
        file_name=f"{ticker}_{period}_volatility.csv",
        mime="text/csv",
        use_container_width=True,
    )

st.caption(
    "Data from Yahoo Finance · Enter any valid Yahoo Finance ticker "
    "(e.g. AAPL, SAN.MC, ^IBEX, BTC-USD) · Not financial advice"
)
