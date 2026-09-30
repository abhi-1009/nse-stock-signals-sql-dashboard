# Stock Market Analysis in SQL - six NSE stocks (2015-2018)

**Problem.** Retail investors follow moving-average "golden cross" signals without checking whether they are reliable or whether the price data is clean.
**Objective.** Build the signals in SQL, measure how often they fire and how they compare with buy-and-hold, and check whether data problems (bonus-issue price cliffs) distort the conclusions.
**Stakeholder / decision.** A retail investor or junior analyst deciding whether to use a 20/50-day golden-cross signal, and on which stocks.
**Success measures.** Every brief checkpoint matches (`scripts/validate_checkpoints.py`); winners/losers are reported on adjusted prices; every claim has evidence and a caveat.

## Data
Daily NSE prices for Bajaj Auto, Eicher Motors, Hero MotoCorp, Infosys, TCS and TVS Motors, 889 trading days each (2015-01-01 to 2018-07-31), supplied with the course. Source, licence and collection method are not stated in the files - confirm with the course provider. Only `close_price` is used. See `data_dictionary.md`.
Missing values: only `deliverable_qty` / `pct_deli_qty` (1 row per stock, 2 distinct dates); not used in any calculation, rows kept (`insights/missing_values.csv`).
Sampling: six hand-picked large caps (4 autos, 2 IT) over 3.5 years - not representative of the market.

## Project layout
```
sql/      00_load_data (MySQL loader) · 01_explore (tasks 1-4 + audit) · 02_moving_averages_master (5-6)
          03_signals (7-9) · 04_all_stocks (10) · 05_data_trap_and_fix (11-13)
          06_dashboard_tables (adjusted prices + signals for the app) · 07_strategy_evaluation (extra)
scripts/  load_csvs.py · build_tables.py · validate_checkpoints.py · audit_data.py
app/      Home.py + pages/ (Streamlit dashboard) · db.py · theme.py · queries.py
data/     the six CSVs      insights/  missing_values.csv (+ your PDF)      certs/  aiven-ca.pem
```

## Setup and run order
1. **Local MySQL 8 (Workbench).** Run `sql/00_load_data.sql` after editing the six file paths (needs `SET GLOBAL local_infile = 1;` and `OPT_LOCAL_INFILE=1` on the connection). Then run `01` to `07` in order. Each file starts with `USE stock_analysis;` - change it if your database has another name (for example Aiven's `defaultdb`); the Python scripts ignore `USE` and use the database in your secrets. Every table is `DROP ... IF EXISTS` first, so files are re-runnable.
2. **Check the numbers:** `python scripts/validate_checkpoints.py` should print 13/13 PASS.
3. **Aiven MySQL.** Create the service, download the CA certificate to `certs/aiven-ca.pem`, and copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` with your host, port, user, password, database.
   - Aiven may require primary keys on new tables. Either run `SET SESSION sql_require_primary_key = 0;` before `06`/`07` in Workbench, or set the service option `sql_require_primary_key` to false in the Aiven console. `build_tables.py` tries the session setting automatically.
   - Fastest route to Aiven: `python scripts/load_csvs.py` (loads the six tables with primary keys), then `python scripts/build_tables.py` (runs `sql/01`-`07`), then `python scripts/validate_checkpoints.py`. Alternatively use Workbench Data Export/Import from your local database.
4. **Dashboard locally:** `pip install -r requirements.txt` then `streamlit run app/Home.py`.
5. **Read-only user (recommended for the public app).** Create a second Aiven user with SELECT-only rights and put *its* credentials in the secrets. The SQL Playground already accepts only a single `SELECT`/`WITH` statement and caps results at 1,000 rows, but database permissions are the real protection.
6. **Deploy:** push to GitHub (secrets.toml is git-ignored), create the app on Streamlit Community Cloud pointing at `app/Home.py`, and paste the `[mysql]` block into the app's Secrets. Commit `certs/aiven-ca.pem` (a public certificate) or set `ssl_ca` accordingly.

## Dashboard pages
Overview · Price & Signals · Compare Stocks · Data Trap · Strategy vs Buy-and-Hold · SQL Playground · Insights & Limits.

## Key results (from the data supplied)
- Checkpoints reproduced: first ma20 2415.53 (2015-01-29), first ma50 2283.80 (2015-03-13), ma20 on 2018-07-31 2918.51; Bajaj first Buy 2015-05-18, first Sell 2015-08-24; 56 Buys and 57 Sells across the six stocks on raw prices; TVS Motors +86.9%.
- **Data trap:** TCS (2018-05-31) and Infosys (2015-06-15) fall about 50% in one day - consistent with 1:1 bonus issues. Verify both against the exchange/company notice and cite it. On raw prices they look like losers (TCS -23.8%, Infosys -30.9%); adjusted they gained +52.4% and +38.2%.
- **Strategy:** on adjusted prices, long-only, no costs, the golden-cross strategy trailed buy-and-hold for all six stocks, with only 6-12 trades per stock (weak statistics).

## Limitations
Six stocks and one 3.5-year window; associations, not causes; no dividends, costs, taxes or news; trades executed at the same-day close; corporate-action dates inferred from prices; only the 20/50 window tested. If new data arrives, add any new split/bonus to `corporate_events` and re-run `sql/06` and `sql/07`.

## Next steps
1. Test other windows (10/30, 50/200) and hold out a period for out-of-sample checks.
2. Add costs and dividends; execute at next-day open.
3. Automate a refresh with a check that flags any one-day move beyond about 30%.

## Reproducibility note
The SQL was validated by running equivalent statements on the supplied CSVs (all 13 checkpoints pass) and the Streamlit pages were exercised end to end; run `validate_checkpoints.py` on your own MySQL/Aiven to confirm there.
