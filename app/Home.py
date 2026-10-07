import plotly.graph_objects as go
import streamlit as st

import db
import theme

theme.setup("Overview", "📈")
prices, summary = db.load_prices(), db.load_summary()
events, latest = db.load_events(), db.load_latest_signals()
if prices.empty or summary.empty:
    st.warning("The dashboard tables are empty. Run sql/06 and sql/07 on the database first.")
    st.stop()

theme.hero("Do moving-average signals deserve our trust?",
           "Golden-cross Buy/Sell signals on six NSE stocks, with a data-quality twist",
           ["6 NSE stocks", "889 trading days", "Jan 2015 – Jul 2018", "MySQL · Aiven · Streamlit"])

# ---- KPI cards ----
buys, sells = int(summary["buys_adj"].sum()), int(summary["sells_adj"].sum())
best, worst = summary.sort_values("pct_change_adj").iloc[-1], summary.sort_values("pct_change_adj").iloc[0]
theme.kpi_row([
    ("Stocks", summary.shape[0], "4 autos · 2 IT", "🏢", "#2563eb"),
    ("Days of data", f"{prices.groupby('stock').size().max():,}", "per stock", "📅", "#0ea5e9"),
    ("Buy / Sell (adj.)", f"{buys} / {sells}", "56 / 57 on raw prices", "🔁", "#8b5cf6"),
    ("Events fixed", len(events), "bonus issues", "🛠️", "#f59e0b"),
    ("Best performer", theme.pct(best["pct_change_adj"]), f"{best['stock']} · adjusted", "🚀", theme.GOOD),
    ("Weakest performer", theme.pct(worst["pct_change_adj"]), f"{worst['stock']} · adjusted", "🐢", theme.BAD)])

# ---- problem / objective / decision ----
theme.info_cards([
    ("🎯 The problem", "Retail investors follow a <i>golden cross</i> (20-day average crossing the 50-day average) "
                       "without checking whether it is reliable or whether the price data is clean."),
    ("🧭 The objective", "Build the signals in SQL, measure how often they fire and how they compare with simply "
                         "holding, and check whether data problems distort the answer."),
    ("👤 Who decides", "A retail investor or junior analyst deciding whether to use this signal, and on which "
                       "stocks. Success = signals that survive a data check and a baseline.")])

# ---- stocks at a glance ----
st.subheader("Stocks at a glance")
sig = latest.set_index("stock") if not latest.empty else None
theme.stock_cards([dict(stock=r.stock, change=r.pct_change_adj, buys=int(r.buys_adj), sells=int(r.sells_adj),
                        sig=sig.loc[r.stock, "signal"], sig_date=sig.loc[r.stock, "date"].strftime("%d %b %Y"))
                   for r in summary.itertuples() if sig is not None and r.stock in sig.index])
theme.takeaway("The latest signal is a snapshot of the crossing, not a forecast; read it with the long-run change "
               "and the Price & Signals page before drawing any conclusion.")

# ---- growth chart ----
piv = prices.pivot(index="date", columns="stock", values="adj_close")
rebased = piv / piv.iloc[0] * 100
fig = go.Figure([go.Scatter(x=rebased.index, y=rebased[s], name=s, mode="lines",
                            line=dict(color=theme.STOCK_COLORS[s], width=2)) for s in theme.STOCKS if s in rebased])
fig.add_hline(y=100, line_dash="dot", line_color="#9ca3af")
theme.style_fig(fig, "How ₹100 invested on 1 Jan 2015 would have grown (prices adjusted for bonus issues)",
                "Value of ₹100 invested", "")
st.plotly_chart(fig, width="stretch")
theme.takeaway(f"{best['stock']} grew the most and {worst['stock']} the least once TCS and Infosys are adjusted for "
               "their bonus issues; without adjustment both would wrongly look like big losers.")
st.caption("Data: NSE daily prices supplied with the course (source, licence and collection method not stated in "
           "the files). Only closing prices are used. Logos are trademarks of their respective owners, shown for "
           "identification only. Not investment advice.")