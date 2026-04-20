from typing import Optional

from fastapi import APIRouter, Query
from db.client import read_screener

router = APIRouter()


@router.get("")
def get_screener(
    sort: str = Query("gap_desc", description="gap_desc | exposure_desc | reaction_asc | reaction_desc"),
    sector: Optional[str] = Query(None),
    confidence: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """Return ranked company risk screener with latest prices."""
    df = read_screener(sort=sort, sector=sector, confidence=confidence, region=region, limit=limit)
    results = df.to_dict(orient="records")
    return {
        "results": results,
        "total_count": len(results),
        "returned_count": len(results),
        "filters_applied": {
            "sort": sort, "sector": sector,
            "confidence": confidence, "region": region, "limit": limit,
        },
    }
