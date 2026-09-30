-- =====================================================================
-- 01_explore.sql  |  Part 1 (Tasks 1-4) + data audit  |  MySQL 8
-- =====================================================================
USE stock_analysis;

-- TASK 1: history available (expect ~889 days, 2015-01-01 -> 2018-07-31)
SELECT COUNT(*)  AS trading_days,
       MIN(`date`) AS first_day,
       MAX(`date`) AS last_day
FROM bajaj_auto;

-- TASK 2: Eicher's five best closes (note the month they fall in)
SELECT `date`, close_price
FROM eicher_motors
ORDER BY close_price DESC
LIMIT 5;

-- TASK 3: TCS average close by year (n shown so partial 2018 is visible)
SELECT YEAR(`date`)                  AS year,
       ROUND(AVG(close_price), 2)    AS avg_close,
       COUNT(*)                      AS trading_days
FROM tcs
GROUP BY YEAR(`date`)
ORDER BY year;

-- TASK 4: rows where deliverable_qty is NULL, all six stocks
SELECT 'bajaj_auto' AS stock, `date` FROM bajaj_auto    WHERE deliverable_qty IS NULL
UNION ALL
SELECT 'eicher_motors', `date` FROM eicher_motors        WHERE deliverable_qty IS NULL
UNION ALL
SELECT 'hero_motocorp', `date` FROM hero_motocorp        WHERE deliverable_qty IS NULL
UNION ALL
SELECT 'infosys', `date` FROM infosys                    WHERE deliverable_qty IS NULL
UNION ALL
SELECT 'tcs', `date` FROM tcs                            WHERE deliverable_qty IS NULL
UNION ALL
SELECT 'tvs_motors', `date` FROM tvs_motors              WHERE deliverable_qty IS NULL;

-- ---------------------------------------------------------------------
-- DATA AUDIT (feeds the README missing-value table)
-- ---------------------------------------------------------------------
-- A1. NULL count per column for one table (repeat per table, or use the
--     Python audit in scripts/audit_data.py which does all six at once)
SELECT
  SUM(open_price IS NULL)      AS null_open,
  SUM(close_price IS NULL)     AS null_close,
  SUM(no_of_shares IS NULL)    AS null_shares,
  SUM(deliverable_qty IS NULL) AS null_deliverable_qty,
  SUM(pct_deli_qty IS NULL)    AS null_pct_deli_qty
FROM bajaj_auto;

-- A2. Do all six tables trade on identical dates? (expect 889 = 889)
SELECT COUNT(*) AS common_days
FROM bajaj_auto b
JOIN eicher_motors e ON e.`date` = b.`date`
JOIN hero_motocorp h ON h.`date` = b.`date`
JOIN infosys i       ON i.`date` = b.`date`
JOIN tcs t           ON t.`date` = b.`date`
JOIN tvs_motors v    ON v.`date` = b.`date`;

-- A3. Duplicate dates? (expect 0 rows)
SELECT `date`, COUNT(*) AS n FROM bajaj_auto GROUP BY `date` HAVING COUNT(*) > 1;
