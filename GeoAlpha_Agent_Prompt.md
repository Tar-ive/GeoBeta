# GeoAlpha — AI Agent Development Prompt
## Skeleton Build: Local + GitHub + Zerve

---

## What you are building

GeoAlpha is a live geopolitical risk intelligence terminal. It answers:
1. Which S&P 500 companies are most exposed to current tariff regimes based on their SEC filings?
2. Has the stock market priced that exposure in — or is there a gap?
3. What do prediction markets say about where the trade war goes next?

The system is already partially set up:
- Neon Postgres database is live and schema has been applied
- All API keys have been acquired (Polymarket, Kalshi, FRED, Alpha Vantage, GDELT, Anthropic, SEC EDGAR)
- The unified data model has been designed

Your job is to build the full skeleton codebase — locally, structured for GitHub, with clear seams
between what runs locally vs what runs inside Zerve.

---

## Architecture (from whiteboard diagram)

The whiteboard shows this data flow:

```
[Data Sources]
  EDGAR / Polymarket / Kalshi / GDELT / FRED / Alpha Vantage
        ↓
[Zerve Notebook Blocks in Canvas — calling APIs]
        ↓
  [Scheduled Job] ←——— triggers refresh
        ↓
[Cached Data] (Neon Postgres — persisted between Zerve runs)
        ↓
  [Geopolitical Map block] ←— feeds into
        ↓
[Zerve / GeoBeta Middleware — FastAPI]  →→→  [Alerts / Dashboard]
        ↓
[Analysis Engine]
        ↓
[Prediction Model — pretrained from Hugging Face]
        ↓
[Weights] (stored, versioned)
        ↓
[Streamlit Dashboard] containing:
  - Escalation Index
  - Mispriced Stocks
  - Prediction Market Screener
  - GEO MAP
  - Sector / Stock Heatmap
  - Backtesting

Also in Zerve canvas (shown as GenAI star shape):
  - Supply Chain Analyzer (LLM block)
  - Escalation Index Calculation (diamond shape = computation node)

Zerve legend from whiteboard:
  Rectangle = Assets
  Star = GenAI block
  Cylinder = Cron Job (Scheduled Job)
```

Additional demo notes on whiteboard (features to highlight in demo):
1. Backtested System
2. Pentagon Pizza (unknown reference — likely a test dataset or internal joke name)
3. Polymarket Egg (likely Polymarket integration demo)
4. Trump TruthSocial Post (likely a social signal data source or demo scenario)

---

## Where to build what — the local vs Zerve split

This is the core decision. Here is the rule:

**Build locally (Python repo on GitHub) if:**
- The code is reusable logic (data parsers, scoring functions, DB clients, API wrappers)
- The code needs to be version controlled and tested
- It is the Streamlit app
- It is the FastAPI middleware layer
- It is anything Dev B (frontend) touches

**Build inside Zerve canvas (not in this repo) if:**
- It is a DAG block that passes DataFrames to the next block
- It is a GenAI block (supply chain extractor)
- It is a Scheduled Job trigger
- It runs on Zerve's compute (Fleet parallelization)

**The bridge:** Zerve blocks import from this GitHub repo using Zerve's Git integration.
That means all the logic lives here as importable Python modules. Zerve blocks are thin —
they import from this repo and call one function. The heavy logic is testable locally.

---

## Repository structure to build

