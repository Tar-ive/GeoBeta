"""
Mock data for offline development and Streamlit testing.
Mirrors the real API response shape exactly.
Set USE_MOCK=true to use this instead of hitting the real API.
"""

MOCK_SCREENER = [
    {
        "ticker": "NVDA", "company_name": "NVIDIA Corporation",
        "sector": "Technology", "sub_sector": "Semiconductors",
        "tariff_exposure_score": 91.0, "exposure_level": "critical",
        "confidence_level": "high", "confidence_reason": "Direct chip export ban language in 10-K",
        "regions": {"China": 0.21, "Taiwan": 0.15},
        "price_date": "2026-04-17", "close_price": 201.68,
        "price_delta_liberation_day_pct": -8.5,
        "market_reaction_score": 85.0, "reaction_score_adj": 12.0,
    },
    {
        "ticker": "AAPL", "company_name": "Apple Inc.",
        "sector": "Technology", "sub_sector": "Consumer Electronics",
        "tariff_exposure_score": 82.5, "exposure_level": "high",
        "confidence_level": "high", "confidence_reason": "Explicit China manufacturing + revenue %",
        "regions": {"China": 0.19, "Europe": 0.25},
        "price_date": "2026-04-17", "close_price": 270.23,
        "price_delta_liberation_day_pct": 3.2,
        "market_reaction_score": 42.0, "reaction_score_adj": -30.5,
    },
    {
        "ticker": "NKE", "company_name": "Nike Inc.",
        "sector": "Consumer Discretionary", "sub_sector": "Apparel & Footwear",
        "tariff_exposure_score": 71.0, "exposure_level": "high",
        "confidence_level": "high", "confidence_reason": "96% footwear manufactured in Asia",
        "regions": {"China": 0.16, "Vietnam": 0.28},
        "price_date": "2026-04-17", "close_price": 46.03,
        "price_delta_liberation_day_pct": -11.3,
        "market_reaction_score": 92.0, "reaction_score_adj": 21.0,
    },
    {
        "ticker": "TSLA", "company_name": "Tesla Inc.",
        "sector": "Consumer Discretionary", "sub_sector": "Electric Vehicles",
        "tariff_exposure_score": 76.0, "exposure_level": "high",
        "confidence_level": "high", "confidence_reason": "Gigafactory Shanghai + China sales",
        "regions": {"China": 0.22, "Europe": 0.28},
        "price_date": "2026-04-17", "close_price": 400.62,
        "price_delta_liberation_day_pct": -4.1,
        "market_reaction_score": 55.0, "reaction_score_adj": -16.0,
    },
    {
        "ticker": "CAT", "company_name": "Caterpillar Inc.",
        "sector": "Industrials", "sub_sector": "Heavy Machinery",
        "tariff_exposure_score": 58.0, "exposure_level": "medium",
        "confidence_level": "medium", "confidence_reason": "Retaliatory tariff risk on exports",
        "regions": {"China": 0.08, "Europe": 0.22},
        "price_date": "2026-04-17", "close_price": 794.65,
        "price_delta_liberation_day_pct": -5.2,
        "market_reaction_score": 60.0, "reaction_score_adj": 2.0,
    },
]

MOCK_ESCALATION = {
    "current": {
        "computed_at": "2026-04-20T12:00:00+00:00",
        "index_score": 0.784,
        "label": "high",
        "component_deal_inverted": 0.82,
        "component_tariff_odds": 0.76,
        "component_gdelt_intensity": 0.71,
        "component_import_price": 0.84,
        "component_ppi": 0.75,
        "index_7d_change": 0.062,
    },
    "history": [
        {"computed_at": "2026-04-06T12:00:00+00:00", "index_score": 0.674, "label": "medium", "index_7d_change": 0.031},
        {"computed_at": "2026-04-13T12:00:00+00:00", "index_score": 0.722, "label": "high", "index_7d_change": 0.048},
        {"computed_at": "2026-04-20T12:00:00+00:00", "index_score": 0.784, "label": "high", "index_7d_change": 0.062},
    ],
    "trend": "rising",
}

MOCK_EVENTS = [
    {
        "headline": "India-US trade talks to begin in Washington today, Trump tariffs in focus",
        "country": "India", "severity": 6.8, "tone": -3.2,
        "event_timestamp": "2026-04-20T05:00:00+00:00",
        "domain": "hindustantimes.com",
        "source_url": "https://www.hindustantimes.com/india-news/indiaus-trade-talks-to-begin-in-washington-soon",
        "affected_tickers": [], "affected_sectors": ["Technology", "Industrials"],
    },
    {
        "headline": "This tariff-refund portal is about to be America's hottest website",
        "country": "United States", "severity": 4.5, "tone": 1.1,
        "event_timestamp": "2026-04-19T23:30:00+00:00",
        "domain": "wgbh.org",
        "source_url": "https://www.wgbh.org/news/national/2026-04-19/tariff-refund-portal",
        "affected_tickers": ["AAPL", "NKE"], "affected_sectors": ["Consumer Discretionary"],
    },
]

MOCK_BACKTEST = [
    {
        "event_name": "US-China Trade War: Section 301 Tariffs Begin",
        "event_date": "2018-07-06", "event_type": "trade_war",
        "index_was_rising_pre_event": True,
        "pre_event_trajectory": {"day_minus_7": 0.42, "day_minus_3": 0.51, "day_minus_1": 0.55},
        "post_event_sector_returns": {"XLI": -0.062, "XLK": -0.038, "XLY": -0.071},
        "accuracy_note": "Index was rising. Model correctly predicted direction in 4 of 5 sector calls.",
    },
    {
        "event_name": "WHO Declares COVID-19 a Pandemic",
        "event_date": "2020-03-11", "event_type": "pandemic_shock",
        "index_was_rising_pre_event": True,
        "pre_event_trajectory": {"day_minus_7": 0.38, "day_minus_3": 0.52, "day_minus_1": 0.63},
        "post_event_sector_returns": {"XLV": -0.112, "XLK": -0.189, "XLY": -0.245},
        "accuracy_note": "Model sensitivity: 0.91, specificity: 0.74.",
    },
]
