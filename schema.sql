-- GeoBeta Unified Schema
-- Target: Neon Postgres
-- Apply: psql $NEON_DATABASE_URL -f schema.sql
-- Sources: Polymarket, Kalshi, GDELT, FRED, Alpha Vantage

-- ─────────────────────────────────────────────
-- COMPANIES
-- One row per S&P 500 company. Written daily or on filing change.
-- Tariff exposure scores and confidence fields are computed externally.
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS companies (
    id                      BIGSERIAL PRIMARY KEY,
    source_id               TEXT UNIQUE NOT NULL,          -- ticker.lower()
    ticker                  TEXT NOT NULL,
    company_name            TEXT NOT NULL,
    sector                  TEXT,
    sub_sector              TEXT,
    tariff_exposure_score   NUMERIC(5,2),
    exposure_level          TEXT,                          -- 'low' | 'medium' | 'high' | 'critical'
    confidence_level        TEXT,                          -- 'low' | 'medium' | 'high'
    confidence_reason       TEXT,
    regions                 JSONB,                         -- e.g. {"China": 0.35, "EU": 0.20}
    exposure_pct_map        JSONB,                         -- tariff exposure breakdown by region
    key_filing_quote        TEXT,
    filing_date             DATE,
    filing_type             TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_companies_ticker      ON companies (ticker);
CREATE INDEX IF NOT EXISTS idx_companies_sector      ON companies (sector);
CREATE INDEX IF NOT EXISTS idx_companies_exposure    ON companies (exposure_level);


-- ─────────────────────────────────────────────
-- STOCK_PRICES
-- One row per ticker per trading day. Written daily from Alpha Vantage.
-- ticker is denormalized (TEXT, not FK) so prices can load before company rows exist.
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS stock_prices (
    id                              BIGSERIAL PRIMARY KEY,
    source_id                       TEXT UNIQUE NOT NULL,  -- "{ticker}_{price_date}"
    ticker                          TEXT NOT NULL,
    price_date                      DATE NOT NULL,
    open_price                      NUMERIC(12,4),
    high_price                      NUMERIC(12,4),
    low_price                       NUMERIC(12,4),
    close_price                     NUMERIC(12,4) NOT NULL,
    adjusted_close                  NUMERIC(12,4),
    volume                          BIGINT,
    dividend_amount                 NUMERIC(10,4),
    split_coefficient               NUMERIC(10,6),
    price_delta_liberation_day_pct  NUMERIC(8,4),
    market_reaction_score           NUMERIC(5,2),
    reaction_score_adj              NUMERIC(5,2),
    created_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_stock_prices_ticker_date ON stock_prices (ticker, price_date);
CREATE INDEX IF NOT EXISTS idx_stock_prices_date               ON stock_prices (price_date);
CREATE INDEX IF NOT EXISTS idx_stock_prices_ticker             ON stock_prices (ticker);


-- ─────────────────────────────────────────────
-- PREDICTION_MARKETS
-- One snapshot row per market per ingestion run. Written every 15 min.
-- source = 'polymarket' | 'kalshi'
-- odds = YES probability normalized to 0.0000–1.0000
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS prediction_markets (
    id                  BIGSERIAL PRIMARY KEY,
    source_id           TEXT UNIQUE NOT NULL,  -- "{source}_{source_market_id}"
    source              TEXT NOT NULL,          -- 'polymarket' | 'kalshi'
    source_market_id    TEXT NOT NULL,
    question            TEXT NOT NULL,
    odds                NUMERIC(5,4),           -- YES probability 0.0000–1.0000
    volume              NUMERIC(18,4),
    expiry_date         TIMESTAMPTZ,
    sector_tags         JSONB,                  -- e.g. ["trade", "tariffs"]
    ticker_tags         JSONB,                  -- e.g. ["AAPL", "TSLA"]
    odds_7d_change      NUMERIC(5,4),
    category            TEXT,
    market_status       TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_pm_source_market ON prediction_markets (source, source_market_id);
CREATE INDEX IF NOT EXISTS idx_pm_expiry               ON prediction_markets (expiry_date);
CREATE INDEX IF NOT EXISTS idx_pm_category             ON prediction_markets (category);
CREATE INDEX IF NOT EXISTS idx_pm_source               ON prediction_markets (source);


-- ─────────────────────────────────────────────
-- GEOPOLITICAL_EVENTS
-- One row per GDELT article, deduplicated by URL hash. Written every 15 min.
-- goldstein_scale is nullable (artlist mode doesn't return it; event mode does).
-- severity is computed from tone and goldstein_scale in the pipeline.
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS geopolitical_events (
    id                  BIGSERIAL PRIMARY KEY,
    source_id           TEXT UNIQUE NOT NULL,  -- md5(source_url)
    source_event_id     TEXT,
    headline            TEXT NOT NULL,
    lat                 NUMERIC(9,6),
    lon                 NUMERIC(9,6),
    country             TEXT,
    severity            NUMERIC(5,2),
    goldstein_scale     NUMERIC(5,2),
    tone                NUMERIC(5,2),
    affected_tickers    JSONB,
    affected_sectors    JSONB,
    source_url          TEXT,
    domain              TEXT,
    language            TEXT,
    event_timestamp     TIMESTAMPTZ NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_severity_ts ON geopolitical_events (severity, event_timestamp);
CREATE INDEX IF NOT EXISTS idx_events_country     ON geopolitical_events (country);
CREATE INDEX IF NOT EXISTS idx_events_ts          ON geopolitical_events (event_timestamp DESC);


-- ─────────────────────────────────────────────
-- MACRO_SIGNALS
-- One row per FRED series per observation date. Written daily.
-- value is NUMERIC; empty-string FRED values are stored as NULL.
-- trend_score and direction are computed by the pipeline after ingestion.
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS macro_signals (
    id                  BIGSERIAL PRIMARY KEY,
    source_id           TEXT UNIQUE NOT NULL,  -- "{series_id}_{observation_date}"
    series_id           TEXT NOT NULL,
    series_name         TEXT,
    observation_date    DATE NOT NULL,
    value               NUMERIC(18,6),
    trend_score         NUMERIC(5,2),
    direction           TEXT,                  -- 'up' | 'down' | 'flat'
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_macro_series_date ON macro_signals (series_id, observation_date);
CREATE INDEX IF NOT EXISTS idx_macro_series             ON macro_signals (series_id);
CREATE INDEX IF NOT EXISTS idx_macro_obs_date           ON macro_signals (observation_date DESC);


-- ─────────────────────────────────────────────
-- ESCALATION_INDEX
-- One row per computation run. Written every 15 min by the scoring pipeline.
-- All component scores are on 0.0000–1.0000 scale before weighting.
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS escalation_index (
    id                          BIGSERIAL PRIMARY KEY,
    source_id                   TEXT UNIQUE NOT NULL,  -- computed_at::text
    computed_at                 TIMESTAMPTZ NOT NULL,
    index_score                 NUMERIC(5,4),
    label                       TEXT,                  -- 'low' | 'medium' | 'high' | 'critical'
    component_deal_inverted     NUMERIC(5,4),
    component_tariff_odds       NUMERIC(5,4),
    component_gdelt_intensity   NUMERIC(5,4),
    component_import_price      NUMERIC(5,4),
    component_ppi               NUMERIC(5,4),
    index_7d_change             NUMERIC(5,4),
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_escalation_computed ON escalation_index (computed_at DESC);


-- ─────────────────────────────────────────────
-- BACKTEST_EVENTS
-- One row per historical geopolitical/macro event used for backtesting.
-- Written manually or via a batch historical loader.
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS backtest_events (
    id                          BIGSERIAL PRIMARY KEY,
    source_id                   TEXT UNIQUE NOT NULL,
    event_name                  TEXT NOT NULL,
    event_date                  DATE NOT NULL,
    event_type                  TEXT,                  -- 'trade_war' | 'covid' | 'fed_pivot' | 'sanctions' etc.
    pre_event_trajectory        JSONB,                 -- escalation index values in 7 days before
    post_event_sector_returns   JSONB,                 -- sector ETF returns 30 days after
    index_was_rising_pre_event  BOOLEAN,
    accuracy_note               TEXT,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_backtest_date ON backtest_events (event_date);
CREATE INDEX IF NOT EXISTS idx_backtest_type ON backtest_events (event_type);


-- ═════════════════════════════════════════════════════════════════
-- USEFUL QUERIES FOR ZERVE BLOCKS
-- ═════════════════════════════════════════════════════════════════

-- 1. Screener: top 50 companies by tariff exposure score with latest price
--    SELECT c.ticker, c.company_name, c.sector, c.tariff_exposure_score,
--           c.exposure_level, c.confidence_level,
--           sp.close_price, sp.price_date, sp.price_delta_liberation_day_pct
--    FROM companies c
--    LEFT JOIN LATERAL (
--        SELECT close_price, price_date, price_delta_liberation_day_pct
--        FROM stock_prices WHERE ticker = c.ticker
--        ORDER BY price_date DESC LIMIT 1
--    ) sp ON true
--    ORDER BY c.tariff_exposure_score DESC NULLS LAST
--    LIMIT 50;

-- 2. Active prediction markets sorted by tariff relevance
--    SELECT source, question, odds, volume, expiry_date, odds_7d_change, category
--    FROM prediction_markets
--    WHERE expiry_date > NOW()
--    ORDER BY odds DESC;

-- 3. Recent high-severity geopolitical events
--    SELECT headline, country, severity, tone, event_timestamp, source_url
--    FROM geopolitical_events
--    WHERE severity >= 7
--    ORDER BY event_timestamp DESC
--    LIMIT 20;

-- 4. Escalation index time series (last 30 days)
--    SELECT computed_at, index_score, label,
--           component_tariff_odds, component_gdelt_intensity, index_7d_change
--    FROM escalation_index
--    WHERE computed_at >= NOW() - INTERVAL '30 days'
--    ORDER BY computed_at ASC;

-- 5. Macro signals for a specific series
--    SELECT observation_date, value, trend_score, direction
--    FROM macro_signals
--    WHERE series_id = 'UNRATE'
--    ORDER BY observation_date DESC
--    LIMIT 24;
