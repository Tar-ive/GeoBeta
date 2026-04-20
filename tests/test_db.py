"""Tests for db.client (requires live DB connection via .env)."""
import os
import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("PG_HOST") and not os.environ.get("NEON_DATABASE_URL"),
    reason="No database connection configured",
)


def test_get_engine():
    from db.client import get_engine
    engine = get_engine()
    assert engine is not None


def test_read_table_companies():
    from db.client import read_table
    df = read_table("companies")
    assert not df.empty
    assert "ticker" in df.columns


def test_read_screener_returns_dataframe():
    from db.client import read_screener
    df = read_screener(limit=5)
    assert len(df) <= 5


def test_check_freshness():
    from db.client import check_freshness
    result = check_freshness("companies")
    assert "is_fresh" in result
    assert "age_minutes" in result
