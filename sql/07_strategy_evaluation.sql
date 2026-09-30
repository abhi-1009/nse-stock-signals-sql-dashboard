-- =====================================================================
-- 07_strategy_evaluation.sql | Extra: golden-cross strategy vs buy-and-hold
-- (the "baseline / overfitting / subgroup / error-analysis" checklist rows,
--  done in SQL). Uses ADJUSTED prices (signals_adj).
-- Rules: buy at the close of a Buy-signal day, sell at the close of the next
--   Sell-signal day; an unclosed final trade is marked to the last close
--   (is_open = 1). Long-only, no costs, no dividends, cash earns 0.
-- Caveat: trading at the same-day close the signal is computed on is slightly
--   optimistic (real trades happen next open); no brokerage/tax included.
-- =====================================================================
USE stock_analysis;

DROP TABLE IF EXISTS strategy_trades;
CREATE TABLE strategy_trades AS
WITH ev AS (
  SELECT stock, `date`, adj_close, `signal`,
         ROW_NUMBER() OVER (PARTITION BY stock ORDER BY `date`) AS rn
  FROM signals_adj
  WHERE `signal` <> 'Hold'
),
lastday AS (
  SELECT s.stock, s.`date` AS last_date, s.adj_close AS last_price
  FROM signals_adj s
  JOIN (SELECT stock, MAX(`date`) AS d FROM signals_adj GROUP BY stock) m
    ON m.stock = s.stock AND m.d = s.`date`
),
paired AS (
  SELECT b.stock,
         b.`date`     AS entry_date,
         b.adj_close  AS entry_price,
         s.`date`     AS sell_date,
         s.adj_close  AS sell_price
  FROM ev b
  LEFT JOIN ev s ON s.stock = b.stock AND s.rn = b.rn + 1 AND s.`signal` = 'Sell'
  WHERE b.`signal` = 'Buy'
)
SELECT p.stock,
       p.entry_date,
       COALESCE(p.sell_date, l.last_date)   AS exit_date,
       p.entry_price,
       COALESCE(p.sell_price, l.last_price) AS exit_price,
       CASE WHEN p.sell_date IS NULL THEN 1 ELSE 0 END AS is_open,
       ROUND(100.0 * (COALESCE(p.sell_price, l.last_price) / p.entry_price - 1), 2) AS trade_return_pct,
       DATEDIFF(COALESCE(p.sell_date, l.last_date), p.entry_date) AS hold_days,
       CASE WHEN p.entry_date < '2017-01-01' THEN '2015-16' ELSE '2017-18' END AS entry_period
FROM paired p
JOIN lastday l ON l.stock = p.stock;

DROP TABLE IF EXISTS strategy_summary;
CREATE TABLE strategy_summary AS
WITH t AS (
  SELECT stock,
         COUNT(*)                                        AS n_trades,
         SUM(trade_return_pct > 0)                       AS wins,
         SUM(hold_days <= 30 AND is_open = 0)            AS quick_flips_30d,
         SUM(hold_days <= 30 AND is_open = 0 AND trade_return_pct < 0) AS losing_quick_flips,
         ROUND(100.0 * (EXP(SUM(LN(1 + trade_return_pct / 100.0))) - 1), 1) AS strategy_return_pct
  FROM strategy_trades
  GROUP BY stock
),
bh AS (
  SELECT stock, ROUND(pct_change_adj, 1) AS buy_hold_pct FROM stock_summary
)
SELECT t.stock, t.n_trades, t.wins,
       ROUND(100.0 * t.wins / t.n_trades, 0) AS win_rate_pct,
       t.quick_flips_30d, t.losing_quick_flips,
       t.strategy_return_pct, bh.buy_hold_pct,
       ROUND(t.strategy_return_pct - bh.buy_hold_pct, 1) AS strategy_minus_buyhold
FROM t JOIN bh ON bh.stock = t.stock;

-- Overfitting / stability check: first half vs second half of the period
DROP TABLE IF EXISTS strategy_by_period;
CREATE TABLE strategy_by_period AS
SELECT stock, entry_period,
       COUNT(*) AS n_trades,
       ROUND(AVG(trade_return_pct), 2) AS avg_trade_return_pct,
       SUM(trade_return_pct > 0) AS wins
FROM strategy_trades
GROUP BY stock, entry_period;

SELECT * FROM strategy_summary ORDER BY stock;
SELECT * FROM strategy_by_period ORDER BY stock, entry_period;
