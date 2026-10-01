import plotly.graph_objects as go
import streamlit as st

import db
import theme

theme.setup("Strategy vs Buy-and-Hold", "🏁")
theme.header("Strategy vs Buy-and-Hold", "Did following the golden-cross signals beat simply holding the stock?")
theme.how_to_read(
    "- **Strategy:** buy at the close on a Buy-signal day, sell at the close on the next Sell-signal day, "
    "otherwise stay in cash. Long-only. Adjusted prices are used.\n"
    "- **Buy-and-hold:** buy on 1 Jan 2015 and hold to 31 Jul 2018.\n"
    "- No brokerage, taxes, dividends or interest are included, and trades happen at the same-day close, "
    "which flatters the strategy slightly.\n"
    "- With only 6-12 trades per stock, treat every number as indicative, not proven.")

ss = db.load_strategy_summary()
bp = db.load_strategy_by_period()
if ss.empty:
    st.warning("No data returned. Run sql/07_strategy_evaluation.sql first.")
    st.stop()

fig = go.Figure()
fig.add_trace(go.Bar(x=ss["stock"], y=ss["strategy_return_pct"], name="Golden-cross strategy", marker_color="#2563eb"))
fig.add_trace(go.Bar(x=ss["stock"], y=ss["buy_hold_pct"], name="Buy-and-hold", marker_color="#9ca3af"))
fig.update_layout(barmode="group", hovermode="x unified")
theme.style_fig(fig, "Total return, Jan 2015 - Jul 2018", "Return (%)", "")
st.plotly_chart(fig, width="stretch")
lag = int((ss["strategy_minus_buyhold"] < 0).sum())
theme.takeaway(f"The signal strategy trailed buy-and-hold for {lag} of {len(ss)} stocks, "
               "so on this data the golden cross did not add value over simply holding.")

st.subheader("The numbers, with sample size")
tbl = ss[["stock", "n_trades", "wins", "win_rate_pct", "quick_flips_30d", "losing_quick_flips",
          "strategy_return_pct", "buy_hold_pct", "strategy_minus_buyhold"]].rename(columns={
    "stock": "Stock", "n_trades": "Trades (n)", "wins": "Winning trades", "win_rate_pct": "Win rate (%)",
    "quick_flips_30d": "Round trips ≤ 30 days", "losing_quick_flips": "...of which lost money",
    "strategy_return_pct": "Strategy return (%)", "buy_hold_pct": "Buy-and-hold (%)",
    "strategy_minus_buyhold": "Difference (pts)"})
st.dataframe(tbl, hide_index=True, width="stretch")
if (ss["n_trades"] < 30).all():
    st.caption("⚠️ Every stock has fewer than 30 trades, so win rates and returns are statistically weak.")

left, right = st.columns(2)
with left:
    st.subheader("Is it stable over time?")
    if not bp.empty:
        f2 = go.Figure()
        for per, colr in [("2015-16", "#0072B2"), ("2017-18", "#E69F00")]:
            sub = bp[bp["entry_period"] == per]
            f2.add_trace(go.Bar(x=sub["stock"], y=sub["avg_trade_return_pct"], name=per, marker_color=colr))
        f2.update_layout(barmode="group", hovermode="x unified")
        theme.style_fig(f2, "Average return per trade by entry period", "Average trade return (%)", "", height=400)
        st.plotly_chart(f2, width="stretch")
        theme.takeaway("If the two halves disagree for a stock, the signal is not consistently reliable "
                       "(an overfitting warning).")
with right:
    st.subheader("Trade log")
    stock = st.selectbox("Stock", theme.STOCKS)
    tr = db.load_trades(stock)
    if tr.empty:
        st.info("No trades for this stock.")
    else:
        colors = [theme.GOOD if v > 0 else theme.BAD for v in tr["trade_return_pct"]]
        f3 = go.Figure(go.Bar(x=tr["entry_date"].dt.strftime("%Y-%m-%d"), y=tr["trade_return_pct"], marker_color=colors))
        theme.style_fig(f3, f"{stock}: return of each trade", "Trade return (%)", "Entry date", height=340)
        f3.update_layout(showlegend=False)
        st.plotly_chart(f3, width="stretch")
        t = tr[["entry_date", "exit_date", "entry_price", "exit_price", "trade_return_pct", "hold_days", "is_open"]].copy()
        t["entry_date"] = t["entry_date"].dt.strftime("%Y-%m-%d")
        t["exit_date"] = t["exit_date"].dt.strftime("%Y-%m-%d")
        t["is_open"] = t["is_open"].map({0: "closed", 1: "open (marked to last close)"})
        st.dataframe(t.rename(columns={"entry_date": "Entry", "exit_date": "Exit", "entry_price": "Entry (₹)",
                                       "exit_price": "Exit (₹)", "trade_return_pct": "Return (%)",
                                       "hold_days": "Days held", "is_open": "Status"}),
                     hide_index=True, width="stretch")
