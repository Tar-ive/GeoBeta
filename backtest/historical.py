"""
Historical escalation index computation (no-lookahead).
Reconstructs what the index would have been on any historical date
using only data available at that time.

Called by Zerve block F (backtest blocks).
"""
from datetime import datetime

import pandas as pd

HISTORICAL_EVENTS = [
    {
        "event_name": "US-China Trade War: Section 301 Tariffs Begin",
        "event_date": "2018-07-06",
        "event_type": "trade_war",
    },
    {
        "event_name": "Phase 1 Trade Deal Signed",
        "event_date": "2020-01-15",
        "event_type": "trade_deal",
    },
    {
        "event_name": "WHO Declares COVID-19 a Pandemic",
        "event_date": "2020-03-11",
        "event_type": "pandemic_shock",
    },
    {
        "event_name": "Liberation Day Tariffs Announced",
        "event_date": "2025-04-02",
        "event_type": "trade_war",
    },
]


def compute_index_on_date(
    date: str,
    hist_macro_df: pd.DataFrame,
) -> float:
    """Compute a simplified escalation index for a single historical date.

    Uses only PPI and PCEPI data available on or before that date.
    No prediction market data (not available historically).

    Args:
        date: Target date string 'YYYY-MM-DD'.
        hist_macro_df: DataFrame with columns: series_id, observation_date, value.

    Returns:
        Escalation index score in [0, 1].
    """
    cutoff = pd.to_datetime(date).date()
    df = hist_macro_df[pd.to_datetime(hist_macro_df["observation_date"]).dt.date <= cutoff]

    # Use PPI trend as proxy for escalation pressure
    ppi = df[df["series_id"] == "PPIFIS"]["value"].dropna()
    pcepi = df[df["series_id"] == "PCEPI"]["value"].dropna()

    score = 0.5  # default baseline

    if len(ppi) >= 12:
        recent_avg = ppi.iloc[-3:].mean()
        prior_avg = ppi.iloc[-12:-3].mean()
        if prior_avg > 0:
            ppi_change = (recent_avg - prior_avg) / prior_avg
            score = min(1.0, max(0.0, 0.5 + ppi_change * 5))

    if len(pcepi) >= 12:
        recent_avg = pcepi.iloc[-3:].mean()
        prior_avg = pcepi.iloc[-12:-3].mean()
        if prior_avg > 0:
            pce_change = (recent_avg - prior_avg) / prior_avg
            score = (score + min(1.0, max(0.0, 0.5 + pce_change * 5))) / 2

    return round(score, 4)


def compute_full_history(hist_macro_df: pd.DataFrame) -> pd.DataFrame:
    """Compute the escalation index for every month from 2017-01-01 to present.

    Args:
        hist_macro_df: Historical macro DataFrame (FRED data from 2017 onward).

    Returns:
        DataFrame with columns: date, index_score
    """
    dates = pd.date_range(start="2017-01-01", end=datetime.today(), freq="MS")
    rows = []
    for dt in dates:
        date_str = dt.strftime("%Y-%m-%d")
        score = compute_index_on_date(date_str, hist_macro_df)
        rows.append({"date": date_str, "index_score": score})

    return pd.DataFrame(rows)
