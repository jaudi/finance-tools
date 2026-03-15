import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io

st.set_page_config(page_title="Commodities · Finance Tools", page_icon="🛢️", layout="wide")

PRIMARY = "#003f88"
CLRS    = ["#003f88", "#0066cc", "#C0392B", "#F39C12", "#1A936F", "#8E44AD"]

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

st.title("🛢️ Commodities Dashboard")
st.markdown(
    '<p class="ev-caption">Live prices · Historical charts · '
    'Performance comparison · CSV download</p>',
    unsafe_allow_html=True,
)

COMMODITIES = {
    "Gold":        ("GC=F",  "USD/oz"),
    "Silver":      ("SI=F",  "USD/oz"),
    "Crude Oil":   ("CL=F",  "USD/bbl"),
    "Natural Gas": ("NG=F",  "USD/MMBtu"),
    "Copper":      ("HG=F",  "USD/lb"),
    "Wheat":       ("ZW=F",  "USD/bu"),
}

PERIODS = {"5 Days": "5d", "1 Month": "1mo", "3 Months": "3mo",
           "6 Months": "6mo", "1 Year": "1y", "5 Years": "5y", "Max": "max"}

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Settings")
    selected = st.multiselect(
        "Select commodities",
        list(COMMODITIES.keys()),
        default=list(COMMODITIES.keys()),
    )
    period_label = st.selectbox("Time period", list(PERIODS.keys()), index=4)
    period       = PERIODS[period_label]

if not selected:
    st.warning("Select at least one commodity.")
    st.stop()

# ── Fetch data ────────────────────────────────────────────────────────────────
import yfinance as yf

@st.cache_data(ttl=900)
def fetch_commodity_data(tickers, period):
    data = {}
    for name, (ticker, unit) in tickers.items():
        try:
            df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
            if not df.empty:
                data[name] = df["Close"]
        except Exception as e:
            st.warning(f"Could not load data for {name}: {e}")
    return data

ticker_map = {k: v for k, v in COMMODITIES.items() if k in selected}

with st.spinner("Fetching market data..."):
    raw_data = fetch_commodity_data(ticker_map, period)

if not raw_data:
    st.error("Could not fetch data. Try again later.")
    st.stop()

# ── KPI cards — last price + change ───────────────────────────────────────────
st.header("Current Prices")
cols = st.columns(len(raw_data))

for i, (name, series) in enumerate(raw_data.items()):
    series = series.dropna()
    if len(series) < 2:
        continue
    last    = float(series.iloc[-1])
    prev    = float(series.iloc[-2])
    chg     = last - prev
    chg_pct = chg / prev * 100
    _, unit = COMMODITIES[name]
    cls     = "kpi-green" if chg >= 0 else "kpi-red"
    sign    = "▲" if chg >= 0 else "▼"
    with cols[i]:
        st.markdown(
            f'<div class="kpi-card {cls}">'
            f'<div class="kpi-label">{name}</div>'
            f'<div class="kpi-value">${last:,.2f}</div>'
            f'<div class="kpi-sub">{sign} {abs(chg_pct):.2f}% · {unit}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

# ── Performance comparison (normalised) ───────────────────────────────────────
st.header("Performance Comparison")

_layout = dict(
    template="plotly_white", height=420,
    font=dict(family="Inter, Segoe UI, sans-serif", size=12),
    paper_bgcolor="white", plot_bgcolor="rgba(248,249,252,1)",
    margin=dict(t=52, b=45, l=65, r=20),
    legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="rgba(0,0,0,0.08)",
                borderwidth=1, font=dict(size=11)),
    hoverlabel=dict(bgcolor="white", font_size=12),
)

fig_perf = go.Figure()
for i, (name, series) in enumerate(raw_data.items()):
    series = series.dropna()
    if len(series) < 2:
        continue
    norm = series / series.iloc[0] * 100
    fig_perf.add_trace(go.Scatter(
        x=norm.index, y=norm.values,
        name=name, mode="lines",
        line=dict(width=2.5, color=CLRS[i % len(CLRS)]),
        hovertemplate=f"{name}: %{{y:.1f}} (base 100)<extra></extra>",
    ))
fig_perf.add_hline(y=100, line_dash="dot", line_color="rgba(0,0,0,0.2)")
fig_perf.update_layout(title=f"Normalised Performance — Base 100 ({period_label})",
                       title_font=dict(size=15, color=PRIMARY), **_layout)
fig_perf.update_yaxes(tickformat=".0f")
st.plotly_chart(fig_perf, use_container_width=True)

# ── Individual charts ──────────────────────────────────────────────────────────
st.header("Individual Charts")

items = list(raw_data.items())
for row_start in range(0, len(items), 2):
    row_items = items[row_start:row_start + 2]
    cols2 = st.columns(2)
    for j, (name, series) in enumerate(row_items):
        series = series.dropna()
        if series.empty:
            continue
        _, unit = COMMODITIES[name]
        chg_total = float((series.iloc[-1] / series.iloc[0] - 1) * 100)
        line_color = CLRS[list(raw_data.keys()).index(name) % len(CLRS)]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=series.index, y=series.values,
            name=name, mode="lines",
            line=dict(width=2.5, color=line_color),
            fill="tozeroy",
            fillcolor=f"rgba(0,63,136,0.06)",
            hovertemplate=f"{name}: %{{y:,.2f}} {unit}<extra></extra>",
        ))
        fig.update_layout(
            title=f"{name} · {period_label} · {chg_total:+.1f}%",
            title_font=dict(size=14, color=PRIMARY),
            showlegend=False,
            **{k: v for k, v in _layout.items() if k != "legend"},
            height=300,
        )
        fig.update_yaxes(tickprefix="$", tickformat=",.2f")
        with cols2[j]:
            st.plotly_chart(fig, use_container_width=True)

# ── Download CSV ───────────────────────────────────────────────────────────────
st.header("Download Data")
if raw_data:
    combined = pd.DataFrame(raw_data)
    combined.index.name = "Date"
    csv = combined.to_csv().encode("utf-8")
    st.download_button(
        "📥 Download CSV",
        data=csv,
        file_name=f"commodities_{period}.csv",
        mime="text/csv",
        use_container_width=False,
    )

st.caption("Data from Yahoo Finance · Futures prices · Delays may apply")
