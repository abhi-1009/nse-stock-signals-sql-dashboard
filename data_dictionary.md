# Data dictionary

## Raw tables (one per stock, 889 rows each, 2015-01-01 to 2018-07-31)
`bajaj_auto`, `eicher_motors`, `hero_motocorp`, `infosys`, `tcs`, `tvs_motors`

| Column | Type | Meaning |
|---|---|---|
| `date` | DATE (PK) | Trading day (CSV format `31-July-2018` is converted on load) |
| `open_price`, `high_price`, `low_price`, `close_price` | DECIMAL | Prices in rupees. **Only `close_price` is analysed.** |
| `wap` | DECIMAL | Weighted average price for the day |
| `no_of_shares`, `no_of_trades` | BIGINT | Volume traded and number of trades |
| `total_turnover` | DECIMAL | Value traded in rupees |
| `deliverable_qty` | BIGINT | Shares actually delivered (1 NULL per stock) |
| `pct_deli_qty` | DECIMAL | Delivered quantity as % of traded quantity (1 NULL per stock) |
| `spread_high_low`, `spread_close_open` | DECIMAL | High - low, and close - open |

## Built tables
| Table | Built by | Columns / meaning |
|---|---|---|
| `bajaj1` | sql/02 | `date, close_price, ma20, ma50` (NULL until a full window exists) |
| `master_table` | sql/02 | `date, bajaj, tcs, tvs, infosys, eicher, hero` (close prices) |
| `bajaj2` | sql/03 | `date, close_price, signal` (`Buy` / `Sell` / `Hold`) |
| `corporate_events` | sql/06 | `stock, event_date, event_type, factor, note` - prices before `event_date` are divided by `factor` |
| `prices_all` | sql/06 | `stock, date, close_price, adj_close` (5,334 rows) |
| `signals_raw` | sql/06 | `stock, date, close_price, ma20, ma50, signal` on raw prices |
| `signals_adj` | sql/06 | same plus `adj_close`; averages and signals on adjusted prices |
| `stock_summary` | sql/06 | first/last close, raw vs adjusted % change, Buy/Sell counts (raw and adjusted) |
| `strategy_trades` | sql/07 | one row per Buy-to-Sell trade: entry/exit, return %, days held, open flag, period |
| `strategy_summary` | sql/07 | trades, win rate, quick round trips, strategy vs buy-and-hold return |
| `strategy_by_period` | sql/07 | average trade return for 2015-16 vs 2017-18 entries |

## Definitions
- **20-/50-day moving average:** mean close of the current and previous 19 / 49 trading days; NULL until a full window exists.
- **Buy:** `ma20 > ma50` today and `ma20 <= ma50` yesterday. **Sell:** the mirror image. Everything else is Hold (including any day with a NULL average).
- **Adjusted close:** close divided by the event factor for all dates before the event date.
- `signal` is a reserved word in MySQL: always write it with backticks.
