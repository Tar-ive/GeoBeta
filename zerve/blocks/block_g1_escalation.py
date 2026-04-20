"""
ZERVE BLOCK: G1 — Escalation Index Computation
LAYER: Development
INPUTS: all_markets_df (D3), events_df (C1), macro_df (E1)
OUTPUTS: escalation_result

SETUP:
  1. In Zerve Secrets, add: NEON_DATABASE_URL
  2. Connect Blocks D3, C1, E1 → this block → Block G2

HOW THIS WORKS IN ZERVE:
  Runs the escalation index formula against live data from all three pipelines
  and upserts the result to the escalation_index table.
"""
import sys
try:
    sys.path.insert(0, "/repo/geopolitical-alpha")
    from scoring.escalation import compute_escalation_index
    from db.upsert import upsert_escalation_index
except ImportError as e:
    raise ImportError(f"Repo import failed: {e}")

escalation_result = compute_escalation_index(
    markets_df=all_markets_df,
    events_df=events_df,
    macro_df=macro_df,
)

upsert_escalation_index({
    "source_id": escalation_result["computed_at"],
    "computed_at": escalation_result["computed_at"],
    "index_score": escalation_result["index_score"],
    "label": escalation_result["label"],
    **{f"component_{k}": v for k, v in escalation_result["components"].items()},
})

print(f"Escalation Index: {escalation_result['index_score']:.4f} ({escalation_result['label']})")
print(f"Components: {escalation_result['components']}")
