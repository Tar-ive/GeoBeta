"""
ZERVE BLOCK: D2 — Kalshi Fetcher
LAYER: Development
INPUTS: none
OUTPUTS: kalshi_df

SETUP:
  1. Requirements: requests
  2. In Zerve Secrets, add: KALSHI_API_KEY, NEON_DATABASE_URL
  3. Connect this block → Block D3 (market normalizer)

HOW THIS WORKS IN ZERVE:
  Fetches open Kalshi event markets and upserts to prediction_markets table.
"""
import os, sys
try:
    sys.path.insert(0, "/repo/geopolitical-alpha")
    from ingestion.kalshi import fetch_markets, parse_market
    from db.upsert import upsert_market
except ImportError as e:
    raise ImportError(f"Repo import failed: {e}")

import pandas as pd

api_key = os.environ.get("KALSHI_API_KEY", "")
raw_markets = fetch_markets(api_key=api_key)
parsed = [parse_market(m) for m in raw_markets]
for m in parsed:
    upsert_market(m)

kalshi_df = pd.DataFrame(parsed)
print(f"Fetched and upserted {len(kalshi_df)} Kalshi markets")
