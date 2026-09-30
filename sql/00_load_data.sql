-- =====================================================================
-- 00_load_data.sql  |  MySQL 8  |  Run in MySQL Workbench (local first)
-- Creates the six price tables and loads the CSVs (Appendix A of guide).
-- Prereq (once):  SET GLOBAL local_infile = 1;
--   Workbench > connection > Advanced > "Others": OPT_LOCAL_INFILE=1
-- Edit the six '/path/to/...csv' paths below before running.
-- Assumption: only close_price is analysed; all other columns are kept.
-- =====================================================================
CREATE DATABASE IF NOT EXISTS stock_analysis;
USE stock_analysis;

-- ---------- bajaj_auto ----------
DROP TABLE IF EXISTS bajaj_auto;
CREATE TABLE bajaj_auto (
  `date` DATE PRIMARY KEY,
  open_price DECIMAL(12,2), high_price DECIMAL(12,2), low_price DECIMAL(12,2),
  close_price DECIMAL(12,2), wap DECIMAL(16,4),
  no_of_shares BIGINT, no_of_trades BIGINT, total_turnover DECIMAL(20,2),
  deliverable_qty BIGINT, pct_deli_qty DECIMAL(6,2),
  spread_high_low DECIMAL(12,2), spread_close_open DECIMAL(12,2)
);
LOAD DATA LOCAL INFILE '/path/to/Bajaj_Auto.csv' INTO TABLE bajaj_auto
FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n' IGNORE 1 LINES
(@d,@o,@h,@l,@c,@w,@s,@tr,@to,@dq,@pd,@shl,@sco)
SET `date` = STR_TO_DATE(@d, '%d-%M-%Y'),
  open_price = NULLIF(@o,''), high_price = NULLIF(@h,''), low_price = NULLIF(@l,''),
  close_price = NULLIF(@c,''), wap = NULLIF(@w,''), no_of_shares = NULLIF(@s,''),
  no_of_trades = NULLIF(@tr,''), total_turnover = NULLIF(@to,''),
  deliverable_qty = NULLIF(@dq,''), pct_deli_qty = NULLIF(@pd,''),
  spread_high_low = NULLIF(@shl,''), spread_close_open = NULLIF(TRIM(@sco),'');

-- ---------- eicher_motors ----------
DROP TABLE IF EXISTS eicher_motors;
CREATE TABLE eicher_motors LIKE bajaj_auto;
LOAD DATA LOCAL INFILE '/path/to/Eicher_Motors.csv' INTO TABLE eicher_motors
FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n' IGNORE 1 LINES
(@d,@o,@h,@l,@c,@w,@s,@tr,@to,@dq,@pd,@shl,@sco)
SET `date` = STR_TO_DATE(@d, '%d-%M-%Y'),
  open_price = NULLIF(@o,''), high_price = NULLIF(@h,''), low_price = NULLIF(@l,''),
  close_price = NULLIF(@c,''), wap = NULLIF(@w,''), no_of_shares = NULLIF(@s,''),
  no_of_trades = NULLIF(@tr,''), total_turnover = NULLIF(@to,''),
  deliverable_qty = NULLIF(@dq,''), pct_deli_qty = NULLIF(@pd,''),
  spread_high_low = NULLIF(@shl,''), spread_close_open = NULLIF(TRIM(@sco),'');

-- ---------- hero_motocorp ----------
DROP TABLE IF EXISTS hero_motocorp;
CREATE TABLE hero_motocorp LIKE bajaj_auto;
LOAD DATA LOCAL INFILE '/path/to/Hero_Motocorp.csv' INTO TABLE hero_motocorp
FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n' IGNORE 1 LINES
(@d,@o,@h,@l,@c,@w,@s,@tr,@to,@dq,@pd,@shl,@sco)
SET `date` = STR_TO_DATE(@d, '%d-%M-%Y'),
  open_price = NULLIF(@o,''), high_price = NULLIF(@h,''), low_price = NULLIF(@l,''),
  close_price = NULLIF(@c,''), wap = NULLIF(@w,''), no_of_shares = NULLIF(@s,''),
  no_of_trades = NULLIF(@tr,''), total_turnover = NULLIF(@to,''),
  deliverable_qty = NULLIF(@dq,''), pct_deli_qty = NULLIF(@pd,''),
  spread_high_low = NULLIF(@shl,''), spread_close_open = NULLIF(TRIM(@sco),'');

