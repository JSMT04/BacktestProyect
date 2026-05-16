/**
 * BacktestPro — TypeScript type definitions
 * Matches the API contracts defined in STAGE 6.1 and component tree in STAGE 6.3
 */

// =========================================================
// ENUMS / UNION TYPES
// =========================================================

export type Timeframe = '1m' | '5m' | '15m' | '30m' | '1h' | '4h' | '1d' | '1w' | '1M';
export type ChartType = 'candlestick' | 'heikin_ashi' | 'line' | 'area' | 'bar';
export type AssetType = 'crypto' | 'forex' | 'stock' | 'index' | 'commodity';
export type Direction = 'LONG' | 'SHORT';
export type ExitReason = 'TP' | 'SL' | 'Signal' | 'TrailingStop' | 'End';
export type JobStatus = 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
export type StrategyMode = 'visual' | 'code';
export type PositionType = 'fixed_usd' | 'percent_capital' | 'contracts';
export type CommissionType = 'percent' | 'fixed_usd';
export type ConditionOperator = 'crosses_above' | 'crosses_below' | 'greater_than' | 'less_than';

// =========================================================
// DATA MODULE
// =========================================================

export interface OHLCVBar {
  t: number;  // Unix timestamp (seconds)
  o: number;  // Open
  h: number;  // High
  l: number;  // Low
  c: number;  // Close
  v: number;  // Volume
}

export interface SymbolInfo {
  symbol: string;
  name: string;
  type: AssetType;
  exchange: string;
  base_currency: string;
  quote_currency: string | null;
}

export interface SymbolSearchResponse {
  results: SymbolInfo[];
  total: number;
}

export interface OHLCVResponse {
  symbol: string;
  timeframe: string;
  start: string;
  end: string;
  source: string;
  from_cache: boolean;
  cache_age_hours: number | null;
  total_candles: number;
  data: OHLCVBar[];
}

export interface TimeframeItem {
  value: Timeframe;
  label: string;
  seconds: number;
}

export interface TimeframeResponse {
  timeframes: TimeframeItem[];
}

// =========================================================
// INDICATORS
// =========================================================

export interface IndicatorConfig {
  id: string;
  type: string;          // 'EMA', 'SMA', 'RSI', 'MACD', 'BBANDS', etc.
  params: Record<string, number | string>;
  panel: 'main' | string;  // 'main', 'sub_1', 'sub_2', etc.
  color?: string;
  line_width?: number;
  // MACD-specific
  color_macd?: string;
  color_signal?: string;
  color_hist_bull?: string;
  color_hist_bear?: string;
  // Bollinger Bands-specific
  color_upper?: string;
  color_lower?: string;
  color_mid?: string;
  source?: string;
}

export interface IndicatorRequest {
  symbol: string;
  timeframe: string;
  start: string;
  end: string;
  indicators: IndicatorConfig[];
}

export interface IndicatorDataPoint {
  t: number;
  v: number;
}

export interface IndicatorLineData {
  panel: string;
  type: 'line';
  data: IndicatorDataPoint[];
  overbought?: number;
  oversold?: number;
}

export interface IndicatorMACDData {
  panel: string;
  type: 'macd';
  macd: IndicatorDataPoint[];
  signal: IndicatorDataPoint[];
  histogram: IndicatorDataPoint[];
}

export interface IndicatorBandsData {
  panel: string;
  type: 'bands';
  upper: IndicatorDataPoint[];
  middle: IndicatorDataPoint[];
  lower: IndicatorDataPoint[];
}

export type IndicatorData = IndicatorLineData | IndicatorMACDData | IndicatorBandsData;

export interface IndicatorResponse {
  indicators: Record<string, IndicatorData>;
}

// =========================================================
// BACKTESTING
// =========================================================

export interface PositionConfig {
  type: PositionType;
  value: number;
}

export interface CommissionConfig {
  type: CommissionType;
  value: number;
}

export interface StopLossConfig {
  type: string;   // 'percent', 'pips', 'atr'
  value: number;
}

export interface TakeProfitConfig {
  type: string;   // 'percent', 'rr_ratio', 'pips'
  value: number;
}

export interface TrailingStopConfig {
  enabled: boolean;
  value: number;
  type: string;   // 'percent', 'pips', 'atr'
}

export interface ConditionSide {
  type: string;
  params: Record<string, number | string>;
  source?: string;
}

export interface StrategyCondition {
  indicator_a: ConditionSide;
  operator: ConditionOperator;
  indicator_b?: ConditionSide;
  value?: number;
}

export interface StrategyConfig {
  mode: StrategyMode;
  entry_long: StrategyCondition[];
  entry_short: StrategyCondition[];
  exit_long: StrategyCondition[];
  exit_short: StrategyCondition[];
  stop_loss?: StopLossConfig;
  take_profit?: TakeProfitConfig;
  trailing_stop?: TrailingStopConfig;
  code?: string;  // Python code when mode='code'
}

