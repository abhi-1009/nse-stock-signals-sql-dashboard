"""Ready-made queries for the SQL Playground (one per brief task). MySQL 8 syntax."""

_PRICES = """prices AS (
  SELECT 'Bajaj Auto' AS stock, `date`, close_price FROM bajaj_auto
  UNION ALL SELECT 'Eicher Motors', `date`, close_price FROM eicher_motors
  UNION ALL SELECT 'Hero Motocorp', `date`, close_price FROM hero_motocorp
  UNION ALL SELECT 'Infosys',       `date`, close_price FROM infosys
  UNION ALL SELECT 'TCS',           `date`, close_price FROM tcs
  UNION ALL SELECT 'TVS Motors',    `date`, close_price FROM tvs_motors
)"""

PLAYGROUND = {
    "Task 1 - How much history do we have?": (
        "Trading days, first and last date for Bajaj Auto.",
        """SELECT COUNT(*) AS trading_days,
       MIN(`date`) AS first_day,
       MAX(`date`) AS last_day
FROM bajaj_auto"""),
    "Task 2 - Eicher's five best closes": (
        "The five highest closing prices for Eicher Motors (all in the same month).",
        """SELECT `date`, close_price
FROM eicher_motors
ORDER BY close_price DESC
LIMIT 5"""),
    "Task 3 - TCS average close by year": (
        "Yearly average close for TCS. 2018 holds only seven months (see trading_days).",
        """SELECT YEAR(`date`) AS year,
       ROUND(AVG(close_price), 2) AS avg_close,
       COUNT(*) AS trading_days
FROM tcs
GROUP BY YEAR(`date`)
ORDER BY year"""),
    "Task 4 - Find the holes (NULL deliverable_qty)": (
        "Every row across the six stocks where deliverable_qty is missing.",
        """SELECT 'bajaj_auto' AS stock, `date` FROM bajaj_auto WHERE deliverable_qty IS NULL
UNION ALL SELECT 'eicher_motors', `date` FROM eicher_motors WHERE deliverable_qty IS NULL
UNION ALL SELECT 'hero_motocorp', `date` FROM hero_motocorp WHERE deliverable_qty IS NULL
UNION ALL SELECT 'infosys', `date` FROM infosys WHERE deliverable_qty IS NULL
UNION ALL SELECT 'tcs', `date` FROM tcs WHERE deliverable_qty IS NULL
UNION ALL SELECT 'tvs_motors', `date` FROM tvs_motors WHERE deliverable_qty IS NULL"""),
    "Task 5 - Bajaj moving averages (table bajaj1)": (
        "20- and 50-day moving averages, NULL until a full window exists. First ma20 is 2015-01-29.",
        """SELECT `date`, close_price, ma20, ma50
FROM bajaj1
WHERE ma20 IS NOT NULL
ORDER BY `date`
LIMIT 60"""),
    "Task 6 - Master table (all six closes)": (
        "One row per date with each stock's closing price.",
        """SELECT * FROM master_table ORDER BY `date` DESC LIMIT 30"""),
    "Task 7 - Bajaj Buy/Sell days (table bajaj2)": (
        "Only the crossover days (Buy/Sell); every other day is Hold.",
        """SELECT `date`, close_price, `signal`
FROM bajaj2
WHERE `signal` <> 'Hold'
ORDER BY `date`"""),
    "Task 8 - How often did it trigger?": (
        "Signal counts for Bajaj. Must sum to 889; Buy and Sell differ by at most 1.",
        """SELECT `signal`, COUNT(*) AS days
FROM bajaj2
GROUP BY `signal`
ORDER BY `signal`"""),
    "Task 9 - Signal on 2018-06-21": (
        "The Bajaj signal for one date (no rows = market closed).",
        """SELECT `signal` FROM bajaj2 WHERE `date` = '2018-06-21'"""),
    "Task 10 - All six stocks in one query": (
        "Buys, sells and latest signal per stock, raw prices, unrounded averages. Totals: 56 Buys, 57 Sells.",
        f"""WITH {_PRICES},
ma AS (
  SELECT stock, `date`, close_price,
    CASE WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY `date`) >= 20
         THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY `date`
              ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) END AS ma20,
    CASE WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY `date`) >= 50
         THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY `date`
              ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) END AS ma50
  FROM prices
),
lagged AS (
  SELECT *, LAG(ma20) OVER (PARTITION BY stock ORDER BY `date`) AS prev_ma20,
            LAG(ma50) OVER (PARTITION BY stock ORDER BY `date`) AS prev_ma50
  FROM ma
),
sig AS (
  SELECT stock, `date`, close_price,
    CASE WHEN ma50 IS NULL OR prev_ma50 IS NULL THEN 'Hold'
         WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50 THEN 'Buy'
         WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50 THEN 'Sell'
         ELSE 'Hold' END AS `signal`
  FROM lagged
),
latest AS (
  SELECT stock, `date`, `signal`,
         ROW_NUMBER() OVER (PARTITION BY stock ORDER BY `date` DESC) AS rn
  FROM sig WHERE `signal` <> 'Hold'
)
SELECT s.stock, SUM(s.`signal` = 'Buy') AS buys, SUM(s.`signal` = 'Sell') AS sells,
       MAX(l.`date`) AS last_signal_date, MAX(l.`signal`) AS last_signal
FROM sig s JOIN latest l ON l.stock = s.stock AND l.rn = 1
GROUP BY s.stock ORDER BY s.stock"""),
    "Task 11 - Who went up? (raw prices)": (
        "First vs last close per stock. TVS tops at 86.9%; TCS and Infosys look negative - a trap.",
        f"""WITH {_PRICES},
ends AS (SELECT stock, MIN(`date`) AS d0, MAX(`date`) AS d1 FROM prices GROUP BY stock)
SELECT e.stock, f.close_price AS first_close, l.close_price AS last_close,
       ROUND(100.0 * (l.close_price - f.close_price) / f.close_price, 1) AS pct_change
FROM ends e
JOIN prices f ON f.stock = e.stock AND f.`date` = e.d0
JOIN prices l ON l.stock = e.stock AND l.`date` = e.d1
ORDER BY pct_change DESC"""),
    "Task 12 - The data trap (worst day per stock)": (
        "Two stocks lose about 50% in one day - that is a bonus issue, not a crash.",
        f"""WITH {_PRICES},
moves AS (
  SELECT stock, `date`, close_price,
         ROUND(100.0 * (close_price / LAG(close_price) OVER (PARTITION BY stock ORDER BY `date`) - 1), 1) AS pct_move
  FROM prices
),
ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY stock ORDER BY pct_move) AS rn
  FROM moves WHERE pct_move IS NOT NULL
)
SELECT stock, `date`, close_price, pct_move FROM ranked WHERE rn = 1 ORDER BY pct_move"""),
    "Task 13 - Fix it (adjusted % change, TCS and Infosys)": (
        "Prices before each bonus issue are divided by 2, then first vs last close is compared.",
        """WITH adjusted AS (
  SELECT 'TCS' AS stock, `date`,
         CASE WHEN `date` < '2018-05-31' THEN close_price / 2 ELSE close_price END AS adj_close
  FROM tcs
  UNION ALL
  SELECT 'Infosys', `date`,
         CASE WHEN `date` < '2015-06-15' THEN close_price / 2 ELSE close_price END
  FROM infosys
)
SELECT stock,
       ROUND(100.0 * (MAX(CASE WHEN `date` = '2018-07-31' THEN adj_close END) /
                      MAX(CASE WHEN `date` = '2015-01-01' THEN adj_close END) - 1), 1) AS adjusted_pct_change
FROM adjusted GROUP BY stock ORDER BY stock"""),
    "Extra - Strategy vs buy-and-hold": (
        "Golden-cross strategy return vs buy-and-hold on adjusted prices (long-only, no costs).",
        """SELECT * FROM strategy_summary ORDER BY stock"""),
}

SCHEMA_HELP = """
**Raw tables** (889 rows each): `bajaj_auto`, `eicher_motors`, `hero_motocorp`, `infosys`, `tcs`, `tvs_motors`
→ `date, open_price, high_price, low_price, close_price, wap, no_of_shares, no_of_trades,
total_turnover, deliverable_qty, pct_deli_qty, spread_high_low, spread_close_open`

**Built tables:** `bajaj1` (date, close_price, ma20, ma50) · `bajaj2` (date, close_price, signal) ·
`master_table` (date, bajaj, tcs, tvs, infosys, eicher, hero) · `prices_all` (stock, date, close_price, adj_close) ·
`signals_raw` / `signals_adj` (stock, date, close_price, [adj_close], ma20, ma50, signal) ·
`stock_summary` · `corporate_events` · `strategy_trades` · `strategy_summary` · `strategy_by_period`

`signal` is a reserved word in MySQL - write it with backticks: `` `signal` ``.
"""
