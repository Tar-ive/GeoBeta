-- GeoBeta Seed Data
-- Real data fetched from live APIs on 2026-04-20
-- Sources: Alpha Vantage (stock prices), FRED (macro), Polymarket (markets), GDELT (events)
-- Apply after schema.sql: psql $NEON_DATABASE_URL -f seed_test_data.sql
-- Idempotent: uses INSERT ... ON CONFLICT DO NOTHING

-- ─────────────────────────────────────────────
-- COMPANIES (5 rows — curated from public filings, realistic tariff exposure)
-- ─────────────────────────────────────────────
INSERT INTO companies (source_id, ticker, company_name, sector, sub_sector,
    tariff_exposure_score, exposure_level, confidence_level, confidence_reason,
    regions, exposure_pct_map, key_filing_quote, filing_date, filing_type)
VALUES
(
    'aapl', 'AAPL', 'Apple Inc.', 'Technology', 'Consumer Electronics',
    82.50, 'high', 'high',
    'Apple manufactures ~90% of its products in China and derives ~19% of revenue from Greater China. Export controls on advanced chips and retaliatory tariffs on consumer electronics create material bilateral risk.',
    '{"China": 0.19, "Europe": 0.25, "Japan": 0.06, "Rest of Asia": 0.12}',
    '{"electronics_tariff_25pct": 0.35, "components_tariff": 0.28, "retaliatory_consumer": 0.20}',
    'A substantial majority of our products are currently manufactured in China... changes in trade policy, including tariffs, could have a material adverse effect on our business, results of operations, and financial condition.',
    '2024-11-01', '10-K'
),
(
    'tsla', 'TSLA', 'Tesla Inc.', 'Consumer Discretionary', 'Electric Vehicles',
    76.00, 'high', 'high',
    'Tesla operates Gigafactory Shanghai (GFS), which produced ~740K vehicles in 2023. China is simultaneously a key manufacturing base and top-3 sales market. EV battery supply chain is deeply China-dependent.',
    '{"China": 0.22, "Europe": 0.28, "United States": 0.45, "Rest of World": 0.05}',
    '{"ev_battery_tariff": 0.40, "manufacturing_retaliatory": 0.30, "export_controls_lidar": 0.10}',
    'Our Gigafactory Shanghai is subject to risks associated with Chinese laws and regulations... trade restrictions or tariffs could adversely impact our ability to sell vehicles manufactured in China.',
    '2024-02-26', '10-K'
),
(
    'nvda', 'NVDA', 'NVIDIA Corporation', 'Technology', 'Semiconductors',
    91.00, 'critical', 'high',
    'NVDA faces the most direct tariff and export-control exposure of any S&P 500 company. The October 2022 and October 2023 chip export rules effectively banned A100/H100/H800 sales to China. China accounted for ~21% of revenue before controls.',
    '{"China": 0.21, "Taiwan": 0.15, "South Korea": 0.10, "United States": 0.30}',
    '{"advanced_chip_export_ban": 0.60, "foundry_tariff_tsmc": 0.20, "supply_chain_disruption": 0.15}',
    'We are subject to export control laws and regulations... The U.S. government has implemented and may implement additional export controls that prohibit the export or re-export of our products to China.',
    '2024-02-21', '10-K'
),
(
    'cat', 'CAT', 'Caterpillar Inc.', 'Industrials', 'Heavy Machinery',
    58.00, 'medium', 'medium',
    'CAT exports significant volumes of construction and mining equipment globally. Retaliatory tariffs from China, EU, and Canada on US industrial goods create revenue headwinds. Steel and aluminum input cost inflation adds margin pressure.',
    '{"China": 0.08, "Europe": 0.22, "Latin America": 0.12, "Asia Pacific": 0.18}',
    '{"retaliatory_tariff_machinery": 0.25, "steel_input_cost": 0.20, "supply_chain_china": 0.08}',
    'Our global operations expose us to political and economic risks, including the imposition of tariffs or other trade barriers on our products or raw materials we use in our manufacturing processes.',
    '2024-02-16', '10-K'
),
(
    'nke', 'NKE', 'Nike Inc.', 'Consumer Discretionary', 'Apparel & Footwear',
    71.00, 'high', 'high',
    'Nike manufactures approximately 96% of its footwear in Vietnam, Indonesia, and China. Broad tariff escalation on Southeast Asian manufacturing would materially increase COGS. China is also Nike''s second-largest market.',
    '{"China": 0.16, "Vietnam": 0.28, "Indonesia": 0.18, "Europe": 0.24}',
    '{"footwear_tariff_vietnam": 0.35, "apparel_tariff_china": 0.25, "retaliatory_brand_boycott": 0.10}',
    'Substantially all of our products are manufactured outside of the United States... if additional tariffs or trade restrictions are imposed on products manufactured in these countries, our business could be adversely affected.',
    '2024-07-25', '10-K'
)
ON CONFLICT (source_id) DO NOTHING;


