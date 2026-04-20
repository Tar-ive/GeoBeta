"""
Tariff Exposure Score calculation.
Aggregates LLM extractions from SEC filings into a single 0–100 score.

Called by Zerve block A5 (scorer) after the GenAI block A4 runs.
"""
from typing import Optional

RISK_SCORE_MAP = {
    "NONE": 0,
    "LOW": 20,
    "MEDIUM": 45,
    "HIGH": 70,
    "CRITICAL": 90,
}

LEVEL_THRESHOLDS = [
    (15,  "none"),
    (35,  "low"),
    (60,  "medium"),
    (80,  "high"),
    (101, "critical"),
]


def exposure_level_from_score(score: float) -> str:
    """Map a numeric exposure score to a level label.

    Args:
        score: 0–100 numeric score.

    Returns:
        'none' | 'low' | 'medium' | 'high' | 'critical'
    """
    for threshold, label in LEVEL_THRESHOLDS:
        if score < threshold:
            return label
    return "critical"


def score_from_extractions(extractions: list[dict]) -> dict:
    """Aggregate GenAI block outputs for one ticker into a unified exposure profile.

    Weights the most recent filing at 60% and prior filings at 40%.

    Args:
        extractions: List of extraction dicts from nlp.extractor.extract_supply_chain.
                     Each dict should have: exposure_level, regions, key_quote,
                     revenue_pct_china, revenue_pct_asia, confidence_signals.

    Returns:
        {
            exposure_score: float (0–100),
            exposure_level: str,
            regions: dict,
            exposure_pct_map: dict,
            key_quote: str,
        }
    """
    if not extractions:
        return {
            "exposure_score": 0.0,
            "exposure_level": "none",
            "regions": {},
            "exposure_pct_map": {},
            "key_quote": "",
        }

    # Sort by filing recency (extractions should have filing_date)
    sorted_exts = sorted(
        extractions,
        key=lambda x: x.get("filing_date", "1900-01-01"),
        reverse=True,
    )

    if len(sorted_exts) == 1:
        weights = [1.0]
    else:
        weights = [0.60, 0.40] + [0.0] * max(0, len(sorted_exts) - 2)
    weighted_score = 0.0
    all_regions: dict = {}
    all_pct_map: dict = {}
    best_quote = ""

    for ext, w in zip(sorted_exts, weights):
        level = str(ext.get("exposure_level", "LOW")).upper()
        base_score = RISK_SCORE_MAP.get(level, RISK_SCORE_MAP["LOW"])

        # Adjust upward for high China/Asia revenue percentages
        china_pct = float(ext.get("revenue_pct_china", 0) or 0)
        asia_pct = float(ext.get("revenue_pct_asia", 0) or 0)
        adjustment = min(20, china_pct * 0.3 + asia_pct * 0.1)

        weighted_score += w * (base_score + adjustment)

        # Merge regions from all filings
        for region, pct in (ext.get("regions") or {}).items():
            all_regions[region] = max(all_regions.get(region, 0), pct)

        for category, pct in (ext.get("exposure_pct_map") or {}).items():
            all_pct_map[category] = max(all_pct_map.get(category, 0), pct)

        if not best_quote and ext.get("key_quote"):
            best_quote = ext["key_quote"]

    final_score = round(min(100.0, max(0.0, weighted_score)), 2)
    return {
        "exposure_score": final_score,
        "exposure_level": exposure_level_from_score(final_score),
        "regions": all_regions,
        "exposure_pct_map": all_pct_map,
        "key_quote": best_quote,
    }
