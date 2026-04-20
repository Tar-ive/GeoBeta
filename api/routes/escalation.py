from fastapi import APIRouter, Query
from db.client import read_escalation_history

router = APIRouter()


@router.get("")
def get_escalation_index(days: int = Query(30, ge=1, le=365)):
    """Return escalation index time series and current reading."""
    df = read_escalation_history(days=days)
    if df.empty:
        return {"current": None, "history": [], "trend": "unknown"}

    history = df.to_dict(orient="records")
    current = history[-1]

    # Simple trend: compare last score to 7 days ago
    trend = "stable"
    if len(history) >= 2:
        delta = history[-1]["index_score"] - history[0]["index_score"]
        if delta > 0.05:
            trend = "rising"
        elif delta < -0.05:
            trend = "falling"

    return {"current": current, "history": history, "trend": trend}
