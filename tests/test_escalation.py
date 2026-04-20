"""Tests for escalation index computation."""
import pandas as pd
import pytest
from scoring.escalation import compute_escalation_index, escalation_label, compute_gdelt_intensity


def test_escalation_label():
    assert escalation_label(0.1) == "calm"
    assert escalation_label(0.45) == "elevated"
    assert escalation_label(0.75) == "crisis"


def test_gdelt_intensity_empty():
    assert compute_gdelt_intensity(pd.DataFrame()) == 0.0


def test_gdelt_intensity_with_data():
    df = pd.DataFrame({"tone": [-5.0, -3.0, -8.0, 2.0], "severity": [7, 5, 8, 3]})
    score = compute_gdelt_intensity(df)
    assert 0.0 <= score <= 1.0


def test_compute_escalation_index_empty():
    result = compute_escalation_index(
        markets_df=pd.DataFrame(),
        events_df=pd.DataFrame(),
        macro_df=pd.DataFrame(),
    )
    assert "index_score" in result
    assert "label" in result
    assert "computed_at" in result
    assert 0.0 <= result["index_score"] <= 1.0