export interface BacktestConfig {
  name: string;
  symbol: string;
  timeframe: string;
  start: string;
  end: string;
  initial_capital: number;
  position_config: PositionConfig;
  commission: CommissionConfig;
  slippage_pips: number;
  strategy: StrategyConfig;
}

export interface BacktestJob {
  job_id: string;
  status: JobStatus;
  websocket_url: string;
  created_at: string;
}

export interface Trade {
  trade_id: number;
  direction: Direction;
  entry_time: string;
  entry_price: number;
  exit_time: string;
  exit_price: number;
  size_usd: number;
  size_units?: number;
  pnl_usd: number;
  pnl_pct: number;
  commission_paid: number;
  mae_pct: number;
  mfe_pct: number;
  exit_reason: ExitReason;
  bars_held: number;
}

export interface BacktestMetrics {
  net_profit_usd: number;
  net_profit_pct: number;
  gross_profit_usd: number;
  gross_loss_usd: number;
  profit_factor: number;
  max_drawdown_usd: number;
  max_drawdown_pct: number;
  max_drawdown_duration_bars: number;
  recovery_factor: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  calmar_ratio: number;
  var_95_pct: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate_pct: number;
  avg_win_usd: number;
  avg_loss_usd: number;
  best_trade_usd: number;
  worst_trade_usd: number;
  avg_trade_duration_hours: number;
  max_consecutive_wins: number;
  max_consecutive_losses: number;
  exposure_time_pct: number;
  total_bars: number;
  initial_capital: number;
  final_capital: number;
}

export interface EquityPoint {
  t: number;
  equity: number;
  drawdown_pct: number;
}

export interface BacktestResultData {
  metrics: BacktestMetrics;
  trades: Trade[];
  equity_curve: EquityPoint[];
}

export interface BacktestFullResponse {
  job_id: string;
  name: string;
  status: JobStatus;
  created_at: string;
  completed_at?: string;
  duration_seconds?: number;
  config: BacktestConfig;
  result?: BacktestResultData;
}

export interface BacktestSummary {
  job_id: string;
  name: string;
  symbol: string;
  timeframe: string;
  status: JobStatus;
  net_profit_pct?: number;
  win_rate_pct?: number;
  total_trades?: number;
  created_at: string;
}

export interface BacktestHistoryResponse {
  items: BacktestSummary[];
  total: number;
  limit: number;
  offset: number;
}

// =========================================================
// STRATEGIES
// =========================================================

export interface Strategy {
  strategy_id: string;
  name: string;
  description?: string;
  current_version: number;
  strategy_data: StrategyConfig;
  created_at: string;
  updated_at: string;
}

export interface StrategyCreateRequest {
  name: string;
  description?: string;
  strategy_data: Record<string, unknown>;
}

export interface StrategyResponse {
  strategy_id: string;
  name: string;
  version: number;
  created_at: string;
}

// =========================================================
// AUTH
// =========================================================

export interface AuthRegisterRequest {
  username: string;
  password: string;
}

export interface AuthRegisterResponse {
  user_id: string;
  username: string;
  created_at: string;
}

export interface AuthLoginRequest {
  username: string;
  password: string;
}

export interface AuthLoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

// =========================================================
// WEBSOCKET EVENTS
// =========================================================

export interface WSConnectedEvent {
  event: 'connected';
  job_id: string;
  status: JobStatus;
  timestamp: string;
}

export interface WSStartedEvent {
  event: 'started';
  job_id: string;
  total_bars: number;
  timestamp: string;
}

export interface WSProgressEvent {
  event: 'progress';
  job_id: string;
  progress_pct: number;
  bars_processed: number;
  total_bars: number;
  trades_found: number;
  elapsed_seconds: number;
  estimated_remaining_seconds: number;
}

export interface WSCompletedEvent {
  event: 'completed';
  job_id: string;
  duration_seconds: number;
  total_trades: number;
  net_profit_pct: number;
  timestamp: string;
}

export interface WSFailedEvent {
  event: 'failed';
  job_id: string;
  error: {
    code: string;
    message: string;
  };
  timestamp: string;
}

export interface WSCancelledEvent {
  event: 'cancelled';
  job_id: string;
  timestamp: string;
}

export type WSBacktestEvent =
  | WSConnectedEvent
  | WSStartedEvent
  | WSProgressEvent
  | WSCompletedEvent
  | WSFailedEvent
  | WSCancelledEvent;

// =========================================================
// ERROR
// =========================================================

export interface APIErrorDetail {
  code: string;
  message: string;
  details: Record<string, unknown>;
}

export interface APIErrorResponse {
  error: APIErrorDetail;
}

// =========================================================
// UI STATE TYPES
// =========================================================

export interface DateRange {
  start: Date;
  end: Date;
}
