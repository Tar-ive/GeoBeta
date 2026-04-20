"""Tests for scoring modules."""
import pytest
from scoring.exposure import score_from_extractions, exposure_level_from_score
from scoring.reaction import compute_gap_score, gap_label, normalize_deltas
from scoring.confidence import compute_confidence


def test_exposure_level_thresholds():
    assert exposure_level_from_score(5) == "none"
    assert exposure_level_from_score(25) == "low"
    assert exposure_level_from_score(50) == "medium"
    assert exposure_level_from_score(75) == "high"
    assert exposure_level_from_score(90) == "critical"


def test_score_from_extractions_empty():
    result = score_from_extractions([])
    assert result["exposure_score"] == 0.0
    assert result["exposure_level"] == "none"


def test_score_from_extractions_high():
    extractions = [
        {
            "exposure_level": "HIGH",
            "revenue_pct_china": 20.0,
            "revenue_pct_asia": 35.0,
            "regions": {"China": 0.20},
            "exposure_pct_map": {},
            "key_quote": "Our operations in China...",
            "filing_date": "2024-01-01",
        }
    ]
    result = score_from_extractions(extractions)
    assert result["exposure_score"] > 50
    assert result["exposure_level"] in ("medium", "high", "critical")


def test_normalize_deltas():
    deltas = {"AAPL": 3.0, "NVDA": -10.0, "CAT": -5.0}
    scores = normalize_deltas(deltas)
    assert scores["NVDA"] == 100
    assert scores["AAPL"] == 0
    assert 0 < scores["CAT"] < 100


def test_gap_label():
    assert gap_label(30) == "underpriced risk"
    assert gap_label(0) == "fairly priced"
    assert gap_label(-25) == "overpriced fear"


def test_confidence_high():
    signals = [{
        "has_explicit_revenue_pct": True,
        "has_direct_tariff_mention": True,
        "chunk_count": 5,
        "extraction_quality": "high",
    }]
    level, reason = compute_confidence(signals)
    assert level == "high"
    assert "revenue" in reason.lower() or "tariff" in reason.lower()


def test_confidence_low_no_data():
    level, _ = compute_confidence([])
    assert level == "low"
