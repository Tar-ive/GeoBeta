"""
ZERVE BLOCK: B3 — Market Reaction Scorer
LAYER: Development
INPUTS: prices_df (from Block B1)
OUTPUTS: reaction_df

SETUP:
  1. In Zerve Secrets, add: NEON_DATABASE_URL
  2. Connect Block B1 → this block

HOW THIS WORKS IN ZERVE:
  Computes sector-adjusted reaction scores and updates stock_prices table.
"""
import sys
try:
    sys.path.insert(0, "/repo/GeoBeta")
    from scoring.reaction import compute_delta, normalize_deltas, compute_sector_adjustment
    from db.upsert import upsert_stock_price
    from db.client import read_table
except ImportError as e:
    raise ImportError(f"Repo import failed: {e}")

import pandas as pd

# Compute raw deltas from Liberation Day
tickers = prices_df["ticker"].unique().tolist()
raw_deltas = {t: compute_delta(prices_df, t) for t in tickers}
normalized = normalize_deltas(raw_deltas)

# Join with sector info from companies table
companies_df = read_table("companies", limit=500)
reaction_df = pd.DataFrame([
    {"ticker": t, "market_reaction_score": s} for t, s in normalized.items()
])
reaction_df = reaction_df.merge(companies_df[["ticker", "sector"]], on="ticker", how="left")
reaction_df = compute_sector_adjustment(reaction_df)

print(f"Computed reaction scores for {len(reaction_df)} tickers")
print(reaction_df[["ticker", "market_reaction_score", "reaction_score_adj"]].head(10))
