-- =====================================================================
-- 05_data_trap_and_fix.sql | Part 3 (Tasks 11-13) | MySQL 8
-- =====================================================================
USE stock_analysis;

-- TASK 11: who went up? first close vs last close per stock (RAW prices)
WITH prices AS (
  SELECT 'Bajaj Auto' AS stock, `date`, close_price FROM bajaj_auto
  UNION ALL SELECT 'Eicher Motors', `date`, close_price FROM eicher_motors
  UNION ALL SELECT 'Hero Motocorp', `date`, close_price FROM hero_motocorp
  UNION ALL SELECT 'Infosys',       `date`, close_price FROM infosys
  UNION ALL SELECT 'TCS',           `date`, close_price FROM tcs
  UNION ALL SELECT 'TVS Motors',    `date`, close_price FROM tvs_motors
),
ends AS (SELECT stock, MIN(`date`) AS d0, MAX(`date`) AS d1 FROM prices GROUP BY stock)
SELECT e.stock,
       f.close_price AS first_close,
       l.close_price AS last_close,
       ROUND(100.0 * (l.close_price - f.close_price) / f.close_price, 1) AS pct_change
FROM ends e
JOIN prices f ON f.stock = e.stock AND f.`date` = e.d0
JOIN prices l ON l.stock = e.stock AND l.`date` = e.d1
ORDER BY pct_change DESC;
-- Checkpoint: TVS Motors tops at 86.9%; two stocks negative (TCS and Infosys - a trap!)

-- TASK 12: the data trap - each stock's single worst day (day-over-day % move)
WITH prices AS (
  SELECT 'Bajaj Auto' AS stock, `date`, close_price FROM bajaj_auto
  UNION ALL SELECT 'Eicher Motors', `date`, close_price FROM eicher_motors
  UNION ALL SELECT 'Hero Motocorp', `date`, close_price FROM hero_motocorp
  UNION ALL SELECT 'Infosys',       `date`, close_price FROM infosys
  UNION ALL SELECT 'TCS',           `date`, close_price FROM tcs
  UNION ALL SELECT 'TVS Motors',    `date`, close_price FROM tvs_motors
),
moves AS (
  SELECT stock, `date`, close_price,
         ROUND(100.0 * (close_price / LAG(close_price) OVER (PARTITION BY stock ORDER BY `date`) - 1), 1) AS pct_move
  FROM prices
),
ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY stock ORDER BY pct_move) AS rn
  FROM moves
  WHERE pct_move IS NOT NULL           -- drop each stock's first day (NULL move)
)
SELECT stock, `date`, close_price, pct_move
FROM ranked
WHERE rn = 1
ORDER BY pct_move;
-- Two rows are ~ -50%: TCS 2018-05-31 and Infosys 2015-06-15 (1:1 bonus issues).
-- ACTION: verify both with a source (NSE/company announcement) and cite it in the PDF.

-- TASK 13: adjust prices before each event by /2, then % change (CASE version)
WITH adjusted AS (
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
FROM adjusted
GROUP BY stock
ORDER BY stock;
