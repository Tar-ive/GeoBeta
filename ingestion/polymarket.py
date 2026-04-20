"""
Polymarket CLOB API ingestion.
Paginates through all markets, filters by keywords, normalizes to unified schema.

Called by Zerve block D1.
"""
import hashlib
from typing import Optional

import requests

CLOB_BASE = "https://clob.polymarket.com"
MACRO_KEYWORDS = [
    "tariff", "trade war", "fed rate", "federal reserve", "inflation",
    "recession", "gdp", "china", "sanction", "interest rate", "unemployment",
]


def fetch_markets(keywords: Optional[list[str]] = None) -> list[dict]:
    """Fetch all Polymarket markets, optionally filtered by keyword.

    Paginates through the full market list using next_cursor.

    Args:
        keywords: If provided, only return markets whose question contains
                  at least one keyword (case-insensitive).

    Returns:
        List of raw market dicts from the API.
    """
    if keywords is None:
        keywords = MACRO_KEYWORDS

    results = []
    cursor = None

    while True:
        params = {}
        if cursor:
            params["next_cursor"] = cursor

        resp = requests.get(f"{CLOB_BASE}/markets", params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        markets = data.get("data", [])
        for m in markets:
            question = (m.get("question") or "").lower()
            if not keywords or any(kw in question for kw in keywords):
                results.append(m)

        cursor = data.get("next_cursor")
        if not cursor or cursor == "LTE=":  # LTE= is base64 for "-1" = end
            break

    return results


def parse_market(raw: dict) -> dict:
    """Normalize a raw Polymarket market to the unified prediction_markets schema.

    Args:
        raw: Raw market dict from the Polymarket API.

    Returns:
        Dict matching prediction_markets table columns.
    """
    source_market_id = raw.get("condition_id", "")
    source_id = f"polymarket_{source_market_id}"

    # YES token is the one with outcome "Yes" or index 0
    odds = None
    tokens = raw.get("tokens", [])
    for token in tokens:
        if str(token.get("outcome", "")).lower() in {"yes", "1", "true"}:
            price = token.get("price")
            if price is not None:
                odds = round(float(price), 4)
            break
    if odds is None and tokens:
        odds = round(float(tokens[0].get("price", 0)), 4)

    # Infer category from tags
    tags = raw.get("tags", [])
    category = _infer_category(tags, raw.get("question", ""))

    return {
        "source_id": source_id,
        "source": "polymarket",
        "source_market_id": source_market_id,
        "question": raw.get("question", ""),
        "odds": odds,
        "volume": None,  # not in /markets endpoint
        "expiry_date": raw.get("end_date_iso"),
        "sector_tags": tags,
        "ticker_tags": [],
        "odds_7d_change": None,
        "category": category,
        "market_status": "closed" if raw.get("closed") else "active",
    }


def _infer_category(tags: list[str], question: str) -> str:
    q = question.lower()
    if any(t in ("federal reserve", "interest rates", "monetary policy") for t in tags):
        return "monetary_policy"
    if "tariff" in q or "trade" in q:
        return "trade_policy"
    if "inflation" in q or "cpi" in q or "pce" in q:
        return "inflation"
    if "gdp" in q or "recession" in q:
        return "macro"
    if any(t in ("Politics", "Elections") for t in tags):
        return "politics"
    return "other"
