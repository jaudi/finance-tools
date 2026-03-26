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

/* ── Compact sidebar navigation on mobile ───────────────────────────────────── */
@media screen and (max-width: 768px) {
    /* Reduce padding on each nav link */
    [data-testid="stSidebarNavLink"] {
        padding-top: 0.25rem !important;
        padding-bottom: 0.25rem !important;
        font-size: 0.82rem !important;
        line-height: 1.3 !important;
    }
    /* Tighten nav section spacing */
    [data-testid="stSidebarNav"] {
        padding-top: 0.25rem !important;
        padding-bottom: 0.25rem !important;
    }
    /* Narrower sidebar so it doesn't cover the full screen */
    [data-testid="stSidebar"] > div:first-child {
        width: 220px !important;
        min-width: 220px !important;
    }
    /* Reduce sidebar header padding */
    [data-testid="stSidebar"] .block-container {
        padding-top: 1rem !important;
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
    }
}

/* ── Hide built-in sidebar navigation (use home page as directory) ─────────── */
[data-testid="stSidebarNav"] {
    display: none !important;
}

/* ── Home page: style Open link inside tool cards ──────────────────────────── */
[data-testid="stPageLink"] a {
    display: block;
    margin-top: 0.6rem;
    font-size: 0.82rem;
    font-weight: 600;
    color: #0066cc !important;
    text-decoration: none !important;
}
[data-testid="stPageLink"] a:hover {
    color: #003f88 !important;
    text-decoration: underline !important;
}
</style>
"""

def inject_mobile_css():
    """Inject mobile-responsive CSS. Call once per page, after st.set_page_config."""
    st.markdown(_MOBILE_CSS, unsafe_allow_html=True)
