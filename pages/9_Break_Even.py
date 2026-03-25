import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
from datetime import datetime

PRIMARY = "#003f88"
ACCENT  = "#0066cc"
GREEN   = "#1A936F"
RED     = "#C0392B"

st.set_page_config(page_title="Break-Even Analysis · Finance Tools", page_icon="⚖️", layout="wide")

st.markdown("""
    <style>
        .block-container { padding-top: 1.5rem; }
        h2 { font-size: 1.25rem !important; color: #333;
             border-bottom: 2px solid #eee; padding-bottom: 6px; margin-top: 1.5rem; }
        .ev-caption { color: #888; font-size: 0.88rem; margin-top: -6px; margin-bottom: 1rem; }
        .kpi-card  { background: #f7f9fc; border-left: 4px solid #0066cc;
                     border-radius: 6px; padding: 0.9rem 1rem; height: 100%; }
        .kpi-green { border-left-color: #1A936F !important; }
        .kpi-red   { border-left-color: #C0392B !important; }
        .kpi-label { font-size: 0.78rem; color: #888; font-weight: 600; text-transform: uppercase; }
        .kpi-value { font-size: 1.6rem; font-weight: 800; color: #003f88; line-height: 1.2; }
        .kpi-sub   { font-size: 0.78rem; color: #999; margin-top: 2px; }
    </style>
""", unsafe_allow_html=True)

st.title("⚖️ Break-Even Analysis")
st.markdown(
    '<p class="ev-caption">Fixed costs · Variable costs · Selling price · Break-even point · Margin of safety</p>',
    unsafe_allow_html=True,
)

# ── Inputs ─────────────────────────────────────────────────────────────────────
st.header("Assumptions")
c1, c2 = st.columns(2)

with c1:
    st.subheader("Fixed Costs (per period)")
    fixed_items = {
        "Rent & Utilities":    st.number_input("Rent & Utilities ($)", min_value=0.0, value=5000.0, step=100.0),
        "Payroll":             st.number_input("Payroll ($)",          min_value=0.0, value=20000.0, step=500.0),
        "Insurance":           st.number_input("Insurance ($)",        min_value=0.0, value=500.0,  step=50.0),
        "Depreciation":        st.number_input("Depreciation ($)",     min_value=0.0, value=1000.0, step=100.0),
        "Marketing":           st.number_input("Marketing ($)",        min_value=0.0, value=2000.0, step=100.0),
        "Other Fixed":         st.number_input("Other Fixed ($)",      min_value=0.0, value=500.0,  step=100.0),
    }

with c2:
    st.subheader("Revenue & Variable Costs")
    selling_price  = st.number_input("Selling price per unit ($)", min_value=0.01, value=100.0, step=1.0)
    variable_cost  = st.number_input("Variable cost per unit ($)", min_value=0.0,  value=40.0,  step=1.0)
    current_units  = st.number_input("Current / expected units sold", min_value=0, value=500, step=10)
    company        = st.text_input("Company / product name", value="My Product")

total_fixed = sum(fixed_items.values())
contribution_margin = selling_price - variable_cost

if contribution_margin <= 0:
    st.error("Selling price must be greater than variable cost per unit.")
    st.stop()

cm_ratio        = contribution_margin / selling_price
bep_units       = total_fixed / contribution_margin
bep_revenue     = total_fixed / cm_ratio
current_revenue = current_units * selling_price
current_profit  = (contribution_margin * current_units) - total_fixed
safety_units    = current_units - bep_units
safety_revenue  = current_revenue - bep_revenue
safety_pct      = (safety_units / current_units * 100) if current_units > 0 else 0

# ── KPI cards ──────────────────────────────────────────────────────────────────
st.header("Results")
k1, k2, k3, k4 = st.columns(4)

profit_cls = "kpi-green" if current_profit >= 0 else "kpi-red"
safety_cls = "kpi-green" if safety_units >= 0 else "kpi-red"

