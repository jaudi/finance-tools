import streamlit as st

st.set_page_config(
    page_title="Finance Tools · FinancePlots",
    page_icon="📊",
    layout="wide",
)

st.markdown("""
    <style>
        .block-container { padding-top: 2rem; }
        .tool-card {
            background: #ffffff;
            border: 1px solid #e8edf4;
            border-radius: 12px;
            padding: 1.4rem 1.5rem;
            height: 100%;
        }
        .tool-icon  { font-size: 1.8rem; margin-bottom: 0.5rem; }
        .tool-title { font-size: 1rem; font-weight: 700; color: #003f88; margin-bottom: 0.3rem; }
        .tool-desc  { font-size: 0.85rem; color: #666; line-height: 1.55; }
        .section-label {
            font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
            letter-spacing: 0.08em; color: #0066cc; margin-bottom: 0.5rem;
        }
    </style>
""", unsafe_allow_html=True)

from mobile_css import inject_mobile_css
inject_mobile_css()

st.title("📊 Finance Tools")
st.markdown(
    "A free finance toolkit built by **FinancePlots**. "
    "No login required — open source, runs in your browser."
)
st.markdown("---")

# ── Business / FP&A ───────────────────────────────────────────────────────────
st.markdown('<p class="section-label">Business & FP&A</p>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    st.markdown("""<div class="tool-card">
        <div class="tool-icon">📈</div>
        <div class="tool-title">5-Year Financial Model</div>
        <div class="tool-desc">Project revenue, costs and profits over 5 years.
        Income statement, cash flow, balance sheet and PDF export.</div>
    </div>""", unsafe_allow_html=True)
    st.page_link("pages/1_Financial_Model.py", label="Open →", use_container_width=False)
with c2:
    st.markdown("""<div class="tool-card">
        <div class="tool-icon">💰</div>
        <div class="tool-title">Annual Budget</div>
        <div class="tool-desc">Monthly P&L with sales forecast, direct costs and
        overheads by category. Download/upload Excel template. PDF export.</div>
    </div>""", unsafe_allow_html=True)
    st.page_link("pages/2_Annual_Budget.py", label="Open →", use_container_width=False)

st.markdown("<br>", unsafe_allow_html=True)

# ── Lending ───────────────────────────────────────────────────────────────────
st.markdown('<p class="section-label">Lending</p>', unsafe_allow_html=True)
c3, c3b = st.columns(2)
with c3:
    st.markdown("""<div class="tool-card">
        <div class="tool-icon">🏦</div>
        <div class="tool-title">Lending Calculator</div>
        <div class="tool-desc">Loan amortisation schedule and mortgage analysis
        with early repayment strategy — compare loan rate vs savings rate.</div>
    </div>""", unsafe_allow_html=True)
    st.page_link("pages/3_Lending.py", label="Open →", use_container_width=False)

st.markdown("<br>", unsafe_allow_html=True)

# ── Markets & Investing ───────────────────────────────────────────────────────
st.markdown('<p class="section-label">Markets & Investing</p>', unsafe_allow_html=True)
c4, c5, c6, c7 = st.columns(4)
with c4:
    st.markdown("""<div class="tool-card">
        <div class="tool-icon">📦</div>
        <div class="tool-title">Portfolio Analysis</div>
        <div class="tool-desc">Global index portfolio — expected return,
        Sharpe ratio, VaR and allocation chart.</div>
    </div>""", unsafe_allow_html=True)
    st.page_link("pages/4_Portfolio_Analysis.py", label="Open →", use_container_width=False)
with c5:
    st.markdown("""<div class="tool-card">
        <div class="tool-icon">📉</div>
        <div class="tool-title">Stock Comparison</div>
        <div class="tool-desc">Compare two stocks — price history, cumulative
        returns, correlation and key ratios.</div>
    </div>""", unsafe_allow_html=True)
    st.page_link("pages/5_Stock_Comparison.py", label="Open →", use_container_width=False)
with c6:
    st.markdown("""<div class="tool-card">
        <div class="tool-icon">💹</div>
        <div class="tool-title">Compound Interest</div>
        <div class="tool-desc">See how initial capital and monthly contributions
        grow over time. Preloaded with historical market return benchmarks.</div>
    </div>""", unsafe_allow_html=True)
    st.page_link("pages/6_Compound_Interest.py", label="Open →", use_container_width=False)
with c7:
    st.markdown("""<div class="tool-card">
        <div class="tool-icon">🇪🇸</div>
        <div class="tool-title">IBEX 35</div>
        <div class="tool-desc">Spanish IBEX 35 — price history, 50/150/200-day
        moving averages and cumulative returns.</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Planning & Valuation ──────────────────────────────────────────────────────
st.markdown('<p class="section-label">Planning & Valuation</p>', unsafe_allow_html=True)
c8, c9, c10 = st.columns(3)
with c8:
    st.markdown("""<div class="tool-card">
        <div class="tool-icon">💧</div>
        <div class="tool-title">13-Week Cash Flow Forecast</div>
        <div class="tool-desc">Rolling weekly cash forecast with inflows, outflows
        and closing balance. PDF export.</div>
    </div>""", unsafe_allow_html=True)
    st.page_link("pages/8_Cash_Flow_Forecast.py", label="Open →", use_container_width=False)
with c9:
    st.markdown("""<div class="tool-card">
        <div class="tool-icon">⚖️</div>
        <div class="tool-title">Break-Even Analysis</div>
        <div class="tool-desc">Fixed vs variable costs, contribution margin,
        break-even units and margin of safety. PDF export.</div>
    </div>""", unsafe_allow_html=True)
    st.page_link("pages/9_Break_Even.py", label="Open →", use_container_width=False)
with c10:
    st.markdown("""<div class="tool-card">
        <div class="tool-icon">🏢</div>
        <div class="tool-title">Business Valuation</div>
        <div class="tool-desc">DCF, EBITDA multiple and revenue multiple — blended
        valuation range with industry benchmarks. PDF export.</div>
    </div>""", unsafe_allow_html=True)
    st.page_link("pages/10_Valuation.py", label="Open →", use_container_width=False)

# ── Fundraising ───────────────────────────────────────────────────────────────
st.markdown('<p class="section-label">Fundraising</p>', unsafe_allow_html=True)
c_pitch, _ = st.columns(2)
with c_pitch:
    st.markdown("""<div class="tool-card">
        <div class="tool-icon">🎯</div>
        <div class="tool-title">Pitch Deck Builder</div>
        <div class="tool-desc">9-slide investor pitch deck with cover, problem, solution,
        market size, business model, traction, financials, team and the ask.
        Download as editable PowerPoint (.pptx).</div>
    </div>""", unsafe_allow_html=True)
    st.page_link("pages/13_Pitch_Deck.py", label="Open →", use_container_width=False)

st.markdown("<br>", unsafe_allow_html=True)

# ── Utilities ─────────────────────────────────────────────────────────────────
st.markdown('<p class="section-label">Utilities</p>', unsafe_allow_html=True)
c_util, _ = st.columns(2)
with c_util:
    st.markdown("""<div class="tool-card">
        <div class="tool-icon">🎥</div>
        <div class="tool-title">Screen Recorder</div>
        <div class="tool-desc">Record your screen and download the video to share
        with colleagues. Runs entirely in your browser — nothing is uploaded.</div>
    </div>""", unsafe_allow_html=True)
    st.page_link("pages/12_Screen_Recorder.py", label="Open →", use_container_width=False)

st.markdown("---")
st.markdown(
    "<small>Built by <b>FinancePlots</b> · Data from Yahoo Finance · "
    "For informational purposes only · Not financial advice</small>",
    unsafe_allow_html=True,
)
