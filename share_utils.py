import urllib.parse
import streamlit as st

_SITE_URL = "https://www.financeplots.com"

_TOOL_NAMES = {
    "breakeven":  "Break-Even Analysis",
    "financial":  "5-Year Financial Model",
    "budget":     "Annual Budget",
    "lending":    "Lending Calculator",
    "portfolio":  "Portfolio Analysis",
    "compound":   "Compound Interest Calculator",
    "cashflow":   "13-Week Cash Flow Forecast",
    "valuation":  "Business Valuation Calculator",
    "personal":   "Personal Budget Planner",
}


def _tool_name(filename: str) -> str:
    key = filename.replace(".pdf", "").split("_")[0].lower()
    return _TOOL_NAMES.get(key, "Finance Tool")


def share_pdf_button(pdf_buf, filename="report.pdf"):
    """
    Renders WhatsApp and X share buttons linking to FinancePlots.
    pdf_buf and filename are kept for API compatibility but not used for sharing
    (direct file sharing from web is blocked in sandboxed iframes).
    """
    tool = _tool_name(filename)
    wa_text = f"I just used this free finance tool — {tool} 📊 {_SITE_URL}"
    x_text  = f"Just used {tool} on FinancePlots — free finance tools 📊"

    wa_url = f"https://wa.me/?text={urllib.parse.quote(wa_text)}"
    x_url  = (
        f"https://x.com/intent/tweet"
        f"?text={urllib.parse.quote(x_text)}"
        f"&url={urllib.parse.quote(_SITE_URL)}"
    )

    st.markdown(
        f"""
        <div style="display:flex;gap:8px;margin-top:6px;">
            <a href="{wa_url}" target="_blank"
               style="flex:1;display:flex;align-items:center;justify-content:center;
                      gap:5px;background:#25D366;color:#fff;text-decoration:none;
                      border-radius:6px;padding:0.45rem 0;font-size:0.85rem;
                      font-weight:600;font-family:sans-serif;">
                📤 WhatsApp
            </a>
            <a href="{x_url}" target="_blank"
               style="flex:1;display:flex;align-items:center;justify-content:center;
                      gap:5px;background:#000;color:#fff;text-decoration:none;
                      border-radius:6px;padding:0.45rem 0;font-size:0.85rem;
                      font-weight:600;font-family:sans-serif;">
                𝕏 Share on X
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )
