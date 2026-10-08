"""Shared look-and-feel: colours, page setup, chart styling, text helpers."""
import base64
from functools import lru_cache
from pathlib import Path

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
.stApp {background: linear-gradient(180deg,#e8f0ff 0%,#f6f9ff 280px,#ffffff 100%);}
.block-container {padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1250px;}
[data-testid="stHeader"] {background: transparent;}
h1,h2,h3 {color:#0f2a5c; letter-spacing:-0.4px;} h1 {font-weight:800;}
/* sidebar */
[data-testid="stSidebar"] {background: linear-gradient(180deg,#0f2a5c 0%,#1e3a8a 100%);}
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a span, [data-testid="stSidebar"] label p,
[data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] .stCaption p {color:#e0e7ff !important;}
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {background:rgba(255,255,255,.16); border-radius:10px;}
/* hero */
.hero {background: linear-gradient(120deg,#0f2a5c 0%,#1d4ed8 60%,#38bdf8 130%); border-radius:20px; padding:26px 30px; color:#fff; box-shadow:0 10px 30px rgba(30,64,175,.25);}
.hero h1 {color:#fff; margin:0; font-size:2.1rem; line-height:1.2;} .hero p {color:#dbeafe; margin:8px 0 14px 0; font-size:1.02rem;}
.chip {display:inline-block; background:rgba(255,255,255,.16); border:1px solid rgba(255,255,255,.28); color:#fff; padding:3px 12px; border-radius:999px; font-size:.78rem; margin:0 6px 4px 0;}
/* cards */
.row {display:flex; flex-wrap:wrap; gap:14px; margin:16px 0;}
.card {flex:1 1 190px; background:#fff; border-radius:16px; padding:16px 18px; box-shadow:0 2px 12px rgba(15,42,92,.08); border:1px solid #e6ecf7;}
.kpi {flex:1 1 135px; padding:14px 14px; border-top:4px solid var(--c);} .kpi .top {display:flex; justify-content:space-between; align-items:center;}
.kpi .l {color:#6b7280; font-size:.7rem; font-weight:600; text-transform:uppercase; letter-spacing:.2px; overflow-wrap:normal; word-break:normal; hyphens:none; font-kerning:none; font-feature-settings:"kern" 0;} .kpi .i {font-size:1.25rem; flex:0 0 auto; margin-left:6px;}
.kpi .v {font-size:1.6rem; font-weight:800; color:#0f2a5c; line-height:1.25; margin-top:4px;} .kpi .s {color:#6b7280; font-size:.78rem;}
.info {flex:1 1 280px;} .info h4 {margin:0 0 6px 0; color:#1e3a8a;} .info p {margin:0; color:#374151; font-size:.92rem; line-height:1.5;}
.scard {flex:1 1 30%; min-width:240px;} .scard .hd {display:flex; align-items:center; gap:12px;} .scard .nm {font-weight:700; color:#0f2a5c;}
.scard .pc {font-size:1.6rem; font-weight:800; margin:8px 0 2px 0;} .scard .ft {display:flex; justify-content:space-between; align-items:center; color:#6b7280; font-size:.78rem;} .scard .ft span {white-space:nowrap;}
.badge {display:inline-flex; align-items:center; justify-content:center; border-radius:50%; color:#fff; font-weight:800; flex:0 0 auto;}
.takeaway {background:#eff6ff; border-left:4px solid #2563eb; padding:8px 14px; border-radius:8px; color:#1e3a8a; font-size:.93rem; margin:4px 0 18px 0;}
.subtitle {color:#4b5563; font-size:1.05rem; margin-top:-8px; margin-bottom:14px;}
.pill {display:inline-block; padding:2px 10px; border-radius:999px; font-size:.8rem; font-weight:600;}
.pill-buy {background:#dcfce7; color:#166534;} .pill-sell {background:#fee2e2; color:#991b1b;}
[data-testid="stPlotlyChart"], [data-testid="stDataFrame"] {background:#fff; border-radius:14px; box-shadow:0 2px 12px rgba(15,42,92,.07); padding:6px;}
.eyebrow {letter-spacing:1.6px; font-size:.74rem; font-weight:700; color:#93c5fd; margin-bottom:6px;}
.eyebrow-l {letter-spacing:1.4px; font-size:.72rem; font-weight:700; color:#2563eb; margin-bottom:2px;}
.notice {background:#fffbeb; border:1px solid #fcd34d; border-left:5px solid #f59e0b; border-radius:14px; padding:14px 20px; margin:16px 0;}
.notice h4 {margin:0 0 6px 0; color:#92400e;} .notice ul {margin:0; padding-left:18px; color:#78350f; font-size:.9rem; line-height:1.55;}
.rec {background:#fff; border-radius:16px; border:1px solid #e6ecf7; border-top:5px solid var(--c); padding:16px 20px; margin:12px 0; box-shadow:0 2px 12px rgba(15,42,92,.08);}
.rec h4 {margin:0 0 8px 0; color:#0f2a5c;} .rec .tag {float:right; background:#eff6ff; color:#1e3a8a; border-radius:999px; padding:2px 10px; font-size:.75rem; font-weight:600;}
.rec .chain {display:flex; flex-wrap:wrap; gap:10px; margin:8px 0;} .rec .step {flex:1 1 200px; background:#f8fafc; border-radius:10px; padding:10px 12px; font-size:.86rem; color:#374151; line-height:1.45;}
.rec .step b {display:block; color:#1e3a8a; font-size:.74rem; text-transform:uppercase; letter-spacing:.5px; margin-bottom:3px;}
.rec .meta {color:#6b7280; font-size:.8rem; margin-top:6px;}
footer {visibility:hidden;}
</style>
"""

TICKER = {"Bajaj Auto": "BAJ", "Eicher Motors": "EIC", "Hero Motocorp": "HER", "Infosys": "INF", "TCS": "TCS", "TVS Motors": "TVS"}
_HERE = Path(__file__).resolve().parent
_LOGO_DIRS = [_HERE.parent / "assets" / "logos", _HERE / "assets" / "logos"]   # project root or app/ folder


@lru_cache(maxsize=None)
def _logo_src(stock: str):
    """Data-URI of your logo file (e.g. tcs.png; any letter case) from assets/logos, else None."""
    slug = stock.lower().replace(" ", "_")
    mimes = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".svg": "image/svg+xml"}
    for d in _LOGO_DIRS:
        if d.exists():
            for f in sorted(d.iterdir()):
                if f.name.lower().startswith(slug + ".") and f.suffix.lower() in mimes:
                    return f"data:{mimes[f.suffix.lower()]};base64," + base64.b64encode(f.read_bytes()).decode()
    return None


def badge(stock: str, size: int = 42) -> str:
    """Logo box from assets/logos if present (wide wordmarks fit), otherwise a coloured ticker badge."""
    src = _logo_src(stock)
    if src:
        return (f'<img src="{src}" style="height:{size}px;width:{int(size * 1.9)}px;object-fit:contain;flex:0 0 auto;'
                f'border-radius:10px;background:#fff;padding:4px;border:1px solid #e5e7eb">')
    return (f'<span class="badge" style="width:{size}px;height:{size}px;background:{STOCK_COLORS[stock]};'
            f'font-size:{size * 0.3:.0f}px">{TICKER[stock]}</span>')


def kpi_row(items):
    """items: (label, value, sub, icon, colour). Renders a responsive row of KPI cards."""
    cards = "".join(
        f'<div class="card kpi" style="--c:{c}"><div class="top"><span class="l">{l}</span><span class="i">{i}</span></div>'
        f'<div class="v">{v}</div><div class="s">{s}</div></div>' for l, v, s, i, c in items)
    st.markdown(f'<div class="row">{cards}</div>', unsafe_allow_html=True)


def hero(title: str, subtitle: str, chips, eyebrow: str = "SQL – STOCK MARKET ANALYSIS"):
    chips_html = "".join(f'<span class="chip">{c}</span>' for c in chips)
    st.markdown(f'<div class="hero"><div class="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{subtitle}</p>{chips_html}</div>', unsafe_allow_html=True)


def info_cards(items):
    """items: (emoji + title, text)."""
    html = "".join(f'<div class="card info"><h4>{t}</h4><p>{p}</p></div>' for t, p in items)
    st.markdown(f'<div class="row">{html}</div>', unsafe_allow_html=True)


def stock_cards(rows):
    """rows: dicts with stock, change, sig, sig_date, buys, sells."""
    html = ""
    for r in rows:
        col = GOOD if r["change"] >= 0 else BAD
        html += (f'<div class="card scard"><div class="hd">{badge(r["stock"])}<div><div class="nm">{r["stock"]}</div>'
                 f'<div class="s" style="color:#6b7280;font-size:.78rem">{r["buys"]} Buys · {r["sells"]} Sells</div></div></div>'
                 f'<div class="pc" style="color:{col}">{pct(r["change"])}</div>'
                 f'<div class="ft"><span>Total change</span><span>{signal_pill(r["sig"])} {r["sig_date"]}</span></div></div>')
    st.markdown(f'<div class="row">{html}</div>', unsafe_allow_html=True)


def setup(title: str, icon: str = "📈"):
    """Must be the first Streamlit call on every page."""
    st.set_page_config(page_title=f"{title} | SQL Stock Market Analysis", page_icon=icon, layout="wide")
    st.markdown(_CSS, unsafe_allow_html=True)
    with st.sidebar:
        st.markdown("### 📈 SQL – Stock Market Analysis")
        st.caption("Six NSE stocks · Jan 2015 – Jul 2018 · MySQL on Aiven")


def header(title: str, subtitle: str = "", stock: str = ""):
    logo = f'<span style="margin-right:12px;vertical-align:middle">{badge(stock, 46)}</span>' if stock else ""
    st.markdown(f'<div class="eyebrow-l">SQL – STOCK MARKET ANALYSIS</div><h1 style="margin:0">{logo}{title}</h1>', unsafe_allow_html=True)
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
        height=height, margin=dict(l=10, r=10, t=100, b=10),
        title_y=0.96, title_yanchor="top",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=12)),
        hovermode="x unified", plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="sans-serif", size=13, color="#1f2937"),
    )
    fig.update_xaxes(title=xtitle, showgrid=False, linecolor="#d1d5db")
    fig.update_yaxes(title=ytitle, gridcolor="#eef0f3", zeroline=False)
    return fig


def inr0(x) -> str:
    """Whole rupees with Indian digit grouping, e.g. ₹1,00,000."""
    s = str(int(round(abs(x)))); head, tail = s[:-3], s[-3:]
    if head:
        s = ",".join([head[max(i - 2, 0):i] for i in range(len(head), 0, -2)][::-1]) + "," + tail
    return ("-" if x < 0 else "") + "₹" + s


def inr(x) -> str:
    return f"₹{x:,.2f}"


def pct(x, d: int = 1) -> str:
    return f"{x:+.{d}f}%"


def signal_pill(sig: str) -> str:
    cls = "pill-buy" if sig == "Buy" else "pill-sell"
    arrow = "▲" if sig == "Buy" else "▼"
    return f'<span class="pill {cls}">{arrow} {sig}</span>'


def notice(title: str, items):
    """A visible (never collapsed) box for assumptions, limits and biases."""
    li = "".join(f"<li>{i}</li>" for i in items)
    st.markdown(f'<div class="notice"><h4>{title}</h4><ul>{li}</ul></div>', unsafe_allow_html=True)


def rec_card(who: str, title: str, finding: str, why: str, action: str, measure: str, meta: str, color: str):
    """One recommendation with its reasoning chain: finding -> why it matters -> action -> how measured."""
    steps = "".join(f'<div class="step"><b>{h}</b>{b}</div>' for h, b in
                    (("1 · Finding", finding), ("2 · Why it matters", why), ("3 · Action", action), ("4 · How to measure", measure)))
    st.markdown(f'<div class="rec" style="--c:{color}"><span class="tag">{who}</span><h4>{title}</h4>'
                f'<div class="chain">{steps}</div><div class="meta">{meta}</div></div>', unsafe_allow_html=True)