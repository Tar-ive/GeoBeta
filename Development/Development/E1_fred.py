"""
ZERVE BLOCK: E1 — FRED Macro Fetcher
LAYER: Development
INPUTS: none
OUTPUTS: macro_df

SETUP:
  1. Requirements: requests, pandas
  2. In Zerve Secrets, add: FRED_API_KEY, NEON_DATABASE_URL
  3. Connect this block → Block E2

HOW THIS WORKS IN ZERVE:
  Fetches all configured FRED series and upserts to macro_signals table.
"""
import os, sys
try:
    sys.path.insert(0, "/repo/GeoBeta")
    from ingestion.fred import fetch_all_series, compute_trend_score
    from db.upsert import upsert_macro_signal
except ImportError as e:
    raise ImportError(f"Repo import failed: {e}")

import pandas as pd

api_key = os.environ["FRED_API_KEY"]
macro_df = fetch_all_series(api_key=api_key, start_date="2020-01-01")

for series_id, group in macro_df.groupby("series_id"):
    trend = compute_trend_score(group["value"])
    for _, row in group.iterrows():
        upsert_macro_signal({
            "source_id": f"{row['series_id']}_{row['observation_date']}",
            **row.to_dict(),
            "trend_score": trend["trend_score"],
            "direction": trend["direction"],
        })

print(f"Fetched and upserted {len(macro_df)} macro observations across {macro_df['series_id'].nunique()} series")
