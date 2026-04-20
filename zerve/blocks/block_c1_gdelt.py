"""
ZERVE BLOCK: C1 — GDELT Event Fetcher
LAYER: Development
INPUTS: none
OUTPUTS: events_df

SETUP:
  1. Requirements: requests
  2. In Zerve Secrets, add: NEON_DATABASE_URL
  3. No API key required for GDELT

HOW THIS WORKS IN ZERVE:
  Polls GDELT every 15 min (via Zerve Scheduled Job on this canvas).
  Fetches tariff/geopolitical articles and upserts to geopolitical_events table.
"""
import sys
try:
    sys.path.insert(0, "/repo/geopolitical-alpha")
    from ingestion.gdelt import fetch_events, parse_event
    from db.upsert import upsert_event
except ImportError as e:
    raise ImportError(f"Repo import failed: {e}")

import pandas as pd

raw_events = fetch_events(
    query="tariff OR trade war OR sanction OR geopolitical",
    timespan_minutes=1440,
    max_records=50,
)
parsed = [parse_event(e) for e in raw_events]
for ev in parsed:
    upsert_event(ev)

events_df = pd.DataFrame(parsed)
print(f"Fetched and upserted {len(events_df)} GDELT events")
