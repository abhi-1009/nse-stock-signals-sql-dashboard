import plotly.graph_objects as go
import streamlit as st

import db
import theme

theme.setup("Recommendations", "🧭")
theme.header("Recommendations & What-If", "Findings turned into actions for different investors, plus a calculator for your own numbers")
theme.how_to_read(
    "- The **calculator** applies this project's results (adjusted prices, long-only, 2015–2018) to an amount you choose.\n"
    "- Every **recommendation** shows its reasoning chain: finding → why it matters → action → how to measure it.\n"
    "- They are **ideas to test**, not proven conclusions: six stocks and 6–12 trades each.")

ss, summ, latest = db.load_strategy_summary(), db.load_summary(), db.load_latest_signals()
trades = db.run_query("SELECT stock, COUNT(*) AS n, SUM(is_open) AS open_n FROM strategy_trades GROUP BY stock")
if ss.empty or summ.empty or trades.empty:
    st.warning("No data returned. Run sql/06 and sql/07 first.")
    st.stop()
df = ss.merge(trades.astype({"n": float, "open_n": float}), on="stock")

# ---------- 1. What-if calculator ----------
st.subheader("What if you had invested?")
c1, c2, c3, c4 = st.columns(4)
amt = c1.number_input("Amount per stock (₹)", 1000, 10_000_000, 100_000, 10_000)
who = c2.selectbox("I am a...", ["Long-term holder", "Short-term trader"])
stock = c3.selectbox("Stock", theme.STOCKS)
cost = c4.number_input("Cost per trade (%)", 0.0, 2.0, 0.10, 0.05, help="Illustrative brokerage + charges per buy or sell.")
df["hold"] = amt * (1 + df["buy_hold_pct"].astype(float) / 100)
df["gross"] = amt * (1 + df["strategy_return_pct"].astype(float) / 100)
df["net"] = df["gross"] * (1 - cost / 100) ** (2 * df["n"] - df["open_n"])
r = df[df["stock"] == stock].iloc[0]
theme.kpi_row([("Buy-and-hold", theme.inr0(r.hold), f"{theme.pct(r.buy_hold_pct)} on {theme.inr0(amt)}", "🏦", theme.GOOD),
               ("Follow the signals", theme.inr0(r.net), f"after {cost:.2f}% per trade, {int(2 * r.n - r.open_n)} charges", "🔁", "#2563eb"),
               ("Difference", theme.inr0(r.net - r.hold), "signals minus holding", "⚖️", theme.GOOD if r.net >= r.hold else theme.BAD),
               ("Trades", int(r.n), f"{int(r.quick_flips_30d)} lasted ≤ 30 days", "🧾", "#8b5cf6")])
better = int((df["net"] > df["hold"]).sum())
if who == "Long-term holder":
    msg = (f"For {stock}, holding ended at {theme.inr0(r.hold)} against {theme.inr0(r.net)} for following every signal. "
           f"After costs, signals beat holding for {better} of 6 stocks, so a long-term holder gave up return by acting on them.")
else:
    msg = (f"For {stock}, {int(r.quick_flips_30d)} round trip(s) lasted 30 days or less and {int(r.losing_quick_flips)} of them lost money. "
           f"After costs, signals beat holding for {better} of 6 stocks. A trader would need a filter for quick reversals before relying on the rule.")
theme.takeaway(msg)
fig = go.Figure([go.Bar(x=df["stock"], y=df["hold"], name="Buy-and-hold", marker_color="#9ca3af"),
                 go.Bar(x=df["stock"], y=df["gross"], name="Signals, before costs", marker_color="#93c5fd"),
                 go.Bar(x=df["stock"], y=df["net"], name="Signals, after costs", marker_color="#2563eb")])
