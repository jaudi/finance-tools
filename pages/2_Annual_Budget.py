import streamlit as st
import pandas as pd
import io
import plotly.graph_objects as go
from datetime import datetime

import sys as _sys_ab, os as _os_ab
_sys_ab.path.insert(0, _os_ab.path.join(_os_ab.dirname(__file__), ".."))
from pdf_utils import (
    new_doc, build_header, section_heading, kpi_row,
    data_table, chart_image, spacer, NumberedCanvas, CONTENT_W,
)
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

# ── Constants ──────────────────────────────────────────────────────────────────
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

PRIMARY = "#003f88"
ACCENT  = "#0066cc"
CLRS    = ["#003f88", "#0066cc", "#3399ff", "#00B4AE", "#1A936F", "#C0392B", "#F39C12"]

PDF_HDR = colors.HexColor("#003f88")
PDF_ACC = colors.HexColor("#0066cc")
PDF_ALT = colors.HexColor("#EAF1FB")

OVERHEAD_LINES = [
    "Payroll Costs",
    "HR",
    "Legal & Professional",
    "Facilities",
    "IT",
    "Travel & Subsistence",
    "Other",
]

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Annual Budget · Finance Tools",
    page_icon="💰",
    layout="wide",
)

st.markdown("""
    <style>
        .block-container { padding-top: 1.5rem; }
        h2 { font-size: 1.25rem !important; color: #333;
             border-bottom: 2px solid #eee; padding-bottom: 6px; margin-top: 1.5rem; }
        .ev-caption { color: #888; font-size: 0.88rem; margin-top: -6px; margin-bottom: 1rem; }
        .kpi-card {
            background: #f7f9fc;
            border-left: 4px solid #0066cc;
            border-radius: 6px;
            padding: 0.9rem 1rem;
            height: 100%;
        }
        .kpi-positive { border-left-color: #1A936F !important; }
        .kpi-negative { border-left-color: #C0392B !important; }
        .kpi-label { font-size: 0.78rem; color: #888; font-weight: 600; text-transform: uppercase; }
        .kpi-value { font-size: 1.6rem; font-weight: 800; color: #003f88; line-height: 1.2; }
        .kpi-sub   { font-size: 0.78rem; color: #999; margin-top: 2px; }
    </style>
""", unsafe_allow_html=True)

st.title("💰 Annual Budget")
st.markdown(
    '<p class="ev-caption">Sales forecast · Direct costs · Overheads · '
    'Monthly P&L · PDF export</p>',
    unsafe_allow_html=True,
)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Settings")
    company_name = st.text_input("Company / report name", value="My Company")
    budget_year  = st.number_input("Budget Year", min_value=2000, max_value=2100,
                                   value=2025, step=1)
    currency     = st.selectbox("Currency symbol", ["$", "£", "€"])

    st.markdown("---")
    st.caption("Revenue lines (up to 5)")
    n_rev = int(st.number_input("Revenue lines", min_value=1, max_value=5,
                                 value=2, step=1, label_visibility="collapsed"))
    st.caption("Direct cost lines (up to 5)")
    n_dc  = int(st.number_input("Direct cost lines", min_value=1, max_value=5,
                                 value=2, step=1, label_visibility="collapsed"))

# ── Default DataFrames ─────────────────────────────────────────────────────────
def _zero_df(labels):
    return pd.DataFrame({"Category": labels, **{m: 0.0 for m in MONTHS}})

def default_sales(n):
    return _zero_df([f"Revenue Line {i + 1}" for i in range(n)])

def default_dc(n):
    return _zero_df([f"Direct Cost {i + 1}" for i in range(n)])

def default_oh():
    return _zero_df(OVERHEAD_LINES)

# ── Session state — reset when row count changes ───────────────────────────────
if st.session_state.get("_n_rev") != n_rev:
    st.session_state.sales_df   = default_sales(n_rev)
    st.session_state["_n_rev"]  = n_rev

if st.session_state.get("_n_dc") != n_dc:
    st.session_state.dc_df      = default_dc(n_dc)
    st.session_state["_n_dc"]   = n_dc

if "oh_df" not in st.session_state:
    st.session_state.oh_df = default_oh()

