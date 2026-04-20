"""
ZERVE BLOCK: A1 — S&P 500 Ticker List
LAYER: Development
INPUTS: none
OUTPUTS: tickers_df

SETUP:
  1. No secrets needed (uses a hardcoded curated list)
  2. Connect this block → Block A2 (EDGAR Fetcher)

HOW THIS WORKS IN ZERVE:
  Produces the master list of tickers to process.
  Edit the TICKERS list to add/remove companies.
"""
import pandas as pd

TICKERS = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA", "AVGO",
    "JPM", "LLY", "UNH", "XOM", "V", "JNJ", "MA", "PG", "HD", "MRK",
    "ABBV", "CVX", "KO", "PEP", "BAC", "ADBE", "CRM", "NFLX", "TMO",
    "ACN", "MCD", "CSCO", "ABT", "WMT", "CAT", "NKE", "GE", "BA",
]

tickers_df = pd.DataFrame({"ticker": TICKERS})
print(f"Loaded {len(tickers_df)} tickers")
print(tickers_df.head())
