"""
Alpha Vantage stock price ingestion.
Fetches daily OHLCV data and computes delta from a given anchor date.

Called by Zerve block B1.
"""
import os
import time
from typing import Optional

import pandas as pd
import requests

AV_BASE = "https://www.alphavantage.co/query"
DEFAULT_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "")


def fetch_daily_prices(
    ticker: str,
    api_key: str = DEFAULT_KEY,
    start_date: Optional[str] = None,
) -> pd.DataFrame:
    """Fetch daily OHLCV prices for a single ticker.

    Uses TIME_SERIES_DAILY (free) if available; falls back gracefully.

    Args:
        ticker: Stock ticker symbol.
        api_key: Alpha Vantage API key.
        start_date: Optional 'YYYY-MM-DD' to filter rows after this date.

    Returns:
        DataFrame with columns: ticker, price_date, open, high, low, close, volume
        All numeric columns are float/int (not strings).
    """
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": ticker,
        "apikey": api_key,
        "outputsize": "full",
        "datatype": "json",
    }
    resp = requests.get(AV_BASE, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if "Information" in data or "Note" in data:
        msg = data.get("Information") or data.get("Note")
        raise RuntimeError(f"Alpha Vantage rate limit or premium required: {msg}")

    ts = data.get("Time Series (Daily)", {})
    rows = []
    for date_str, vals in ts.items():
        rows.append({
            "ticker": ticker,
            "price_date": date_str,
            "open_price": float(vals["1. open"]),
            "high_price": float(vals["2. high"]),
            "low_price": float(vals["3. low"]),
            "close_price": float(vals["4. close"]),
            "volume": int(vals["5. volume"]),
            "adjusted_close": float(vals.get("5. adjusted close", vals["4. close"])),
            "dividend_amount": float(vals.get("7. dividend amount", 0)),
            "split_coefficient": float(vals.get("8. split coefficient", 1)),
        })

    df = pd.DataFrame(rows)
    df["price_date"] = pd.to_datetime(df["price_date"]).dt.date
    df = df.sort_values("price_date")

    if start_date:
        df = df[df["price_date"] >= pd.to_datetime(start_date).date()]

    return df.reset_index(drop=True)


def compute_delta_from_date(prices_df: pd.DataFrame, anchor_date: str) -> float:
    """Compute percentage price change from anchor_date to most recent close.

    Args:
        prices_df: DataFrame from fetch_daily_prices (must have price_date, close_price).
        anchor_date: Reference date string 'YYYY-MM-DD' (e.g. Liberation Day 2025-04-02).

    Returns:
        Percentage change as a float (e.g. -8.5 means -8.5%).
        Returns 0.0 if anchor_date is not in the data.
    """
    anchor = pd.to_datetime(anchor_date).date()
    anchor_rows = prices_df[prices_df["price_date"] <= anchor]
    if anchor_rows.empty:
        return 0.0

    anchor_price = anchor_rows.iloc[-1]["close_price"]
    latest_price = prices_df.iloc[-1]["close_price"]
    return round(((latest_price - anchor_price) / anchor_price) * 100, 4)


def fetch_all_tickers(
    tickers: list[str],
    api_key: str = DEFAULT_KEY,
    start_date: Optional[str] = None,
    requests_per_minute: int = 5,
) -> pd.DataFrame:
    """Fetch daily prices for a list of tickers with rate limiting.

    Args:
        tickers: List of ticker symbols.
        api_key: Alpha Vantage API key.
        start_date: Optional start date filter.
        requests_per_minute: Free tier = 5, premium = 75+.

    Returns:
        Combined DataFrame for all tickers.
    """
    delay = 60.0 / requests_per_minute
    frames = []
    for i, ticker in enumerate(tickers):
        try:
            df = fetch_daily_prices(ticker, api_key, start_date)
            frames.append(df)
            print(f"[alpha_vantage] {ticker}: {len(df)} rows")
        except Exception as e:
            print(f"[alpha_vantage] Error fetching {ticker}: {e}")
        if i < len(tickers) - 1:
            time.sleep(delay)

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