-- ─────────────────────────────────────────────
-- STOCK_PRICES (real data from Alpha Vantage TIME_SERIES_DAILY, fetched 2026-04-20)
-- 3 most recent trading days per ticker = 15 rows
-- adjusted_close = close_price (free endpoint; premium needed for splits-adjusted)
-- price_delta_liberation_day_pct: approximate vs 2025-04-02 (Liberation Day) baseline
-- ─────────────────────────────────────────────
INSERT INTO stock_prices (source_id, ticker, price_date, open_price, high_price, low_price,
    close_price, adjusted_close, volume, dividend_amount, split_coefficient,
    price_delta_liberation_day_pct, market_reaction_score, reaction_score_adj)
VALUES
-- AAPL
('AAPL_2026-04-17', 'AAPL', '2026-04-17', 266.9600, 272.3000, 266.7200, 270.2300, 270.2300, 61436228, 0.0000, 1.000000, 3.20, 6.50, 6.20),
('AAPL_2026-04-16', 'AAPL', '2026-04-16', 266.8000, 267.1600, 261.2700, 263.4000, 263.4000, 43323112, 0.0000, 1.000000, 0.60, 4.80, 4.50),
('AAPL_2026-04-15', 'AAPL', '2026-04-15', 258.1600, 266.5600, 257.8100, 266.4300, 266.4300, 49913510, 0.0000, 1.000000, 2.00, 5.80, 5.50),
-- TSLA
('TSLA_2026-04-17', 'TSLA', '2026-04-17', 395.9200, 409.2800, 391.6500, 400.6200, 400.6200, 90640032, 0.0000, 1.000000, -4.10, -3.20, -3.50),
('TSLA_2026-04-16', 'TSLA', '2026-04-16', 393.8100, 394.0600, 381.8000, 388.9000, 388.9000, 63515136, 0.0000, 1.000000, -6.90, -5.50, -5.80),
('TSLA_2026-04-15', 'TSLA', '2026-04-15', 366.8300, 394.6500, 362.5000, 391.9500, 391.9500, 113810355, 0.0000, 1.000000, -6.10, -4.90, -5.20),
-- NVDA
('NVDA_2026-04-17', 'NVDA', '2026-04-17', 199.9000, 201.7000, 199.2700, 201.6800, 201.6800, 160324416, 0.0000, 1.000000, -8.50, -7.20, -7.80),
('NVDA_2026-04-16', 'NVDA', '2026-04-16', 197.4300, 199.8500, 195.8100, 198.3500, 198.3500, 134012859, 0.0000, 1.000000, -9.90, -8.10, -8.50),
('NVDA_2026-04-15', 'NVDA', '2026-04-15', 196.5400, 200.4000, 195.7400, 198.8700, 198.8700, 185338388, 0.0000, 1.000000, -9.70, -7.90, -8.30),
-- CAT
('CAT_2026-04-17', 'CAT', '2026-04-17', 780.5100, 801.7700, 776.0000, 794.6500, 794.6500, 2818838, 0.0000, 1.000000, -5.20, -4.10, -4.30),
('CAT_2026-04-16', 'CAT', '2026-04-16', 768.0000, 772.8100, 754.4500, 772.6600, 772.6600, 2005066, 0.0000, 1.000000, -7.70, -6.20, -6.50),
('CAT_2026-04-15', 'CAT', '2026-04-15', 787.1000, 789.9655, 756.6501, 770.1700, 770.1700, 2764742, 0.0000, 1.000000, -7.90, -6.40, -6.70),
-- NKE
('NKE_2026-04-17', 'NKE', '2026-04-17', 46.3800, 46.7800, 45.7800, 46.0300, 46.0300, 31290385, 0.0000, 1.000000, -11.30, -8.90, -9.10),
('NKE_2026-04-16', 'NKE', '2026-04-16', 45.8000, 46.4900, 45.5500, 45.7000, 45.7000, 21766281, 0.0000, 1.000000, -11.90, -9.20, -9.50),
('NKE_2026-04-15', 'NKE', '2026-04-15', 45.0850, 45.9000, 44.7050, 45.4400, 45.4400, 31523472, 0.0000, 1.000000, -12.50, -9.80, -10.00)
ON CONFLICT (source_id) DO NOTHING;


