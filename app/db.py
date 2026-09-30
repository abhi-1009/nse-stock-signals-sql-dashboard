"""Database access: engine, cached queries, and the SQL-playground safety guard.

Connection settings come from .streamlit/secrets.toml ([mysql] block) or, for
local testing only, the DATABASE_URL environment variable.
"""
import os
import re
from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

ROOT = Path(__file__).resolve().parent.parent


@st.cache_resource
def get_engine():
    """One pooled engine for the whole app (SSL for Aiven)."""
    secrets = None
    try:
        secrets = st.secrets["mysql"]
    except Exception:
        secrets = None
    if secrets is not None:
        ca = Path(secrets.get("ssl_ca", ROOT / "certs" / "aiven-ca.pem"))
        if not ca.is_absolute():
            ca = ROOT / ca
        url = URL.create("mysql+pymysql", username=secrets["user"], password=secrets["password"],
                         host=secrets["host"], port=int(secrets["port"]), database=secrets["database"])
        connect_args = {"ssl": {"ca": str(ca)}} if ca.exists() else {}
        return create_engine(url, connect_args=connect_args, pool_pre_ping=True, pool_recycle=280)
    if os.environ.get("DATABASE_URL"):
        return create_engine(os.environ["DATABASE_URL"])
    st.error("No database configured. Add a [mysql] block to .streamlit/secrets.toml "
             "(see secrets.toml.example).")
    st.stop()


@st.cache_data(ttl=600, show_spinner=False)
def _cached_query(sql: str, params: tuple) -> pd.DataFrame:
    with get_engine().connect() as conn:
        df = pd.read_sql(text(sql), conn, params=dict(params))
    for c in df.columns:
        if c in ("date", "entry_date", "exit_date", "event_date", "first_day", "last_day",
                 "last_signal_date"):
            df[c] = pd.to_datetime(df[c])
    return df


def run_query(sql: str, params: dict | None = None) -> pd.DataFrame:
    """Cached read. Errors are shown to the user instead of crashing the page."""
    try:
        return _cached_query(sql, tuple(sorted((params or {}).items())))
    except Exception as exc:  # noqa: BLE001 - surface any DB error politely
        st.error(f"Database error: {exc}")
        return pd.DataFrame()


# ---------- named loaders (tables built by sql/06 and sql/07) ----------
def load_prices() -> pd.DataFrame:
    return run_query("SELECT stock, `date`, close_price, adj_close FROM prices_all ORDER BY stock, `date`")


def load_signals(stock: str, adjusted: bool) -> pd.DataFrame:
    if adjusted:
        sql = ("SELECT `date`, adj_close AS price, ma20, ma50, `signal` FROM signals_adj "
               "WHERE stock = :s ORDER BY `date`")
    else:
        sql = ("SELECT `date`, close_price AS price, ma20, ma50, `signal` FROM signals_raw "
               "WHERE stock = :s ORDER BY `date`")
    return run_query(sql, {"s": stock})


def load_summary() -> pd.DataFrame:
    return run_query("SELECT * FROM stock_summary ORDER BY stock")


def load_events() -> pd.DataFrame:
    return run_query("SELECT * FROM corporate_events ORDER BY stock")


def load_strategy_summary() -> pd.DataFrame:
    return run_query("SELECT * FROM strategy_summary ORDER BY stock")


def load_strategy_by_period() -> pd.DataFrame:
    return run_query("SELECT * FROM strategy_by_period ORDER BY stock, entry_period")


def load_trades(stock: str) -> pd.DataFrame:
    return run_query("SELECT * FROM strategy_trades WHERE stock = :s ORDER BY entry_date", {"s": stock})


def load_latest_signals() -> pd.DataFrame:
    return run_query(
        "SELECT stock, `date`, `signal` FROM ("
        " SELECT stock, `date`, `signal`, ROW_NUMBER() OVER (PARTITION BY stock ORDER BY `date` DESC) AS rn"
        " FROM signals_adj WHERE `signal` <> 'Hold') x WHERE rn = 1 ORDER BY stock")


# ---------- SQL playground guard ----------
_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|replace|rename|call|"
    r"load|outfile|infile|handler|lock|unlock|set|use|into|sleep|benchmark|shutdown|kill)\b", re.I)


def _strip_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    return re.sub(r"--[^\n]*", " ", sql)


def validate_readonly(sql: str) -> tuple[bool, str, str]:
    """Return (ok, message, cleaned_sql). Only one SELECT/WITH statement is allowed."""
    cleaned = _strip_comments(sql).strip().rstrip(";").strip()
    if not cleaned:
        return False, "Please type a query.", ""
    if ";" in cleaned:
        return False, "Only one statement at a time (remove the extra ';').", ""
    if not re.match(r"^(select|with)\b", cleaned, re.I):
        return False, "Only SELECT queries (optionally starting with WITH) are allowed.", ""
    bad = _FORBIDDEN.search(cleaned)
    if bad:
        return False, f"The keyword '{bad.group(0)}' is not allowed in this read-only playground.", ""
    return True, "ok", cleaned


def run_readonly(sql: str, limit: int = 1000) -> tuple[pd.DataFrame, bool]:
    """Run a validated query via the raw DBAPI cursor (no bind-parameter parsing).

    Returns (dataframe, truncated). Raises on database errors.
    """
    engine = get_engine()
    raw = engine.raw_connection()
    try:
        cur = raw.cursor()
        if engine.dialect.name == "mysql":
            cur.execute("SET SESSION MAX_EXECUTION_TIME=10000")  # 10 s cap on SELECTs
        cur.execute(sql)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchmany(limit + 1)
        cur.close()
    finally:
        raw.close()
    truncated = len(rows) > limit
    return pd.DataFrame(rows[:limit], columns=cols), truncated
