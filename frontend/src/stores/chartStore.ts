import { create } from 'zustand';
import type { Timeframe, ChartType, IndicatorConfig, OHLCVBar, DateRange, IndicatorData } from '../types';
import { fetchOHLCV, calculateIndicators } from '../services/api';

interface ChartStore {
  // State
  symbol: string;
  timeframe: Timeframe;
  dateRange: { start: Date; end: Date };
  chartType: ChartType;
  activeIndicators: IndicatorConfig[];
  indicatorData: Record<string, IndicatorData>;
  ohlcvData: OHLCVBar[];
  isLoadingData: boolean;
  dataSource: string;
  fromCache: boolean;

  // Actions
  setSymbol: (s: string) => void;
  setTimeframe: (tf: Timeframe) => void;
  setDateRange: (range: DateRange) => void;
  setChartType: (ct: ChartType) => void;
  addIndicator: (indicator: IndicatorConfig) => void;
  removeIndicator: (id: string) => void;
  loadData: () => Promise<void>;
  loadIndicators: () => Promise<void>;
}

const useChartStore = create<ChartStore>((set, get) => ({
  symbol: 'BTC/USDT',
  timeframe: '1d',
  dateRange: {
    start: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000), // 1 year ago
    end: new Date(),
  },
  chartType: 'candlestick',
  activeIndicators: [],
  indicatorData: {},
  ohlcvData: [],
  isLoadingData: false,
  dataSource: '',
  fromCache: false,

  setSymbol: (symbol) => {
    set({ symbol });
    get().loadData();
  },

  setTimeframe: (timeframe) => {
    set({ timeframe });
    get().loadData();
  },

  setDateRange: (dateRange) => {
    set({ dateRange });
    get().loadData();
  },

  setChartType: (chartType) => set({ chartType }),

  addIndicator: (indicator) => {
    const current = get().activeIndicators;
    if (current.find((i) => i.id === indicator.id)) return;
    set({ activeIndicators: [...current, indicator] });
    get().loadIndicators();
  },

  removeIndicator: (id) => {
    set({
      activeIndicators: get().activeIndicators.filter((i) => i.id !== id),
      indicatorData: Object.fromEntries(
        Object.entries(get().indicatorData).filter(([key]) => key !== id)
      ),
    });
  },

  loadData: async () => {
    const { symbol, timeframe, dateRange } = get();
    set({ isLoadingData: true });

    try {
      const response = await fetchOHLCV(
        symbol,
        timeframe,
        dateRange.start.toISOString(),
        dateRange.end.toISOString()
      );

      set({
        ohlcvData: response.data,
        dataSource: response.source,
        fromCache: response.from_cache,
        isLoadingData: false,
      });

      // Reload indicators if any are active
      if (get().activeIndicators.length > 0) {
        get().loadIndicators();
      }
    } catch (error) {
      console.error('Failed to load OHLCV data:', error);
      set({ isLoadingData: false, ohlcvData: [] });
    }
  },

  loadIndicators: async () => {
    const { symbol, timeframe, dateRange, activeIndicators } = get();
    if (activeIndicators.length === 0) return;

    try {
      const response = await calculateIndicators({
        symbol,
        timeframe,
        start: dateRange.start.toISOString(),
        end: dateRange.end.toISOString(),
        indicators: activeIndicators,
      });

      set({ indicatorData: response.indicators });
    } catch (error) {
      console.error('Failed to load indicators:', error);
    }
  },
}));

export default useChartStore;
