import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
import sys, os
from datetime import datetime

st.set_page_config(page_title="Personal Budget · Finance Tools", page_icon="💰", layout="wide")

PRIMARY = "#003f88"
GREEN   = "#1A936F"
RED     = "#C0392B"
CLRS    = ["#003f88", "#0066cc", "#1A936F", "#F39C12", "#C0392B", "#8E44AD", "#16A085", "#E67E22"]

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

st.title("💰 Personal Budget Planner")
st.markdown(
    '<p class="ev-caption">Monthly income & expenses · Savings rate · Spending breakdown · CSV export</p>',
    unsafe_allow_html=True,
)

# ── Settings ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Settings")
    budget_name    = st.text_input("Your name / label", value="My Budget")
    currency_label = st.selectbox("Currency", ["$ USD", "€ EUR", "£ GBP", "CHF", "Other"])
    cur_sym = {"$ USD": "$", "€ EUR": "€", "£ GBP": "£", "CHF": "CHF ", "Other": ""}.get(currency_label, "")
    period  = st.radio("Budget period", ["Monthly", "Annual"], horizontal=True)
    multiplier = 1 if period == "Monthly" else 12

st.header("Income")
st.caption("Enter your monthly income from all sources.")

INCOME_CATS = [
    "Salary / Wages (net)",
    "Freelance / Side Income",
    "Rental Income",
    "Investment Dividends",
    "Other Income",
]
income_vals = {}
inc_cols = st.columns(len(INCOME_CATS))
for i, cat in enumerate(INCOME_CATS):
    with inc_cols[i]:
        income_vals[cat] = st.number_input(
            cat, min_value=0.0, value=0.0, step=100.0, key=f"inc_{cat}"
        )

total_income = sum(income_vals.values())

# ── Expenses ──────────────────────────────────────────────────────────────────
st.header("Expenses")
st.caption("Enter your average monthly spending in each category.")

EXPENSE_CATS = {
    "🏠 Housing": ["Rent / Mortgage", "Utilities", "Internet & Phone", "Home Insurance"],
    "🚗 Transport": ["Car Payment / Lease", "Fuel / Public Transport", "Car Insurance", "Parking & Tolls"],
    "🛒 Living": ["Groceries", "Dining Out", "Personal Care", "Clothing"],
    "🏥 Health": ["Health Insurance", "Gym / Sports", "Medical & Pharmacy"],
    "🎬 Leisure": ["Streaming & Subscriptions", "Entertainment", "Holidays & Travel", "Hobbies"],
    "📚 Education": ["Courses & Books", "Childcare / School Fees"],
    "💳 Finance": ["Loan Repayments", "Credit Card Interest", "Life Insurance"],
    "🎁 Other": ["Gifts & Charity", "Miscellaneous"],
}

expense_vals = {}
for group, cats in EXPENSE_CATS.items():
    with st.expander(group, expanded=False):
        cols = st.columns(len(cats))
        for j, cat in enumerate(cats):
            with cols[j]:
                expense_vals[cat] = st.number_input(
                    cat, min_value=0.0, value=0.0, step=10.0, key=f"exp_{cat}"
                )

total_expenses = sum(expense_vals.values())
net_saving     = total_income - total_expenses
saving_rate    = (net_saving / total_income * 100) if total_income > 0 else 0.0

# Apply period multiplier for display
disp_income   = total_income   * multiplier
disp_expenses = total_expenses * multiplier
disp_saving   = net_saving     * multiplier

