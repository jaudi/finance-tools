import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
from datetime import datetime

PRIMARY = "#003f88"
ACCENT  = "#0066cc"
CLRS    = ["#003f88", "#0066cc", "#1A936F", "#C0392B", "#F39C12"]

st.set_page_config(page_title="Lending · Finance Tools", page_icon="🏦", layout="wide")

st.markdown("""
    <style>
        .block-container { padding-top: 1.5rem; }
        h2 { font-size: 1.25rem !important; color: #333;
             border-bottom: 2px solid #eee; padding-bottom: 6px; margin-top: 1.5rem; }
        .ev-caption { color: #888; font-size: 0.88rem; margin-top: -6px; margin-bottom: 1rem; }
        .kpi-card { background: #f7f9fc; border-left: 4px solid #0066cc;
                    border-radius: 6px; padding: 0.9rem 1rem; height: 100%; }
        .kpi-red  { border-left-color: #C0392B !important; }
        .kpi-green{ border-left-color: #1A936F !important; }
        .kpi-label{ font-size: 0.78rem; color: #888; font-weight: 600; text-transform: uppercase; }
        .kpi-value{ font-size: 1.6rem; font-weight: 800; color: #003f88; line-height: 1.2; }
        .kpi-sub  { font-size: 0.78rem; color: #999; margin-top: 2px; }
    </style>
""", unsafe_allow_html=True)

st.title("🏦 Lending Calculator")
st.markdown(
    '<p class="ev-caption">Loan amortisation · Mortgage analysis · Early repayment strategy</p>',
    unsafe_allow_html=True,
)

# ── Shared functions ───────────────────────────────────────────────────────────
def monthly_payment(rate, years, amount):
    r = rate / 12
    n = years * 12
    return amount * r / (1 - (1 + r) ** -n)

def amortisation_schedule(rate, years, amount):
    r       = rate / 12
    payment = monthly_payment(rate, years, amount)
    balance = amount
    rows    = []
    for period in range(1, years * 12 + 1):
        interest   = balance * r
        principal  = payment - interest
        balance   -= principal
        rows.append({
            "Period":    period,
            "Payment":   round(payment, 2),
            "Interest":  round(interest, 2),
            "Principal": round(principal, 2),
            "Balance":   round(max(balance, 0), 2),
        })
    return pd.DataFrame(rows)

def savings_monthly(target, months, annual_rate):
    r = annual_rate / 12
    if r == 0:
        return target / months
    return target * r / ((1 + r) ** months - 1)

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["📋 Loan Calculator", "🏠 Mortgage & Early Repayment"])

# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — LOAN CALCULATOR
# ════════════════════════════════════════════════════════════════════════════════
with tab1:
    with st.sidebar:
        st.header("Loan Parameters")
        l_amount = st.number_input("Loan Amount", min_value=1_000, max_value=10_000_000,
                                   value=20_000, step=500)
        l_rate   = st.slider("Annual Interest Rate (%)", 0.1, 20.0, 5.0, 0.1)
        l_years  = st.slider("Duration (Years)", 1, 40, 5, 1)

    df = amortisation_schedule(l_rate / 100, l_years, l_amount)
    total_paid     = df["Payment"].sum()
    total_interest = df["Interest"].sum()
    total_principal= df["Principal"].sum()

    # KPI cards
    k1, k2, k3, k4 = st.columns(4)
    kpis = [
        (k1, "Monthly Payment",  df["Payment"].iloc[0],  f"{l_years} years",              ""),
        (k2, "Total Repayment",  total_paid,             f"Loan: ${l_amount:,.0f}",        ""),
        (k3, "Total Interest",   total_interest,         f"{total_interest/l_amount*100:.1f}% of loan", "kpi-red"),
        (k4, "Interest Saved vs Interest-only",
             total_interest - (l_amount * (l_rate/100) * l_years),
             "vs. interest-only loan", "kpi-green"),
    ]
    for col, label, val, sub, cls in kpis:
        with col:
            st.markdown(
                f'<div class="kpi-card {cls}">'
                f'<div class="kpi-label">{label}</div>'
                f'<div class="kpi-value">${val:,.0f}</div>'
                f'<div class="kpi-sub">{sub}</div></div>',
                unsafe_allow_html=True,
            )
    st.markdown("<br>", unsafe_allow_html=True)

    # Charts
    _layout = dict(template="plotly_white", height=360,
                   font=dict(family="Inter, Segoe UI, sans-serif", size=12),
                   paper_bgcolor="white", plot_bgcolor="rgba(248,249,252,1)",
                   margin=dict(t=50, b=45, l=70, r=20), bargap=0.2,
                   hoverlabel=dict(bgcolor="white", font_size=12))

    col_l, col_r = st.columns(2)

    with col_l:
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=df["Period"], y=df["Interest"], name="Interest",
                                  mode="lines", line=dict(width=2.5, color=CLRS[3]),
                                  fill="tozeroy", fillcolor="rgba(192,57,43,0.08)"))
        fig1.add_trace(go.Scatter(x=df["Period"], y=df["Principal"], name="Principal",
                                  mode="lines", line=dict(width=2.5, color=CLRS[2]),
                                  fill="tozeroy", fillcolor="rgba(26,147,111,0.08)"))
        fig1.update_layout(title="Interest vs Principal by Period",
                           title_font=dict(size=15, color=PRIMARY), **_layout)
        fig1.update_xaxes(title="Month")
        fig1.update_yaxes(tickprefix="$", tickformat=",.0f")
        st.plotly_chart(fig1, use_container_width=True)

    with col_r:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=df["Period"], y=df["Balance"], name="Remaining Balance",
                                  mode="lines", line=dict(width=2.5, color=CLRS[0]),
                                  fill="tozeroy", fillcolor="rgba(0,63,136,0.07)"))
        fig2.update_layout(title="Outstanding Balance Over Time",
                           title_font=dict(size=15, color=PRIMARY), **_layout)
        fig2.update_xaxes(title="Month")
        fig2.update_yaxes(tickprefix="$", tickformat=",.0f")
        st.plotly_chart(fig2, use_container_width=True)

    # Breakdown donut
    fig3 = go.Figure(go.Pie(
        labels=["Principal", "Total Interest"],
        values=[l_amount, total_interest],
        hole=0.52,
        marker=dict(colors=[CLRS[2], CLRS[3]]),
    ))
    fig3.update_layout(title="Payment Breakdown", title_font=dict(size=15, color=PRIMARY),
                       **{k: v for k, v in _layout.items() if k != "bargap"})
    st.plotly_chart(fig3, use_container_width=True)

    # Amortisation table
    with st.expander("Full Amortisation Schedule"):
        st.dataframe(df.set_index("Period"), use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — MORTGAGE + EARLY REPAYMENT
# ════════════════════════════════════════════════════════════════════════════════
with tab2:
    with st.sidebar:
        st.markdown("---")
        st.header("Mortgage Parameters")
        m_amount  = st.number_input("Mortgage Amount", min_value=10_000,
                                    max_value=10_000_000, value=250_000, step=5_000)
        m_rate    = st.slider("Mortgage Interest Rate (%)", 0.1, 20.0, 4.5, 0.1)
        m_years   = st.slider("Mortgage Duration (Years)", 1, 40, 25, 1)
        m_sav_rate= st.slider("Savings/Investment Rate (%)", 0.1, 20.0, 6.0, 0.1,
                              help="What annual return you could get if you invested instead of repaying early")

    mdf = amortisation_schedule(m_rate / 100, m_years, m_amount)
    m_total_paid     = mdf["Payment"].sum()
    m_total_interest = mdf["Interest"].sum()

    # KPI cards
    mk1, mk2, mk3, mk4 = st.columns(4)
    m_kpis = [
        (mk1, "Monthly Payment",  mdf["Payment"].iloc[0], f"{m_years}-year mortgage",        ""),
        (mk2, "Total Cost",       m_total_paid,           f"Loan: ${m_amount:,.0f}",          ""),
        (mk3, "Total Interest",   m_total_interest,       f"{m_total_interest/m_amount*100:.1f}% of mortgage", "kpi-red"),
    ]
    for col, label, val, sub, cls in m_kpis:
        with col:
            st.markdown(
                f'<div class="kpi-card {cls}">'
                f'<div class="kpi-label">{label}</div>'
                f'<div class="kpi-value">${val:,.0f}</div>'
                f'<div class="kpi-sub">{sub}</div></div>',
                unsafe_allow_html=True,
            )
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Early Repayment Analysis ───────────────────────────────────────────────
    st.header("Early Repayment Analysis")
    st.caption("How much would you save by paying off the mortgage 5 years early?")

    n_months = m_years * 12
    if n_months > 60:
        cutoff_idx        = n_months - 60 - 1          # index of month (n-60)
        balance_at_cutoff = mdf.loc[cutoff_idx, "Balance"]
        months_to_save    = int(mdf.loc[cutoff_idx, "Period"])
        interest_saved    = mdf.loc[cutoff_idx + 1:, "Interest"].sum()
        monthly_saving    = savings_monthly(balance_at_cutoff, months_to_save, m_sav_rate / 100)

        # KPI for early repayment
        er1, er2, er3, er4 = st.columns(4)
        recommend = m_sav_rate > m_rate
        rec_cls   = "kpi-green" if recommend else "kpi-red"

        cards = [
            (er1, "Balance at Year -5",   balance_at_cutoff, f"After {m_years-5} years",         ""),
            (er2, "Interest Saved",        interest_saved,    "Last 5 years eliminated",           "kpi-green"),
            (er3, "Monthly Saving Needed", monthly_saving,    f"Over {months_to_save} months",      ""),
            (er4, "Strategy",
             "Invest" if recommend else "Repay",
             f"Savings rate ({m_sav_rate}%) {'>' if recommend else '<'} mortgage rate ({m_rate}%)",
             rec_cls),
        ]
        for col, label, val, sub, cls in cards:
            with col:
                display = f"${val:,.0f}" if isinstance(val, (int, float)) else val
                st.markdown(
                    f'<div class="kpi-card {cls}">'
                    f'<div class="kpi-label">{label}</div>'
                    f'<div class="kpi-value">{display}</div>'
                    f'<div class="kpi-sub">{sub}</div></div>',
                    unsafe_allow_html=True,
                )
        st.markdown("<br>", unsafe_allow_html=True)

        if recommend:
            st.info(
                f"**Invest instead of repaying early.** "
                f"Your savings/investment rate ({m_sav_rate}%) exceeds the mortgage rate ({m_rate}%). "
                f"You generate more wealth by investing the ${monthly_saving:,.0f}/mo than by paying down the mortgage.",
                icon="💡",
            )
        else:
            st.info(
                f"**Pay off early.** "
                f"Your mortgage rate ({m_rate}%) exceeds what savings earn ({m_sav_rate}%). "
                f"Save ${monthly_saving:,.0f}/mo for {months_to_save} months to eliminate the last 5 years "
                f"and save ${interest_saved:,.0f} in interest.",
                icon="💡",
            )
    else:
        st.warning("Mortgage must be longer than 5 years for early repayment analysis.")

    # Charts
    _layout2 = dict(template="plotly_white", height=360,
                    font=dict(family="Inter, Segoe UI, sans-serif", size=12),
                    paper_bgcolor="white", plot_bgcolor="rgba(248,249,252,1)",
                    margin=dict(t=50, b=45, l=70, r=20), bargap=0.2,
                    hoverlabel=dict(bgcolor="white", font_size=12))

    col_ml, col_mr = st.columns(2)
    with col_ml:
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(x=mdf["Period"], y=mdf["Interest"], name="Interest",
                                  mode="lines", line=dict(width=2.5, color=CLRS[3]),
                                  fill="tozeroy", fillcolor="rgba(192,57,43,0.08)"))
        fig4.add_trace(go.Scatter(x=mdf["Period"], y=mdf["Principal"], name="Principal",
                                  mode="lines", line=dict(width=2.5, color=CLRS[2]),
                                  fill="tozeroy", fillcolor="rgba(26,147,111,0.08)"))
        if n_months > 60:
            fig4.add_vline(x=months_to_save, line_dash="dot", line_color="#F39C12",
                           annotation_text="Early repayment target",
                           annotation_position="top left")
        fig4.update_layout(title="Interest vs Principal", title_font=dict(size=15, color=PRIMARY),
                           **_layout2)
        fig4.update_xaxes(title="Month")
        fig4.update_yaxes(tickprefix="$", tickformat=",.0f")
        st.plotly_chart(fig4, use_container_width=True)

    with col_mr:
        fig5 = go.Figure()
        fig5.add_trace(go.Scatter(x=mdf["Period"], y=mdf["Balance"], name="Balance",
                                  mode="lines", line=dict(width=2.5, color=CLRS[0]),
                                  fill="tozeroy", fillcolor="rgba(0,63,136,0.07)"))
        if n_months > 60:
            fig5.add_vline(x=months_to_save, line_dash="dot", line_color="#F39C12",
                           annotation_text="Early repayment target",
                           annotation_position="top left")
        fig5.update_layout(title="Outstanding Balance", title_font=dict(size=15, color=PRIMARY),
                           **_layout2)
        fig5.update_xaxes(title="Month")
        fig5.update_yaxes(tickprefix="$", tickformat=",.0f")
        st.plotly_chart(fig5, use_container_width=True)

    with st.expander("Full Mortgage Schedule"):
        st.dataframe(mdf.set_index("Period"), use_container_width=True)

