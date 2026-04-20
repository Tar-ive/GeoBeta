"""
HTTP client for the GeoAlpha FastAPI layer.
All Streamlit components import from here.
Falls back to mock_api automatically on any request failure.
"""
import os
from typing import Optional

import httpx
import streamlit as st

from . import mock_api

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
API_KEY = os.environ.get("API_KEY", "")
USE_MOCK = os.environ.get("USE_MOCK", "false").lower() == "true"

_HEADERS = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}


def _get(path: str, params: Optional[dict] = None) -> dict | list:
    if USE_MOCK:
        return _mock_dispatch(path, params)
    try:
        r = httpx.get(f"{API_BASE_URL}{path}", params=params, headers=_HEADERS, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return _mock_dispatch(path, params)


def _post(path: str, body: dict) -> dict:
    if USE_MOCK:
        return _mock_dispatch(path, body)
    try:
        r = httpx.post(f"{API_BASE_URL}{path}", json=body, headers=_HEADERS, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception:
        return _mock_dispatch(path, body)


def _mock_dispatch(path: str, _params=None) -> dict | list:
    if "screener" in path:
        return {"results": mock_api.MOCK_SCREENER, "total_count": len(mock_api.MOCK_SCREENER), "returned_count": len(mock_api.MOCK_SCREENER), "filters_applied": {}}
    if "escalation" in path:
        return mock_api.MOCK_ESCALATION
    if "events" in path:
        return {"events": mock_api.MOCK_EVENTS, "count": len(mock_api.MOCK_EVENTS)}
    if "backtest" in path:
        return {"events": mock_api.MOCK_BACKTEST}
    if "nlp" in path:
        return {"results": mock_api.MOCK_SCREENER[:5], "interpreted_filters": {}, "response_time_ms": 0}
    return {}


@st.cache_data(ttl=300)
def fetch_escalation_index(days: int = 30) -> dict:
    return _get("/escalation-index", {"days": days})


@st.cache_data(ttl=300)
def fetch_screener(
    sort: str = "gap_desc",
    sector: Optional[str] = None,
    confidence: Optional[str] = None,
    region: Optional[str] = None,
    limit: int = 50,
) -> list:
    params = {"sort": sort, "limit": limit}
    if sector:
        params["sector"] = sector
    if confidence:
        params["confidence"] = confidence
    if region:
        params["region"] = region
    return _get("/screener", params).get("results", [])


@st.cache_data(ttl=300)
def fetch_company_detail(ticker: str) -> dict:
    return _get("/company-risk", {"ticker": ticker})


@st.cache_data(ttl=300)
def fetch_events(severity: Optional[float] = None, limit: int = 20) -> list:
    params: dict = {"limit": limit}
    if severity is not None:
        params["severity"] = severity
    return _get("/events", params).get("events", [])


@st.cache_data(ttl=3600)
def fetch_backtest() -> dict:
    return _get("/backtest")


def post_nlp_query(query: str) -> dict:
    return _post("/nlp-query", {"query": query})
