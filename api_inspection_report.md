# GeoBeta API Inspection Report

Inspected: 2026-04-20  
Inspector: Claude (data engineer setup pass)

---

## 1. Polymarket (`https://clob.polymarket.com/markets`)

### Response shape
```
{
  "data": [ Market, Market, ... ]
}
```
Flat array nested under `data`. No top-level count or pagination fields were observed in the live response (docs reference `next_cursor` but the field was absent in production). The endpoint appears to return all markets in a single response (~hundreds of records).

### Fields used
| Field | Raw Type | Target Column | Notes |
|-------|----------|---------------|-------|
| `condition_id` | string | `source_market_id` | Ethereum condition ID, used as market identifier |
| `question` | string | `question` | Free-text prediction question |
| `tokens[].price` | number (0–1) | `odds` | Take the "Yes" token price as the YES probability |
| `tokens[].outcome` | string | — | Used to identify which token is YES |
| `end_date_iso` | ISO 8601 string | `expiry_date` | Parse with `fromisoformat()` → TIMESTAMPTZ |
| `tags` | string[] | `sector_tags` | Array of category strings; stored as JSONB |
| `active` | boolean | — | Used as filter; stored in `market_status` |
| `closed` | boolean | `market_status` | "active", "closed", or derived from flags |

### Fields ignored
`fpmm`, `market_slug`, `question_id`, `description`, `icon`, `image`, `neg_risk*`, `rewards`, `minimum_order_size`, `minimum_tick_size`, `maker_base_fee`, `taker_base_fee`, `game_start_time`, `seconds_delay`, `is_50_50_outcome`, `notifications_enabled`, `enable_order_book`, `accepting_orders`, `accepting_order_timestamp`

### Type coercions
- `tokens[].price` → NUMERIC(5,4) (already 0–1 float; no rescaling needed)
- `end_date_iso` → `TIMESTAMPTZ` via `datetime.fromisoformat()`
- `tags` → stored as JSONB (list of strings)

### Data quality issues
- `accepting_order_timestamp` is consistently `null` across all observed records
- `rewards.rates` is consistently `null`
- `neg_risk_market_id` and `neg_risk_request_id` are frequently empty strings (not null)
- Some archived markets have empty `condition_id`, `question_id`, `fpmm` — treat these as junk rows and skip on ingest
- `volume` is not available on the `/markets` endpoint; a separate CLOB endpoint is needed
- The first page of results contains primarily historical (closed) sports betting markets; macro/geopolitical markets exist further in the dataset

### Assumptions
- YES probability = `tokens[i].price` where `tokens[i].outcome.lower() in {"yes", "1", "true"}`
- `source_id` = `"polymarket_" + condition_id`

---

## 2. Kalshi (`https://trading.kalshi.com/trade-api/v2/markets?status=open&limit=10`)

### Response shape
```
{
  "markets": [ Market, Market, ... ],
  "cursor": "eyJh..."
}
```
Cursor-based pagination. Pass `cursor` value as query param in subsequent requests. Empty cursor = no more pages.

### Access status
The domain `trading.kalshi.com` was unreachable during inspection (DNS resolution failure). Schema documented from official Kalshi API v2 reference docs. All field types verified against the OpenAPI specification.

### Fields used
| Field | Raw Type | Target Column | Notes |
|-------|----------|---------------|-------|
| `ticker` | string | `source_market_id` | Kalshi market identifier |
| `yes_bid_dollars` | string (FixedPointDollars) | — | Input to odds calculation |
| `yes_ask_dollars` | string (FixedPointDollars) | — | Input to odds calculation |
| `last_price_dollars` | string (FixedPointDollars) | `odds` | Mid-price fallback |
| `volume_fp` | string (FixedPointCount) | `volume` | Trading volume |
| `close_time` | ISO 8601 string | `expiry_date` | Market expiration |
| `rules_primary` | string | `question` | Market question/rules |
| `status` | enum string | `market_status` | active, closed, finalized, etc. |

### Fields ignored
`event_ticker`, `market_type`, `no_bid_dollars`, `no_ask_dollars`, `settlement_timer_seconds`, `previous_*`, `open_interest_fp`, `notional_value_dollars`, `result`, `can_close_early`, `fractional_trading_enabled`, `expiration_value`, `rules_secondary`, `price_level_structure`, `price_ranges`, `mve_*`, `functional_strike`, `custom_strike`, `floor_strike`, `cap_strike`, `primary_participant_key`, `is_provisional`

