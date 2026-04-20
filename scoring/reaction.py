"""
Market Reaction Score calculation.
Measures how much each stock moved relative to its sector peers since Liberation Day.

Called by Zerve block B3.
"""
import pandas as pd

LIBERATION_DAY = "2025-04-02"


def compute_delta(
    prices_df: pd.DataFrame,
    ticker: str,
    anchor_date: str = LIBERATION_DAY,
) -> float:
    """Compute percentage price change from anchor_date to most recent close.

    Args:
        prices_df: DataFrame with columns ticker, price_date, close_price.
        ticker: The ticker to compute delta for.
        anchor_date: Reference date (default: Liberation Day 2025-04-02).

    Returns:
        Percentage change as a float (e.g. -8.5 for -8.5%).
    """
    df = prices_df[prices_df["ticker"] == ticker].copy()
    df["price_date"] = pd.to_datetime(df["price_date"])
    anchor = pd.to_datetime(anchor_date)

    before = df[df["price_date"] <= anchor]
    after = df[df["price_date"] > anchor]

    if before.empty or after.empty:
        return 0.0

    anchor_price = before.sort_values("price_date").iloc[-1]["close_price"]
    latest_price = after.sort_values("price_date").iloc[-1]["close_price"]

    return round(((latest_price - anchor_price) / anchor_price) * 100, 4)


def normalize_deltas(deltas: dict[str, float]) -> dict[str, int]:
    """Normalize raw price deltas to 0–100 reaction scores.

    The most negative delta = 100 (strongest market reaction).
    Flat or positive deltas = 0 (no market reaction to tariff risk).

    Args:
        deltas: {ticker: pct_change} dict.

    Returns:
        {ticker: reaction_score (0–100)} dict.
    """
    if not deltas:
        return {}

    values = list(deltas.values())
    min_val = min(values)
    max_val = max(values)

    # If everything moved the same, return flat
    if max_val == min_val:
        return {t: 0 for t in deltas}

    scores = {}
    for ticker, delta in deltas.items():
        # Negative delta → higher reaction score
        normalized = (max_val - delta) / (max_val - min_val) * 100
        scores[ticker] = max(0, min(100, round(normalized)))

    return scores


def compute_sector_adjustment(reaction_scores: pd.DataFrame) -> pd.DataFrame:
    """Add sector_avg_reaction and reaction_score_adj columns to the screener DataFrame.

    Adjusts each company's reaction score relative to its sector average.
    A positive adj means the stock reacted MORE than sector peers (underpriced gap).

    Args:
        reaction_scores: DataFrame with columns: ticker, sector, market_reaction_score.

    Returns:
        Same DataFrame with two new columns added.
    """
    df = reaction_scores.copy()
    sector_avg = df.groupby("sector")["market_reaction_score"].transform("mean")
    df["sector_avg_reaction"] = sector_avg.round(2)
    df["reaction_score_adj"] = (df["market_reaction_score"] - sector_avg).round(2)
    return df


def compute_gap_score(exposure_score: float, reaction_score_adj: float) -> float:
    """Compute the gap between fundamental tariff exposure and market reaction.

    Positive gap = market hasn't priced in the exposure (underpriced risk).
    Negative gap = market overreacted vs. actual exposure (overpriced fear).

    Args:
        exposure_score: Tariff Exposure Score (0–100).
        reaction_score_adj: Sector-adjusted market reaction score (0–100).

    Returns:
        Gap score as a float (-100 to +100).
    """
    return round(exposure_score - reaction_score_adj, 2)


def gap_label(gap_score: float) -> str:
    """Classify a gap score into a human-readable label.

    Args:
        gap_score: Output of compute_gap_score.

    Returns:
        'underpriced risk' | 'fairly priced' | 'overpriced fear'
    """
    if gap_score > 15:
        return "underpriced risk"
    if gap_score < -15:
        return "overpriced fear"
    return "fairly priced"
