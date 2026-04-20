"""
GDELT GEO 2.0 API ingestion.
Fetches recent news articles matching geopolitical queries.

Called by Zerve block C1.
"""
import hashlib
from datetime import datetime, timezone
from typing import Optional

import requests

GDELT_BASE = "https://api.gdeltproject.org/api/v2/geo/geo"
DEFAULT_QUERY = "tariff OR trade war OR sanction OR geopolitical risk"


def fetch_events(
    query: str = DEFAULT_QUERY,
    timespan_minutes: int = 1440,
    max_records: int = 50,
) -> list[dict]:
    """Fetch recent GDELT articles matching the query.

    Args:
        query: GDELT full-text search query string.
        timespan_minutes: Lookback window in minutes (1440 = last 24h).
        max_records: Max articles to return (GDELT caps at 250).

    Returns:
        List of raw article dicts from GDELT.
    """
    params = {
        "query": query,
        "mode": "artlist",
        "maxrecords": min(max_records, 250),
        "format": "json",
        "timespan": timespan_minutes,
    }
    resp = requests.get(GDELT_BASE, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    return data.get("articles", [])


def parse_event(raw: dict) -> dict:
    """Normalize a raw GDELT article to the unified geopolitical_events schema.

    Args:
        raw: Raw article dict from GDELT artlist response.

    Returns:
        Dict matching geopolitical_events table columns.
        lat/lon/goldstein_scale are None (not in artlist mode).
    """
    url = raw.get("url", "")
    source_id = hashlib.md5(url.encode()).hexdigest()

    # Parse seendate: "20260419T233000Z" → datetime
    seendate = raw.get("seendate", "")
    event_timestamp = _parse_seendate(seendate)

    # Parse tone: comma-delimited string "tone,pos,neg,polarity,activity,selfref,wordcount"
    tone_raw = raw.get("tone", "")
    tone = _parse_tone(tone_raw)

    return {
        "source_id": source_id,
        "source_event_id": None,
        "headline": raw.get("title", ""),
        "lat": None,
        "lon": None,
        "country": raw.get("sourcecountry"),
        "severity": None,   # computed downstream from tone / goldstein
        "goldstein_scale": None,
        "tone": tone,
        "affected_tickers": [],
        "affected_sectors": [],
        "source_url": url,
        "domain": raw.get("domain"),
        "language": raw.get("language"),
        "event_timestamp": event_timestamp.isoformat() if event_timestamp else None,
    }


def _parse_seendate(seendate: str) -> Optional[datetime]:
    """Parse GDELT seendate string to UTC datetime."""
    if not seendate:
        return None
    try:
        # Format: "20260419T233000Z"
        return datetime.strptime(seendate, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        try:
            # Alternate format: "20260419233000"
            return datetime.strptime(seendate[:14], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        except ValueError:
            return None


def _parse_tone(tone_str: str) -> Optional[float]:
    """Extract the first value (overall tone score) from GDELT's comma-delimited tone string."""
    if not tone_str:
        return None
    try:
        return float(tone_str.split(",")[0])
    except (ValueError, IndexError):
        return None
