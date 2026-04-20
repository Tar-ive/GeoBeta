"""
ZERVE BLOCK: C2 — Event Enricher (ticker/sector tagger)
LAYER: Development
INPUTS: events_df (from Block C1)
OUTPUTS: enriched_events_df

SETUP:
  1. In Zerve Secrets, add: NEON_DATABASE_URL
  2. Connect Block C1 → this block

HOW THIS WORKS IN ZERVE:
  Tags each GDELT event with affected tickers and sectors based on keyword matching
  against company names in the companies table.
"""
import sys
try:
    sys.path.insert(0, "/repo/GeoBeta")
    from db.client import read_table
    from db.upsert import upsert_event
except ImportError as e:
    raise ImportError(f"Repo import failed: {e}")

import pandas as pd

companies_df = read_table("companies")
ticker_map = dict(zip(companies_df["company_name"].str.lower(), companies_df["ticker"]))
sector_map = dict(zip(companies_df["ticker"], companies_df["sector"]))

def tag_event(row):
    headline = (row.get("headline") or "").lower()
    matched_tickers = [t for name, t in ticker_map.items() if name.split()[0] in headline]
    matched_sectors = list(set(sector_map[t] for t in matched_tickers if t in sector_map))
    return pd.Series({"affected_tickers": matched_tickers, "affected_sectors": matched_sectors})

enriched_events_df = events_df.copy()
tags = enriched_events_df.apply(tag_event, axis=1)
enriched_events_df[["affected_tickers", "affected_sectors"]] = tags

for _, row in enriched_events_df.iterrows():
    upsert_event(row.to_dict())

print(f"Enriched {len(enriched_events_df)} events with ticker/sector tags")
