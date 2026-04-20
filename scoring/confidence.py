"""
Confidence level rating for tariff exposure assessments.
Evaluates signal quality to rate how reliable the exposure score is.

Called by Zerve block A5.
"""

HIGH_CONFIDENCE_CRITERIA = {
    "min_chunks_analyzed": 3,
    "requires_explicit_revenue_pct": True,
    "requires_direct_tariff_mention": True,
    "max_filing_age_days": 180,
}


def compute_confidence(signals_list: list[dict]) -> tuple[str, str]:
    """Aggregate confidence signals from multiple filing chunks.

    Args:
        signals_list: List of dicts from GenAI block output, each with:
            - has_explicit_revenue_pct: bool
            - has_direct_tariff_mention: bool
            - filing_date: str
            - chunk_count: int
            - extraction_quality: 'high' | 'medium' | 'low'

    Returns:
        (level, reason) where level is 'high' | 'medium' | 'low'
    """
    if not signals_list:
        return ("low", "No filing data available for this ticker.")

    total_chunks = sum(s.get("chunk_count", 1) for s in signals_list)
    has_revenue_pct = any(s.get("has_explicit_revenue_pct") for s in signals_list)
    has_tariff_mention = any(s.get("has_direct_tariff_mention") for s in signals_list)
    quality_scores = [s.get("extraction_quality", "low") for s in signals_list]
    high_quality_count = quality_scores.count("high")

    # High confidence: explicit revenue %, direct tariff mention, many chunks
    if (
        has_revenue_pct
        and has_tariff_mention
        and total_chunks >= HIGH_CONFIDENCE_CRITERIA["min_chunks_analyzed"]
        and high_quality_count >= 1
    ):
        return (
            "high",
            f"Explicit revenue exposure % found; direct tariff language confirmed across {total_chunks} filing sections.",
        )

    # Medium confidence: some direct evidence but incomplete
    if has_tariff_mention or has_revenue_pct:
        reasons = []
        if has_tariff_mention:
            reasons.append("direct tariff mentions found")
        if has_revenue_pct:
            reasons.append("revenue exposure % disclosed")
        else:
            reasons.append("revenue % not explicitly stated — estimated from geographic segment data")
        return ("medium", "; ".join(reasons).capitalize() + ".")

    # Low confidence: no direct evidence found
    return (
        "low",
        "No explicit tariff language or geographic revenue breakdown found in analyzed filing sections. Score is estimated from indirect signals.",
    )
