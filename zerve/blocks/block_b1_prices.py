"""
ZERVE BLOCK: B1 — Stock Price Fetcher
LAYER: Development
INPUTS: tickers_df (from Block A1)
OUTPUTS: prices_df

SETUP:
  1. In Zerve Secrets, add: ALPHA_VANTAGE_API_KEY, NEON_DATABASE_URL
  2. Requirements: requests, pandas
  3. Connect Block A1 → this block

HOW THIS WORKS IN ZERVE:
  Fetches daily prices for all tickers and upserts to stock_prices table.
  Respects Alpha Vantage rate limit (5 req/min on free tier).
"""
import os, sys
try:
    sys.path.insert(0, "/repo/geopolitical-alpha")
    from ingestion.alpha_vantage import fetch_all_tickers
    from db.upsert import upsert_stock_price
except ImportError as e:
    raise ImportError(f"Repo import failed: {e}")

import pandas as pd

api_key = os.environ["ALPHA_VANTAGE_API_KEY"]
prices_df = fetch_all_tickers(
    tickers_df["ticker"].tolist(),
    api_key=api_key,
    start_date="2025-01-01",
)

for _, row in prices_df.iterrows():
    upsert_stock_price({
        "source_id": f"{row['ticker']}_{row['price_date']}",
        **row.to_dict(),
    })

print(f"Fetched and upserted {len(prices_df)} price rows for {prices_df['ticker'].nunique()} tickers")