-- ---------- infosys ----------
DROP TABLE IF EXISTS infosys;
CREATE TABLE infosys LIKE bajaj_auto;
LOAD DATA LOCAL INFILE '/path/to/Infosys.csv' INTO TABLE infosys
FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n' IGNORE 1 LINES
(@d,@o,@h,@l,@c,@w,@s,@tr,@to,@dq,@pd,@shl,@sco)
SET `date` = STR_TO_DATE(@d, '%d-%M-%Y'),
  open_price = NULLIF(@o,''), high_price = NULLIF(@h,''), low_price = NULLIF(@l,''),
  close_price = NULLIF(@c,''), wap = NULLIF(@w,''), no_of_shares = NULLIF(@s,''),
  no_of_trades = NULLIF(@tr,''), total_turnover = NULLIF(@to,''),
  deliverable_qty = NULLIF(@dq,''), pct_deli_qty = NULLIF(@pd,''),
  spread_high_low = NULLIF(@shl,''), spread_close_open = NULLIF(TRIM(@sco),'');

-- ---------- tcs ----------
DROP TABLE IF EXISTS tcs;
CREATE TABLE tcs LIKE bajaj_auto;
LOAD DATA LOCAL INFILE '/path/to/TCS.csv' INTO TABLE tcs
FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n' IGNORE 1 LINES
(@d,@o,@h,@l,@c,@w,@s,@tr,@to,@dq,@pd,@shl,@sco)
SET `date` = STR_TO_DATE(@d, '%d-%M-%Y'),
  open_price = NULLIF(@o,''), high_price = NULLIF(@h,''), low_price = NULLIF(@l,''),
  close_price = NULLIF(@c,''), wap = NULLIF(@w,''), no_of_shares = NULLIF(@s,''),
  no_of_trades = NULLIF(@tr,''), total_turnover = NULLIF(@to,''),
  deliverable_qty = NULLIF(@dq,''), pct_deli_qty = NULLIF(@pd,''),
  spread_high_low = NULLIF(@shl,''), spread_close_open = NULLIF(TRIM(@sco),'');

-- ---------- tvs_motors ----------
DROP TABLE IF EXISTS tvs_motors;
CREATE TABLE tvs_motors LIKE bajaj_auto;
LOAD DATA LOCAL INFILE '/path/to/TVS_Motors.csv' INTO TABLE tvs_motors
FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n' IGNORE 1 LINES
(@d,@o,@h,@l,@c,@w,@s,@tr,@to,@dq,@pd,@shl,@sco)
SET `date` = STR_TO_DATE(@d, '%d-%M-%Y'),
  open_price = NULLIF(@o,''), high_price = NULLIF(@h,''), low_price = NULLIF(@l,''),
  close_price = NULLIF(@c,''), wap = NULLIF(@w,''), no_of_shares = NULLIF(@s,''),
  no_of_trades = NULLIF(@tr,''), total_turnover = NULLIF(@to,''),
  deliverable_qty = NULLIF(@dq,''), pct_deli_qty = NULLIF(@pd,''),
  spread_high_low = NULLIF(@shl,''), spread_close_open = NULLIF(TRIM(@sco),'');

-- ---------- sanity check: every table must show 889 rows, 2015-01-01 .. 2018-07-31
SELECT 'bajaj_auto' AS tbl, COUNT(*) AS n, MIN(`date`) AS first_day, MAX(`date`) AS last_day FROM bajaj_auto
UNION ALL SELECT 'eicher_motors', COUNT(*), MIN(`date`), MAX(`date`) FROM eicher_motors
UNION ALL SELECT 'hero_motocorp', COUNT(*), MIN(`date`), MAX(`date`) FROM hero_motocorp
UNION ALL SELECT 'infosys',       COUNT(*), MIN(`date`), MAX(`date`) FROM infosys
UNION ALL SELECT 'tcs',           COUNT(*), MIN(`date`), MAX(`date`) FROM tcs
UNION ALL SELECT 'tvs_motors',    COUNT(*), MIN(`date`), MAX(`date`) FROM tvs_motors;
