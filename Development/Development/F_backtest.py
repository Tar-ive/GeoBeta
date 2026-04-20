"""
ZERVE BLOCK: F — Backtest Runner
LAYER: Development
INPUTS: macro_df (from E1), prices_df (from B1)
OUTPUTS: backtest_df

SETUP:
  1. In Zerve Secrets, add: NEON_DATABASE_URL
  2. Connect Block E1 and Block B1 → this block

HOW THIS WORKS IN ZERVE:
  Runs the full historical backtest against all 4 configured events
  and upserts results to backtest_events table.
"""
import sys
try:
    sys.path.insert(0, "/repo/GeoBeta")
    from backtest.analyzer import run_full_backtest
    from db.upsert import upsert_escalation_index  # reuse for backtest writes
    from db.client import get_engine
except ImportError as e:
    raise ImportError(f"Repo import failed: {e}")

import pandas as pd
from sqlalchemy import text

backtest_df = run_full_backtest(macro_df, prices_df)

engine = get_engine()
with engine.begin() as conn:
    for _, row in backtest_df.iterrows():
        import json
        conn.execute(text("""
            INSERT INTO backtest_events (source_id, event_name, event_date, event_type,
                pre_event_trajectory, post_event_sector_returns,
                index_was_rising_pre_event, accuracy_note, updated_at)
            VALUES (:source_id, :event_name, :event_date, :event_type,
                :pre::jsonb, :post::jsonb, :rising, :note, NOW())
            ON CONFLICT (source_id) DO UPDATE SET
                pre_event_trajectory = EXCLUDED.pre_event_trajectory,
                post_event_sector_returns = EXCLUDED.post_event_sector_returns,
                index_was_rising_pre_event = EXCLUDED.index_was_rising_pre_event,
                accuracy_note = EXCLUDED.accuracy_note, updated_at = NOW()
        """), {
            "source_id": row["event_name"].lower().replace(" ", "-") + "-" + row["event_date"],
            "event_name": row["event_name"], "event_date": row["event_date"],
            "event_type": row["event_type"],
            "pre": json.dumps(row["pre_event_trajectory"]),
            "post": json.dumps(row["post_event_sector_returns"]),
            "rising": row["index_was_rising_pre_event"],
            "note": row["accuracy_note"],
        })

print(f"Backtest complete: {len(backtest_df)} events analyzed")
print(backtest_df[["event_name", "index_was_rising_pre_event"]].to_string())
