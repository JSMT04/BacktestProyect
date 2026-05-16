"""Pydantic schemas for request/response validation (API contracts from STAGE 6.1)."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# =========================================================
# ERROR SCHEMA
# =========================================================
class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorDetail


# =========================================================
# DATA MODULE — SYMBOLS
# =========================================================
class SymbolInfo(BaseModel):
    symbol: str
    name: str
    type: str  # 'crypto', 'forex', 'stock', 'index', 'commodity'
    exchange: str
    base_currency: str
    quote_currency: Optional[str] = None


class SymbolSearchResponse(BaseModel):
    results: List[SymbolInfo]
    total: int


# =========================================================
# DATA MODULE — OHLCV
# =========================================================
class OHLCVBar(BaseModel):
    t: int      # Unix timestamp (seconds)
    o: float    # Open
    h: float    # High
    l: float    # Low
    c: float    # Close
    v: float    # Volume


class OHLCVResponse(BaseModel):
    symbol: str
    timeframe: str
    start: str
    end: str
    source: str
    from_cache: bool
    cache_age_hours: Optional[float] = None
    total_candles: int
    data: List[OHLCVBar]


# =========================================================
# DATA MODULE — INDICATORS
# =========================================================
class IndicatorParams(BaseModel):
    id: str
    type: str
    params: Dict[str, Any]
    panel: str = "main"
    color: Optional[str] = None
    line_width: Optional[int] = 1
    # MACD-specific colors
    color_macd: Optional[str] = None
    color_signal: Optional[str] = None
    color_hist_bull: Optional[str] = None
    color_hist_bear: Optional[str] = None
    # Bollinger Bands-specific colors
    color_upper: Optional[str] = None
    color_lower: Optional[str] = None
    color_mid: Optional[str] = None
    source: Optional[str] = "close"


class IndicatorRequest(BaseModel):
    symbol: str
    timeframe: str
    start: str
    end: str
    indicators: List[IndicatorParams]


class IndicatorDataPoint(BaseModel):
    t: int
    v: float


# =========================================================
# BACKTESTING MODULE
# =========================================================
class PositionConfig(BaseModel):
    type: str = "percent_capital"   # 'fixed_usd', 'percent_capital', 'contracts'
    value: float = 10.0


class CommissionConfig(BaseModel):
    type: str = "percent"           # 'percent', 'fixed_usd'
    value: float = 0.1


class StopLossConfig(BaseModel):
    type: str = "percent"
    value: float = 2.0


class TakeProfitConfig(BaseModel):
    type: str = "rr_ratio"
    value: float = 2.0


class TrailingStopConfig(BaseModel):
    enabled: bool = False
    value: float = 1.0
    type: str = "percent"


class ConditionSide(BaseModel):
    type: str
    params: Dict[str, Any] = Field(default_factory=dict)
    source: Optional[str] = "close"


class StrategyCondition(BaseModel):
    indicator_a: ConditionSide
    operator: str  # 'crosses_above', 'crosses_below', 'greater_than', 'less_than'
    indicator_b: Optional[ConditionSide] = None
    value: Optional[float] = None


class StrategyConfig(BaseModel):
    mode: str = "visual"  # 'visual' or 'code'
    entry_long: List[StrategyCondition] = Field(default_factory=list)
    entry_short: List[StrategyCondition] = Field(default_factory=list)
    exit_long: List[StrategyCondition] = Field(default_factory=list)
    exit_short: List[StrategyCondition] = Field(default_factory=list)
    stop_loss: Optional[StopLossConfig] = None
    take_profit: Optional[TakeProfitConfig] = None
    trailing_stop: Optional[TrailingStopConfig] = None
    code: Optional[str] = None  # Python code when mode='code'


class BacktestRunRequest(BaseModel):
    name: str
    symbol: str
    timeframe: str
    start: str
    end: str
    initial_capital: float = 10000.0
    position_config: PositionConfig = Field(default_factory=PositionConfig)
    commission: CommissionConfig = Field(default_factory=CommissionConfig)
    slippage_pips: float = 0.0
    strategy: StrategyConfig


class BacktestJobResponse(BaseModel):
    job_id: str
    status: str
    websocket_url: str
    created_at: str


class Trade(BaseModel):
    trade_id: int
    direction: str  # 'LONG' or 'SHORT'
    entry_time: str
    entry_price: float
    exit_time: str
    exit_price: float
    size_usd: float
    size_units: Optional[float] = None
    pnl_usd: float
    pnl_pct: float
    commission_paid: float
    mae_pct: float
    mfe_pct: float
    exit_reason: str  # 'TP', 'SL', 'Signal', 'TrailingStop', 'End'
    bars_held: int


class BacktestMetrics(BaseModel):
    net_profit_usd: float = 0.0
    net_profit_pct: float = 0.0
    gross_profit_usd: float = 0.0
    gross_loss_usd: float = 0.0
    profit_factor: float = 0.0
    max_drawdown_usd: float = 0.0
    max_drawdown_pct: float = 0.0
    max_drawdown_duration_bars: int = 0
    recovery_factor: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    var_95_pct: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate_pct: float = 0.0
    avg_win_usd: float = 0.0
    avg_loss_usd: float = 0.0
    best_trade_usd: float = 0.0
    worst_trade_usd: float = 0.0
    avg_trade_duration_hours: float = 0.0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    exposure_time_pct: float = 0.0
    total_bars: int = 0
    initial_capital: float = 0.0
    final_capital: float = 0.0


class EquityPoint(BaseModel):
    t: int
    equity: float
    drawdown_pct: float


class BacktestResultData(BaseModel):
    metrics: BacktestMetrics
    trades: List[Trade]
    equity_curve: List[EquityPoint]


class BacktestFullResponse(BaseModel):
    job_id: str
    name: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    config: Dict[str, Any]
    result: Optional[BacktestResultData] = None


class BacktestSummary(BaseModel):
    job_id: str
    name: str
    symbol: str
    timeframe: str
    status: str
    net_profit_pct: Optional[float] = None
    win_rate_pct: Optional[float] = None
    total_trades: Optional[int] = None
    created_at: str


class BacktestHistoryResponse(BaseModel):
    items: List[BacktestSummary]
    total: int
    limit: int
    offset: int


# =========================================================
# STRATEGIES MODULE
# =========================================================
class StrategyCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    strategy_data: Dict[str, Any]


class StrategyResponse(BaseModel):
    strategy_id: str
    name: str
    version: int
    created_at: str


class StrategyListItem(BaseModel):
    strategy_id: str
    name: str
    description: Optional[str] = None
    current_version: int
    created_at: str
    updated_at: str


# =========================================================
# AUTH MODULE
# =========================================================
class AuthRegisterRequest(BaseModel):
    username: str
    password: str


class AuthRegisterResponse(BaseModel):
    user_id: str
    username: str
    created_at: str


class AuthLoginRequest(BaseModel):
    username: str
    password: str


class AuthLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# =========================================================
# TIMEFRAMES
# =========================================================
class TimeframeItem(BaseModel):
    value: str
    label: str
    seconds: int


class TimeframeResponse(BaseModel):
    timeframes: List[TimeframeItem]
