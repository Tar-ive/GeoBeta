from fastapi import APIRouter
from db.client import read_backtest

router = APIRouter()


@router.get("")
def get_backtest():
    """Return historical backtest events and model accuracy data."""
    return {"events": read_backtest()}