# ── Template builder ───────────────────────────────────────────────────────────
def build_template(n_rev, n_dc):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        default_sales(n_rev).to_excel(writer, sheet_name="Sales Forecast", index=False)
        default_dc(n_dc).to_excel(   writer, sheet_name="Direct Costs",    index=False)
        default_oh().to_excel(        writer, sheet_name="Overheads",       index=False)

        wb = writer.book
        for ws in wb.worksheets:
            ws.column_dimensions["A"].width = 28
            for letter in "BCDEFGHIJKLM":
                ws.column_dimensions[letter].width = 10

            # Freeze header row
            ws.freeze_panes = "B2"

    buf.seek(0)
    return buf.read()

# ── Download / Upload ──────────────────────────────────────────────────────────
col_dl, col_up = st.columns([1, 2])

with col_dl:
    st.download_button(
        "📥 Download Template",
        data=build_template(n_rev, n_dc),
        file_name=f"budget_template_{int(budget_year)}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        help="Download an Excel template, fill it in, then upload it below.",
    )

with col_up:
    uploaded = st.file_uploader(
        "Or upload a filled template (.xlsx)",
        type=["xlsx"],
        label_visibility="collapsed",
    )
    if uploaded:
        try:
            xl = pd.read_excel(uploaded, sheet_name=None)
            if "Sales Forecast" in xl:
                st.session_state.sales_df = xl["Sales Forecast"].fillna(0)
            if "Direct Costs" in xl:
                st.session_state.dc_df = xl["Direct Costs"].fillna(0)
            if "Overheads" in xl:
                st.session_state.oh_df = xl["Overheads"].fillna(0)
            st.success("Template loaded successfully.")
        except Exception as e:
            st.error(f"Could not read file: {e}")

st.markdown("---")

# ── Column config for data_editor ─────────────────────────────────────────────
_num_cfg = {
    m: st.column_config.NumberColumn(m, min_value=0, step=100, format="%.0f")
    for m in MONTHS
}
_cat_cfg = st.column_config.TextColumn("Category", width="medium")

# ── Input: Sales Forecast ──────────────────────────────────────────────────────
st.subheader(f"Sales Forecast ({currency})")
st.caption("Monthly revenue by line. Rename category labels as needed.")

sales_df = st.data_editor(
    st.session_state.sales_df,
    column_config={"Category": _cat_cfg, **_num_cfg},
    use_container_width=True,
    hide_index=True,
    key="sales_editor",
)

# ── Input: Direct Costs ────────────────────────────────────────────────────────
st.subheader(f"Direct Costs ({currency})")
st.caption("Variable costs directly tied to revenue — materials, direct labour, commissions, etc.")

dc_df = st.data_editor(
    st.session_state.dc_df,
    column_config={"Category": _cat_cfg, **_num_cfg},
    use_container_width=True,
    hide_index=True,
    key="dc_editor",
)

# ── Input: Overheads ──────────────────────────────────────────────────────────
st.subheader(f"Overheads ({currency})")
st.caption("Fixed and semi-fixed operating costs. Categories are locked to standard FP&A structure.")

oh_df = st.data_editor(
    st.session_state.oh_df,
    column_config={"Category": _cat_cfg, **_num_cfg},
    use_container_width=True,
    hide_index=True,
    disabled=["Category"],
    key="oh_editor",
)

# ── Calculations ───────────────────────────────────────────────────────────────
sales_m  = sales_df[MONTHS].sum()
dc_m     = dc_df[MONTHS].sum()
oh_m     = oh_df[MONTHS].sum()
gp_m     = sales_m - dc_m
ebitda_m = gp_m - oh_m

total_rev    = float(sales_m.sum())
total_dc     = float(dc_m.sum())
total_gp     = float(gp_m.sum())
total_oh     = float(oh_m.sum())
total_ebitda = float(ebitda_m.sum())

gp_pct     = total_gp     / total_rev * 100 if total_rev else 0.0
ebitda_pct = total_ebitda / total_rev * 100 if total_rev else 0.0

oh_by_cat  = oh_df.set_index("Category")[MONTHS].sum(axis=1)

# ── P&L Summary ────────────────────────────────────────────────────────────────
st.markdown("---")
st.header(f"P&L Summary — {int(budget_year)}")

