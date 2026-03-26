import streamlit as st

_MOBILE_CSS = """
<style>
/* ── Mobile-responsive columns ─────────────────────────────────────────────── */

/* Tablet (≤768px): columns wrap to 2 per row */
@media screen and (max-width: 768px) {
    [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
    }
    [data-testid="stHorizontalBlock"] > div,
    [data-testid="stHorizontalBlock"] > [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stHorizontalBlock"] > [data-testid="column"] {
        min-width: calc(50% - 0.5rem) !important;
        flex: 0 0 calc(50% - 0.5rem) !important;
        box-sizing: border-box !important;
    }
}

/* Phone (≤480px): all columns stack full-width */
@media screen and (max-width: 480px) {
    [data-testid="stHorizontalBlock"] > div,
    [data-testid="stHorizontalBlock"] > [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stHorizontalBlock"] > [data-testid="column"] {
        min-width: 100% !important;
        flex: 0 0 100% !important;
        box-sizing: border-box !important;
    }
    .kpi-value {
        font-size: 1.1rem !important;
    }
    .block-container {
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
    }
}

/* Make dataframes and tables horizontally scrollable on mobile */
@media screen and (max-width: 768px) {
    [data-testid="stDataFrame"],
    [data-testid="stDataEditor"] {
        overflow-x: auto !important;
    }
}
</style>
"""

def inject_mobile_css():
    """Inject mobile-responsive CSS. Call once per page, after st.set_page_config."""
    st.markdown(_MOBILE_CSS, unsafe_allow_html=True)
