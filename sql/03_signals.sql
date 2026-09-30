-- =====================================================================
-- 03_signals.sql | Part 2 (Tasks 7-9) | MySQL 8
-- Golden cross: Buy when ma20 crosses ABOVE ma50, Sell when it crosses BELOW.
-- A cross is a two-day event: yesterday not above, today above.
-- `signal` is a reserved word in MySQL -> always use backticks.
-- =====================================================================
USE stock_analysis;

-- TASK 7: bajaj2 (date, close_price, signal)
DROP TABLE IF EXISTS bajaj2;
CREATE TABLE bajaj2 AS
WITH t AS (
  SELECT `date`, close_price, ma20, ma50,
         LAG(ma20) OVER (ORDER BY `date`) AS prev_ma20,
         LAG(ma50) OVER (ORDER BY `date`) AS prev_ma50
  FROM bajaj1
)
SELECT `date`, close_price,
  CASE
    WHEN ma50 IS NULL OR prev_ma50 IS NULL THEN 'Hold'      -- NULL guard FIRST
    WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50 THEN 'Buy'
    WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50 THEN 'Sell'
    ELSE 'Hold'
  END AS `signal`
FROM t;

-- Checkpoints: 889 rows; first Buy 2015-05-18; first Sell 2015-08-24
SELECT `date`, `signal` FROM bajaj2 WHERE `signal` = 'Buy'  ORDER BY `date` LIMIT 1;
SELECT `date`, `signal` FROM bajaj2 WHERE `signal` = 'Sell' ORDER BY `date` LIMIT 1;

-- TASK 8: how often did it trigger? (sum = 889; Buy and Sell differ by <= 1)
SELECT `signal`, COUNT(*) AS days
FROM bajaj2
GROUP BY `signal`
ORDER BY `signal`;

-- TASK 9: signal on a given day (test with 2015-05-18 -> Buy first)
SELECT `signal` FROM bajaj2 WHERE `date` = '2018-06-21';

-- MYSQL_ONLY_START
DROP FUNCTION IF EXISTS bajaj_signal;
DELIMITER $$
CREATE FUNCTION bajaj_signal(d DATE)
RETURNS VARCHAR(4) DETERMINISTIC READS SQL DATA
BEGIN
  DECLARE s VARCHAR(4);
  SELECT `signal` INTO s FROM bajaj2 WHERE `date` = d;
  RETURN s;          -- NULL on non-trading days (weekends/holidays): documented choice
END $$
DELIMITER ;

SELECT bajaj_signal('2015-05-18') AS should_be_buy,
       bajaj_signal('2018-06-21') AS task9_answer;
-- MYSQL_ONLY_END
