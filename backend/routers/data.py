"""Data router — endpoints for OHLCV data, symbol search, timeframes, and indicators.

TASK-106: GET /api/v1/data/ohlcv
TASK-107: GET /api/v1/data/symbols/search
TASK-108: GET /api/v1/data/timeframes
TASK-113: POST /api/v1/data/indicators
"""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from core.exceptions import DataFetchError, InsufficientDataError, SymbolNotFoundException
from services.data_manager import data_manager
from services.indicator_service import indicator_service

logger = logging.getLogger("backtestpro.routers.data")

router = APIRouter(prefix="/api/v1/data", tags=["data"])


# =========================================================
# TASK-107: Symbol Search
# =========================================================
@router.get("/symbols/search")
async def search_symbols(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
):
    """Search for trading symbols across all data sources."""
    result = data_manager.search_symbols(q, limit)
    return result


# =========================================================
# TASK-106: OHLCV Data
# =========================================================
@router.get("/ohlcv")
async def get_ohlcv(
    symbol: str = Query(..., description="Symbol (e.g., BTC/USDT, AAPL, EURUSD=X)"),
    timeframe: str = Query(..., description="Timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M)"),
    start: str = Query(..., description="Start date ISO 8601"),
    end: str = Query(..., description="End date ISO 8601"),
    force_refresh: bool = Query(False, description="Bypass cache"),
):
    """Get OHLCV candlestick data for a symbol.

    Automatically detects the data source based on symbol format:
    - Contains "/" → Binance (crypto)
    - Ends with "=X" → yfinance (forex)
    - Ends with "=F" → yfinance (commodities)
    - Other → yfinance (stocks/indices)
    """
    # Validate timeframe
    valid_timeframes = {"1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"}
    if timeframe not in valid_timeframes:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid timeframe '{timeframe}'. Valid: {', '.join(sorted(valid_timeframes))}"
        )

    # Validate date range
    try:
        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
        if start_dt >= end_dt:
            raise ValueError("start must be before end")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Invalid date range: {e}")

    # Fetch data
    result = await data_manager.get_ohlcv(symbol, timeframe, start, end, force_refresh)

    if result["total_candles"] == 0:
        raise InsufficientDataError(
            f"No hay datos disponibles para '{symbol}' en el rango solicitado."
        )

    return result


# =========================================================
# TASK-108: Timeframes
# =========================================================
@router.get("/timeframes")
async def get_timeframes():
    """Get list of available timeframes."""
    timeframes = [
        {"value": "1m", "label": "1 Minuto", "seconds": 60},
        {"value": "5m", "label": "5 Minutos", "seconds": 300},
        {"value": "15m", "label": "15 Minutos", "seconds": 900},
        {"value": "30m", "label": "30 Minutos", "seconds": 1800},
        {"value": "1h", "label": "1 Hora", "seconds": 3600},
        {"value": "4h", "label": "4 Horas", "seconds": 14400},
        {"value": "1d", "label": "1 Día", "seconds": 86400},
        {"value": "1w", "label": "1 Semana", "seconds": 604800},
        {"value": "1M", "label": "1 Mes", "seconds": 2592000},
    ]
    return {"timeframes": timeframes}


# =========================================================
# TASK-113: Indicators
# =========================================================
class IndicatorParam(BaseModel):
    id: str
    type: str
    params: dict = {}
    panel: str = "main"
    color: Optional[str] = None
    line_width: Optional[int] = 1


class IndicatorRequestBody(BaseModel):
    symbol: str
    timeframe: str
    start: str
    end: str
    indicators: List[IndicatorParam]


@router.post("/indicators")
async def calculate_indicators(body: IndicatorRequestBody):
    """Calculate technical indicators for given data.

    First fetches OHLCV data (using cache), then calculates requested indicators.
    """
    import pandas as pd

    # Get the OHLCV data
    ohlcv_result = await data_manager.get_ohlcv(
        body.symbol, body.timeframe, body.start, body.end
    )

    if ohlcv_result["total_candles"] == 0:
        raise InsufficientDataError(
            f"No hay datos disponibles para calcular indicadores en '{body.symbol}'."
        )

    # Convert OHLCV to DataFrame
    data = ohlcv_result["data"]
    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["t"], unit="s", utc=True)
    df = df.set_index("timestamp")
    df = df.rename(columns={"o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"})

    # Calculate indicators
    indicators_config = [ind.model_dump() for ind in body.indicators]
    results = indicator_service.calculate(df, indicators_config)

    return {"indicators": results}