### Type coercions
- All FixedPointDollars fields: `float(str_value)` → stored as NUMERIC(5,4) (already 0–1 scale in dollar terms; Kalshi YES contracts are priced $0–$1)
- All FixedPointCount fields: `float(str_value)` → NUMERIC(18,4)
- `close_time` → TIMESTAMPTZ via `datetime.fromisoformat()`

### Odds calculation
`odds = (float(yes_bid_dollars) + float(yes_ask_dollars)) / 2`  
Fall back to `float(last_price_dollars)` if bid/ask are both zero.

### Data quality issues
- All numeric fields returned as strings with fixed decimal precision (6dp for dollars, 2dp for counts) — must never use as native JSON numbers
- Several nullable fields (`expected_expiration_time`, `settlement_ts`, `occurrence_datetime`) may be absent from response entirely — use `.get()` in pipeline
- `result` field is empty string `""` for unresolved markets (not null or "pending")

### Assumptions
- `source_id` = `"kalshi_" + ticker`
- `category` inferred from `event_ticker` prefix (e.g. `"KXFED"` → `"monetary_policy"`)

---

## 3. GDELT (`https://api.gdeltproject.org/api/v2/geo/geo?query=tariff&mode=artlist`)

### Response shape
```
{
  "articles": [ Article, Article, ... ]
}
```
No pagination. Controlled by `maxrecords` request parameter (max 250). Rate-limited to approximately 1 request per 5 seconds per IP.

### Fields used
| Field | Raw Type | Target Column | Notes |
|-------|----------|---------------|-------|
| `url` | string | `source_url` | Full article URL; MD5 used as `source_id` |
| `title` | string | `headline` | Article headline |
| `seendate` | string (YYYYMMDDTHHMMSSZ) | `event_timestamp` | Parse with `datetime.strptime(v, "%Y%m%dT%H%M%SZ")` → UTC TIMESTAMPTZ |
| `domain` | string | `domain` | Source domain (no protocol) |
| `sourcecountry` | string | `country` | Country name string (not ISO code) |
| `language` | string | `language` | Language of article |

### Fields not returned in artlist mode
- `tone` (comma-delimited tone string) — only in events/GKG mode
- `goldstein_scale` — only in events mode
- Geographic coordinates — only in geo mode with specific parameters

### Fields ignored
`url_mobile`, `socialimage`

### Type coercions
- `seendate` ("20260419T233000Z") → TIMESTAMPTZ: `datetime.strptime(seendate, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)`
- `sourcecountry` stored as-is (TEXT); normalize to ISO-3166 alpha-2 in a future enrichment pass if needed

### Data quality issues
- `tone` field is absent from `artlist` mode; to get tone, switch to `mode=tonechart` or use the GKG 2.0 endpoint
- `goldstein_scale` is entirely absent from geo/artlist responses
- `severity` column must be computed by the pipeline (e.g., from tone sign, keyword density, or goldstein scale via a separate fetch)
- Geographic coordinates not returned in artlist mode; lat/lon must be geocoded from `sourcecountry` or enriched from a separate GDELT geo query
- Language filtering is unreliable — searching for English-language "tariff" news also returns Arabic "taxi fare" (tعريفة) articles
- Rate limiting at scale requires exponential backoff; batch imports need ~250 requests/20 min for full daily coverage

### Assumptions
- `source_id` = `hashlib.md5(url.encode()).hexdigest()`
- `severity` will be computed downstream, initially NULL
- Affected tickers and sectors are tagged manually or via an NLP enrichment step

---

## 4. FRED (`https://api.stlouisfed.org/fred/series/observations`)

### Response shape
```
{
  "realtime_start": "YYYY-MM-DD",
  "realtime_end": "YYYY-MM-DD",
  "observation_start": "YYYY-MM-DD",
  "observation_end": "YYYY-MM-DD",
  "units": "...",
  "output_type": 1,
  "file_type": "json",
  "order_by": "observation_date",
  "sort_order": "asc",
  "count": 999,
  "offset": 0,
  "limit": 100000,
  "observations": [ { "realtime_start", "realtime_end", "date", "value" }, ... ]
}
```

