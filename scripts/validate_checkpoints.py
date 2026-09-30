"""Assert the brief's checkpoint numbers against the database. Exit code 1 if any fail.

Usage:  python scripts/validate_checkpoints.py
"""
import sys

from sqlalchemy import text

from _conn import get_engine

CHECKS = [
    ("889 rows in every raw table",
     "SELECT MIN(n)=889 AND MAX(n)=889 FROM (SELECT COUNT(*) n FROM bajaj_auto UNION ALL SELECT COUNT(*) FROM eicher_motors "
     "UNION ALL SELECT COUNT(*) FROM hero_motocorp UNION ALL SELECT COUNT(*) FROM infosys "
     "UNION ALL SELECT COUNT(*) FROM tcs UNION ALL SELECT COUNT(*) FROM tvs_motors) x"),
    ("TCS 2016 average close = 2419.00",
     "SELECT ROUND(AVG(close_price),2)=2419.00 FROM tcs WHERE `date` BETWEEN '2016-01-01' AND '2016-12-31'"),
    ("bajaj1 first ma20 = 2415.53 on 2015-01-29",
     "SELECT `date`='2015-01-29' AND ma20=2415.53 FROM (SELECT * FROM bajaj1 WHERE ma20 IS NOT NULL ORDER BY `date` LIMIT 1) x"),
    ("bajaj1 first ma50 = 2283.80 on 2015-03-13",
     "SELECT `date`='2015-03-13' AND ma50=2283.80 FROM (SELECT * FROM bajaj1 WHERE ma50 IS NOT NULL ORDER BY `date` LIMIT 1) x"),
    ("bajaj1 ma20 on 2018-07-31 = 2918.51",
     "SELECT ma20=2918.51 FROM bajaj1 WHERE `date`='2018-07-31'"),
    ("master_table 889 rows; 2018-07-31 bajaj 2700.70, tvs 517.45",
     "SELECT (SELECT COUNT(*) FROM master_table)=889 AND bajaj=2700.70 AND tvs=517.45 FROM master_table WHERE `date`='2018-07-31'"),
    ("bajaj2 first Buy 2015-05-18",
     "SELECT `date`='2015-05-18' FROM (SELECT * FROM bajaj2 WHERE `signal`='Buy' ORDER BY `date` LIMIT 1) x"),
    ("bajaj2 first Sell 2015-08-24",
     "SELECT `date`='2015-08-24' FROM (SELECT * FROM bajaj2 WHERE `signal`='Sell' ORDER BY `date` LIMIT 1) x"),
    ("bajaj2 signal counts sum to 889 and Buy/Sell differ by <= 1",
     "SELECT COUNT(*)=889 AND ABS(SUM(`signal`='Buy')-SUM(`signal`='Sell'))<=1 FROM bajaj2"),
    ("Across six stocks: 56 Buys and 57 Sells (raw prices)",
     "SELECT SUM(`signal`='Buy')=56 AND SUM(`signal`='Sell')=57 FROM signals_raw"),
    ("prices_all has 5,334 rows",
     "SELECT COUNT(*)=5334 FROM prices_all"),
    ("TVS Motors raw % change = 86.9",
     "SELECT pct_change_raw=86.9 FROM stock_summary WHERE stock='TVS Motors'"),
    ("Exactly two raw stocks have a negative change",
     "SELECT SUM(pct_change_raw<0)=2 FROM stock_summary"),
]


def main() -> int:
    engine = get_engine()
    failed = 0
    with engine.connect() as conn:
        for label, sql in CHECKS:
            try:
                ok = bool(conn.execute(text(sql)).scalar())
            except Exception as exc:  # noqa: BLE001
                ok = False
                label += f"  (error: {exc})"
            print(("PASS  " if ok else "FAIL  ") + label)
            failed += not ok
    print(f"\n{len(CHECKS) - failed}/{len(CHECKS)} checkpoints passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
