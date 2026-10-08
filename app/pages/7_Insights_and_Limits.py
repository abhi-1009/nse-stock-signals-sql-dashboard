from pathlib import Path

import pandas as pd
import streamlit as st

import db
import theme

theme.setup("Insights & Limits", "🧾")
theme.header("Insights & Limits", "Every claim comes with its evidence and its caveat")

summary = db.load_summary()
ss = db.load_strategy_summary()
events = db.load_events()
latest = db.load_latest_signals()
if summary.empty:
    st.warning("No data returned.")
    st.stop()

tcs = summary[summary["stock"] == "TCS"].iloc[0]
inf = summary[summary["stock"] == "Infosys"].iloc[0]
lag = int((ss["strategy_minus_buyhold"] < 0).sum()) if not ss.empty else 0

st.subheader("Key claims")
with st.expander("1. Unadjusted prices make TCS and Infosys look like big losers - they were not", expanded=True):
    st.markdown(f"**Claim.** After adjusting for 1:1 bonus issues, TCS moved {tcs['pct_change_adj']:+.1f}% "
                f"(raw: {tcs['pct_change_raw']:+.1f}%) and Infosys {inf['pct_change_adj']:+.1f}% "
                f"(raw: {inf['pct_change_raw']:+.1f}%).")
    st.markdown("**Evidence.** SQL Tasks 11-13 (`sql/05_data_trap_and_fix.sql`): one-day drops of about 50% on the event dates.")
    st.markdown("**Caveat.** The event dates were inferred from the price series; the ratio (1:1) and dates must be "
                "confirmed against the exchange/company announcements. Dividends are ignored.")
with st.expander("2. Signals are infrequent, and the price cliff distorts some of them"):
    st.markdown(f"**Claim.** On adjusted prices there are {int(summary['buys_adj'].sum())} Buys and "
                f"{int(summary['sells_adj'].sum())} Sells across six stocks in 3.5 years "
                f"({int(summary['buys_raw'].sum())} / {int(summary['sells_raw'].sum())} on raw prices).")
    st.markdown("**Evidence.** Task 10 (`sql/04_all_stocks.sql`) and the Data Trap page's signal comparison.")
    st.markdown("**Caveat.** Only one window pair (20/50) was tested; other windows would give different counts.")
with st.expander("3. Following the golden cross did not beat buy-and-hold"):
    st.markdown(f"**Claim.** The strategy trailed buy-and-hold for {lag} of {len(ss)} stocks.")
    st.markdown("**Evidence.** `sql/07_strategy_evaluation.sql` and the Strategy page (adjusted prices, long-only).")
    st.markdown("**Caveat.** Very few trades per stock, no costs or dividends, same-day-close execution, "
                "and one 3.5-year window that includes a strong trending period for some stocks.")
with st.expander("4. The latest signal is context, not a forecast"):
    if not latest.empty:
        st.markdown("**Latest signals:** " + ", ".join(
            f"{r['stock']} - {r['signal']} ({pd.Timestamp(r['date']):%d %b %Y})" for _, r in latest.iterrows()))
    st.markdown("**Caveat.** Moving averages use only past prices, so a golden cross confirms a trend that has "
                "already started; it cannot tell you a trend is about to begin.")

st.subheader("Method questions")
st.markdown(
    "- **How early can a golden cross tell you anything?** Not before 50 trading days of history exist, and even then "
    "the 20-day average lags price, so signals arrive after part of the move has happened.\n"
    "- **What changes after fixing the data?** TCS and Infosys move from apparent losers to clear gainers, and "
    "some signals near the events appear or disappear once the cliff is removed (Data Trap page).\n"
    "- **What is missing?** Dividends, brokerage and taxes, news, market-wide moves, volume/liquidity limits, "
    "and any out-of-sample test.")

st.subheader("Limitations and biases")
st.markdown(
    "- **Selection / survivorship bias:** six hand-picked large companies (four autos, two IT) that survived and did well; not the whole market.\n"
    "- **One market phase, in-sample:** 3.5 years that were mostly rising, and every result is measured on the data it was built on.\n"
    "- **Execution (look-ahead) bias:** trades are assumed at the same-day close the signal is computed on, which flatters the strategy.\n"
    "- **Small samples:** 6-12 trades per stock, so differences between stocks may be chance; no significance test was possible.\n"
    "- **Causality:** everything here is association over history; nothing shows a signal *causes* a return.\n"
    "- **Left out:** brokerage, taxes, dividends and news; only two bonus issues were found and adjusted.\n"
    "- **Data provenance:** source, licence and collection method are not stated in the files.\n"
    "- **Recommendations are ideas to test**, not investment advice.")

st.subheader("If new data arrives")
st.markdown("Later data may contain new splits/bonus issues (for example, further corporate actions after July 2018). "
            "Add each one to the `corporate_events` table and re-run `sql/06` and `sql/07`; nothing else changes.")

st.subheader("Next steps")
st.markdown("1. Test other window pairs (10/30, 50/200) and check whether results hold out of sample.\n"
            "2. Add transaction costs and dividends, and execute at next-day open.\n"
            "3. Automate a monthly data refresh with an integrity check for price cliffs.")

st.subheader("Data quality: missing values")
mv = Path(__file__).resolve().parent.parent.parent / "insights" / "missing_values.csv"
if mv.exists():
    st.dataframe(pd.read_csv(mv), hide_index=True, width="stretch")
    st.caption("Only deliverable_qty and pct_deli_qty have gaps (1 row per stock). They are not used in any "
               "calculation, so the rows were kept and the columns left as NULL.")
else:
    st.info("Run scripts/audit_data.py to generate insights/missing_values.csv.")

# ---------- Acknowledgement and thank-you ----------
st.divider()
st.subheader("Acknowledgement")
st.markdown(
    "I thank **Labmentix** for the project brief, the student guide and the dataset, and my mentors and "
    "instructors for their guidance and feedback. Thanks also to the **National Stock Exchange of India** "
    "(public corporate-action circular) and **Business Standard / PTI**, whose published reports confirmed the "
    "bonus-issue dates; to **Aiven** (cloud MySQL) and **Streamlit** (app hosting); and to the open-source tools "
    "behind this work - MySQL, Python, pandas, SQLAlchemy, Plotly and Matplotlib. Company logos shown here are trademarks of their respective owners and "
    "are used for identification only.")

st.markdown(
    """
    <div style="background:#1e3a8a;border-radius:14px;padding:26px 20px;text-align:center;margin:18px 0 8px 0;">
      <div style="color:#ffffff;font-size:2rem;font-weight:750;">Thank you</div>
      <div style="color:#dbeafe;font-size:1rem;margin-top:6px;">
        Thank you for exploring this dashboard. I welcome your feedback and questions.
      </div>
      <div style="color:#93c5fd;font-size:0.85rem;margin-top:12px;">
        Code: github.com/abhi-1009/nse-stock-signals-sql-dashboard
      </div>
      <div style="color:#93c5fd;font-size:0.8rem;margin-top:4px;">
        Learning project - not investment advice.
      </div>
    </div>
    """,
    unsafe_allow_html=True)