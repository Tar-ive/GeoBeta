"""
Idempotent upsert helpers for all GeoAlpha tables.
All functions use INSERT ... ON CONFLICT (source_id) DO UPDATE SET
so pipelines can re-run without creating duplicates.

Import via db.client (re-exported) or directly:
    from db.upsert import upsert_company
"""
import json
from typing import Optional

from sqlalchemy import text

from .client import get_engine


def _defaults(row: dict, defaults: dict) -> dict:
    return {**defaults, **row}


def _jsonb(val) -> Optional[str]:
    """Serialize a value to a JSON string for psycopg2 JSONB binding."""
    if val is None:
        return None
    return json.dumps(val) if not isinstance(val, str) else val


def upsert_company(row: dict) -> None:
    """Upsert one company row.

    Required: source_id, ticker, company_name
    """
    row = _defaults(row, {
        "sector": None, "sub_sector": None,
        "tariff_exposure_score": None, "exposure_level": None,
        "confidence_level": None, "confidence_reason": None,
        "regions": None, "exposure_pct_map": None,
        "key_filing_quote": None, "filing_date": None, "filing_type": None,
    })
    row["regions"] = _jsonb(row.get("regions"))
    row["exposure_pct_map"] = _jsonb(row.get("exposure_pct_map"))

    sql = text("""
        INSERT INTO companies (
            source_id, ticker, company_name, sector, sub_sector,
            tariff_exposure_score, exposure_level, confidence_level, confidence_reason,
            regions, exposure_pct_map, key_filing_quote, filing_date, filing_type,
            updated_at
        ) VALUES (
            :source_id, :ticker, :company_name, :sector, :sub_sector,
            :tariff_exposure_score, :exposure_level, :confidence_level, :confidence_reason,
            :regions::jsonb, :exposure_pct_map::jsonb,
            :key_filing_quote, :filing_date, :filing_type,
            NOW()
        )
        ON CONFLICT (source_id) DO UPDATE SET
            ticker                = EXCLUDED.ticker,
            company_name          = EXCLUDED.company_name,
            sector                = EXCLUDED.sector,
            sub_sector            = EXCLUDED.sub_sector,
            tariff_exposure_score = EXCLUDED.tariff_exposure_score,
            exposure_level        = EXCLUDED.exposure_level,
            confidence_level      = EXCLUDED.confidence_level,
            confidence_reason     = EXCLUDED.confidence_reason,
            regions               = EXCLUDED.regions,
            exposure_pct_map      = EXCLUDED.exposure_pct_map,
            key_filing_quote      = EXCLUDED.key_filing_quote,
            filing_date           = EXCLUDED.filing_date,
            filing_type           = EXCLUDED.filing_type,
            updated_at            = NOW()
    """)
    with get_engine().begin() as conn:
        conn.execute(sql, row)


def upsert_stock_price(row: dict) -> None:
    """Upsert one daily stock price row.

    Required: source_id, ticker, price_date, close_price
    """
    row = _defaults(row, {
        "open_price": None, "high_price": None, "low_price": None,
        "adjusted_close": None, "volume": None,
        "dividend_amount": None, "split_coefficient": None,
        "price_delta_liberation_day_pct": None,
        "market_reaction_score": None, "reaction_score_adj": None,
    })
    sql = text("""
        INSERT INTO stock_prices (
            source_id, ticker, price_date,
            open_price, high_price, low_price, close_price,
            adjusted_close, volume, dividend_amount, split_coefficient,
            price_delta_liberation_day_pct,
            market_reaction_score, reaction_score_adj,
            updated_at
        ) VALUES (
            :source_id, :ticker, :price_date,
            :open_price, :high_price, :low_price, :close_price,
            :adjusted_close, :volume, :dividend_amount, :split_coefficient,
            :price_delta_liberation_day_pct,
            :market_reaction_score, :reaction_score_adj,
            NOW()
        )
        ON CONFLICT (source_id) DO UPDATE SET
            open_price                     = EXCLUDED.open_price,
            high_price                     = EXCLUDED.high_price,
            low_price                      = EXCLUDED.low_price,
            close_price                    = EXCLUDED.close_price,
            adjusted_close                 = EXCLUDED.adjusted_close,
            volume                         = EXCLUDED.volume,
            dividend_amount                = EXCLUDED.dividend_amount,
            split_coefficient              = EXCLUDED.split_coefficient,
            price_delta_liberation_day_pct = EXCLUDED.price_delta_liberation_day_pct,
            market_reaction_score          = EXCLUDED.market_reaction_score,
            reaction_score_adj             = EXCLUDED.reaction_score_adj,
            updated_at                     = NOW()
    """)
    with get_engine().begin() as conn:
        conn.execute(sql, row)


