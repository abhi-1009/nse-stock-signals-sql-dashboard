-- =====================================================================
-- 04_all_stocks.sql | Part 2 (Task 10) | MySQL 8
-- One query, six stocks. PARTITION BY stock in EVERY window function
-- (ROW_NUMBER, AVG, LAG). Averages are NOT rounded (per brief).
-- Checkpoint: 56 Buys and 57 Sells in total across the six stocks.
-- =====================================================================
USE stock_analysis;

WITH prices AS (
  SELECT 'Bajaj Auto'    AS stock, `date`, close_price FROM bajaj_auto
  UNION ALL SELECT 'Eicher Motors',  `date`, close_price FROM eicher_motors
  UNION ALL SELECT 'Hero Motocorp',  `date`, close_price FROM hero_motocorp
  UNION ALL SELECT 'Infosys',        `date`, close_price FROM infosys
  UNION ALL SELECT 'TCS',            `date`, close_price FROM tcs
  UNION ALL SELECT 'TVS Motors',     `date`, close_price FROM tvs_motors
),
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
  SELECT *,
    LAG(ma20) OVER (PARTITION BY stock ORDER BY `date`) AS prev_ma20,
    LAG(ma50) OVER (PARTITION BY stock ORDER BY `date`) AS prev_ma50
  FROM ma
),
sig AS (
  SELECT stock, `date`, close_price,
    CASE
      WHEN ma50 IS NULL OR prev_ma50 IS NULL THEN 'Hold'
      WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50 THEN 'Buy'
      WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50 THEN 'Sell'
      ELSE 'Hold'
    END AS `signal`
  FROM lagged
),
latest AS (
  SELECT stock, `date`, `signal`,
         ROW_NUMBER() OVER (PARTITION BY stock ORDER BY `date` DESC) AS rn
  FROM sig
  WHERE `signal` <> 'Hold'
)
SELECT s.stock,
       SUM(s.`signal` = 'Buy')  AS buys,
       SUM(s.`signal` = 'Sell') AS sells,
       MAX(l.`date`)            AS last_signal_date,
       MAX(l.`signal`)          AS last_signal
FROM sig s
JOIN latest l ON l.stock = s.stock AND l.rn = 1
GROUP BY s.stock
ORDER BY s.stock;