# KPI cards
k1, k2, k3, k4 = st.columns(4)
kpi_defs = [
    (k1, "Total Revenue",   total_rev,    f"Avg {currency}{total_rev/12:,.0f} / mo",    ""),
    (k2, "Gross Profit",    total_gp,     f"Margin: {gp_pct:.1f}%",
         "kpi-positive" if total_gp >= 0 else "kpi-negative"),
    (k3, "Total Overheads", total_oh,     f"Avg {currency}{total_oh/12:,.0f} / mo",     ""),
    (k4, "EBITDA",          total_ebitda, f"Margin: {ebitda_pct:.1f}%",
         "kpi-positive" if total_ebitda >= 0 else "kpi-negative"),
]

for col, label, value, sub, cls in kpi_defs:
    sign = "-" if value < 0 else ""
    display = f"{sign}{currency}{abs(value):,.0f}"
    with col:
        st.markdown(
            f'<div class="kpi-card {cls}">'
            f'<div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{display}</div>'
            f'<div class="kpi-sub">{sub}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

# ── Monthly P&L table ──────────────────────────────────────────────────────────
def _fmt(val):
    return f"{currency}{val:,.0f}" if val >= 0 else f"({currency}{abs(val):,.0f})"

def _pct_rev(val):
    return f"{val / total_rev * 100:.1f}%" if total_rev else "—"

rows = []

for _, r in sales_df.iterrows():
    rows.append({"": f"  {r['Category']}",
                 **{m: _fmt(r[m]) for m in MONTHS},
                 "FY Total": _fmt(r[MONTHS].sum()),
                 "% Rev": _pct_rev(r[MONTHS].sum())})
rows.append({"": "▸ Total Revenue",
             **{m: _fmt(sales_m[m]) for m in MONTHS},
             "FY Total": _fmt(total_rev),
             "% Rev": "100.0%"})

rows.append({"": "", **{m: "" for m in MONTHS}, "FY Total": "", "% Rev": ""})

for _, r in dc_df.iterrows():
    rows.append({"": f"  {r['Category']}",
                 **{m: _fmt(r[m]) for m in MONTHS},
                 "FY Total": _fmt(r[MONTHS].sum()),
                 "% Rev": _pct_rev(r[MONTHS].sum())})
rows.append({"": "▸ Total Direct Costs",
             **{m: _fmt(dc_m[m]) for m in MONTHS},
             "FY Total": _fmt(total_dc),
             "% Rev": _pct_rev(total_dc)})

rows.append({"": "", **{m: "" for m in MONTHS}, "FY Total": "", "% Rev": ""})

rows.append({"": "GROSS PROFIT",
             **{m: _fmt(gp_m[m]) for m in MONTHS},
             "FY Total": _fmt(total_gp),
             "% Rev": f"{gp_pct:.1f}%"})
rows.append({"": "Gross Margin %",
             **{m: f"{gp_m[m]/sales_m[m]*100:.1f}%" if sales_m[m] else "—" for m in MONTHS},
             "FY Total": f"{gp_pct:.1f}%",
             "% Rev": ""})

rows.append({"": "", **{m: "" for m in MONTHS}, "FY Total": "", "% Rev": ""})

for _, r in oh_df.iterrows():
    rows.append({"": f"  {r['Category']}",
                 **{m: _fmt(r[m]) for m in MONTHS},
                 "FY Total": _fmt(r[MONTHS].sum()),
                 "% Rev": _pct_rev(r[MONTHS].sum())})
rows.append({"": "▸ Total Overheads",
             **{m: _fmt(oh_m[m]) for m in MONTHS},
             "FY Total": _fmt(total_oh),
             "% Rev": _pct_rev(total_oh)})

rows.append({"": "", **{m: "" for m in MONTHS}, "FY Total": "", "% Rev": ""})

rows.append({"": "EBITDA",
             **{m: _fmt(ebitda_m[m]) for m in MONTHS},
             "FY Total": _fmt(total_ebitda),
             "% Rev": f"{ebitda_pct:.1f}%"})
rows.append({"": "EBITDA Margin %",
             **{m: f"{ebitda_m[m]/sales_m[m]*100:.1f}%" if sales_m[m] else "—" for m in MONTHS},
             "FY Total": f"{ebitda_pct:.1f}%",
             "% Rev": ""})

pl_df = pd.DataFrame(rows).set_index("")
st.dataframe(pl_df, use_container_width=True)

# ── Charts ────────────────────────────────────────────────────────────────────
st.header("Visualizations")

_layout = dict(
    template="plotly_white",
    height=370,
    font=dict(family="Inter, Segoe UI, Arial, sans-serif", size=12),
    paper_bgcolor="white",
    plot_bgcolor="rgba(248,249,252,1)",
    margin=dict(t=52, b=45, l=70, r=20),
    bargap=0.25,
    legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="rgba(0,0,0,0.08)",
                borderwidth=1, font=dict(size=11)),
    hoverlabel=dict(bgcolor="white", bordercolor="rgba(0,0,0,0.1)", font_size=12),
)

