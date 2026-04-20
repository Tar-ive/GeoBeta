# Zerve Setup Guide — GeoAlpha

This guide walks you through connecting this GitHub repo to a Zerve canvas
and configuring all blocks, secrets, and scheduled jobs.

---

## 1. Connect the GitHub repo via Zerve Git Integration

1. Open your Zerve canvas
2. Go to **Settings → Source Control**
3. Click **Connect Repository**
4. Authorize Zerve to access your GitHub account
5. Select the `geopolitical-alpha` repo and the `main` branch
6. Zerve will clone the repo to `/repo/geopolitical-alpha/` inside the canvas runtime
7. All `zerve/blocks/*.py` files import from this path via `sys.path.insert(0, "/repo/geopolitical-alpha")`

---

## 2. Configure Zerve Secrets

In **Canvas Settings → Secrets & Constants**, add:

| Secret Name | Value | Used By |
|-------------|-------|---------|
| `NEON_DATABASE_URL` | `postgresql://...` | All blocks that write to DB |
| `ALPHA_VANTAGE_API_KEY` | Your AV key | Block B1 |
| `FRED_API_KEY` | Your FRED key | Block E1 |
| `KALSHI_API_KEY` | Your Kalshi key | Block D2 |
| `ANTHROPIC_API_KEY` | Your Anthropic key | Block A4 (GenAI) |

---

## 3. Create blocks in order

Create each block as a **Python block** and paste in the corresponding file from `zerve/blocks/`.

### Pipeline A — EDGAR + Exposure Scoring
| Block | File | Type |
|-------|------|------|
| A1 | `block_a1_tickers.py` | Python |
| A2 | `block_a2_edgar.py` | Python |
| A3 | `block_a3_chunker.py` | Python |
| A4 | (GenAI block — see section 4) | GenAI ⭐ |
| A5 | `block_a5_scorer.py` | Python |

### Pipeline B — Stock Prices
| Block | File | Type |
|-------|------|------|
| B1 | `block_b1_prices.py` | Python |
| B3 | `block_b3_reaction.py` | Python |

### Pipeline C — GDELT Events
| Block | File | Type |
|-------|------|------|
| C1 | `block_c1_gdelt.py` | Python |
| C2 | `block_c2_enricher.py` | Python |

### Pipeline D — Prediction Markets
| Block | File | Type |
|-------|------|------|
| D1 | `block_d1_polymarket.py` | Python |
| D2 | `block_d2_kalshi.py` | Python |
| D3 | `block_d3_markets.py` | Python |

### Pipeline E — FRED Macro
| Block | File | Type |
|-------|------|------|
| E1 | `block_e1_fred.py` | Python |
| E2 | `block_e2_macro.py` | Python |

### Pipeline F — Backtest
| Block | File | Type |
|-------|------|------|
| F | `block_f_backtest.py` | Python |

### Pipeline G — Escalation Index
| Block | File | Type |
|-------|------|------|
| G1 | `block_g1_escalation.py` | Python |
| G2 | `block_g2_master.py` | Python |

---

## 4. Configure the GenAI block (A4)

1. Create a **GenAI block** (star icon) in the canvas
2. Set **Model**: Claude (claude-sonnet-4-6 or equivalent)
3. Paste the full contents of `zerve/genai_prompts/supply_chain_extractor.txt` into the **System Prompt** field
4. Set **Input**: `filtered_chunks_df` column `chunk_text` (one row per LLM call)
5. Set **Output column name**: `genai_extraction`
6. Connect Block A3 → Block A4 → Block A5

---

## 5. Wire the block edges

Connect blocks in this order (left to right = data flow):

```
A1 → A2 → A3 → A4 (GenAI) → A5
A1 → B1 → B3
           ↓
C1 → C2
D1 →
D2 → D3
E1 → E2
       ↓
A5, D3, C1, E1 → G1 → G2
B1, E1 → F
```

---

## 6. Set up Scheduled Jobs (Cron)

Create the following Scheduled Jobs in the **Cron** layer:

| Job Name | Trigger | Blocks to Run | Purpose |
|----------|---------|---------------|---------|
| `daily-prices` | `0 18 * * 1-5` (6pm weekdays) | B1, B3 | Fetch market close prices |
| `daily-macro` | `0 9 * * *` (9am daily) | E1, E2 | Refresh FRED data |
| `events-refresh` | `*/15 * * * *` (every 15 min) | C1, C2 | Poll GDELT |
| `markets-refresh` | `*/15 * * * *` (every 15 min) | D1, D2, D3 | Poll prediction markets |
| `escalation-compute` | `*/15 * * * *` (every 15 min) | G1, G2 | Recompute index |
| `weekly-edgar` | `0 8 * * 1` (Monday 8am) | A1-A5 | Re-run filing analysis |

---

## 7. Configure the Deployment layer

1. In Zerve canvas, go to the **Deployment** tab
2. Create an **API Controller** pointing to Block G2's `master_df` output
3. Set the API endpoint base URL (Zerve will provide a public URL)
4. Update `API_BASE_URL` in your local `.env` to point to this URL
5. Add the Zerve API key to `API_KEY` in your local `.env`

---

## 8. Common errors and fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: ingestion` | Git integration not configured or wrong path | Check Settings → Source Control; verify path is `/repo/geopolitical-alpha` |
| `KeyError: NEON_DATABASE_URL` | Secret not added to canvas | Add secret in Canvas Settings → Secrets |
| `ModuleNotFoundError: zerve` | `spread` called outside Zerve | The `zerve` module is only available inside Zerve runtime; blocks work fine locally without it |
| `Rate limit` on Alpha Vantage | Too many API calls | Reduce ticker list in A1 or upgrade to premium plan |
| GDELT returns empty | Rate limited or query too specific | Broaden query; add `time.sleep(5)` between runs |
| `psycopg2.OperationalError` | Neon connection pool exhausted | Increase pool_size in `db/client.py` or use connection pooling via PgBouncer |
