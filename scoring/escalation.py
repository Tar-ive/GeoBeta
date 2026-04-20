"""
Escalation Index calculation.
Combines prediction market odds, GDELT intensity, and macro signals
into a single 0–1 geopolitical risk score.

Called by Zerve block G1.
"""
from datetime import datetime, timezone

import numpy as np
import pandas as pd

WEIGHTS = {
    "deal_inverted":  0.30,
    "tariff_odds":    0.25,
    "gdelt":          0.20,
    "import_price":   0.15,
    "ppi":            0.10,
}

LABEL_THRESHOLDS = [
    (0.30, "calm"),
    (0.60, "elevated"),
    (1.01, "crisis"),
]


def escalation_label(score: float) -> str:
    """Map escalation index score (0–1) to a label.

    Returns: 'calm' | 'elevated' | 'crisis'
    """
    for threshold, label in LABEL_THRESHOLDS:
        if score < threshold:
            return label
    return "crisis"


def compute_gdelt_intensity(events_df: pd.DataFrame) -> float:
    """Compute normalized GDELT intensity score from recent events.

    Uses event count and average negative tone to produce a 0–1 score.

    Args:
        events_df: DataFrame with columns: tone, severity, event_timestamp.

    Returns:
        Float in [0, 1].
    """
    if events_df.empty:
        return 0.0

    count_score = min(1.0, len(events_df) / 50.0)

    if "tone" in events_df.columns and events_df["tone"].notna().any():
        avg_tone = events_df["tone"].dropna().mean()
        # GDELT tone: negative = bad. Map to 0–1 (more negative → higher score).
        tone_score = min(1.0, max(0.0, (-avg_tone) / 10.0))
    else:
        tone_score = 0.5

    return round(count_score * 0.5 + tone_score * 0.5, 4)


def compute_escalation_index(
    markets_df: pd.DataFrame,
    events_df: pd.DataFrame,
    macro_df: pd.DataFrame,
) -> dict:
    """Compute the full Escalation Index from the three data sources.

    Args:
        markets_df: prediction_markets DataFrame (needs odds, category columns).
        events_df: geopolitical_events DataFrame (needs tone, event_timestamp).
        macro_df: macro_signals DataFrame (needs series_id, value, observation_date).

    Returns:
        {
            index_score: float (0–1),
            label: str,
            components: dict,
            computed_at: str (ISO 8601 UTC),
        }
    """
    # Component 1: deal_inverted — inverse of trade-deal probability
    # If there's a "trade deal" market, high odds of a deal → low escalation
    deal_markets = markets_df[
        markets_df["question"].str.lower().str.contains("trade deal|trade agreement", na=False)
    ] if not markets_df.empty else pd.DataFrame()
    deal_odds = deal_markets["odds"].mean() if not deal_markets.empty else 0.3
    component_deal_inverted = round(1.0 - float(deal_odds or 0.3), 4)

    # Component 2: tariff_odds — average odds of tariff escalation markets
    tariff_markets = markets_df[
        markets_df["category"].isin(["trade_policy"]) if "category" in markets_df.columns else []
    ] if not markets_df.empty else pd.DataFrame()
    component_tariff_odds = round(float(tariff_markets["odds"].mean()) if not tariff_markets.empty else 0.5, 4)

    # Component 3: GDELT intensity
    component_gdelt = compute_gdelt_intensity(events_df)

    # Component 4: import price index trend (PPIFIS or similar)
    component_import_price = _macro_component(macro_df, "PPIFIS")

    # Component 5: PPI trend
    component_ppi = _macro_component(macro_df, "PPIFIS")

    index_score = round(
        WEIGHTS["deal_inverted"]  * component_deal_inverted +
        WEIGHTS["tariff_odds"]    * component_tariff_odds +
        WEIGHTS["gdelt"]          * component_gdelt +
        WEIGHTS["import_price"]   * component_import_price +
        WEIGHTS["ppi"]            * component_ppi,
        4,
    )

    return {
        "index_score": index_score,
        "label": escalation_label(index_score),
        "components": {
            "deal_inverted":  component_deal_inverted,
            "tariff_odds":    component_tariff_odds,
            "gdelt":          component_gdelt,
            "import_price":   component_import_price,
            "ppi":            component_ppi,
        },
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }


def _macro_component(macro_df: pd.DataFrame, series_id: str) -> float:
    """Extract a 0–1 trend component from a macro series."""
    if macro_df.empty or "series_id" not in macro_df.columns:
        return 0.5
    series = macro_df[macro_df["series_id"] == series_id]["value"].dropna()
    if len(series) < 2:
        return 0.5
    # Normalize recent value relative to 2-year range
    recent = series.iloc[-1]
    lo, hi = series.min(), series.max()
    if hi == lo:
        return 0.5
    return round(min(1.0, max(0.0, (recent - lo) / (hi - lo))), 4)
