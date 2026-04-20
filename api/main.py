"""
GeoAlpha FastAPI middleware layer.
Sits between the Neon database and the Streamlit dashboard.
Handles caching, auth, and staleness warnings.

Start: uvicorn api.main:app --host 0.0.0.0 --port 8000
Docs:  http://localhost:8000/docs
"""
import os
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .middleware import AuthMiddleware
from .routes import company, screener, escalation, events, nlp, backtest

app = FastAPI(
    title="GeoAlpha API",
    description="Geopolitical risk intelligence for S&P 500 companies.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuthMiddleware)

app.include_router(company.router,    prefix="/company-risk",    tags=["Company"])
app.include_router(screener.router,   prefix="/screener",        tags=["Screener"])
app.include_router(escalation.router, prefix="/escalation-index",tags=["Escalation"])
app.include_router(events.router,     prefix="/events",          tags=["Events"])
app.include_router(nlp.router,        prefix="/nlp-query",       tags=["NLP"])
app.include_router(backtest.router,   prefix="/backtest",        tags=["Backtest"])


@app.get("/health", tags=["Health"])
def health_check():
    """Returns API health status and database freshness."""
    from db.client import check_freshness
    try:
        freshness = check_freshness("companies")
        db_fresh = freshness["is_fresh"]
        last_updated = freshness["last_updated"]
    except Exception:
        db_fresh = False
        last_updated = None

    return {
        "status": "ok",
        "db_fresh": db_fresh,
        "last_updated": last_updated,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
