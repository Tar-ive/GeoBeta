"""
FRED (Federal Reserve Economic Data) ingestion.
Fetches macro series observations and computes trend scores.

Called by Zerve block E1.
"""
import os
from typing import Optional

import pandas as pd
import requests

FRED_BASE = "https://api.stlouisfed.org/fred"
DEFAULT_KEY = os.environ.get("FRED_API_KEY", "")

SERIES_META = {
    "UNRATE":  "Unemployment Rate",
    "PCEPI":   "PCE Price Index",
    "MANEMP":  "Manufacturing Employment",
    "PPIFIS":  "PPI: Final Demand",
    "BOGMBASE":"Monetary Base",
}


def fetch_series(
    series_id: str,
    api_key: str = DEFAULT_KEY,
    start_date: str = "2020-01-01",
) -> pd.DataFrame:
    """Fetch all observations for a FRED series.

    Args:
        series_id: FRED series ID (e.g. 'UNRATE').
        api_key: FRED API key.
        start_date: Earliest observation date 'YYYY-MM-DD'.

    Returns:
        DataFrame with columns: series_id, series_name, observation_date, value
        Empty-string FRED values ("." or "") are stored as NaN.
    """
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start_date,
        "sort_order": "asc",
        "limit": 10000,
    }
    resp = requests.get(f"{FRED_BASE}/series/observations", params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if "error_message" in data:
        raise RuntimeError(f"FRED error for {series_id}: {data['error_message']}")

    rows = []
    for obs in data.get("observations", []):
        val_str = obs.get("value", ".")
        value = None if val_str in (".", "", None) else float(val_str)
        rows.append({
            "series_id": series_id,
            "series_name": SERIES_META.get(series_id, series_id),
            "observation_date": obs["date"],
            "value": value,
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df["observation_date"] = pd.to_datetime(df["observation_date"]).dt.date
    return df


def fetch_all_series(
    api_key: str = DEFAULT_KEY,
    start_date: str = "2020-01-01",
) -> pd.DataFrame:
    """Fetch all configured macro series and return a combined DataFrame.

    Args:
        api_key: FRED API key.
        start_date: Earliest observation date.

    Returns:
        Combined DataFrame for all series in SERIES_META.
    """
    frames = []
    for series_id in SERIES_META:
        try:
            df = fetch_series(series_id, api_key, start_date)
            frames.append(df)
            print(f"[fred] {series_id}: {len(df)} observations")
        except Exception as e:
            print(f"[fred] Error fetching {series_id}: {e}")
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def compute_trend_score(
    series_values: pd.Series,
    window_days: int = 30,
) -> dict:
    """Compute a normalized trend score for a macro series.

    Compares the mean of the last `window_days` values to the prior period.

    Args:
        series_values: Pandas Series of numeric values (chronological order).
        window_days: Window for the recent period.

    Returns:
        {trend_score: float (0–100), direction: str, change_pct: float}
    """
    clean = series_values.dropna()
    if len(clean) < window_days * 2:
        return {"trend_score": 50.0, "direction": "flat", "change_pct": 0.0}

    recent = clean.iloc[-window_days:].mean()
    prior = clean.iloc[-window_days * 2:-window_days].mean()

    if prior == 0:
        return {"trend_score": 50.0, "direction": "flat", "change_pct": 0.0}

    change_pct = ((recent - prior) / abs(prior)) * 100
    trend_score = min(100.0, max(0.0, 50.0 + change_pct * 2))
    direction = "up" if change_pct > 1 else ("down" if change_pct < -1 else "flat")

    return {
        "trend_score": round(trend_score, 2),
        "direction": direction,
        "change_pct": round(change_pct, 4),
    }