def _ax(fig, money=True):
    fig.update_xaxes(showgrid=False, showline=True, linecolor="rgba(0,0,0,0.12)",
                     tickfont=dict(size=11), zeroline=False)
    fmt = dict(tickprefix=currency, tickformat=",.0f") if money else dict(ticksuffix="%")
    fig.update_yaxes(gridcolor="rgba(0,0,0,0.06)", showline=False, tickfont=dict(size=11),
                     zeroline=True, zerolinecolor="rgba(0,0,0,0.2)", **fmt)

# Chart 1: Revenue vs Costs by month
fig1 = go.Figure()
fig1.add_trace(go.Bar(x=MONTHS, y=sales_m.values, name="Revenue",
                      marker_color=CLRS[0], opacity=0.88))
fig1.add_trace(go.Bar(x=MONTHS, y=dc_m.values, name="Direct Costs",
                      marker_color=CLRS[5], opacity=0.80))
fig1.add_trace(go.Bar(x=MONTHS, y=oh_m.values, name="Overheads",
                      marker_color=CLRS[2], opacity=0.80))
fig1.update_layout(title="Revenue vs Costs by Month", barmode="group",
                   title_font=dict(size=16, color=PRIMARY), **_layout)
_ax(fig1, money=True)

# Chart 2: Monthly EBITDA (green/red bars)
bar_colors = [CLRS[4] if v >= 0 else CLRS[5] for v in ebitda_m.values]
fig2 = go.Figure()
fig2.add_trace(go.Bar(x=MONTHS, y=ebitda_m.values, name="EBITDA",
                      marker_color=bar_colors, opacity=0.88))
fig2.add_hline(y=0, line_width=1.5, line_color="rgba(0,0,0,0.25)")
fig2.update_layout(title="Monthly EBITDA", title_font=dict(size=16, color=PRIMARY),
                   showlegend=False, **_layout)
_ax(fig2, money=True)

# Chart 3: Overhead breakdown donut
oh_nonzero = oh_by_cat[oh_by_cat > 0]
fig3 = go.Figure()
if not oh_nonzero.empty:
    fig3.add_trace(go.Pie(
        labels=oh_nonzero.index.tolist(),
        values=oh_nonzero.values,
        hole=0.52,
        marker=dict(colors=CLRS[:len(oh_nonzero)]),
        textfont=dict(size=11),
        hovertemplate="%{label}: " + currency + "%{value:,.0f}<extra></extra>",
    ))
else:
    fig3.add_annotation(text="No overhead data yet", x=0.5, y=0.5,
                        showarrow=False, font=dict(size=14, color="#aaa"))
fig3.update_layout(title="Overhead Breakdown", title_font=dict(size=16, color=PRIMARY),
                   **{k: v for k, v in _layout.items() if k != "bargap"})

# Chart 4: Cumulative EBITDA
cum = ebitda_m.cumsum()
fill_color = "rgba(26,147,111,0.10)" if total_ebitda >= 0 else "rgba(192,57,43,0.10)"
line_color  = CLRS[4] if total_ebitda >= 0 else CLRS[5]
fig4 = go.Figure()
fig4.add_trace(go.Scatter(
    x=MONTHS, y=cum.values, name="Cumulative EBITDA",
    mode="lines+markers",
    line=dict(width=3, color=line_color),
    marker=dict(size=8, line=dict(width=2, color="white")),
    fill="tozeroy", fillcolor=fill_color,
    hovertemplate="%{x}: " + currency + "%{y:,.0f}<extra></extra>",
))
fig4.add_hline(y=0, line_width=1.5, line_color="rgba(0,0,0,0.25)")
fig4.update_layout(title="Cumulative EBITDA", title_font=dict(size=16, color=PRIMARY),
                   showlegend=False, **_layout)
