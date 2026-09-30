"""Shared look-and-feel: colours, page setup, chart styling, text helpers."""
import streamlit as st

STOCKS = ["Bajaj Auto", "Eicher Motors", "Hero Motocorp", "Infosys", "TCS", "TVS Motors"]
# Okabe-Ito colour-blind-safe palette, one fixed colour per stock on every page
STOCK_COLORS = {
    "Bajaj Auto": "#0072B2", "Eicher Motors": "#E69F00", "Hero Motocorp": "#009E73",
    "Infosys": "#CC79A7", "TCS": "#D55E00", "TVS Motors": "#56B4E9",
}
BUY, SELL = "#16a34a", "#dc2626"
PRICE, MA20, MA50 = "#374151", "#f59e0b", "#2563eb"
GOOD, BAD, NEUTRAL = "#16a34a", "#dc2626", "#6b7280"

_CSS = """
<style>
.block-container {padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1250px;}
h1 {font-weight: 750; letter-spacing: -0.5px;}
div[data-testid="stMetric"] {background:#f9fafb; border:1px solid #e5e7eb; border-radius:12px;
  padding:14px 18px; box-shadow:0 1px 2px rgba(0,0,0,.04);}
div[data-testid="stMetricLabel"] p {font-size:0.85rem; color:#6b7280;}
.takeaway {background:#eff6ff; border-left:4px solid #2563eb; padding:8px 14px; border-radius:6px;
  color:#1e3a8a; font-size:0.93rem; margin:4px 0 18px 0;}
.subtitle {color:#6b7280; font-size:1.05rem; margin-top:-8px; margin-bottom:14px;}
.pill {display:inline-block; padding:2px 10px; border-radius:999px; font-size:0.8rem; font-weight:600;}
.pill-buy {background:#dcfce7; color:#166534;} .pill-sell {background:#fee2e2; color:#991b1b;}
footer {visibility:hidden;}
</style>
"""


def setup(title: str, icon: str = "📈"):
    """Must be the first Streamlit call on every page."""
    st.set_page_config(page_title=f"{title} | Stock Signals", page_icon=icon, layout="wide")
    st.markdown(_CSS, unsafe_allow_html=True)
    with st.sidebar:
        st.markdown("### 📈 Stock Signals")
        st.caption("Six NSE stocks · Jan 2015 – Jul 2018 · MySQL on Aiven")


def header(title: str, subtitle: str = ""):
    st.title(title)
    if subtitle:
        st.markdown(f'<div class="subtitle">{subtitle}</div>', unsafe_allow_html=True)


def takeaway(text: str):
    """One plain-English takeaway sentence under a chart."""
    st.markdown(f'<div class="takeaway">💡 {text}</div>', unsafe_allow_html=True)


def how_to_read(text: str):
    with st.expander("ℹ️ How to read this page"):
        st.markdown(text)


def style_fig(fig, title: str = "", ytitle: str = "", xtitle: str = "", height: int = 460):
    fig.update_layout(
        title=dict(text=title, x=0, font=dict(size=17)),
        height=height, margin=dict(l=10, r=10, t=60, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1),
        hovermode="x unified", plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="sans-serif", size=13, color="#1f2937"),
    )
    fig.update_xaxes(title=xtitle, showgrid=False, linecolor="#d1d5db")
    fig.update_yaxes(title=ytitle, gridcolor="#eef0f3", zeroline=False)
    return fig


def inr(x) -> str:
    return f"₹{x:,.2f}"


def pct(x, d: int = 1) -> str:
    return f"{x:+.{d}f}%"


def signal_pill(sig: str) -> str:
    cls = "pill-buy" if sig == "Buy" else "pill-sell"
    arrow = "▲" if sig == "Buy" else "▼"
    return f'<span class="pill {cls}">{arrow} {sig}</span>'