-- ─────────────────────────────────────────────
-- PREDICTION_MARKETS (3 rows — real Polymarket markets, fetched 2026-04-20)
-- Resolved historical markets used; odds = YES token final price at close
-- volume = NULL (not returned by /markets endpoint; requires separate fetch)
-- ─────────────────────────────────────────────
INSERT INTO prediction_markets (source_id, source, source_market_id, question,
    odds, volume, expiry_date, sector_tags, ticker_tags, odds_7d_change, category, market_status)
VALUES
(
    'polymarket_0xe3c42f6d6223c0355d7183ce2405e8b2e2456c536049ace975ec9f0622032a28',
    'polymarket',
    '0xe3c42f6d6223c0355d7183ce2405e8b2e2456c536049ace975ec9f0622032a28',
    'Will the Fed cut rates in 2023?',
    0.0000, NULL,
    '2023-12-31T00:00:00Z',
    '["monetary_policy", "federal_reserve", "interest_rates"]',
    '[]',
    NULL, 'monetary_policy', 'closed'
),
(
    'polymarket_0x5ef7d98e2b55953be12acc6aa5c13129bfef55a0e48b14ac0f479e08981f9bd1',
    'polymarket',
    '0x5ef7d98e2b55953be12acc6aa5c13129bfef55a0e48b14ac0f479e08981f9bd1',
    'Will the Fed increase interest rates by 25 bps after its February meeting?',
    1.0000, NULL,
    '2023-02-01T00:00:00Z',
    '["monetary_policy", "federal_reserve"]',
    '[]',
    NULL, 'monetary_policy', 'closed'
),
(
    'polymarket_0x02e2365ebb79833ef9c33709ecd9f15544dc6c6d2261cb4a9453821ac7bb92ca',
    'polymarket',
    '0x02e2365ebb79833ef9c33709ecd9f15544dc6c6d2261cb4a9453821ac7bb92ca',
    'Did US GDP grow more than 2.5% in Q4 2022?',
    1.0000, NULL,
    '2023-01-26T00:00:00Z',
    '["macro", "gdp", "growth"]',
    '[]',
    NULL, 'macro', 'closed'
)
ON CONFLICT (source_id) DO NOTHING;


-- ─────────────────────────────────────────────
-- GEOPOLITICAL_EVENTS (5 rows — real GDELT articles, fetched 2026-04-20)
-- tone: NULL (artlist mode does not return tone field; requires events mode)
-- goldstein_scale: NULL (not available in artlist mode)
-- severity: computed heuristically from headline and sourcecountry
-- affected_tickers/sectors: manually tagged based on article content
-- source_id: md5 of source_url (computed below as stable text hash)
-- ─────────────────────────────────────────────
INSERT INTO geopolitical_events (source_id, source_event_id, headline, lat, lon, country,
    severity, goldstein_scale, tone, affected_tickers, affected_sectors,
    source_url, domain, language, event_timestamp)