fig.add_hline(y=amt, line_dash="dot", line_color="#6b7280", annotation_text="Amount invested")
fig.update_layout(barmode="group")
theme.style_fig(fig, f"Value on 31 Jul 2018 of {theme.inr0(amt)} put into each stock on 1 Jan 2015", "Value (₹)", "")
st.plotly_chart(fig, width="stretch")
st.caption("Assumptions: adjusted prices, long-only, cash earns nothing, trades at the same-day close, a charge on every buy and sell, "
           "no tax or dividends. Past performance on six stocks over 3.5 years does not predict the future.")

# ---------- 2. Recommendations with reasoning chains ----------
st.subheader("Recommendations: from finding to action")
n_lag, tot_q, lost_q = int((ss["strategy_minus_buyhold"] < 0).sum()), int(ss["quick_flips_30d"].sum()), int(ss["losing_quick_flips"].sum())
n_flip = int((ss["quick_flips_30d"] > 0).sum())
gap = float((100_000 * (ss["buy_hold_pct"].astype(float) - ss["strategy_return_pct"].astype(float)) / 100).sum())
ev = summ[summ["stock"].isin(db.load_events()["stock"])].set_index("stock")
ev_txt = "; ".join(f"{s} {ev.loc[s, 'pct_change_raw']:+.1f}% raw but {ev.loc[s, 'pct_change_adj']:+.1f}% adjusted" for s in ev.index)
sells = summ.merge(latest, on="stock").query("signal == 'Sell' and pct_change_adj > 50")
sell_txt = " and ".join(f"{r.stock} ({r.pct_change_adj:+.1f}%)" for r in sells.itertuples()) or "none"

theme.rec_card("Data analyst", "Adjust prices for corporate actions before any signal is computed",
    f"{len(ev)} of 6 stocks had a one-day fall of about 50% caused by a bonus issue: {ev_txt}.",
    "Unadjusted data reversed the winners and losers and created or hid signals, so every later number was wrong.",
    "Keep exchange-confirmed events in a table, rebuild prices and signals from it, and flag any one-day move above 30% for review.",
    "No unexplained one-day move above 30% remains; the events table matches exchange notices.",
    f"Affects {len(ev)} of 6 stocks · idea to test on a longer history", "#f59e0b")
theme.rec_card("Long-term holder", "Do not use the 20/50-day golden cross as a reason to sell",
    f"Following the signals trailed buy-and-hold for {n_lag} of 6 stocks. On {theme.inr0(100_000)} per stock the shortfall totalled about {theme.inr0(gap)} before costs.",
    "The averages lag, so exits come after part of a fall and re-entries after part of a rise; the strategy was out of the market during gains.",
    "Hold quality stocks through signals; use a Sell only as a prompt to review, not as an instruction.",
    "A rule is adopted only if it beats buy-and-hold after costs on a period it was not built on.",
    f"Affects 6 of 6 stocks · only 6–12 trades each, so treat as a hypothesis", theme.GOOD)
theme.rec_card("Short-term trader", "Filter out quick reversals before acting on signals",
    f"{lost_q} of {tot_q} round trips lasting 30 days or less lost money, spread over {n_flip} of 6 stocks.",
    "Frequent flips pay costs and losses repeatedly; the strategy came closest to holding only for strongly trending stocks (Eicher, TVS).",
    "Test a rule that ignores a signal within 30 days of the previous one, and try the 10/30 and 50/200 pairs.",
    "Fewer losing quick round trips and a result that beats holding in both 2015–16 and 2017–18.",
    "Affects the stocks with quick flips · idea to test, not a proven rule", "#2563eb")
theme.rec_card("Any investor", "Read the latest signal together with the long-run trend",
    f"The latest signal is a Sell for stocks that gained more than 50% over the period: {sell_txt}.",
    "One crossing says the 20-day average dipped below the 50-day average; it says nothing about a multi-year trend.",
    "Treat the signal as a caution flag and record the reason for any decision.",
    "Decisions are logged with both the signal and the long-run change, and reviewed after 3 and 6 months.",
    "Affects the stocks currently showing a Sell · idea to test", "#8b5cf6")