Offset-based pagination. `count` field tells total rows available; default limit is 100,000 (handles most series in one request).

### Fields used
| Field | Raw Type | Target Column | Notes |
|-------|----------|---------------|-------|
| `date` | "YYYY-MM-DD" string | `observation_date` | Parse to DATE |
| `value` | numeric string or "." | `value` | Cast to NUMERIC; "." or "" → NULL |

### Fields ignored
`realtime_start`, `realtime_end` (per-observation vintage tracking), top-level metadata fields

### Type coercions
- `value`: `None if v in (".", "") else Decimal(v)`
- `date`: `datetime.strptime(d, "%Y-%m-%d").date()`

### Data quality issues
- Empty observations use `"."` as the value string (not JSON null, not empty string) — must explicitly handle
- UNRATE for 2025-10-01 returned `"."` in the live fetch on 2026-04-20; stored as NULL
- Some series have sporadic missing observations; the pipeline must not fail on NULL values
- FRED API key required; free registration at https://fred.stlouisfed.org/docs/api/api_key.html

### Assumptions
- `source_id` = `f"{series_id}_{observation_date}"` (e.g., `"UNRATE_2026-03-01"`)
- `series_name` populated from a separate `/fred/series` metadata call or hardcoded per series
- `trend_score` and `direction` computed by the pipeline after ingestion (e.g., 12-month z-score)

### Live data fetched (UNRATE, 2026-04-20)
| Date | Value |
|------|-------|
| 2026-03-01 | 4.3 |
| 2026-02-01 | 4.4 |
| 2026-01-01 | 4.3 |
| 2025-12-01 | 4.4 |
| 2025-11-01 | 4.5 |
| 2025-10-01 | . (NULL) |

### Live data fetched (PCEPI, 2026-04-20)
| Date | Value |
|------|-------|
| 2026-02-01 | 129.449 |
| 2026-01-01 | 128.965 |
| 2025-12-01 | 128.576 |
| 2025-11-01 | 128.152 |
| 2025-10-01 | 127.871 |

---

## 5. Alpha Vantage (`TIME_SERIES_DAILY_ADJUSTED`)

### Access note
`TIME_SERIES_DAILY_ADJUSTED` requires a premium subscription ($50+/month). The free-tier key (Z3PB9ZPRZVHKU746) returns only `TIME_SERIES_DAILY`. Seed data uses `TIME_SERIES_DAILY`; adjusted close is set equal to close price until premium access is established.

### Response shape
```
{
  "Meta Data": {
    "1. Information": "Daily Prices ...",
    "2. Symbol": "AAPL",
    "3. Last Refreshed": "YYYY-MM-DD",
    "4. Output Size": "Compact",
    "5. Time Zone": "US/Eastern"
  },
  "Time Series (Daily)": {
    "YYYY-MM-DD": {
      "1. open": "195.20",
      "2. high": "197.50",
      "3. low": "193.80",
      "4. close": "196.40",
      "5. volume": "72341200"
    },
    ...
  }
}
```

For `TIME_SERIES_DAILY_ADJUSTED` (premium), the date object also includes:
- `"5. adjusted close"`, `"6. volume"`, `"7. dividend amount"`, `"8. split coefficient"`

### Fields used
| Field | Raw Type | Target Column | Notes |
|-------|----------|---------------|-------|
| date key | string (YYYY-MM-DD) | `price_date` | Top-level key of time series object |
| `"1. open"` | numeric string | `open_price` | |
| `"2. high"` | numeric string | `high_price` | |
| `"3. low"` | numeric string | `low_price` | |
| `"4. close"` | numeric string | `close_price` | |
| `"5. volume"` | integer string | `volume` | |
| `"Meta Data"."2. Symbol"` | string | `ticker` | |

### Fields ignored
`"Meta Data"."1. Information"`, `"Meta Data"."3. Last Refreshed"`, `"Meta Data"."4. Output Size"`, `"Meta Data"."5. Time Zone"`

### Type coercions
- All price fields: `Decimal(str_value)` → NUMERIC(12,4)
- `volume`: `int(str_value)` → BIGINT
- date key: `datetime.strptime(key, "%Y-%m-%d").date()` → DATE

