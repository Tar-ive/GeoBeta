import time
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from db.client import read_screener
from nlp.screener import parse_nlp_query, apply_filters

router = APIRouter()


class NLPQueryRequest(BaseModel):
    query: str


@router.post("")
def post_nlp_query(body: NLPQueryRequest):
    """Convert a natural language query into a filtered screener result."""
    start = time.perf_counter()

    filters = parse_nlp_query(body.query)
    df = read_screener(
        sort=filters.get("sort", "gap_desc"),
        sector=filters["sectors"][0] if filters.get("sectors") else None,
        confidence=filters["confidence_levels"][0] if filters.get("confidence_levels") else None,
        limit=filters.get("limit", 20),
    )
    df = apply_filters(df, filters)

    return {
        "results": df.to_dict(orient="records"),
        "interpreted_filters": filters,
        "response_time_ms": round((time.perf_counter() - start) * 1000),
    }
