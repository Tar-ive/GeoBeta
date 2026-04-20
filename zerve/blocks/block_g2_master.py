"""
ZERVE BLOCK: G2 — Master Summary
LAYER: Development
INPUTS: escalation_result (G1), scored_companies_df (A5)
OUTPUTS: master_df (final state for dashboard)

SETUP:
  1. Connect Block G1 and Block A5 → this block
  2. This is the terminal block — connect to Deployment layer output

HOW THIS WORKS IN ZERVE:
  Combines escalation index with company scores to produce the master DataFrame
  that powers the dashboard screener. Also computes gap scores.
"""
import sys
try:
    sys.path.insert(0, "/repo/geopolitical-alpha")
    from scoring.reaction import compute_gap_score, gap_label
    from db.client import read_screener
except ImportError as e:
    raise ImportError(f"Repo import failed: {e}")

import pandas as pd

master_df = read_screener(sort="gap_desc", limit=500)
if "tariff_exposure_score" in master_df.columns and "reaction_score_adj" in master_df.columns:
    master_df["gap_score"] = master_df.apply(
        lambda r: compute_gap_score(r["tariff_exposure_score"] or 0, r["reaction_score_adj"] or 0),
        axis=1,
    )
    master_df["gap_label"] = master_df["gap_score"].apply(gap_label)

print(f"Master DataFrame: {len(master_df)} companies")
print(master_df[["ticker", "tariff_exposure_score", "gap_score", "gap_label"]].head(10))
