"""
ZERVE BLOCK: A2 — EDGAR Fetcher
LAYER: Development
INPUTS: tickers_df (from Block A1)
OUTPUTS: raw_filings_df

SETUP:
  1. In Zerve canvas Requirements, add: requests, beautifulsoup4, lxml
  2. No secrets needed (EDGAR is a public API)
  3. Connect Block A1 → this block

HOW THIS WORKS IN ZERVE:
  Imports ingestion.edgar from the GitHub repo connected via Git integration.
  Uses Zerve's spread() for parallel fetching across all tickers.
"""
import sys
try:
    sys.path.insert(0, "/repo/GeoBeta")
    from ingestion.edgar import fetch_ticker
    from db.upsert import upsert_company
except ImportError as e:
    raise ImportError(f"Could not import from repo. Check Git integration path. Error: {e}")

import pandas as pd
from zerve import spread

all_results = spread(fetch_ticker, tickers_df["ticker"].tolist())
raw_filings_df = pd.DataFrame([
    row for sublist in all_results for row in sublist
])

print(f"Fetched {len(raw_filings_df)} filing chunks from {raw_filings_df['ticker'].nunique()} companies")
print(raw_filings_df[["ticker", "filing_type", "filing_date"]].head(10))