# ── KPI Cards ─────────────────────────────────────────────────────────────────
st.header("Summary")
k1, k2, k3, k4 = st.columns(4)
for col, label, value, sub, cls in [
    (k1, f"{period} Income",   f"{cur_sym}{disp_income:,.0f}",   "All sources", ""),
    (k2, f"{period} Expenses", f"{cur_sym}{disp_expenses:,.0f}", "All categories", "kpi-red"),
    (k3, f"{period} Savings",  f"{cur_sym}{disp_saving:,.0f}",   f"Net after expenses",
     "kpi-green" if disp_saving >= 0 else "kpi-red"),
    (k4, "Savings Rate",       f"{saving_rate:.1f}%",            "% of income saved",
     "kpi-green" if saving_rate >= 20 else ("" if saving_rate >= 10 else "kpi-red")),
]:
    with col:
        st.markdown(
            f'<div class="kpi-card {cls}">'
            f'<div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div>'
            f'<div class="kpi-sub">{sub}</div></div>',
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

if total_income == 0 and total_expenses == 0:
    st.info("Enter your income and expenses above to see your budget breakdown.")
    st.stop()

# ── Charts ────────────────────────────────────────────────────────────────────
_layout = dict(
    template="plotly_white",
    font=dict(family="Inter, Segoe UI, sans-serif", size=12),
    paper_bgcolor="white", plot_bgcolor="rgba(248,249,252,1)",
    margin=dict(t=52, b=45, l=65, r=20),
    legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="rgba(0,0,0,0.08)",
                borderwidth=1, font=dict(size=11)),
    hoverlabel=dict(bgcolor="white", font_size=12),
)

col_l, col_r = st.columns(2)

# Donut: spending by group
with col_l:
    group_totals = {
        g: sum(expense_vals.get(c, 0) for c in cats)
        for g, cats in EXPENSE_CATS.items()
    }
    group_totals = {k: v for k, v in group_totals.items() if v > 0}

    if group_totals:
        fig_donut = go.Figure(go.Pie(
            labels=[g.split(" ", 1)[1] for g in group_totals],
            values=list(group_totals.values()),
            hole=0.55,
            marker_colors=CLRS[:len(group_totals)],
            textinfo="percent+label",
            hovertemplate="%{label}: " + cur_sym + "%{value:,.0f}<extra></extra>",
        ))
        fig_donut.update_layout(
            title="Spending Breakdown",
            title_font=dict(size=15, color=PRIMARY),
            showlegend=False, height=380,
            **{k: v for k, v in _layout.items() if k not in ("legend",)},
        )
        st.plotly_chart(fig_donut, use_container_width=True)

# Bar: income vs expenses vs savings
with col_r:
    fig_bar = go.Figure()
    labels = ["Income", "Expenses", "Savings"]
    values = [disp_income, disp_expenses, disp_saving]
    colors = ["#0066cc", RED, GREEN if disp_saving >= 0 else RED]
    fig_bar.add_trace(go.Bar(
        x=labels, y=values,
        marker_color=colors, opacity=0.88,
        hovertemplate="%{x}: " + cur_sym + "%{y:,.0f}<extra></extra>",
    ))
    fig_bar.add_hline(y=0, line_color="rgba(0,0,0,0.2)", line_dash="dot")
    fig_bar.update_layout(
        title=f"{period} Overview",
        title_font=dict(size=15, color=PRIMARY),
        showlegend=False, height=380,
        **{k: v for k, v in _layout.items() if k not in ("legend",)},
    )
    fig_bar.update_yaxes(tickprefix=cur_sym, tickformat=",.0f")
    st.plotly_chart(fig_bar, use_container_width=True)

# ── Savings Rate Gauge ─────────────────────────────────────────────────────────
fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number+delta",
    value=saving_rate,
    number={"suffix": "%", "font": {"size": 36}},
    delta={"reference": 20, "suffix": "% vs 20% target"},
    gauge={
        "axis": {"range": [-50, 60], "ticksuffix": "%"},
        "bar": {"color": GREEN if saving_rate >= 20 else ("#F39C12" if saving_rate >= 10 else RED)},
        "steps": [
            {"range": [-50, 0],  "color": "#fdecea"},
            {"range": [0, 10],   "color": "#fff8e6"},
            {"range": [10, 20],  "color": "#e8f5e9"},
            {"range": [20, 60],  "color": "#d0f0e8"},
        ],
        "threshold": {"line": {"color": PRIMARY, "width": 3}, "thickness": 0.8, "value": 20},
    },
    title={"text": "Savings Rate<br><span style='font-size:0.8em;color:#999'>Target: 20%+</span>"},
))
fig_gauge.update_layout(height=280, margin=dict(t=60, b=20, l=40, r=40))
st.plotly_chart(fig_gauge, use_container_width=True)

