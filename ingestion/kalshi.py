"""
Kalshi event market ingestion.
Fetches open markets, normalizes prices from FixedPointDollars strings.

Called by Zerve block D2.
"""
import os
from typing import Optional

import requests

KALSHI_BASE = "https://trading.kalshi.com/trade-api/v2"
DEFAULT_KEY = os.environ.get("KALSHI_API_KEY", "")

MACRO_KEYWORDS = [
    "fed", "rate", "inflation", "tariff", "trade", "gdp", "recession",
    "china", "sanction", "unemployment", "treasury",
]


def fetch_markets(
    api_key: str = DEFAULT_KEY,
    keywords: Optional[list[str]] = None,
    status: str = "open",
) -> list[dict]:
    """Fetch Kalshi markets using cursor-based pagination.

    Args:
        api_key: Kalshi API key (not required for public markets).
        keywords: Filter markets by keyword in rules_primary (case-insensitive).
        status: Market status filter ('open', 'closed', etc.).

    Returns:
        List of raw market dicts from the Kalshi API.
    """
    if keywords is None:
        keywords = MACRO_KEYWORDS

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    results = []
    cursor = None

    while True:
        params: dict = {"status": status, "limit": 200}
        if cursor:
            params["cursor"] = cursor

        try:
            resp = requests.get(
                f"{KALSHI_BASE}/markets",
                params=params,
                headers=headers,
                timeout=15,
            )
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"[kalshi] Request failed: {e}")
            break

        data = resp.json()
        markets = data.get("markets", [])

        for m in markets:
            text = (m.get("rules_primary") or m.get("ticker") or "").lower()
            if not keywords or any(kw in text for kw in keywords):
                results.append(m)

        cursor = data.get("cursor")
        if not cursor:
            break

    return results


def parse_market(raw: dict) -> dict:
    """Normalize a raw Kalshi market to the unified prediction_markets schema.

    Kalshi prices are FixedPointDollars strings (e.g. "0.560000") on 0–1 scale.

    Args:
        raw: Raw market dict from the Kalshi API.

    Returns:
        Dict matching prediction_markets table columns.
    """
    ticker = raw.get("ticker", "")
    source_id = f"kalshi_{ticker}"

    # Compute mid-price from YES bid + ask
    bid = raw.get("yes_bid_dollars", "0") or "0"
    ask = raw.get("yes_ask_dollars", "0") or "0"
    last = raw.get("last_price_dollars", "0") or "0"

    try:
        mid = (float(bid) + float(ask)) / 2
        odds = round(mid if mid > 0 else float(last), 4)
    except (ValueError, TypeError):
        odds = None

    volume_raw = raw.get("volume_fp", "0") or "0"
    try:
        volume = float(volume_raw)
    except (ValueError, TypeError):
        volume = None

    category = _infer_category_kalshi(ticker, raw.get("event_ticker", ""))

    return {
        "source_id": source_id,
        "source": "kalshi",
        "source_market_id": ticker,
        "question": raw.get("rules_primary", ticker),
        "odds": odds,
        "volume": volume,
        "expiry_date": raw.get("close_time"),
        "sector_tags": [],
        "ticker_tags": [],
        "odds_7d_change": None,
        "category": category,
        "market_status": raw.get("status", "unknown"),
    }


def _infer_category_kalshi(ticker: str, event_ticker: str) -> str:
    combined = (ticker + event_ticker).upper()
    if "FED" in combined or "RATE" in combined:
        return "monetary_policy"
    if "TARIFF" in combined or "TRADE" in combined:
        return "trade_policy"
    if "INF" in combined or "CPI" in combined:
        return "inflation"
    if "GDP" in combined or "REC" in combined:
        return "macro"
    return "other"