_ax(fig4, money=True)

col_l, col_r = st.columns(2)
with col_l:
    st.plotly_chart(fig1, use_container_width=True)
    st.plotly_chart(fig3, use_container_width=True)
with col_r:
    st.plotly_chart(fig2, use_container_width=True)
    st.plotly_chart(fig4, use_container_width=True)

# ── PDF Export ────────────────────────────────────────────────────────────────
st.header("Export")

if st.button("📄 Export PDF Report", type="primary", use_container_width=True):
    try:
        def _neg(val):
            return f"{currency}{val:,.0f}" if val >= 0 else f"({currency}{abs(val):,.0f})"

        buf = io.BytesIO()
        doc = new_doc(buf)
        story = []

        story.append(build_header(f"Annual Budget {int(budget_year)}", company_name))
        story.append(spacer(0.4))

        story.append(kpi_row([
            ("Total Revenue",    _neg(total_rev),    "Full year"),
            ("Gross Profit",     _neg(total_gp),     f"Margin: {gp_pct:.1f}%"),
            ("Total Overheads",  _neg(total_oh),     "Full year"),
            ("EBITDA",           _neg(total_ebitda), f"Margin: {ebitda_pct:.1f}%"),
        ]))
        story.append(spacer(0.4))

        for fig_obj, title in [
            (fig1, "Revenue vs Direct Costs"),
            (fig2, "Gross Profit & EBITDA"),
            (fig3, "Monthly P&L"),
            (fig4, "Cost Breakdown"),
        ]:
            story.append(section_heading(title))
            story.append(spacer(0.2))
            story.append(chart_image(fig_obj, height_ratio=0.44))
            story.append(spacer(0.3))

        # Annual P&L table
        story.append(section_heading("Annual P&L"))
        story.append(spacer(0.2))

        pdf_pl_rows = []
        for _, r in sales_df.iterrows():
            fy = float(r[MONTHS].sum())
            pdf_pl_rows.append([f"  {r['Category']}", _neg(fy), _pct_rev(fy)])
        pdf_pl_rows.append(["▸ Total Revenue", _neg(total_rev), "100.0%"])
        pdf_pl_rows.append(["", "", ""])
        for _, r in dc_df.iterrows():
            fy = float(r[MONTHS].sum())
            pdf_pl_rows.append([f"  {r['Category']}", _neg(fy), _pct_rev(fy)])
        pdf_pl_rows.append(["▸ Total Direct Costs", _neg(total_dc), _pct_rev(total_dc)])
        pdf_pl_rows.append(["GROSS PROFIT", _neg(total_gp), f"{gp_pct:.1f}%"])
        pdf_pl_rows.append(["", "", ""])
        for _, r in oh_df.iterrows():
            fy = float(r[MONTHS].sum())
            pdf_pl_rows.append([f"  {r['Category']}", _neg(fy), _pct_rev(fy)])
        pdf_pl_rows.append(["▸ Total Overheads", _neg(total_oh), _pct_rev(total_oh)])
        pdf_pl_rows.append(["EBITDA", _neg(total_ebitda), f"{ebitda_pct:.1f}%"])

        story.append(data_table(
            ["Line Item", "Full Year", "% Revenue"],
            pdf_pl_rows,
            col_widths=[CONTENT_W * 0.55, CONTENT_W * 0.25, CONTENT_W * 0.20],
        ))

        doc.build(story, canvasmaker=NumberedCanvas)
        buf.seek(0)

        st.download_button(
            "⬇️ Download PDF",
            buf,
            file_name=f"budget_{company_name.replace(' ', '_')}_{int(budget_year)}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    except Exception as e:
        st.error(f"PDF generation error: {e}")

# ── Disclaimer ─────────────────────────────────────────────────────────────────
with st.expander("Notes & assumptions"):
    st.markdown("""
    - **EBITDA** = Gross Profit − Total Overheads (depreciation, amortisation, interest and tax are excluded)
    - All figures are in the selected currency with no FX conversion
    - This tool is for internal planning purposes only and does not constitute financial advice
    - Overhead categories follow standard FP&A classification; reclassify as needed for your chart of accounts
    """)
