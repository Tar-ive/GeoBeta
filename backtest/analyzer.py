"""
Backtest accuracy analyzer.
Evaluates how well the escalation index predicted each historical event.
"""
import pandas as pd

from .historical import HISTORICAL_EVENTS, compute_full_history


def analyze_event(
    event: dict,
    hist_escalation_df: pd.DataFrame,
    hist_prices_df: pd.DataFrame,
) -> dict:
    """Analyze model accuracy around a single historical event.

    Args:
        event: Event dict with event_name, event_date, event_type.
        hist_escalation_df: DataFrame from compute_full_history (date, index_score).
        hist_prices_df: Historical stock prices DataFrame (ticker, price_date, close_price).

    Returns:
        Dict with: pre_event_trajectory, post_event_sector_returns,
                   was_rising, accuracy_note
    """
    event_dt = pd.to_datetime(event["event_date"])

    # Pre-event trajectory: index scores for 7 days before
    pre = hist_escalation_df[
        (pd.to_datetime(hist_escalation_df["date"]) >= event_dt - pd.Timedelta(days=7)) &
        (pd.to_datetime(hist_escalation_df["date"]) < event_dt)
    ].sort_values("date")

    trajectory = {
        f"day_minus_{7 - i}": round(row["index_score"], 4)
        for i, (_, row) in enumerate(pre.iterrows())
    }

    was_rising = False
    if len(pre) >= 2:
        was_rising = pre.iloc[-1]["index_score"] > pre.iloc[0]["index_score"]

    # Post-event sector returns (30-day window)
    post_start = event_dt
    post_end = event_dt + pd.Timedelta(days=30)
    post_prices = hist_prices_df[
        (pd.to_datetime(hist_prices_df["price_date"]) >= post_start) &
        (pd.to_datetime(hist_prices_df["price_date"]) <= post_end)
    ]

    sector_returns: dict = {}
    # TODO: join with companies table to get sector, then compute sector ETF-equivalent returns
    # For now return empty dict; Zerve block F will populate this from hist_prices_df + sector map

    accuracy = "rising" if was_rising else "flat/falling"
    accuracy_note = (
        f"Index was {accuracy} in the 7 days before the event. "
        f"Event type: {event.get('event_type', 'unknown')}."
    )

    return {
        "event_name": event["event_name"],
        "event_date": event["event_date"],
        "event_type": event.get("event_type"),
        "pre_event_trajectory": trajectory,
        "post_event_sector_returns": sector_returns,
        "index_was_rising_pre_event": was_rising,
        "accuracy_note": accuracy_note,
    }


def run_full_backtest(
    hist_macro_df: pd.DataFrame,
    hist_prices_df: pd.DataFrame,
) -> pd.DataFrame:
    """Run analyze_event for all HISTORICAL_EVENTS.

    Args:
        hist_macro_df: FRED macro data DataFrame.
        hist_prices_df: Historical stock prices DataFrame.

    Returns:
        DataFrame of backtest results, one row per event.
    """
    hist_escalation_df = compute_full_history(hist_macro_df)
    results = []
    for event in HISTORICAL_EVENTS:
        result = analyze_event(event, hist_escalation_df, hist_prices_df)
        results.append(result)
    return pd.DataFrame(results)