```
geopolitical-alpha/
│
├── README.md
├── .env.example
├── requirements.txt
├── requirements-dev.txt
│
├── db/
│   ├── __init__.py
│   ├── client.py              # DB connection + all read/write functions
│   ├── models.py              # Pydantic models matching Postgres schema
│   └── upsert.py              # Idempotent upsert helpers
│
├── ingestion/
│   ├── __init__.py
│   ├── edgar.py               # EDGAR fetcher + text chunker
│   ├── alpha_vantage.py       # Stock price fetcher
│   ├── polymarket.py          # Polymarket odds fetcher
│   ├── kalshi.py              # Kalshi odds fetcher
│   ├── gdelt.py               # GDELT event fetcher
│   └── fred.py                # FRED macro data fetcher
│
├── scoring/
│   ├── __init__.py
│   ├── exposure.py            # Tariff Exposure Score calculation
│   ├── reaction.py            # Market Reaction Score + gap calculation
│   ├── escalation.py          # Escalation Index formula
│   └── confidence.py          # Confidence level rating logic
│
├── nlp/
│   ├── __init__.py
│   ├── extractor.py           # LLM prompt + parsing for supply chain extraction
│   └── screener.py            # NLP query → structured filters
│
├── backtest/
│   ├── __init__.py
│   ├── historical.py          # Historical escalation index calculation
│   └── analyzer.py            # Backtest accuracy analysis
│
├── api/
│   ├── __init__.py
│   ├── main.py                # FastAPI app (the middleware layer)
│   ├── routes/
│   │   ├── company.py         # GET /company-risk
│   │   ├── screener.py        # GET /screener
│   │   ├── escalation.py      # GET /escalation-index
│   │   ├── events.py          # GET /events
│   │   ├── nlp.py             # POST /nlp-query
│   │   └── backtest.py        # GET /backtest
│   └── middleware.py          # Auth, rate limiting, staleness checks
│
├── dashboard/
│   ├── app.py                 # Main Streamlit entry point
│   ├── api_client.py          # HTTP client wrapping FastAPI routes
│   ├── mock_api.py            # Mock data for offline dev (full mock dataset)
│   └── components/
│       ├── __init__.py
│       ├── map.py             # Plotly world map
│       ├── screener.py        # Company screener table
│       ├── panel.py           # Explainability side panel
│       ├── gauge.py           # Escalation index gauge
│       ├── heatmap.py         # Sector/stock heatmap
│       ├── backtest.py        # Historical backtesting charts
│       └── nlp_input.py       # Natural language screener input
│
├── zerve/
│   ├── README.md              # Instructions for importing this repo into Zerve
│   ├── blocks/
│   │   ├── block_a1_tickers.py        # Paste into Zerve block A1
│   │   ├── block_a2_edgar.py          # Paste into Zerve block A2
│   │   ├── block_a3_chunker.py        # Paste into Zerve block A3
│   │   ├── block_a5_scorer.py         # Paste into Zerve block A5
│   │   ├── block_b1_prices.py         # Paste into Zerve block B1
│   │   ├── block_b3_reaction.py       # Paste into Zerve block B3
│   │   ├── block_c1_gdelt.py          # Paste into Zerve block C1
│   │   ├── block_c2_enricher.py       # Paste into Zerve block C2
│   │   ├── block_d1_polymarket.py     # Paste into Zerve block D1
│   │   ├── block_d2_kalshi.py         # Paste into Zerve block D2
│   │   ├── block_d3_markets.py        # Paste into Zerve block D3
│   │   ├── block_e1_fred.py           # Paste into Zerve block E1
│   │   ├── block_e2_macro.py          # Paste into Zerve block E2
│   │   ├── block_f_backtest.py        # Paste into Zerve backtest blocks
│   │   ├── block_g1_escalation.py     # Paste into Zerve block G1
│   │   └── block_g2_master.py         # Paste into Zerve block G2
│   └── genai_prompts/
│       ├── supply_chain_extractor.txt  # System prompt for GenAI block A4
│       └── nlp_screener.txt            # System prompt for NLP query route
│
└── tests/
    ├── __init__.py
    ├── test_edgar.py
    ├── test_scoring.py
    ├── test_escalation.py
    ├── test_db.py
    └── fixtures/
        ├── sample_filing.txt      # Sample EDGAR filing text for tests
        ├── sample_prices.json     # Sample Alpha Vantage response
        └── sample_events.json     # Sample GDELT response
```

---

## Build instructions — file by file

Build each file as a proper Python module with real skeleton implementations.
For each file, the skeleton should:
- Have all the function signatures defined
- Have docstrings explaining what each function does
- Have type hints on all arguments and return values
- Have the imports correct
- Have TODO comments where the actual implementation goes
- Have at least one working implementation per file (not all TODOs)
  so the import chain can be validated end-to-end

Do NOT write placeholder `pass` statements for everything. Each file should be
genuinely useful as a starting point, not just a stub.

---

### db/client.py

```python
"""
Neon Postgres client for GeoAlpha.
All Zerve blocks and the FastAPI layer import from this module.
Connection string is read from NEON_DATABASE_URL environment variable.

Usage in Zerve block:
    import sys
    sys.path.insert(0, '/path/to/geopolitical-alpha')  # or via Git import
    from db.client import read_screener, upsert_company
"""
```

