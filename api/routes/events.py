from typing import Optional

from fastapi import APIRouter, Query
from db.client import read_events

router = APIRouter()


@router.get("")
def get_events(
    severity: Optional[float] = Query(None, ge=0, le=10),
    country: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    """Return recent geopolitical events."""
    df = read_events(severity=severity, country=country, limit=limit)
    return {"events": df.to_dict(orient="records"), "count": len(df)}
