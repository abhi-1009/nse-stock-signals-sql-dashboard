"""Data audit on the raw CSVs: row counts, dates, NULLs, alignment across stocks.

Usage:  python scripts/audit_data.py            (CSVs expected in ./data)
Writes: insights/missing_values.csv  (column, count, %, how handled, why)
Raises AssertionError if a basic sanity check fails.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FILES = {"Bajaj Auto": "Bajaj_Auto.csv", "Eicher Motors": "Eicher_Motors.csv",
         "Hero Motocorp": "Hero_Motocorp.csv", "Infosys": "Infosys.csv",
         "TCS": "TCS.csv", "TVS Motors": "TVS_Motors.csv"}


def load(path: Path) -> pd.DataFrame:
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        raise SystemExit(f"Missing file: {path}")
    df["Date"] = pd.to_datetime(df["Date"], format="%d-%B-%Y")
    return df


def main():
    frames = {s: load(DATA / f) for s, f in FILES.items()}
    rows = []
    date_sets = []
    for s, df in frames.items():
        assert len(df) == 889, f"{s}: expected 889 rows, got {len(df)}"
        assert df["Date"].is_unique, f"{s}: duplicate dates"
        assert df["Close Price"].notna().all(), f"{s}: NULL close price"
        assert (df["Close Price"] > 0).all(), f"{s}: non-positive close price"
        date_sets.append(set(df["Date"]))
        for col, n in df.isna().sum().items():
            if n:
                rows.append({"stock": s, "column": col, "missing_rows": int(n),
                             "missing_pct": round(100 * n / len(df), 2),
                             "handling": "Kept as NULL (row retained)",
                             "why": "Column not used in any calculation; likely exchange reporting gap"})
    assert all(d == date_sets[0] for d in date_sets), "Stocks do not share identical trading dates"
    out = pd.DataFrame(rows)
    (ROOT / "insights").mkdir(exist_ok=True)
    out.to_csv(ROOT / "insights" / "missing_values.csv", index=False)
    print("All checks passed: 6 files x 889 rows, identical dates, no NULL/zero close prices.")
    print(out.to_string(index=False))
    dates = sorted({d for df in frames.values() for d in df.loc[df['Deliverable Quantity'].isna(), 'Date']})
    print("Dates with missing Deliverable Quantity:", [d.strftime('%Y-%m-%d') for d in dates])


if __name__ == "__main__":
    main()
