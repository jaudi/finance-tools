import base64
import streamlit.components.v1 as components


def share_pdf_button(pdf_buf, filename="report.pdf"):
    """
    Renders a Share PDF button using the Web Share API.
    On mobile: opens the native share sheet (WhatsApp, Telegram, email…).
    On unsupported browsers: shows a fallback note.
    """
    if hasattr(pdf_buf, "seek"):
        pdf_buf.seek(0)
    raw = pdf_buf.read() if hasattr(pdf_buf, "read") else pdf_buf
    b64 = base64.b64encode(raw).decode()
    safe_name = filename.replace('"', "").replace("'", "")

    html = f"""
<style>
.fp-share-btn {{
    display: flex; align-items: center; justify-content: center; gap: 6px;
    width: 100%; background: #25D366; color: #fff; border: none;
    border-radius: 6px; padding: 0.45rem 0;
    font-size: 0.88rem; font-weight: 600; cursor: pointer;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    margin-top: 4px;
}}
.fp-share-btn:active {{ background: #1da851; }}
.fp-note {{
    font-size: 0.75rem; color: #888; margin-top: 4px; display: none;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
}}
</style>
<button class="fp-share-btn" onclick="sharePDF()">📤 Share (WhatsApp / email…)</button>
<div class="fp-note" id="fp-note">Sharing not supported — use Download above.</div>
<script>
async function sharePDF() {{
    const bytes = Uint8Array.from(atob("{b64}"), c => c.charCodeAt(0));
    const file = new File([bytes], "{safe_name}", {{type: "application/pdf"}});
    if (navigator.canShare && navigator.canShare({{files: [file]}})) {{
        try {{ await navigator.share({{files: [file], title: "{safe_name}"}}) }}
        catch(e) {{ if (e.name !== "AbortError") document.getElementById("fp-note").style.display="block" }}
    }} else {{
        document.getElementById("fp-note").style.display = "block";
    }}
}}
</script>
"""
    components.html(html, height=60)