Implement fully:
- `get_engine()` — SQLAlchemy engine using `NEON_DATABASE_URL` env var, with connection pooling
- `get_connection()` — psycopg2 connection (for bulk upserts)
- `read_table(table_name, filters=None, limit=None) -> pd.DataFrame`
- `read_screener(sort="gap_desc", sector=None, confidence=None, region=None, limit=50) -> pd.DataFrame`
  - sorts by gap_score desc by default
  - filters are additive WHERE clauses
  - returns joined data from companies + stock_prices
- `read_escalation_history(days=30) -> pd.DataFrame`
- `read_events(severity=None, country=None, limit=20) -> pd.DataFrame`
- `read_backtest() -> dict`
- `upsert_company(row: dict) -> None` — INSERT ... ON CONFLICT (ticker) DO UPDATE SET ...
- `upsert_stock_price(row: dict) -> None` — ON CONFLICT (ticker, price_date)
- `upsert_market(row: dict) -> None` — ON CONFLICT (source, source_market_id)
- `upsert_event(row: dict) -> None` — ON CONFLICT (source_event_id)
- `upsert_macro_signal(row: dict) -> None` — ON CONFLICT (series_id, observation_date)
- `upsert_escalation_index(row: dict) -> None` — always insert (time series, no conflict key)
- `check_freshness(table_name) -> dict` — returns {is_fresh, age_minutes, last_updated}

---

### ingestion/edgar.py

Implement fully:
- `get_cik(ticker: str) -> str | None` — lookup CIK from EDGAR company search
- `get_recent_filings(cik: str, forms: list[str], limit: int) -> list[dict]`
- `fetch_filing_text(cik: str, accession: str) -> str` — fetch + strip HTML
- `extract_relevant_sections(text: str) -> list[str]` — extract Item 1A, Item 7
- `chunk_text(text: str, chunk_size: int = 1800, overlap: int = 200) -> list[str]`
- `is_relevant_chunk(chunk: str) -> bool` — keyword filter
- `fetch_ticker(ticker: str) -> list[dict]` — full pipeline for one ticker,
  returns list of {ticker, filing_type, filing_date, chunk_text, chunk_index}
  This is the function Zerve block A2+A3 calls.

---

### ingestion/alpha_vantage.py

Implement fully:
- `fetch_daily_prices(ticker: str, api_key: str, start_date: str) -> pd.DataFrame`
- `compute_delta_from_date(prices_df: pd.DataFrame, anchor_date: str) -> float`
- `fetch_all_tickers(tickers: list[str], api_key: str) -> pd.DataFrame`
  — handles rate limiting with exponential backoff, returns combined DataFrame

---

### ingestion/polymarket.py

Implement fully:
- `fetch_markets(keywords: list[str]) -> list[dict]`
  — paginates through all markets, filters by keywords client-side
- `parse_market(raw: dict) -> dict`
  — normalizes to unified schema: {source, source_market_id, question, odds, volume, expiry_date, category}

---

### ingestion/kalshi.py

Implement fully:
- `fetch_markets(api_key: str, keywords: list[str]) -> list[dict]`
- `parse_market(raw: dict) -> dict` — same output schema as polymarket.parse_market

---

### ingestion/gdelt.py

Implement fully:
- `fetch_events(query: str = "tariff OR trade war OR sanction", timespan_minutes: int = 1440) -> list[dict]`
- `parse_event(raw: dict) -> dict`
  — normalizes to {source_event_id, headline, lat, lon, goldstein_scale, source_url, event_timestamp}

---

### ingestion/fred.py

Implement fully:
- `fetch_series(series_id: str, api_key: str, start_date: str) -> pd.DataFrame`
- `fetch_all_series(api_key: str) -> pd.DataFrame`
  — fetches IR, MANEMP, PPIFIS, BOGMBASE, USCPI
- `compute_trend_score(series_values: pd.Series, window_days: int = 30) -> dict`
  — returns {trend_score: float, direction: str, change_pct: float}

---

### scoring/exposure.py

