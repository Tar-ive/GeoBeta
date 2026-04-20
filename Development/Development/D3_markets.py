"""
ZERVE BLOCK: D3 — Markets Aggregator
LAYER: Development
INPUTS: polymarket_df (D1), kalshi_df (D2)
OUTPUTS: all_markets_df

SETUP:
  1. Connect Block D1 and Block D2 → this block
  2. Connect this block → Block G1 (Escalation Index)

HOW THIS WORKS IN ZERVE:
  Combines Polymarket and Kalshi into a single markets DataFrame
  for use in the escalation index computation.
"""
import pandas as pd

all_markets_df = pd.concat([polymarket_df, kalshi_df], ignore_index=True)
print(f"Combined markets: {len(all_markets_df)} total ({len(polymarket_df)} Polymarket + {len(kalshi_df)} Kalshi)")
print(all_markets_df[["source", "question", "odds", "category"]].head(10))
