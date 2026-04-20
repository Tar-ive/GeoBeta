from fastapi import APIRouter, HTTPException, Query
from db.client import read_table, check_freshness

router = APIRouter()


@router.get("")
def get_company_risk(ticker: str = Query(..., description="Stock ticker (e.g. AAPL)")):
    """Return full tariff exposure profile for one company."""
    df = read_table("companies", filters={"ticker": ticker.upper()})
    if df.empty:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker!r} not found.")

    row = df.iloc[0].to_dict()
    freshness = check_freshness("companies")
    if not freshness["is_fresh"]:
        row["data_warning"] = f"Data is {freshness['age_minutes']} minutes old."
    return row
