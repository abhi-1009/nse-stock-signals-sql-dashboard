"""Load the six CSVs into the configured MySQL database (local or Aiven).

Alternative to sql/00_load_data.sql when LOAD DATA LOCAL INFILE is blocked (common on hosted MySQL).
Tables are created WITH a primary key first (Aiven requires one), then filled.

Usage:  python scripts/load_csvs.py
Reads:  ./data/*.csv    Uses: .streamlit/secrets.toml  (or DATABASE_URL)
"""
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from _conn import get_engine

DATA = Path(__file__).resolve().parent.parent / "data"
FILES = {"bajaj_auto": "Bajaj_Auto.csv", "eicher_motors": "Eicher_Motors.csv",
         "hero_motocorp": "Hero_Motocorp.csv", "infosys": "Infosys.csv",
         "tcs": "TCS.csv", "tvs_motors": "TVS_Motors.csv"}
COLS = ["date", "open_price", "high_price", "low_price", "close_price", "wap", "no_of_shares",
        "no_of_trades", "total_turnover", "deliverable_qty", "pct_deli_qty", "spread_high_low",
        "spread_close_open"]
DDL = """CREATE TABLE `{t}` (
  `date` DATE PRIMARY KEY,
  open_price DECIMAL(12,2), high_price DECIMAL(12,2), low_price DECIMAL(12,2),
  close_price DECIMAL(12,2), wap DECIMAL(16,4),
  no_of_shares BIGINT, no_of_trades BIGINT, total_turnover DECIMAL(20,2),
  deliverable_qty BIGINT, pct_deli_qty DECIMAL(6,2),
  spread_high_low DECIMAL(12,2), spread_close_open DECIMAL(12,2))"""


def main():
    engine = get_engine()
    for table, fname in FILES.items():
        try:
            df = pd.read_csv(DATA / fname)
        except FileNotFoundError:
            raise SystemExit(f"Missing file: {DATA / fname}")
        df.columns = COLS
        df["date"] = pd.to_datetime(df["date"], format="%d-%B-%Y").dt.date
        for c in ("deliverable_qty", "no_of_shares", "no_of_trades"):
            df[c] = df[c].astype("Int64")          # integer NULLs stay NULL
        df = df.sort_values("date")
        with engine.begin() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS `{table}`"))
            conn.execute(text(DDL.format(t=table)))
        df.to_sql(table, engine, if_exists="append", index=False, chunksize=500)
        with engine.connect() as conn:
            n = conn.execute(text(f"SELECT COUNT(*) FROM `{table}`")).scalar()
        assert n == 889, f"{table}: expected 889 rows, got {n}"
        print(f"loaded {table}: {n} rows")


if __name__ == "__main__":
    main()
