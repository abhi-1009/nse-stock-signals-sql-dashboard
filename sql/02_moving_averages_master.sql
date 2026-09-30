-- =====================================================================
-- 02_moving_averages_master.sql | Part 2 (Tasks 5-6) | MySQL 8
-- =====================================================================
USE stock_analysis;

-- TASK 5: Bajaj 20- and 50-day moving averages (NULL until window is full)
-- ROWS BETWEEN 19 PRECEDING AND CURRENT ROW = 20 rows (n+1 = window size)
DROP TABLE IF EXISTS bajaj1;
CREATE TABLE bajaj1 AS
SELECT
  `date`,
  close_price,
  CASE WHEN ROW_NUMBER() OVER (ORDER BY `date`) >= 20
       THEN ROUND(AVG(close_price) OVER (ORDER BY `date`
                  ROWS BETWEEN 19 PRECEDING AND CURRENT ROW), 2)
  END AS ma20,
  CASE WHEN ROW_NUMBER() OVER (ORDER BY `date`) >= 50
       THEN ROUND(AVG(close_price) OVER (ORDER BY `date`
                  ROWS BETWEEN 49 PRECEDING AND CURRENT ROW), 2)
  END AS ma50
FROM bajaj_auto;

-- Checkpoints: 889 rows; first ma20 = 2415.53 on 2015-01-29;
--   first ma50 = 2283.80 on 2015-03-13; ma20 on 2018-07-31 = 2918.51
SELECT COUNT(*) AS n FROM bajaj1;
SELECT `date`, ma20 FROM bajaj1 WHERE ma20 IS NOT NULL ORDER BY `date` LIMIT 1;
SELECT `date`, ma50 FROM bajaj1 WHERE ma50 IS NOT NULL ORDER BY `date` LIMIT 1;
SELECT `date`, ma20 FROM bajaj1 WHERE `date` = '2018-07-31';

-- TASK 6: master table, one row per date, closing price of each stock
DROP TABLE IF EXISTS master_table;
CREATE TABLE master_table AS
SELECT b.`date`,
       b.close_price AS bajaj,
       t.close_price AS tcs,
       v.close_price AS tvs,
       i.close_price AS infosys,
       e.close_price AS eicher,
       h.close_price AS hero
FROM bajaj_auto b
JOIN tcs t           ON t.`date` = b.`date`
JOIN tvs_motors v    ON v.`date` = b.`date`
JOIN infosys i       ON i.`date` = b.`date`
JOIN eicher_motors e ON e.`date` = b.`date`
JOIN hero_motocorp h ON h.`date` = b.`date`;

-- Checkpoints: 889 rows, 7 columns, no NULLs; 2018-07-31 -> bajaj 2700.70, tvs 517.45
SELECT COUNT(*) AS n FROM master_table;
SELECT * FROM master_table WHERE `date` = '2018-07-31';