# ── Detailed Table ─────────────────────────────────────────────────────────────
st.header("Detailed Breakdown")
rows = []
for group, cats in EXPENSE_CATS.items():
    group_name = group.split(" ", 1)[1]
    for cat in cats:
        v = expense_vals.get(cat, 0)
        if v > 0:
            pct = v / total_expenses * 100 if total_expenses > 0 else 0
            rows.append({
                "Category": group_name,
                "Item": cat,
                f"Monthly ({cur_sym})": f"{cur_sym}{v:,.0f}",
                f"Annual ({cur_sym})": f"{cur_sym}{v*12:,.0f}",
                "% of Expenses": f"{pct:.1f}%",
                "% of Income": f"{v / total_income * 100:.1f}%" if total_income > 0 else "—",
            })

if rows:
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ── Download CSV ───────────────────────────────────────────────────────────────
st.header("Download")
if rows:
    df_export = pd.DataFrame(rows)
    # Add summary rows
    summary = pd.DataFrame([
        {"Category": "TOTAL", "Item": "Income",   f"Monthly ({cur_sym})": f"{cur_sym}{total_income:,.0f}",   f"Annual ({cur_sym})": f"{cur_sym}{total_income*12:,.0f}",   "% of Expenses": "", "% of Income": "100%"},
        {"Category": "TOTAL", "Item": "Expenses", f"Monthly ({cur_sym})": f"{cur_sym}{total_expenses:,.0f}", f"Annual ({cur_sym})": f"{cur_sym}{total_expenses*12:,.0f}", "% of Expenses": "100%", "% of Income": f"{total_expenses/total_income*100:.1f}%" if total_income>0 else "—"},
        {"Category": "TOTAL", "Item": "Savings",  f"Monthly ({cur_sym})": f"{cur_sym}{net_saving:,.0f}",    f"Annual ({cur_sym})": f"{cur_sym}{net_saving*12:,.0f}",    "% of Expenses": "", "% of Income": f"{saving_rate:.1f}%"},
    ])
    df_full = pd.concat([df_export, summary], ignore_index=True)
    st.download_button(
        "📥 Download Budget (CSV)",
        data=df_full.to_csv(index=False).encode("utf-8"),
        file_name="personal_budget.csv",
        mime="text/csv",
        use_container_width=False,
    )

# ── PDF export ────────────────────────────────────────────────────────────────
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
    story.append(build_header("Personal Budget Planner", budget_name, logo_bytes=logo_bytes))
    story.append(spacer(0.4))

    story.append(kpi_row([
        (f"{period} Income",   f"{cur_sym}{disp_income:,.0f}",   "All sources"),
        (f"{period} Expenses", f"{cur_sym}{disp_expenses:,.0f}", "All categories"),
        (f"{period} Savings",  f"{cur_sym}{disp_saving:,.0f}",   "Net after expenses"),
        ("Savings Rate",       f"{saving_rate:.1f}%",            "Target: 20%+"),
    ]))
    story.append(spacer(0.4))

    if group_totals:
        story.append(section_heading("Spending Breakdown"))
        story.append(spacer(0.2))
        story.append(chart_image(fig_donut, height_ratio=0.45))
        story.append(spacer(0.4))

    story.append(section_heading(f"{period} Overview"))
    story.append(spacer(0.2))
    story.append(chart_image(fig_bar, height_ratio=0.45))
    story.append(spacer(0.4))

    if rows:
        story.append(section_heading("Detailed Breakdown"))
        story.append(spacer(0.2))
        story.append(data_table(
            ["Category", "Item", f"Monthly ({cur_sym})", f"Annual ({cur_sym})", "% of Expenses"],
            [[r["Category"], r["Item"], r[f"Monthly ({cur_sym})"], r[f"Annual ({cur_sym})"], r["% of Expenses"]]
             for r in rows],
        ))

    doc.build(story, canvasmaker=NumberedCanvas)
    buf.seek(0)
    return buf

if st.button("📄 Export PDF Report", type="primary"):
    try:
        pdf = build_pdf()
        st.download_button("⬇️ Download PDF", pdf,
                           file_name=f"personal_budget_{budget_name.replace(' ', '_')}.pdf",
                           mime="application/pdf", use_container_width=True)
        st.caption("📧 To share by email: download above and attach the PDF.")
    except Exception as e:
        st.error(f"PDF generation error: {e}")

st.caption("FinancePlots · Personal budget planner · Not financial advice")