for col, label, value, sub, cls in [
    (k1, "Break-Even Units",   f"{bep_units:,.0f} units",  f"Break-even revenue: ${bep_revenue:,.0f}", ""),
    (k2, "Contribution Margin",f"${contribution_margin:,.2f}",f"CM ratio: {cm_ratio*100:.1f}%", "kpi-green"),
    (k3, "Current Profit",     f"${current_profit:,.0f}",  f"At {current_units:,} units", profit_cls),
    (k4, "Margin of Safety",   f"{safety_pct:.1f}%",       f"{safety_units:,.0f} units above BEP", safety_cls),
]:
    with col:
        st.markdown(
            f'<div class="kpi-card {cls}">'
            f'<div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div>'
            f'<div class="kpi-sub">{sub}</div>'
            f'</div>', unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

# ── Chart ──────────────────────────────────────────────────────────────────────
max_units = max(int(bep_units * 2.2), current_units + 50, 100)
unit_range = list(range(0, max_units + 1, max(1, max_units // 200)))

revenue_line  = [u * selling_price for u in unit_range]
total_cost    = [total_fixed + u * variable_cost for u in unit_range]
fixed_line    = [total_fixed] * len(unit_range)

fig = go.Figure()
fig.add_scatter(x=unit_range, y=revenue_line, name="Revenue",
                line=dict(color=ACCENT, width=3))
fig.add_scatter(x=unit_range, y=total_cost, name="Total Cost",
                line=dict(color=RED, width=3))
fig.add_scatter(x=unit_range, y=fixed_line, name="Fixed Costs",
                line=dict(color="#F39C12", width=2, dash="dot"))
fig.add_vline(x=bep_units, line_dash="dash", line_color=GREEN, line_width=2,
              annotation_text=f"BEP: {bep_units:,.0f} units",
              annotation_font_color=GREEN)
if current_units > 0:
    fig.add_vline(x=current_units, line_dash="dot", line_color="#9B59B6", line_width=2,
                  annotation_text=f"Current: {current_units:,} units",
                  annotation_font_color="#9B59B6")

fig.update_layout(
    title="Break-Even Chart",
    title_font=dict(size=18, color=PRIMARY),
    height=460,
    font=dict(family="Inter, Arial, sans-serif", size=12),
    paper_bgcolor="white", plot_bgcolor="rgba(248,249,252,1)",
    margin=dict(t=60, b=50, l=70, r=20),
    xaxis_title="Units Sold",
    yaxis_title="$ Amount",
    legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="rgba(0,0,0,0.08)", borderwidth=1),
)
fig.update_xaxes(showgrid=False, showline=True, linecolor="rgba(0,0,0,0.12)")
fig.update_yaxes(gridcolor="rgba(0,0,0,0.06)", zeroline=False)
st.plotly_chart(fig, use_container_width=True)

# ── Sensitivity table ──────────────────────────────────────────────────────────
st.header("Sensitivity — Units vs Profit")
st.caption("Profit at different sales volumes.")

volumes = [int(bep_units * m) for m in [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]]
if current_units not in volumes:
    volumes.append(current_units)
volumes = sorted(set(volumes))

sens_rows = []
for u in volumes:
    rev  = u * selling_price
    cost = total_fixed + u * variable_cost
    prof = rev - cost
    sens_rows.append({
        "Units": f"{u:,}",
        "Revenue ($)": f"${rev:,.0f}",
        "Total Cost ($)": f"${cost:,.0f}",
        "Profit ($)": f"${prof:,.0f}",
        "Profit Margin": f"{(prof/rev*100) if rev > 0 else 0:.1f}%",
        "Status": "✅ Profit" if prof > 0 else ("🟡 Break-Even" if prof == 0 else "🔴 Loss"),
    })

st.dataframe(pd.DataFrame(sens_rows), use_container_width=True, hide_index=True)

# ── Fixed cost breakdown ───────────────────────────────────────────────────────
st.header("Fixed Cost Breakdown")
fig2 = go.Figure(go.Pie(
    labels=list(fixed_items.keys()),
    values=list(fixed_items.values()),
    hole=0.4,
    marker=dict(colors=[ACCENT, "#003f88", GREEN, RED, "#F39C12", "#9B59B6"],
                line=dict(color="white", width=2)),
    textinfo="label+percent",
    textposition="outside",
))
fig2.update_layout(
    title="Fixed Cost Composition",
    title_font=dict(size=16, color=PRIMARY),
    height=380,
    font=dict(family="Inter, Arial, sans-serif", size=12),
    paper_bgcolor="white",
    margin=dict(t=50, b=20, l=20, r=20),
)
st.plotly_chart(fig2, use_container_width=True)

# ── PDF export ────────────────────────────────────────────────────────────────
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pdf_utils import (
    new_doc, build_header, section_heading, kpi_row,
    data_table, chart_image, spacer, divider, NumberedCanvas,
)

st.subheader("Export")
logo_file = st.file_uploader("Upload company logo (optional)", type=["png", "jpg", "jpeg"], key="logo")
logo_bytes = logo_file.read() if logo_file else None

def build_pdf():
    buf = io.BytesIO()
    doc = new_doc(buf)

    story = []
    story.append(build_header("Break-Even Analysis", company, logo_bytes=logo_bytes))
    story.append(spacer(0.4))

    story.append(kpi_row([
        ("Break-Even Units",  f"{bep_units:,.0f}",         f"BEP revenue: ${bep_revenue:,.0f}"),
        ("Contribution Margin", f"${contribution_margin:,.2f}", f"CM ratio: {cm_ratio*100:.1f}%"),
        ("Current Profit",    f"${current_profit:,.0f}",   f"At {current_units:,} units"),
        ("Margin of Safety",  f"{safety_pct:.1f}%",        f"{safety_units:,.0f} units above BEP"),
    ]))
    story.append(spacer(0.4))

    story.append(section_heading("Break-Even Chart"))
    story.append(spacer(0.2))
    story.append(chart_image(fig, height_ratio=0.48))
    story.append(spacer(0.4))

    story.append(section_heading("Sensitivity Analysis"))
    story.append(spacer(0.2))
    story.append(data_table(
        ["Units", "Revenue", "Total Cost", "Profit", "Margin"],
        [[r["Units"], r["Revenue ($)"], r["Total Cost ($)"], r["Profit ($)"], r["Profit Margin"]]
         for r in sens_rows],
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    buf.seek(0)
    return buf

if st.button("📄 Export PDF Report", type="primary"):
    try:
        pdf = build_pdf()
        st.download_button("⬇️ Download PDF", pdf,
                           file_name=f"breakeven_{company.replace(' ','_')}.pdf",
                           mime="application/pdf", use_container_width=True)
        st.caption("📧 To share by email: download above and attach the PDF.")
    except Exception as e:
        st.error(f"PDF generation error: {e}")