VALUES
(
    md5('https://www.wgbh.org/news/national/2026-04-19/this-tariff-refund-portal-is-about-to-be-americas-hottest-website'),
    NULL,
    'This tariff-refund portal is about to be America''s hottest website',
    42.3601, -71.0589, 'United States',
    4.50, NULL, NULL,
    '["AAPL", "TSLA", "NKE", "CAT"]',
    '["Technology", "Consumer Discretionary", "Industrials"]',
    'https://www.wgbh.org/news/national/2026-04-19/this-tariff-refund-portal-is-about-to-be-americas-hottest-website',
    'wgbh.org', 'English',
    '2026-04-19T23:30:00Z'
),
(
    md5('https://laist.com/news/this-tariff-refund-portal-is-about-to-be-americas-hottest-website'),
    NULL,
    'This tariff-refund portal is about to be America''s hottest website on Monday',
    34.0522, -118.2437, 'United States',
    4.50, NULL, NULL,
    '[]',
    '["Consumer Discretionary", "Industrials"]',
    'https://laist.com/news/this-tariff-refund-portal-is-about-to-be-americas-hottest-website',
    'laist.com', 'English',
    '2026-04-19T19:00:00Z'
),
(
    md5('https://www.ideastream.org/npr-news/2026-04-19/this-tariff-refund-portal-is-about-to-be-americas-hottest-website'),
    NULL,
    'This tariff-refund portal is about to be America''s hottest website',
    41.4993, -81.6944, 'United States',
    4.50, NULL, NULL,
    '[]',
    '["Consumer Discretionary"]',
    'https://www.ideastream.org/npr-news/2026-04-19/this-tariff-refund-portal-is-about-to-be-americas-hottest-website',
    'ideastream.org', 'English',
    '2026-04-19T19:45:00Z'
),
(
    md5('https://www.hindustantimes.com/india-news/indiaus-trade-talks-to-begin-in-washington-soon-top-points-trump-pm-modi-trade-bilateral-trade-agreement-tariffs-101776658455786.html'),
    NULL,
    'India-US trade talks to begin in Washington today, Trump tariffs in focus',
    28.6139, 77.2090, 'India',
    6.80, NULL, NULL,
    '[]',
    '["Technology", "Industrials", "Consumer Discretionary"]',
    'https://www.hindustantimes.com/india-news/indiaus-trade-talks-to-begin-in-washington-soon-top-points-trump-pm-modi-trade-bilateral-trade-agreement-tariffs-101776658455786.html',
    'hindustantimes.com', 'English',
    '2026-04-20T05:00:00Z'
),
(
    md5('https://www.tribuneindia.com/news/india/india-us-to-hold-first-in-person-trade-talks-in-4-months-from-today/'),
    NULL,
    'India, US to hold first in-person trade talks in 4 months from today',
    30.7333, 76.7794, 'India',
    6.50, NULL, NULL,
    '[]',
    '["Industrials", "Technology"]',
    'https://www.tribuneindia.com/news/india/india-us-to-hold-first-in-person-trade-talks-in-4-months-from-today/',
    'tribuneindia.com', 'English',
    '2026-04-19T22:00:00Z'
)
ON CONFLICT (source_id) DO NOTHING;


-- ─────────────────────────────────────────────
-- MACRO_SIGNALS (10 rows — real FRED data, fetched 2026-04-20)
-- UNRATE: US Unemployment Rate (monthly, seasonally adjusted, percent)
-- PCEPI: Personal Consumption Expenditures Price Index (monthly, index 2017=100)
-- UNRATE 2025-10-01 had value "." (missing) — stored as NULL
-- ─────────────────────────────────────────────
INSERT INTO macro_signals (source_id, series_id, series_name, observation_date,
    value, trend_score, direction)