Implement fully:
- `RISK_SCORE_MAP = {"LOW": 20, "MEDIUM": 45, "HIGH": 70, "CRITICAL": 90}`
- `score_from_extractions(extractions: list[dict]) -> dict`
  — takes list of GenAI block outputs per ticker, returns:
  {exposure_score, exposure_level, regions, exposure_pct_map, key_quote}
  — weights most recent filing 60%, prior 40%
- `exposure_level_from_score(score: int) -> str`
  — NONE (<15), LOW (<35), MEDIUM (<60), HIGH (<80), CRITICAL (≥80)

---

### scoring/reaction.py

Implement fully:
- `LIBERATION_DAY = "2025-04-02"`
- `compute_delta(prices_df: pd.DataFrame, ticker: str, anchor_date: str) -> float`
- `normalize_deltas(deltas: dict[str, float]) -> dict[str, int]`
  — normalizes across all tickers: most negative = 100, flat/positive = 0
- `compute_sector_adjustment(reaction_scores: pd.DataFrame) -> pd.DataFrame`
  — adds sector_avg_reaction and reaction_score_adj columns
- `compute_gap_score(exposure_score: int, reaction_score_adj: int) -> int`
- `gap_label(gap_score: int) -> str`
  — "underpriced risk" (>15), "fairly priced" (-15 to 15), "overpriced fear" (<-15)

---

### scoring/escalation.py

Implement fully:
- `WEIGHTS = {"deal_inverted": 0.30, "tariff_odds": 0.25, "gdelt": 0.20, "import_price": 0.15, "ppi": 0.10}`
- `compute_escalation_index(markets_df, events_df, macro_df) -> dict`
  — returns {index_score, label, components, computed_at}
- `escalation_label(score: int) -> str` — "calm" (<30), "elevated" (<60), "crisis" (≥60)
- `compute_gdelt_intensity(events_df: pd.DataFrame) -> float` — 0–100 normalized

---

### scoring/confidence.py

Implement fully:
- `compute_confidence(signals_list: list[dict]) -> tuple[str, str]`
  — takes list of confidence_signals dicts from GenAI block
  — returns (level, reason) where level is "High" / "Medium" / "Low"
- `HIGH_CONFIDENCE_CRITERIA` — dict defining what makes a High confidence score

---

### nlp/extractor.py

Implement fully:
- `SUPPLY_CHAIN_SYSTEM_PROMPT` — the full system prompt string (copy from spec)
- `extract_supply_chain(chunk_text: str, client: anthropic.Anthropic) -> dict`
  — calls claude-sonnet-4-20250514, parses JSON response, returns extraction dict
- `batch_extract(chunks: list[str], client: anthropic.Anthropic) -> list[dict]`
  — processes list of chunks, handles errors per-chunk gracefully

---

### nlp/screener.py

Implement fully:
- `NLP_SCREENER_SYSTEM_PROMPT` — the full system prompt string (copy from spec)
- `parse_nlp_query(query: str, client: anthropic.Anthropic) -> dict`
  — returns {sectors, regions, min_exposure_score, sort, interpreted_summary}
- `apply_filters(master_df: pd.DataFrame, filters: dict) -> pd.DataFrame`
  — applies parsed filters to dataframe, returns sorted results

---

### backtest/historical.py

Implement fully:
- `HISTORICAL_EVENTS` — list of 4 dicts with event metadata (copy from spec)
- `compute_index_on_date(date: str, hist_macro_df: pd.DataFrame) -> int`
  — no-lookahead escalation index using only macro data available on that date
- `compute_full_history(hist_macro_df: pd.DataFrame) -> pd.DataFrame`
  — returns daily escalation index from 2017-01-01 to present

---

### backtest/analyzer.py

Implement fully:
- `analyze_event(event: dict, hist_escalation_df: pd.DataFrame, hist_prices_df: pd.DataFrame) -> dict`
  — returns pre_event_trajectory, post_event_sector_returns, was_rising, accuracy_note
- `run_full_backtest(hist_macro_df, hist_prices_df) -> pd.DataFrame`
  — runs analyze_event for all 4 historical events

---

### api/main.py

Implement fully:
- FastAPI app with CORS middleware
- Mount all routers from api/routes/
- Health check endpoint: GET /health → {status: "ok", db_fresh: bool, last_updated: str}
- OpenAPI docs enabled at /docs
- Auth middleware: check Authorization header for API key from API_KEY env var

---

### api/routes/company.py

