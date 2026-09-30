import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import db
import theme

theme.setup("Data Trap", "🪤")
theme.header("The Data Trap", "Two stocks 'lost' half their value overnight - except nobody lost anything")
theme.how_to_read(
    "- A **bonus issue (1:1)** gives every shareholder one extra share per share held. The share count doubles "
    "and the quoted price halves, but total value is unchanged.\n"
    "- Left chart: the price as quoted. Right chart: prices before the event divided by 2, so the line is continuous.\n"
    "- The event dates were found from the biggest one-day drop; **confirm each with the exchange/company notice**.")

prices = db.load_prices()
events = db.load_events()
if prices.empty or events.empty:
    st.warning("No data returned.")
    st.stop()

# worst day per stock (raw prices)
p = prices.sort_values(["stock", "date"]).copy()
p["pct_move"] = p.groupby("stock")["close_price"].pct_change() * 100
worst = p.dropna(subset=["pct_move"]).loc[lambda d: d.groupby("stock")["pct_move"].idxmin()]
worst = worst.sort_values("pct_move")[["stock", "date", "close_price", "pct_move"]]
st.subheader("Step 1 - Each stock's single worst day (raw prices)")
w = worst.rename(columns={"stock": "Stock", "date": "Date", "close_price": "Close (₹)", "pct_move": "One-day move (%)"})
w["Date"] = w["Date"].dt.strftime("%Y-%m-%d")
w["One-day move (%)"] = w["One-day move (%)"].round(1)
st.dataframe(w, hide_index=True, width="stretch")
theme.takeaway("Four stocks have worst days between about -6% and -10%; TCS and Infosys show about -50%, "
               "which is far too large for a normal day and points to a corporate action.")

with st.sidebar:
    stock = st.selectbox("Stock to inspect", list(events["stock"]))
ev = events[events["stock"] == stock].iloc[0]
ev_date = pd.Timestamp(ev["event_date"])
d = prices[prices["stock"] == stock]

st.subheader(f"Step 2 - {stock}: before and after adjustment")
c1, c2 = st.columns(2)
for col, ycol, title, color in [(c1, "close_price", "Raw close (as quoted)", theme.SELL),
                                (c2, "adj_close", "Adjusted close (continuous)", theme.GOOD)]:
    fig = go.Figure(go.Scatter(x=d["date"], y=d[ycol], line=dict(color=color, width=2), name=title))
    fig.add_shape(type="line", x0=ev_date.isoformat(), x1=ev_date.isoformat(), yref="paper", y0=0, y1=1,
                  line=dict(color="#6b7280", dash="dash"))
    fig.add_annotation(x=ev_date.isoformat(), yref="paper", y=1.0, text="1:1 bonus", showarrow=False,
                       yanchor="bottom", font=dict(color="#6b7280"))
    theme.style_fig(fig, title, "Price (₹)", "", height=380)
    fig.update_layout(showlegend=False)
    with col:
        st.plotly_chart(fig, width="stretch")
theme.takeaway(f"On {ev_date:%d %b %Y} the quoted {stock} price drops by half in a single day; after dividing "
               "earlier prices by 2, the cliff disappears.")

st.subheader("Step 3 - What the cliff did to the signals")
raw = db.load_signals(stock, adjusted=False)
adj = db.load_signals(stock, adjusted=True)
r = raw[raw["signal"] != "Hold"][["date", "signal"]].rename(columns={"signal": "Raw signal"})
a = adj[adj["signal"] != "Hold"][["date", "signal"]].rename(columns={"signal": "Adjusted signal"})
m = r.merge(a, on="date", how="outer").sort_values("date")


def _status(row):
    if pd.isna(row["Adjusted signal"]):
        return "Only on raw prices (created by the cliff)"
    if pd.isna(row["Raw signal"]):
        return "Only on adjusted prices (hidden by the cliff)"
    return "Same on both" if row["Raw signal"] == row["Adjusted signal"] else "Different"


if m.empty:
    st.info("No signals to compare.")
else:
    m["Status"] = m.apply(_status, axis=1)
    fake = int((m["Status"] != "Same on both").sum())
    changed = m[m["Status"] != "Same on both"].copy()
    changed["date"] = changed["date"].dt.strftime("%Y-%m-%d")
    k1, k2, k3 = st.columns(3)
    k1.metric("Signals on raw prices", len(r))
    k2.metric("Signals on adjusted prices", len(a))
    k3.metric("Signals that differ", fake)
    if fake:
        st.dataframe(changed.rename(columns={"date": "Date"}).fillna("-"), hide_index=True, width="stretch")
    theme.takeaway(f"{fake} of {stock}'s signals change depending on whether the bonus issue is adjusted: the "
                   "price cliff distorts both moving averages, so it can create false crossings or hide real ones.")

st.subheader("Corporate events used for the adjustment")
e = events.rename(columns={"stock": "Stock", "event_date": "Event date", "event_type": "Type",
                           "factor": "Divide earlier prices by", "note": "Note"})
e["Event date"] = e["Event date"].dt.strftime("%Y-%m-%d")
st.dataframe(e, hide_index=True, width="stretch")
