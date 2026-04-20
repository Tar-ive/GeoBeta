"""
Neon Postgres client for GeoAlpha.
All Zerve blocks and the FastAPI layer import from this module.

Connection string priority:
  1. NEON_DATABASE_URL env var (single URL)
  2. PG_HOST / PG_PORT / PG_DATABASE / PG_USER / PG_PASSWORD / PG_SSLMODE

Usage in Zerve block:
    import sys
    sys.path.insert(0, '/repo/geopolitical-alpha')
    from db.client import read_screener, check_freshness
"""
import os
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote_plus

import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


# ── Connection ────────────────────────────────────────────────────────────────

def _build_url() -> str:
    if url := os.environ.get("NEON_DATABASE_URL"):
        return url
    host = os.environ["PG_HOST"]
    port = os.environ.get("PG_PORT", "5432")
    db   = os.environ["PG_DATABASE"]
    user = os.environ["PG_USER"]
    pw   = quote_plus(os.environ["PG_PASSWORD"])
    ssl  = os.environ.get("PG_SSLMODE", "require")
    return f"postgresql+psycopg2://{user}:{pw}@{host}:{port}/{db}?sslmode={ssl}"


_engine: Optional[Engine] = None


def get_engine() -> Engine:
    """Return a shared SQLAlchemy engine (created once, reused)."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            _build_url(),
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
    return _engine


def get_connection() -> psycopg2.extensions.connection:
    """Return a raw psycopg2 connection for bulk operations or COPY."""
    url = os.environ.get("NEON_DATABASE_URL")
    if url:
        return psycopg2.connect(url)
    return psycopg2.connect(
        host=os.environ["PG_HOST"],
        port=int(os.environ.get("PG_PORT", 5432)),
        dbname=os.environ["PG_DATABASE"],
        user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
        sslmode=os.environ.get("PG_SSLMODE", "require"),
    )


# ── Generic reads ─────────────────────────────────────────────────────────────

_ALLOWED_TABLES = {
    "companies", "stock_prices", "prediction_markets",
    "geopolitical_events", "macro_signals", "escalation_index", "backtest_events",
}


def read_table(
    table_name: str,
    filters: Optional[dict] = None,
    limit: Optional[int] = None,
) -> pd.DataFrame:
    """Return a table (or filtered subset) as a DataFrame.

    Args:
        table_name: One of the seven GeoAlpha tables.
        filters: {column: value} equality filters (AND-joined).
        limit: Cap on rows returned.

    Example:
        read_table("companies", {"sector": "Technology"}, limit=20)
    """
    if table_name not in _ALLOWED_TABLES:
        raise ValueError(f"Unknown table {table_name!r}. Allowed: {_ALLOWED_TABLES}")

    clauses, params = [], {}
    for col, val in (filters or {}).items():
        clauses.append(f"{col} = :{col}")
        params[col] = val

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    limit_sql = f"LIMIT {int(limit)}" if limit else ""
    sql = text(f"SELECT * FROM {table_name} {where} {limit_sql}")

    with get_engine().connect() as conn:
        return pd.read_sql(sql, conn, params=params)


# ── Domain reads ──────────────────────────────────────────────────────────────

def read_screener(
    sort: str = "gap_desc",
    sector: Optional[str] = None,
    confidence: Optional[str] = None,
    region: Optional[str] = None,
    limit: int = 50,
) -> pd.DataFrame:
    """Company screener with latest price data joined in.

    Args:
        sort: 'gap_desc' | 'exposure_desc' | 'reaction_asc' | 'reaction_desc'
        sector: Exact sector name filter (e.g. 'Technology').
        confidence: 'low' | 'medium' | 'high'
        region: Filter companies with exposure to this region key in their regions JSONB.
        limit: Max rows returned.

    Returns:
        DataFrame: one row per company, latest stock price lateral-joined.
    """
    order_map = {
        "gap_desc":      "c.tariff_exposure_score DESC NULLS LAST",
        "exposure_desc": "c.tariff_exposure_score DESC NULLS LAST",
        "reaction_asc":  "sp.market_reaction_score ASC NULLS LAST",
        "reaction_desc": "sp.market_reaction_score DESC NULLS LAST",
    }
    if sort not in order_map:
        raise ValueError(f"sort must be one of {list(order_map)}")

    clauses, params = [], {}
    if sector:
        clauses.append("c.sector = :sector")
        params["sector"] = sector
    if confidence:
        clauses.append("c.confidence_level = :confidence")
        params["confidence"] = confidence
    if region:
        clauses.append("c.regions ? :region")
        params["region"] = region

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    params["limit"] = limit

    sql = text(f"""
        SELECT
            c.ticker, c.company_name, c.sector, c.sub_sector,
            c.tariff_exposure_score, c.exposure_level,
            c.confidence_level, c.confidence_reason,
            c.regions, c.exposure_pct_map,
            c.key_filing_quote, c.filing_date, c.filing_type,
            sp.price_date, sp.close_price, sp.adjusted_close, sp.volume,
            sp.price_delta_liberation_day_pct,
            sp.market_reaction_score, sp.reaction_score_adj
        FROM companies c
        LEFT JOIN LATERAL (
            SELECT price_date, close_price, adjusted_close, volume,
                   price_delta_liberation_day_pct, market_reaction_score, reaction_score_adj
            FROM stock_prices
            WHERE ticker = c.ticker
            ORDER BY price_date DESC
            LIMIT 1
        ) sp ON true
        {where}
        ORDER BY {order_map[sort]}
        LIMIT :limit
    """)

    with get_engine().connect() as conn:
        return pd.read_sql(sql, conn, params=params)


def read_escalation_history(days: int = 30) -> pd.DataFrame:
    """Return escalation index time series for the last N calendar days."""
    sql = text("""
        SELECT computed_at, index_score, label,
               component_deal_inverted, component_tariff_odds,
               component_gdelt_intensity, component_import_price,
               component_ppi, index_7d_change
        FROM escalation_index
        WHERE computed_at >= NOW() - make_interval(days => :days)
        ORDER BY computed_at ASC
    """)
    with get_engine().connect() as conn:
        return pd.read_sql(sql, conn, params={"days": days})


def read_events(
    severity: Optional[float] = None,
    country: Optional[str] = None,
    limit: int = 20,
) -> pd.DataFrame:
    """Return recent geopolitical events ordered by event_timestamp DESC.

    Args:
        severity: Minimum severity score (0–10).
        country: Filter to this country name (exact match).
        limit: Max rows.
    """
    clauses, params = [], {"limit": limit}
    if severity is not None:
        clauses.append("severity >= :severity")
        params["severity"] = severity
    if country:
        clauses.append("country = :country")
        params["country"] = country

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = text(f"""
        SELECT headline, country, severity, goldstein_scale, tone,
               event_timestamp, domain, source_url,
               affected_tickers, affected_sectors
        FROM geopolitical_events
        {where}
        ORDER BY event_timestamp DESC
        LIMIT :limit
    """)
    with get_engine().connect() as conn:
        return pd.read_sql(sql, conn, params=params)


def read_backtest() -> dict:
    """Return all backtest events as a dict keyed by event_name."""
    sql = text("""
        SELECT event_name, event_date, event_type,
               pre_event_trajectory, post_event_sector_returns,
               index_was_rising_pre_event, accuracy_note
        FROM backtest_events
        ORDER BY event_date ASC
    """)
    with get_engine().connect() as conn:
        df = pd.read_sql(sql, conn)
    return df.to_dict(orient="records")


# ── Freshness check ───────────────────────────────────────────────────────────

def check_freshness(table_name: str) -> dict:
    """Return staleness info for a table.

    Returns:
        {is_fresh: bool, age_minutes: float, last_updated: str}
        is_fresh = True if age < 60 minutes.
    """
    if table_name not in _ALLOWED_TABLES:
        raise ValueError(f"Unknown table: {table_name!r}")

    sql = text(f"SELECT MAX(updated_at) AS last_updated FROM {table_name}")
    with get_engine().connect() as conn:
        row = conn.execute(sql).fetchone()

    last_updated = row[0] if row and row[0] else None
    if last_updated is None:
        return {"is_fresh": False, "age_minutes": None, "last_updated": None}

    if last_updated.tzinfo is None:
        last_updated = last_updated.replace(tzinfo=timezone.utc)

    age = (datetime.now(timezone.utc) - last_updated).total_seconds() / 60
    return {
        "is_fresh": age < 60,
        "age_minutes": round(age, 1),
        "last_updated": last_updated.isoformat(),
    }