def upsert_market(row: dict) -> None:
    """Upsert one prediction market snapshot.

    Required: source_id, source, source_market_id, question
    """
    row = _defaults(row, {
        "odds": None, "volume": None, "expiry_date": None,
        "sector_tags": None, "ticker_tags": None,
        "odds_7d_change": None, "category": None, "market_status": None,
    })
    row["sector_tags"] = _jsonb(row.get("sector_tags"))
    row["ticker_tags"] = _jsonb(row.get("ticker_tags"))

    sql = text("""
        INSERT INTO prediction_markets (
            source_id, source, source_market_id, question,
            odds, volume, expiry_date, sector_tags, ticker_tags,
            odds_7d_change, category, market_status, updated_at
        ) VALUES (
            :source_id, :source, :source_market_id, :question,
            :odds, :volume, :expiry_date,
            :sector_tags::jsonb, :ticker_tags::jsonb,
            :odds_7d_change, :category, :market_status, NOW()
        )
        ON CONFLICT (source_id) DO UPDATE SET
            question       = EXCLUDED.question,
            odds           = EXCLUDED.odds,
            volume         = EXCLUDED.volume,
            expiry_date    = EXCLUDED.expiry_date,
            sector_tags    = EXCLUDED.sector_tags,
            ticker_tags    = EXCLUDED.ticker_tags,
            odds_7d_change = EXCLUDED.odds_7d_change,
            category       = EXCLUDED.category,
            market_status  = EXCLUDED.market_status,
            updated_at     = NOW()
    """)
    with get_engine().begin() as conn:
        conn.execute(sql, row)


def upsert_event(row: dict) -> None:
    """Upsert one geopolitical event.

    Required: source_id, headline, event_timestamp
    """
    row = _defaults(row, {
        "source_event_id": None, "lat": None, "lon": None, "country": None,
        "severity": None, "goldstein_scale": None, "tone": None,
        "affected_tickers": None, "affected_sectors": None,
        "source_url": None, "domain": None, "language": None,
    })
    row["affected_tickers"] = _jsonb(row.get("affected_tickers"))
    row["affected_sectors"] = _jsonb(row.get("affected_sectors"))

    sql = text("""
        INSERT INTO geopolitical_events (
            source_id, source_event_id, headline,
            lat, lon, country,
            severity, goldstein_scale, tone,
            affected_tickers, affected_sectors,
            source_url, domain, language,
            event_timestamp, updated_at
        ) VALUES (
            :source_id, :source_event_id, :headline,
            :lat, :lon, :country,
            :severity, :goldstein_scale, :tone,
            :affected_tickers::jsonb, :affected_sectors::jsonb,
            :source_url, :domain, :language,
            :event_timestamp, NOW()
        )
        ON CONFLICT (source_id) DO UPDATE SET
            headline         = EXCLUDED.headline,
            lat              = EXCLUDED.lat,
            lon              = EXCLUDED.lon,
            country          = EXCLUDED.country,
            severity         = EXCLUDED.severity,
            goldstein_scale  = EXCLUDED.goldstein_scale,
            tone             = EXCLUDED.tone,
            affected_tickers = EXCLUDED.affected_tickers,
            affected_sectors = EXCLUDED.affected_sectors,
            source_url       = EXCLUDED.source_url,
            domain           = EXCLUDED.domain,
            language         = EXCLUDED.language,
            event_timestamp  = EXCLUDED.event_timestamp,
            updated_at       = NOW()
    """)
    with get_engine().begin() as conn:
        conn.execute(sql, row)


def upsert_macro_signal(row: dict) -> None:
    """Upsert one FRED observation row.

    Required: source_id, series_id, observation_date
    """
    row = _defaults(row, {
        "series_name": None, "value": None,
        "trend_score": None, "direction": None,
    })
    sql = text("""
        INSERT INTO macro_signals (
            source_id, series_id, series_name, observation_date,
            value, trend_score, direction, updated_at
        ) VALUES (
            :source_id, :series_id, :series_name, :observation_date,
            :value, :trend_score, :direction, NOW()
        )
        ON CONFLICT (source_id) DO UPDATE SET
            series_name  = EXCLUDED.series_name,
            value        = EXCLUDED.value,
            trend_score  = EXCLUDED.trend_score,
            direction    = EXCLUDED.direction,
            updated_at   = NOW()
    """)
    with get_engine().begin() as conn:
        conn.execute(sql, row)


def upsert_escalation_index(row: dict) -> None:
    """Upsert one escalation index computation.

    Required: source_id, computed_at
    """
    row = _defaults(row, {
        "index_score": None, "label": None,
        "component_deal_inverted": None, "component_tariff_odds": None,
        "component_gdelt_intensity": None, "component_import_price": None,
        "component_ppi": None, "index_7d_change": None,
    })
    sql = text("""
        INSERT INTO escalation_index (
            source_id, computed_at, index_score, label,
            component_deal_inverted, component_tariff_odds,
            component_gdelt_intensity, component_import_price, component_ppi,
            index_7d_change, updated_at
        ) VALUES (
            :source_id, :computed_at, :index_score, :label,
            :component_deal_inverted, :component_tariff_odds,
            :component_gdelt_intensity, :component_import_price, :component_ppi,
            :index_7d_change, NOW()
        )
        ON CONFLICT (source_id) DO UPDATE SET
            index_score               = EXCLUDED.index_score,
            label                     = EXCLUDED.label,
            component_deal_inverted   = EXCLUDED.component_deal_inverted,
            component_tariff_odds     = EXCLUDED.component_tariff_odds,
            component_gdelt_intensity = EXCLUDED.component_gdelt_intensity,
            component_import_price    = EXCLUDED.component_import_price,
            component_ppi             = EXCLUDED.component_ppi,
            index_7d_change           = EXCLUDED.index_7d_change,
            updated_at                = NOW()
    """)
    with get_engine().begin() as conn:
        conn.execute(sql, row)
