"""
ZERVE BLOCK: D1 — Polymarket Fetcher
LAYER: Development
INPUTS: none
OUTPUTS: polymarket_df

SETUP:
  1. Requirements: requests
  2. In Zerve Secrets, add: NEON_DATABASE_URL
  3. No API key required for Polymarket public endpoints

HOW THIS WORKS IN ZERVE:
  Fetches macro/trade-related markets from Polymarket CLOB API
  and upserts to prediction_markets table.
"""
import sys
try:
    sys.path.insert(0, "/repo/GeoBeta")
    from ingestion.polymarket import fetch_markets, parse_market
    from db.upsert import upsert_market
except ImportError as e:
    raise ImportError(f"Repo import failed: {e}")

import pandas as pd

raw_markets = fetch_markets(keywords=[
    "tariff", "trade", "fed rate", "inflation", "recession", "china", "sanction"
])
parsed = [parse_market(m) for m in raw_markets]
for m in parsed:
    upsert_market(m)

polymarket_df = pd.DataFrame(parsed)
print(f"Fetched and upserted {len(polymarket_df)} Polymarket markets")