Implement fully:
- `GET /company-risk?ticker=AAPL`
  — reads from DB via db.client, returns full company risk schema
  — 404 if ticker not found
  — includes data_warning if data stale

---

### api/routes/screener.py

Implement fully:
- `GET /screener` with query params: sort, sector, confidence, region, limit
  — calls db.client.read_screener()
  — returns {results: [...], total_count, returned_count, filters_applied}

---

### api/routes/nlp.py

Implement fully:
- `POST /nlp-query` body: {query: str}
  — calls nlp.screener.parse_nlp_query()
  — applies filters to DB read
  — returns results + interpreted_filters + response_time_ms

---

### dashboard/app.py

Implement fully as a working Streamlit app skeleton:
- Page config, auto-refresh (5 min)
- Load data from api_client (falls back to mock_api if API unavailable)
- Header with live dot and last-updated
- 4 metric cards
- Two-column layout: map (left) + screener preview (right)
- Two-column layout: events feed (left) + markets + gauge (right)
- Tabs: [Full Screener] [Sector Heatmap] [Backtesting] [About]
- Session state for: selected_ticker, filter_country, filter_sector
- All tabs must render without errors even with mock data

---

### dashboard/api_client.py

Implement fully:
- `API_BASE_URL` from env var, fallback to localhost:8000
- `USE_MOCK` from env var, default False
- All fetch functions with @st.cache_data(ttl=300) caching
- Automatic fallback to mock_api if request fails
- `fetch_escalation_index() -> dict`
- `fetch_screener(...) -> list`
- `fetch_company_detail(ticker) -> dict`
- `fetch_events(...) -> list`
- `fetch_backtest() -> dict`
- `post_nlp_query(query) -> dict`

---

### zerve/blocks/block_a2_edgar.py

Each block file must be structured as:
```python
"""
ZERVE BLOCK: A2 — EDGAR Fetcher
LAYER: Development
INPUTS: tickers_df (from block A1)
OUTPUTS: raw_filings_df

SETUP:
  1. In Zerve canvas Requirements, add: requests
  2. In Zerve Assets > Constants & Secrets, add:
     - No secrets needed for EDGAR (public API)
  3. Connect Block A1 → this block

HOW THIS WORKS IN ZERVE:
  This block imports the ingestion module from the GitHub repo
  connected to this canvas via Zerve's Git integration.
  All logic lives in ingestion/edgar.py — this block is just the runner.
"""

# ── Zerve imports (available in all blocks) ──────────────────────────────────
# tickers_df is passed in from Block A1 automatically via the canvas edge

# ── Repo import (via Zerve Git integration) ──────────────────────────────────
import sys
sys.path.insert(0, "/repo/geopolitical-alpha")  # adjust path after Git import
from ingestion.edgar import fetch_ticker
from db.client import upsert_company  # write results to Neon as we go

# ── Fleet parallelization ─────────────────────────────────────────────────────
from zerve import spread  # Zerve's built-in parallelization function

# ── Run ───────────────────────────────────────────────────────────────────────
import pandas as pd

all_results = spread(fetch_ticker, tickers_df["ticker"].tolist())
raw_filings_df = pd.DataFrame([
    row for sublist in all_results for row in sublist
])

print(f"Fetched {len(raw_filings_df)} filing chunks from {raw_filings_df['ticker'].nunique()} companies")
print(raw_filings_df[["ticker", "filing_type", "filing_date"]].head(10))
```

Write all 16 block files following this exact pattern. Each one:
- Has the full header docstring (ZERVE BLOCK, LAYER, INPUTS, OUTPUTS, SETUP, HOW THIS WORKS)
- Imports from the correct module in the repo
- Is thin — calls one function from the repo, stores output as a named DataFrame
- Prints a validation summary at the end
- Handles the case where the repo import fails (try/except with clear error message)

---

### zerve/genai_prompts/supply_chain_extractor.txt

The full system prompt to paste into the Zerve GenAI Block config for Block A4:

```
You are a supply chain risk analyst specializing in SEC filing analysis.
[... full prompt from spec ...]
```

Write the complete prompt. This file is pasted directly into Zerve — it is not Python.

---

### zerve/README.md

Write a step-by-step guide for how to connect this GitHub repo to a Zerve canvas:

