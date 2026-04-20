"""
ZERVE BLOCK: A5 — Exposure Scorer
LAYER: Development
INPUTS: genai_outputs_df (from Block A4 — GenAI block)
OUTPUTS: scored_companies_df

SETUP:
  1. Connect Block A4 (GenAI) → this block
  2. In Zerve Secrets, add: NEON_DATABASE_URL

HOW THIS WORKS IN ZERVE:
  Aggregates GenAI extraction results per ticker and computes the final
  Tariff Exposure Score, then upserts to the companies table.
"""
import sys
try:
    sys.path.insert(0, "/repo/GeoBeta")
    from scoring.exposure import score_from_extractions
    from scoring.confidence import compute_confidence
    from db.upsert import upsert_company
except ImportError as e:
    raise ImportError(f"Repo import failed: {e}")

import pandas as pd

rows = []
for ticker, group in genai_outputs_df.groupby("ticker"):
    extractions = group.to_dict(orient="records")
    scores = score_from_extractions(extractions)
    confidence_level, confidence_reason = compute_confidence(
        [e.get("confidence_signals", {}) for e in extractions]
    )
    row = {
        "source_id": ticker.lower(),
        "ticker": ticker,
        "company_name": group.iloc[0].get("company_name", ticker),
        **scores,
        "confidence_level": confidence_level,
        "confidence_reason": confidence_reason,
    }
    upsert_company(row)
    rows.append(row)

scored_companies_df = pd.DataFrame(rows)
print(f"Scored and upserted {len(scored_companies_df)} companies")
print(scored_companies_df[["ticker", "exposure_score", "exposure_level", "confidence_level"]].head(10))