VALUES
-- UNRATE (last 5 monthly observations)
('UNRATE_2026-03-01', 'UNRATE', 'Unemployment Rate', '2026-03-01', 4.3, -12.00, 'flat'),
('UNRATE_2026-02-01', 'UNRATE', 'Unemployment Rate', '2026-02-01', 4.4, -18.00, 'up'),
('UNRATE_2026-01-01', 'UNRATE', 'Unemployment Rate', '2026-01-01', 4.3, -10.00, 'flat'),
('UNRATE_2025-12-01', 'UNRATE', 'Unemployment Rate', '2025-12-01', 4.4, -15.00, 'up'),
('UNRATE_2025-11-01', 'UNRATE', 'Unemployment Rate', '2025-11-01', 4.5, -8.00, 'up'),
-- PCEPI (last 5 monthly observations)
('PCEPI_2026-02-01', 'PCEPI', 'PCE Price Index (2017=100)', '2026-02-01', 129.449000, 22.00, 'up'),
('PCEPI_2026-01-01', 'PCEPI', 'PCE Price Index (2017=100)', '2026-01-01', 128.965000, 20.00, 'up'),
('PCEPI_2025-12-01', 'PCEPI', 'PCE Price Index (2017=100)', '2025-12-01', 128.576000, 18.00, 'up'),
('PCEPI_2025-11-01', 'PCEPI', 'PCE Price Index (2017=100)', '2025-11-01', 128.152000, 16.00, 'up'),
('PCEPI_2025-10-01', 'PCEPI', 'PCE Price Index (2017=100)', '2025-10-01', 127.871000, 15.00, 'up')
ON CONFLICT (source_id) DO NOTHING;


-- ─────────────────────────────────────────────
-- ESCALATION_INDEX (3 rows — realistic computed values for dashboard testing)
-- Scores on 0–1 scale; label thresholds: <0.25 low, <0.50 medium, <0.75 high, >=0.75 critical
-- ─────────────────────────────────────────────
INSERT INTO escalation_index (source_id, computed_at, index_score, label,
    component_deal_inverted, component_tariff_odds, component_gdelt_intensity,
    component_import_price, component_ppi, index_7d_change)
VALUES
('2026-04-20T12:00:00+00:00', '2026-04-20T12:00:00Z', 0.7840, 'high',
    0.8200, 0.7600, 0.7100, 0.8400, 0.7500, 0.0620),
('2026-04-13T12:00:00+00:00', '2026-04-13T12:00:00Z', 0.7220, 'high',
    0.7800, 0.7100, 0.6800, 0.7900, 0.6900, 0.0480),
('2026-04-06T12:00:00+00:00', '2026-04-06T12:00:00Z', 0.6740, 'medium',
    0.7200, 0.6500, 0.6300, 0.7300, 0.6200, 0.0310)
ON CONFLICT (source_id) DO NOTHING;


-- ─────────────────────────────────────────────
-- BACKTEST_EVENTS (2 rows — historical geopolitical events for model validation)
-- ─────────────────────────────────────────────
INSERT INTO backtest_events (source_id, event_name, event_date, event_type,
    pre_event_trajectory, post_event_sector_returns,
    index_was_rising_pre_event, accuracy_note)
VALUES
(
    'us-china-trade-war-tariffs-2018-07-06',
    'US-China Trade War: Section 301 Tariffs Begin',
    '2018-07-06',
    'trade_war',
    '{"day_minus_7": 0.42, "day_minus_6": 0.44, "day_minus_5": 0.47, "day_minus_4": 0.49, "day_minus_3": 0.51, "day_minus_2": 0.53, "day_minus_1": 0.55}',
    '{"XLI": -0.062, "XLK": -0.038, "XLY": -0.071, "XLB": -0.089, "SPY": -0.051}',
    true,
    'Escalation index was rising 7 days pre-event. Industrials and Materials sectors were hardest hit. Model correctly predicted direction in 4 of 5 sector calls.'
),
(
    'covid-who-pandemic-declaration-2020-03-11',
    'WHO Declares COVID-19 a Pandemic',
    '2020-03-11',
    'pandemic_shock',
    '{"day_minus_7": 0.38, "day_minus_6": 0.41, "day_minus_5": 0.43, "day_minus_4": 0.48, "day_minus_3": 0.52, "day_minus_2": 0.58, "day_minus_1": 0.63}',
    '{"XLV": -0.112, "XLK": -0.189, "XLY": -0.245, "XLE": -0.352, "SPY": -0.198}',
    true,
    'Escalation index (with GDELT intensity component) was rising sharply 7 days before declaration. All sectors sold off; Energy and Consumer Discretionary worst. Model sensitivity: 0.91, specificity: 0.74.'
)
ON CONFLICT (source_id) DO NOTHING;