### Data quality issues
- **All numeric values are strings** — never use raw JSON values without casting
- Compact output = 100 most recent trading days; full output = 20+ years (watch response size)
- `TIME_SERIES_DAILY_ADJUSTED` is a premium endpoint; free-tier keys receive an `"Information"` error message instead of data
- Weekends and market holidays are absent from the time series (not stored as null rows)
- Alpha Vantage rate-limits free keys to 25 requests/day, 5 requests/minute

### Assumptions
- `source_id` = `f"{ticker}_{price_date}"` (e.g., `"AAPL_2026-04-17"`)
- `adjusted_close = close_price` until premium endpoint is enabled
- `dividend_amount = 0`, `split_coefficient = 1` until premium endpoint is enabled

### Live data fetched (2026-04-20, TIME_SERIES_DAILY)
| Ticker | Date | Open | High | Low | Close | Volume |
|--------|------|------|------|-----|-------|--------|
| AAPL | 2026-04-17 | 266.96 | 272.30 | 266.72 | 270.23 | 61,436,228 |
| AAPL | 2026-04-16 | 266.80 | 267.16 | 261.27 | 263.40 | 43,323,112 |
| AAPL | 2026-04-15 | 258.16 | 266.56 | 257.81 | 266.43 | 49,913,510 |
| TSLA | 2026-04-17 | 395.92 | 409.28 | 391.65 | 400.62 | 90,640,032 |
| TSLA | 2026-04-16 | 393.81 | 394.06 | 381.80 | 388.90 | 63,515,136 |
| TSLA | 2026-04-15 | 366.83 | 394.65 | 362.50 | 391.95 | 113,810,355 |
| NVDA | 2026-04-17 | 199.90 | 201.70 | 199.27 | 201.68 | 160,324,416 |
| NVDA | 2026-04-16 | 197.43 | 199.85 | 195.81 | 198.35 | 134,012,859 |
| NVDA | 2026-04-15 | 196.54 | 200.40 | 195.74 | 198.87 | 185,338,388 |
| CAT | 2026-04-17 | 780.51 | 801.77 | 776.00 | 794.65 | 2,818,838 |
| CAT | 2026-04-16 | 768.00 | 772.81 | 754.45 | 772.66 | 2,005,066 |
| CAT | 2026-04-15 | 787.10 | 789.97 | 756.65 | 770.17 | 2,764,742 |
| NKE | 2026-04-17 | 46.38 | 46.78 | 45.78 | 46.03 | 31,290,385 |
| NKE | 2026-04-16 | 45.80 | 46.49 | 45.55 | 45.70 | 21,766,281 |
| NKE | 2026-04-15 | 45.09 | 45.90 | 44.71 | 45.44 | 31,523,472 |

---

## Cross-Source Normalization Decisions

| Concept | Polymarket field | Kalshi field | Unified column | Normalization |
|---------|-----------------|--------------|----------------|---------------|
| Market probability | `tokens[].price` | `(yes_bid + yes_ask) / 2` | `odds` NUMERIC(5,4) | Both sources already on 0–1 scale |
| Market expiry | `end_date_iso` | `close_time` | `expiry_date` TIMESTAMPTZ | Both ISO 8601; parse with fromisoformat |
| Market ID | `condition_id` | `ticker` | `source_market_id` | Store platform-native ID as TEXT |
| Category tags | `tags` array | derived from `event_ticker` | `sector_tags` JSONB | Normalized in pipeline |
| Volume | not in /markets | `volume_fp` (string) | `volume` NUMERIC(18,4) | Cast `float(str)` for Kalshi |

| Concept | FRED field | Alpha Vantage field | GDELT field | Unified handling |
|---------|-----------|---------------------|-------------|-----------------|
| Timestamp | `date` (YYYY-MM-DD) | date key (YYYY-MM-DD) | `seendate` (YYYYMMDDTHHMMSSZ) | All → UTC; GDELT needs custom strptime |
| Numeric value | `value` (string, "." for null) | all fields (strings) | tone (comma string, first element) | All cast to Decimal; "." → None |
| Country | — | — | `sourcecountry` (name string) | Store as TEXT; future: map to ISO-3166 |