1. How to connect via Zerve's Git integration (Settings → Source Control)
2. How to import the repo so blocks can use `sys.path.insert` to access it
3. Which blocks to create in which order
4. How to configure the GenAI block (A4) with the supply_chain_extractor prompt
5. How to set up the Scheduled Jobs layer
6. How to set up the Deployment layer (API Controller + routes)
7. Common errors and how to fix them

---

## Environment variables

Create `.env.example` with all required vars:

```bash
# Neon Postgres
NEON_DATABASE_URL=postgresql://user:password@ep-xxx.us-east-1.aws.neon.tech/neondb?sslmode=require

# External APIs
ALPHA_VANTAGE_KEY=
FRED_API_KEY=
KALSHI_API_KEY=
ANTHROPIC_API_KEY=

# FastAPI middleware
API_KEY=your-generated-api-key-for-clients
API_HOST=0.0.0.0
API_PORT=8000

# Streamlit dashboard
API_BASE_URL=http://localhost:8000
USE_MOCK=false

# Zerve (set these as Zerve secrets, not local env vars)
# NEON_DATABASE_URL  ← also needed in Zerve secrets
# ALPHA_VANTAGE_KEY  ← also needed in Zerve secrets
# FRED_API_KEY       ← also needed in Zerve secrets
# KALSHI_API_KEY     ← also needed in Zerve secrets
# ANTHROPIC_API_KEY  ← also needed in Zerve secrets
```

---

## requirements.txt

```
fastapi>=0.110.0
uvicorn>=0.29.0
streamlit>=1.32.0
plotly>=5.20.0
pandas>=2.0.0
numpy>=1.26.0
requests>=2.31.0
psycopg2-binary>=2.9.9
sqlalchemy>=2.0.0
anthropic>=0.25.0
pydantic>=2.0.0
python-dotenv>=1.0.0
streamlit-autorefresh>=1.0.0
httpx>=0.27.0
```

## requirements-dev.txt
```
pytest>=8.0.0
pytest-asyncio>=0.23.0
black>=24.0.0
ruff>=0.3.0
```

---

## Validation — how to confirm the skeleton works

After building all files, run these checks in order:

```bash
# 1. Imports work
python -c "from db.client import get_engine; print('✓ db.client')"
python -c "from ingestion.edgar import fetch_ticker; print('✓ ingestion.edgar')"
python -c "from ingestion.polymarket import fetch_markets; print('✓ ingestion.polymarket')"
python -c "from scoring.exposure import score_from_extractions; print('✓ scoring.exposure')"
python -c "from scoring.escalation import compute_escalation_index; print('✓ scoring.escalation')"
python -c "from nlp.extractor import extract_supply_chain; print('✓ nlp.extractor')"
python -c "from backtest.historical import compute_full_history; print('✓ backtest.historical')"
python -c "from api.main import app; print('✓ api.main')"
python -c "from dashboard.api_client import fetch_escalation_index; print('✓ dashboard.api_client')"

# 2. FastAPI starts
uvicorn api.main:app --host 0.0.0.0 --port 8000 &
curl http://localhost:8000/health

# 3. Streamlit starts (with mock data)
USE_MOCK=true streamlit run dashboard/app.py

# 4. Tests pass
pytest tests/ -v
```

All 9 import checks must pass before considering the skeleton complete.
The FastAPI health check must return 200.
The Streamlit app must render without errors using mock data.

---

## What NOT to build

Do not implement:
- The actual Zerve canvas itself (that is done in the Zerve UI)
- The GenAI block execution (that runs inside Zerve natively)
- The Fleet parallelization runtime (Zerve handles this — `spread` is a Zerve builtin)
- Any front-end beyond Streamlit (no React, no Next.js)
- Authentication beyond a simple API key check
- Anything requiring Docker or containerization

---

## Final output

When done, confirm:
- [ ] All files created at the paths specified
- [ ] All 9 import validation commands pass
- [ ] `.env.example` has every variable needed
- [ ] `zerve/README.md` has complete Zerve setup instructions
- [ ] `zerve/genai_prompts/supply_chain_extractor.txt` has the full prompt
- [ ] All 16 Zerve block files follow the standard header format
- [ ] `dashboard/app.py` runs with `USE_MOCK=true` without errors
- [ ] `api/main.py` starts with uvicorn without errors
