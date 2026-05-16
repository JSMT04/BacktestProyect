import axios from 'axios';
import type {
  OHLCVResponse,
  SymbolSearchResponse,
  TimeframeResponse,
  IndicatorRequest,
  IndicatorResponse,
  BacktestConfig,
  BacktestJob,
  BacktestFullResponse,
  BacktestHistoryResponse,
} from '../types';

const API_BASE = '/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// =========================================================
// DATA ENDPOINTS
// =========================================================

export async function searchSymbols(q: string, limit = 10): Promise<SymbolSearchResponse> {
  const { data } = await api.get('/data/symbols/search', { params: { q, limit } });
  return data;
}

export async function fetchOHLCV(
  symbol: string,
  timeframe: string,
  start: string,
  end: string,
  forceRefresh = false
): Promise<OHLCVResponse> {
  const { data } = await api.get('/data/ohlcv', {
    params: { symbol, timeframe, start, end, force_refresh: forceRefresh },
  });
  return data;
}

export async function fetchTimeframes(): Promise<TimeframeResponse> {
  const { data } = await api.get('/data/timeframes');
  return data;
}

export async function calculateIndicators(request: IndicatorRequest): Promise<IndicatorResponse> {
  const { data } = await api.post('/data/indicators', request);
  return data;
}

// =========================================================
// BACKTEST ENDPOINTS
// =========================================================

export async function runBacktest(config: BacktestConfig): Promise<BacktestJob> {
  const { data } = await api.post('/backtest/run', config);
  return data;
}

export async function getBacktest(jobId: string): Promise<BacktestFullResponse> {
  const { data } = await api.get(`/backtest/${jobId}`);
  return data;
}

export async function cancelBacktest(jobId: string): Promise<void> {
  await api.delete(`/backtest/${jobId}`);
}

export async function getBacktestHistory(
  limit = 20,
  offset = 0
): Promise<BacktestHistoryResponse> {
  const { data } = await api.get('/backtest/history/list', { params: { limit, offset } });
  return data;
}

// =========================================================
// STRATEGY ENDPOINTS
// =========================================================

export async function listStrategies() {
  const { data } = await api.get('/strategies');
  return data;
}

export async function createStrategy(payload: { name: string; description?: string; strategy_data: Record<string, any> }) {
  const { data } = await api.post('/strategies', payload);
  return data;
}

export async function getStrategy(strategyId: string) {
  const { data } = await api.get(`/strategies/${strategyId}`);
  return data;
}

// =========================================================
// EXPORT
// =========================================================

export default api;
