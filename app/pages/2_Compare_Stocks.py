import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import db
import theme

theme.setup("Compare Stocks", "⚖️")
theme.header("Compare Stocks", "All six side by side: growth, price change and signal counts")
theme.how_to_read(
    "- The first chart starts every stock at 100, so lines are directly comparable regardless of price level.\n"
    "- The bar chart shows the first-to-last-day change with and without the bonus-issue adjustment.\n"
    "- Signal counts come from the golden-cross rule (20-day vs 50-day average).")

with st.sidebar:
    basis = st.radio("Price basis", ["Adjusted (recommended)", "Raw"], index=0)
    chosen = st.multiselect("Stocks", theme.STOCKS, default=theme.STOCKS)
adjusted = basis.startswith("Adjusted")

prices = db.load_prices()
summary = db.load_summary()
if prices.empty or summary.empty:
    st.warning("No data returned.")
    st.stop()
if not chosen:
    st.info("Pick at least one stock in the sidebar.")
    st.stop()

col = "adj_close" if adjusted else "close_price"
piv = prices.pivot(index="date", columns="stock", values=col)
reb = piv / piv.iloc[0] * 100
fig = go.Figure()
for s in chosen:
    fig.add_trace(go.Scatter(x=reb.index, y=reb[s], name=s, line=dict(color=theme.STOCK_COLORS[s], width=2)))
fig.add_hline(y=100, line_dash="dot", line_color="#9ca3af")
theme.style_fig(fig, f"Growth of ₹100 invested on 1 Jan 2015 ({'adjusted' if adjusted else 'raw'} prices)",
                "Value of ₹100 invested", "")
st.plotly_chart(fig, width="stretch")
end_vals = reb.iloc[-1][chosen].sort_values(ascending=False)
theme.takeaway(f"On {'adjusted' if adjusted else 'raw'} prices, {end_vals.index[0]} ends highest "
               f"(₹{end_vals.iloc[0]:.0f}) and {end_vals.index[-1]} lowest (₹{end_vals.iloc[-1]:.0f}).")

left, right = st.columns(2)
with left:
    sm = summary[summary["stock"].isin(chosen)]
    bar = go.Figure()
    bar.add_trace(go.Bar(x=sm["stock"], y=sm["pct_change_raw"], name="Raw prices", marker_color="#9ca3af"))
    bar.add_trace(go.Bar(x=sm["stock"], y=sm["pct_change_adj"], name="Adjusted prices", marker_color="#2563eb"))
    bar.update_layout(barmode="group", hovermode="x unified")
    theme.style_fig(bar, "Price change, first to last day", "Change (%)", "", height=420)
    st.plotly_chart(bar, width="stretch")
    theme.takeaway("The gap between grey and blue bars is exactly the bonus-issue error: it only affects TCS and Infosys.")
with right:
    b_col, s_col = ("buys_adj", "sells_adj") if adjusted else ("buys_raw", "sells_raw")
    cnt = go.Figure()
    cnt.add_trace(go.Bar(x=sm["stock"], y=sm[b_col], name="Buy", marker_color=theme.BUY))
    cnt.add_trace(go.Bar(x=sm["stock"], y=sm[s_col], name="Sell", marker_color=theme.SELL))
    cnt.update_layout(barmode="group", hovermode="x unified")
    theme.style_fig(cnt, "Golden-cross signals per stock", "Number of signals", "", height=420)
    st.plotly_chart(cnt, width="stretch")
    theme.takeaway(f"{int(sm[b_col].sum())} Buys and {int(sm[s_col].sum())} Sells across the chosen stocks in "
                   "3.5 years: roughly one signal every few months per stock.")

st.subheader("Summary table")
tbl = sm[["stock", "first_close", "last_close", "pct_change_raw", "pct_change_adj",
          "buys_raw", "sells_raw", "buys_adj", "sells_adj"]].rename(columns={
    "stock": "Stock", "first_close": "First close (₹)", "last_close": "Last close (₹)",
    "pct_change_raw": "Change raw (%)", "pct_change_adj": "Change adjusted (%)",
    "buys_raw": "Buys (raw)", "sells_raw": "Sells (raw)", "buys_adj": "Buys (adj.)", "sells_adj": "Sells (adj.)"})
st.dataframe(tbl, hide_index=True, width="stretch")
