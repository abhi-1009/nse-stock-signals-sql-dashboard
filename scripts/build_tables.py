"""Run sql/01..07 against the configured database (e.g. Aiven) to (re)build all tables.

Usage:  python scripts/build_tables.py
Skips USE statements and the MySQL-only function block (create that one in Workbench).
"""
import glob
from pathlib import Path

from _conn import get_engine
from sql_runner import run_file

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def main():
    engine = get_engine()
    raw = engine.raw_connection()
    try:
        cur = raw.cursor()
        try:  # Aiven enforces primary keys by default; CREATE TABLE ... AS SELECT has none
            cur.execute("SET SESSION sql_require_primary_key = 0")
        except Exception as exc:  # noqa: BLE001
            print("Note: could not relax sql_require_primary_key:", exc)
        cur.close()
        for f in sorted(glob.glob(str(SQL_DIR / "0[1-7]*.sql"))):
            run_file(raw, Path(f))
    finally:
        raw.close()
    print("All tables built.")


if __name__ == "__main__":
    main()
