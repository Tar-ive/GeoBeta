"""
Pydantic models matching the GeoAlpha Postgres schema.
Used for API response validation and data pipeline type safety.
"""
from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class Company(BaseModel):
    id: Optional[int] = None
    source_id: str
    ticker: str
    company_name: str
    sector: Optional[str] = None
    sub_sector: Optional[str] = None
    tariff_exposure_score: Optional[float] = None
    exposure_level: Optional[str] = None        # low | medium | high | critical
    confidence_level: Optional[str] = None      # low | medium | high
    confidence_reason: Optional[str] = None
    regions: Optional[dict[str, float]] = None
    exposure_pct_map: Optional[dict[str, float]] = None
    key_filing_quote: Optional[str] = None
    filing_date: Optional[date] = None
    filing_type: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class StockPrice(BaseModel):
    id: Optional[int] = None
    source_id: str                              # "{ticker}_{price_date}"
    ticker: str
    price_date: date
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    close_price: float
    adjusted_close: Optional[float] = None
    volume: Optional[int] = None
    dividend_amount: Optional[float] = None
    split_coefficient: Optional[float] = None
    price_delta_liberation_day_pct: Optional[float] = None
    market_reaction_score: Optional[float] = None
    reaction_score_adj: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PredictionMarket(BaseModel):
    id: Optional[int] = None
    source_id: str                              # "{source}_{source_market_id}"
    source: str                                 # polymarket | kalshi
    source_market_id: str
    question: str
    odds: Optional[float] = Field(None, ge=0.0, le=1.0)
    volume: Optional[float] = None
    expiry_date: Optional[datetime] = None
    sector_tags: Optional[list[str]] = None
    ticker_tags: Optional[list[str]] = None
    odds_7d_change: Optional[float] = None
    category: Optional[str] = None
    market_status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class GeopoliticalEvent(BaseModel):
    id: Optional[int] = None
    source_id: str                              # md5(source_url)
    source_event_id: Optional[str] = None
    headline: str
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lon: Optional[float] = Field(None, ge=-180, le=180)
    country: Optional[str] = None
    severity: Optional[float] = Field(None, ge=0, le=10)
    goldstein_scale: Optional[float] = Field(None, ge=-10, le=10)
    tone: Optional[float] = None
    affected_tickers: Optional[list[str]] = None
    affected_sectors: Optional[list[str]] = None
    source_url: Optional[str] = None
    domain: Optional[str] = None
    language: Optional[str] = None
    event_timestamp: datetime
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MacroSignal(BaseModel):
    id: Optional[int] = None
    source_id: str                              # "{series_id}_{observation_date}"
    series_id: str
    series_name: Optional[str] = None
    observation_date: date
    value: Optional[float] = None
    trend_score: Optional[float] = None
    direction: Optional[str] = None            # up | down | flat
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class EscalationIndex(BaseModel):
    id: Optional[int] = None
    source_id: str
    computed_at: datetime
    index_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    label: Optional[str] = None                # calm | elevated | crisis
    component_deal_inverted: Optional[float] = None
    component_tariff_odds: Optional[float] = None
    component_gdelt_intensity: Optional[float] = None
    component_import_price: Optional[float] = None
    component_ppi: Optional[float] = None
    index_7d_change: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class BacktestEvent(BaseModel):
    id: Optional[int] = None
    source_id: str
    event_name: str
    event_date: date
    event_type: Optional[str] = None
    pre_event_trajectory: Optional[dict[str, Any]] = None
    post_event_sector_returns: Optional[dict[str, Any]] = None
    index_was_rising_pre_event: Optional[bool] = None
    accuracy_note: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ── API response wrappers ─────────────────────────────────────────────────────

class ScreenerResponse(BaseModel):
    results: list[dict]
    total_count: int
    returned_count: int
    filters_applied: dict


class EscalationResponse(BaseModel):
    current: EscalationIndex
    history: list[dict]
    trend: str                                  # rising | falling | stable


class HealthResponse(BaseModel):
    status: str
    db_fresh: bool
    last_updated: Optional[str] = None
    checked_at: str