with st.expander("Notes"):
    st.markdown("""
    - All calculations use the **French amortisation method** (fixed monthly payment, reducing balance)
    - Early repayment analysis compares paying off 5 years early vs saving/investing the difference
    - If your investment return > mortgage rate: investing the extra capital generates more wealth
    - If your mortgage rate > investment return: early repayment is the better financial decision
    - This tool is for illustrative purposes only and does not constitute financial advice
    """)

# ── Export ─────────────────────────────────────────────────────────────────────
st.header("Export")

col_xl, col_pdf = st.columns(2)

# Excel
with col_xl:
    xl_buf = io.BytesIO()
    with pd.ExcelWriter(xl_buf, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Loan Amortisation", index=False)
        mdf.to_excel(writer, sheet_name="Mortgage Schedule", index=False)
        summary = pd.DataFrame({
            "Metric": ["Loan Amount", "Annual Rate (%)", "Duration (yrs)", "Monthly Payment",
                       "Total Repayment", "Total Interest"],
            "Value": [l_amount, l_rate, l_years,
                      round(df["Payment"].iloc[0], 2),
                      round(total_paid, 2), round(total_interest, 2)],
        })
        summary.to_excel(writer, sheet_name="Loan Summary", index=False)
    xl_buf.seek(0)
    st.download_button(
        "📊 Download Excel",
        xl_buf,
        file_name="lending_calculator.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

# PDF
with col_pdf:
    import sys as _sys, os as _os
    _sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), ".."))
    from pdf_utils import (
        new_doc, build_header, section_heading, kpi_row,
        data_table, chart_image, spacer, NumberedCanvas,
    )

    logo_file = st.file_uploader("Upload company logo (optional)", type=["png", "jpg", "jpeg"], key="logo")
    logo_bytes = logo_file.read() if logo_file else None

    if st.button("📄 Export PDF Report", type="primary", use_container_width=True):
        try:
            buf = io.BytesIO()
            doc = new_doc(buf)
            story = []

            story.append(build_header("Mortgage & Loan Calculator",
                                      f"Loan: ${l_amount:,.0f} · {l_rate}% · {l_years} yrs",
                                      logo_bytes=logo_bytes))
            story.append(spacer(0.4))

            story.append(kpi_row([
                ("Monthly Payment",  f"${df['Payment'].iloc[0]:,.0f}", f"{l_years}-year term"),
                ("Total Repayment",  f"${total_paid:,.0f}",            f"Loan: ${l_amount:,.0f}"),
                ("Total Interest",   f"${total_interest:,.0f}",        f"{total_interest/l_amount*100:.1f}% of loan"),
                ("Interest Rate",    f"{l_rate}%",                     "Annual"),
            ]))
            story.append(spacer(0.4))

            story.append(section_heading("Interest vs Principal"))
            story.append(spacer(0.2))
            story.append(chart_image(fig1, height_ratio=0.42))
            story.append(spacer(0.4))

            story.append(section_heading("Amortisation Schedule (first 24 months)"))
            story.append(spacer(0.2))
            preview = df.head(24).copy()
            story.append(data_table(
                list(preview.columns),
                preview.astype(str).values.tolist(),
            ))

            doc.build(story, canvasmaker=NumberedCanvas)
            buf.seek(0)
            st.download_button(
                "⬇️ Download PDF",
                buf,
                file_name="lending_calculator.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
            st.caption("📧 To share by email: download above and attach the PDF.")
        except Exception as e:
            st.error(f"PDF generation error: {e}")
