import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import db
import theme

theme.setup("Price & Signals", "📊")
with st.sidebar:
    stock = st.selectbox("Stock", theme.STOCKS, index=0)
    basis = st.radio("Price basis", ["Adjusted (recommended)", "Raw"], index=0)
    show_ma = st.checkbox("Show moving averages", value=True)

theme.header(stock, "Close price, 20- and 50-day averages, and the golden-cross Buy/Sell days", stock=stock)
theme.how_to_read(
    "- **Grey line** = daily closing price. **Amber** = 20-day average, **blue** = 50-day average.\n"
    "- **▲ Buy** is the single day the 20-day average crosses *above* the 50-day; **▼ Sell** the day it crosses *below*.\n"
    "- Averages only exist after 20 / 50 trading days, so early 2015 has none.\n"
    "- *Adjusted* prices remove the fake ~50% drop caused by bonus issues at TCS and Infosys.")
df = db.load_signals(stock, adjusted=basis.startswith("Adjusted"))
if df.empty:
    st.warning("No data returned.")
    st.stop()
lo, hi = df["date"].min().date(), df["date"].max().date()
with st.sidebar:
    rng = st.date_input("Date range", (lo, hi), min_value=lo, max_value=hi)
if isinstance(rng, (tuple, list)) and len(rng) == 2:
    df = df[(df["date"] >= pd.Timestamp(rng[0])) & (df["date"] <= pd.Timestamp(rng[1]))]
if df.empty:
    st.info("No trading days in that range.")
    st.stop()

sig = df[df["signal"] != "Hold"]
buys, sells = int((sig["signal"] == "Buy").sum()), int((sig["signal"] == "Sell").sum())
chg = (df["price"].iloc[-1] / df["price"].iloc[0] - 1) * 100
last = sig.iloc[-1] if len(sig) else None
theme.kpi_row([
    ("Change in range", theme.pct(chg), "first to last day shown", "📈", theme.GOOD if chg >= 0 else theme.BAD),
    ("Buy signals", buys, "20-day crosses above 50-day", "🟢", theme.BUY),
    ("Sell signals", sells, "20-day crosses below 50-day", "🔴", theme.SELL),
    ("Latest signal", last["signal"] if last is not None else "None",
     pd.Timestamp(last["date"]).strftime("%d %b %Y") if last is not None else "", "🔔", "#8b5cf6")])

fig = go.Figure()
fig.add_trace(go.Scatter(x=df["date"], y=df["price"], name="Close price",
                         line=dict(color=theme.PRICE, width=1.6)))
if show_ma:
    fig.add_trace(go.Scatter(x=df["date"], y=df["ma20"], name="20-day average",
                             line=dict(color=theme.MA20, width=1.6)))
    fig.add_trace(go.Scatter(x=df["date"], y=df["ma50"], name="50-day average",
                             line=dict(color=theme.MA50, width=1.6)))
b, s = sig[sig["signal"] == "Buy"], sig[sig["signal"] == "Sell"]
fig.add_trace(go.Scatter(x=b["date"], y=b["price"], mode="markers", name="Buy",
                         marker=dict(symbol="triangle-up", size=13, color=theme.BUY,
                                     line=dict(width=1, color="white"))))
fig.add_trace(go.Scatter(x=s["date"], y=s["price"], mode="markers", name="Sell",
                         marker=dict(symbol="triangle-down", size=13, color=theme.SELL,
                                     line=dict(width=1, color="white"))))
fig.update_xaxes(rangeslider_visible=True)
theme.style_fig(fig, f"{stock}: closing price and golden-cross signals ({basis.split(' ')[0].lower()} prices)",
                "Price (₹)", "", height=520)
st.plotly_chart(fig, width="stretch")

# signal history + quick reversals
hist = sig[["date", "signal", "price"]].copy()
hist["days_since_previous"] = hist["date"].diff().dt.days
quick = int((hist["days_since_previous"] <= 30).sum())
theme.takeaway(f"{stock} produced {buys} Buy and {sells} Sell signals in this range; "
               f"{quick} signal(s) came within 30 days of the previous one - those quick reversals "
               "are where following the signal tends to cost money.")
with st.expander("Signal history (date, price, days since previous signal)"):
    show = hist.rename(columns={"date": "Date", "signal": "Signal", "price": "Price (₹)",
                                "days_since_previous": "Days since previous"})
    show["Date"] = show["Date"].dt.strftime("%Y-%m-%d")
    st.dataframe(show, hide_index=True, width="stretch")
if stock in ("TCS", "Infosys") and basis == "Raw":
    st.warning("Raw prices include a fake ~50% drop from a bonus issue. Switch to *Adjusted* or see the "
               "Data Trap page.")