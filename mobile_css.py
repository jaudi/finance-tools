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

/* ── Compact home page on mobile ────────────────────────────────────────────── */
@media screen and (max-width: 768px) {
    /* Hide card descriptions — show only icon + title + link */
    .tool-desc {
        display: none !important;
    }
    /* Reduce card padding */
    .tool-card {
        padding: 0.75rem 1rem !important;
    }
    /* Reduce section label spacing */
    .section-label {
        margin-bottom: 0.25rem !important;
    }
    /* Shrink <br> spacers between sections */
    br {
        display: block;
        content: "";
        margin-top: -0.5rem !important;
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

_DARK_THEME_CSS = """
<style>
/* ── Dark theme overrides ──────────────────────────────────────────────────── */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"] {
    background-color: #0e1117 !important;
    color: #e2e8f0 !important;
}
[data-testid="stHeader"] {
    background-color: #0e1117 !important;
}
[data-testid="stSidebar"] {
    background-color: #161b27 !important;
}
/* Tool cards */
.tool-card {
    background: #1a1f2e !important;
    border-color: #2d3748 !important;
}
.tool-title { color: #93c5fd !important; }
.tool-desc  { color: #94a3b8 !important; }
.section-label { color: #60a5fa !important; }
/* Headings and body text */
h1, h2, h3, h4, h5, h6,
[data-testid="stMarkdown"] p,
[data-testid="stMarkdown"] small {
    color: #e2e8f0 !important;
}
hr { border-color: #2d3748 !important; }
/* Page link (Open → buttons) */
[data-testid="stPageLink"] a {
    color: #60a5fa !important;
}
[data-testid="stPageLink"] a:hover {
    color: #93c5fd !important;
}
</style>
"""

_LIGHT_THEME_CSS = """
<style>
/* ── Light theme restore ───────────────────────────────────────────────────── */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"] {
    background-color: #ffffff !important;
    color: #1a1a1a !important;
}
[data-testid="stHeader"] {
    background-color: #ffffff !important;
}
[data-testid="stSidebar"] {
    background-color: #f8fafc !important;
}
.tool-card {
    background: #ffffff !important;
    border-color: #e8edf4 !important;
}
.tool-title { color: #003f88 !important; }
.tool-desc  { color: #666666 !important; }
.section-label { color: #0066cc !important; }
[data-testid="stPageLink"] a {
    color: #0066cc !important;
}
[data-testid="stPageLink"] a:hover {
    color: #003f88 !important;
}
</style>
"""


def inject_mobile_css():
    """Inject mobile-responsive CSS. Call once per page, after st.set_page_config."""
    st.markdown(_MOBILE_CSS, unsafe_allow_html=True)


def inject_theme_css(dark_mode: bool):
    """Inject dark or light theme CSS overrides. Call after inject_mobile_css."""
    st.markdown(_DARK_THEME_CSS if dark_mode else _LIGHT_THEME_CSS, unsafe_allow_html=True)
