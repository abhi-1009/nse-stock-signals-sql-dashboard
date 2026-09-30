-- =====================================================================
-- 06_dashboard_tables.sql | Materialised tables read by the Streamlit app
-- Run AFTER 00-05. Every table is DROP/CREATE so the file can be re-run.
-- Tables built:
--   corporate_events   - the two price events (source of truth for adjustment)
--   prices_all         - six stocks stacked (raw + adjusted close)
--   signals_raw        - MA20/MA50/signal on RAW prices   (Task 10 logic)
--   signals_adj        - MA20/MA50/signal on ADJUSTED prices
--   stock_summary      - first/last close, raw vs adjusted % change, buys/sells
-- =====================================================================
USE stock_analysis;

DROP TABLE IF EXISTS corporate_events;
CREATE TABLE corporate_events (
  stock       VARCHAR(20) NOT NULL,
  event_date  DATE        NOT NULL,      -- first day trading at the new price level
  event_type  VARCHAR(40) NOT NULL,
  factor      DECIMAL(6,2) NOT NULL,     -- prices BEFORE event_date are divided by this
  note        VARCHAR(255),
  PRIMARY KEY (stock, event_date)
);
INSERT INTO corporate_events VALUES
 ('TCS',     '2018-05-31', '1:1 bonus issue', 2.00, 'Close fell ~50% overnight with no change in value; VERIFY on NSE/company notice and cite'),
 ('Infosys', '2015-06-15', '1:1 bonus issue', 2.00, 'Close fell ~50% overnight with no change in value; VERIFY on NSE/company notice and cite');

DROP TABLE IF EXISTS prices_all;
CREATE TABLE prices_all AS
WITH p AS (
  SELECT 'Bajaj Auto' AS stock, `date`, close_price FROM bajaj_auto
  UNION ALL SELECT 'Eicher Motors', `date`, close_price FROM eicher_motors
  UNION ALL SELECT 'Hero Motocorp', `date`, close_price FROM hero_motocorp
  UNION ALL SELECT 'Infosys',       `date`, close_price FROM infosys
  UNION ALL SELECT 'TCS',           `date`, close_price FROM tcs
  UNION ALL SELECT 'TVS Motors',    `date`, close_price FROM tvs_motors
)
SELECT p.stock, p.`date`, p.close_price,
       ROUND(p.close_price / COALESCE(e.factor, 1), 4) AS adj_close
FROM p
LEFT JOIN corporate_events e ON e.stock = p.stock AND p.`date` < e.event_date;

-- ---- signals on RAW close ----
DROP TABLE IF EXISTS signals_raw;
CREATE TABLE signals_raw AS
WITH ma AS (
  SELECT stock, `date`, close_price,
    CASE WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY `date`) >= 20
         THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY `date`
                ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) END AS ma20,
    CASE WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY `date`) >= 50
         THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY `date`
                ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) END AS ma50
  FROM prices_all
),
lagged AS (
  SELECT *, LAG(ma20) OVER (PARTITION BY stock ORDER BY `date`) AS prev_ma20,
            LAG(ma50) OVER (PARTITION BY stock ORDER BY `date`) AS prev_ma50
  FROM ma
)
SELECT stock, `date`, close_price, ROUND(ma20, 2) AS ma20, ROUND(ma50, 2) AS ma50,
  CASE
    WHEN ma50 IS NULL OR prev_ma50 IS NULL THEN 'Hold'
    WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50 THEN 'Buy'
    WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50 THEN 'Sell'
    ELSE 'Hold'
  END AS `signal`
FROM lagged;

-- ---- signals on ADJUSTED close ----
DROP TABLE IF EXISTS signals_adj;
CREATE TABLE signals_adj AS
WITH ma AS (
  SELECT stock, `date`, close_price, adj_close,
    CASE WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY `date`) >= 20
         THEN AVG(adj_close) OVER (PARTITION BY stock ORDER BY `date`
                ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) END AS ma20,
    CASE WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY `date`) >= 50
         THEN AVG(adj_close) OVER (PARTITION BY stock ORDER BY `date`
                ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) END AS ma50
  FROM prices_all
),
lagged AS (
  SELECT *, LAG(ma20) OVER (PARTITION BY stock ORDER BY `date`) AS prev_ma20,
            LAG(ma50) OVER (PARTITION BY stock ORDER BY `date`) AS prev_ma50
  FROM ma
)
SELECT stock, `date`, close_price, adj_close, ROUND(ma20, 2) AS ma20, ROUND(ma50, 2) AS ma50,
  CASE
    WHEN ma50 IS NULL OR prev_ma50 IS NULL THEN 'Hold'
    WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50 THEN 'Buy'
    WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50 THEN 'Sell'
    ELSE 'Hold'
  END AS `signal`
FROM lagged;

-- ---- one-row-per-stock summary (raw vs adjusted) ----
DROP TABLE IF EXISTS stock_summary;
CREATE TABLE stock_summary AS
WITH ends AS (SELECT stock, MIN(`date`) AS d0, MAX(`date`) AS d1 FROM prices_all GROUP BY stock),
chg AS (
  SELECT e.stock, e.d0 AS first_day, e.d1 AS last_day,
         f.close_price AS first_close, l.close_price AS last_close,
         f.adj_close   AS first_adj,   l.adj_close   AS last_adj
  FROM ends e
  JOIN prices_all f ON f.stock = e.stock AND f.`date` = e.d0
  JOIN prices_all l ON l.stock = e.stock AND l.`date` = e.d1
),
raw_cnt AS (
  SELECT stock, SUM(`signal`='Buy') AS buys_raw, SUM(`signal`='Sell') AS sells_raw FROM signals_raw GROUP BY stock
),
adj_cnt AS (
  SELECT stock, SUM(`signal`='Buy') AS buys_adj, SUM(`signal`='Sell') AS sells_adj FROM signals_adj GROUP BY stock
)
SELECT c.stock, c.first_day, c.last_day, c.first_close, c.last_close,
       ROUND(100.0 * (c.last_close / c.first_close - 1), 1) AS pct_change_raw,
       ROUND(100.0 * (c.last_adj   / c.first_adj   - 1), 1) AS pct_change_adj,
       r.buys_raw, r.sells_raw, a.buys_adj, a.sells_adj
FROM chg c
JOIN raw_cnt r ON r.stock = c.stock
JOIN adj_cnt a ON a.stock = c.stock;

-- Sanity checks: 5,334 rows in prices_all; 6 rows in stock_summary
SELECT COUNT(*) AS prices_all_rows FROM prices_all;
SELECT * FROM stock_summary ORDER BY stock;
