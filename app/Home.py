import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import db
import theme

theme.setup("Overview", "📈")
theme.header("Do moving-average signals deserve our trust?",
             "Golden-cross Buy/Sell signals on six NSE stocks, with a data-quality twist")

prices = db.load_prices()
summary = db.load_summary()
events = db.load_events()
latest = db.load_latest_signals()
if prices.empty or summary.empty:
    st.warning("The dashboard tables are empty. Run sql/06 and sql/07 on the database first.")
    st.stop()

# ---- context: problem, objective, stakeholder ----
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("#### 🎯 The problem")
    st.write("Retail investors follow a *golden cross* (20-day average crossing the 50-day average) "
             "without checking whether it is reliable or whether the price data is clean.")
with c2:
    st.markdown("#### 🧭 The objective")
    st.write("Build the signals in SQL, measure how often they fire and how they compare with "
             "simply holding, and check whether data problems distort the answer.")
with c3:
    st.markdown("#### 👤 Who decides")
    st.write("A retail investor or junior analyst deciding whether to use this signal, "
             "and on which stocks. Success = signals that survive a data check and a baseline.")

st.divider()

# ---- KPIs ----
n_days = prices.groupby("stock").size().max()
buys, sells = int(summary["buys_adj"].sum()), int(summary["sells_adj"].sum())
best = summary.sort_values("pct_change_adj", ascending=False).iloc[0]
worst = summary.sort_values("pct_change_adj").iloc[0]
k1, k2, k3, k4 = st.columns(4)
k1.metric("Stocks", summary.shape[0], help="Bajaj, Eicher, Hero, Infosys, TCS, TVS")
k2.metric("Trading days", f"{n_days:,}", help="2015-01-01 to 2018-07-31")
k3.metric("Buy / Sell (adj.)", f"{buys} / {sells}",
          help="Signals on prices adjusted for bonus issues. On raw prices the brief's total is 56 / 57.")
k4.metric("Events fixed", len(events), help="Bonus issues that halved the quoted price")
k5, k6 = st.columns(2)
k5.metric(f"Best: {best['stock']}", theme.pct(best["pct_change_adj"]),
          help="Best performer, first to last day, adjusted prices")
k6.metric(f"Weakest: {worst['stock']}", theme.pct(worst["pct_change_adj"]),
          help="Weakest performer, first to last day, adjusted prices")

# ---- rebased chart ----
piv = prices.pivot(index="date", columns="stock", values="adj_close")
rebased = piv / piv.iloc[0] * 100
fig = go.Figure()
for s in theme.STOCKS:
    if s in rebased:
        fig.add_trace(go.Scatter(x=rebased.index, y=rebased[s], name=s, mode="lines",
                                 line=dict(color=theme.STOCK_COLORS[s], width=2)))
fig.add_hline(y=100, line_dash="dot", line_color="#9ca3af")
theme.style_fig(fig, "How ₹100 invested on 1 Jan 2015 would have grown (prices adjusted for bonus issues)",
                "Value of ₹100 invested", "")
st.plotly_chart(fig, width="stretch")
theme.takeaway(f"{best['stock']} grew the most and {worst['stock']} the least once TCS and Infosys are "
               "adjusted for their bonus issues; without adjustment both would wrongly look like big losers.")

# ---- latest signals ----
st.subheader("Most recent signal per stock")
if not latest.empty:
    cols = st.columns(len(latest))
    for col, (_, r) in zip(cols, latest.iterrows()):
        with col:
            st.markdown(f"**{r['stock']}**")
            st.markdown(theme.signal_pill(r["signal"]), unsafe_allow_html=True)
            st.caption(pd.Timestamp(r["date"]).strftime("%d %b %Y"))
    theme.takeaway("The latest signal is a snapshot of the crossing, not a forecast; check the trend "
                   "on the Price & Signals page before reading anything into it.")

st.markdown("#### Where to go next")
st.markdown("- **Price & Signals** – one stock, with Buy/Sell markers\n"
            "- **Compare Stocks** – all six side by side\n"
            "- **Data Trap** – the two price cliffs and how they were fixed\n"
            "- **Strategy vs Buy-and-Hold** – did following the signals pay off?\n"
            "- **SQL Playground** – run the project's queries yourself\n"
            "- **Insights & Limits** – claims, evidence, caveats")
st.caption("Data: NSE daily prices supplied with the course (source, licence and collection method "
           "not stated in the files). Only closing prices are used. Not investment advice.")