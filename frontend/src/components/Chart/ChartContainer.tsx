import { useEffect, useRef } from 'react';
import { createChart, ColorType, CrosshairMode } from 'lightweight-charts';
import type { IChartApi, ISeriesApi, CandlestickData, LineData, HistogramData, Time, SeriesMarker } from 'lightweight-charts';
import useChartStore from '../../stores/chartStore';
import useBacktestStore from '../../stores/backtestStore';
import type { OHLCVBar, IndicatorData } from '../../types';
import { Loader2 } from 'lucide-react';

export default function ChartContainer() {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);
  const indicatorSeriesRefs = useRef<Map<string, ISeriesApi<'Line'> | ISeriesApi<'Histogram'>>>(new Map());

  const { ohlcvData, isLoadingData, symbol, timeframe, indicatorData, activeIndicators } = useChartStore();

  // Create chart on mount
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#131722' },
        textColor: '#D1D4DC',
        fontSize: 12,
        fontFamily: 'Inter, system-ui, sans-serif',
      },
      grid: {
        vertLines: { color: '#1E222D' },
        horzLines: { color: '#1E222D' },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          color: '#363A45',
          width: 1,
          style: 2,
          labelBackgroundColor: '#2962FF',
        },
        horzLine: {
          color: '#363A45',
          width: 1,
          style: 2,
          labelBackgroundColor: '#2962FF',
        },
      },
      rightPriceScale: {
        borderColor: '#363A45',
        scaleMargins: { top: 0.1, bottom: 0.2 },
      },
      timeScale: {
        borderColor: '#363A45',
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 5,
        barSpacing: 8,
      },
      handleScroll: { vertTouchDrag: false },
    });

    // Candlestick series
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#26A69A',
      downColor: '#EF5350',
      borderUpColor: '#26A69A',
      borderDownColor: '#EF5350',
      wickUpColor: '#26A69A',
      wickDownColor: '#EF5350',
    });

    // Volume series
    const volumeSeries = chart.addHistogramSeries({
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
    });

    chart.priceScale('volume').applyOptions({
      scaleMargins: { top: 0.85, bottom: 0 },
    });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    volumeSeriesRef.current = volumeSeries;

    // Resize observer
    const resizeObserver = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect;
      chart.applyOptions({ width, height });
    });
    resizeObserver.observe(chartContainerRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      volumeSeriesRef.current = null;
      indicatorSeriesRefs.current.clear();
    };
  }, []);

  // Update data when ohlcvData changes
  useEffect(() => {
    if (!candleSeriesRef.current || !volumeSeriesRef.current || ohlcvData.length === 0) return;

    const candleData: CandlestickData[] = ohlcvData.map((bar: OHLCVBar) => ({
      time: bar.t as Time,
      open: bar.o,
      high: bar.h,
      low: bar.l,
      close: bar.c,
    }));

    const volumeData: HistogramData[] = ohlcvData.map((bar: OHLCVBar) => ({
      time: bar.t as Time,
      value: bar.v,
      color: bar.c >= bar.o ? 'rgba(38,166,154,0.3)' : 'rgba(239,83,80,0.3)',
    }));

    candleSeriesRef.current.setData(candleData);
    volumeSeriesRef.current.setData(volumeData);

    // Fit content to view
    chartRef.current?.timeScale().fitContent();
  }, [ohlcvData]);

  // Update indicators when indicatorData changes
  useEffect(() => {
    if (!chartRef.current) return;

    // Remove old indicator series that are no longer active
    const activeIds = new Set(activeIndicators.map((i) => i.id));
    for (const [id, series] of indicatorSeriesRefs.current.entries()) {
      if (!activeIds.has(id)) {
        chartRef.current.removeSeries(series);
        indicatorSeriesRefs.current.delete(id);
      }
    }

    // Add/update indicator series
    for (const [id, data] of Object.entries(indicatorData)) {
      const config = activeIndicators.find((i) => i.id === id);
      if (!config) continue;

      const indData = data as IndicatorData;

      if (indData.type === 'line' && indData.panel === 'main') {
        // Line overlay on main chart
        let series = indicatorSeriesRefs.current.get(id) as ISeriesApi<'Line'> | undefined;
        if (!series) {
          series = chartRef.current.addLineSeries({
            color: config.color || '#2962FF',
            lineWidth: (config.line_width || 1) as 1 | 2 | 3 | 4,
            crosshairMarkerVisible: false,
            priceLineVisible: false,
            lastValueVisible: false,
          });
          indicatorSeriesRefs.current.set(id, series);
        }

        const lineData: LineData[] = (indData as { data: { t: number; v: number }[] }).data.map((p) => ({
          time: p.t as Time,
          value: p.v,
        }));
        series.setData(lineData);
      }

      if (indData.type === 'bands' && indData.panel === 'main') {
        // Bollinger Bands — draw upper, middle, lower as separate line series
        const bandKeys = ['upper', 'middle', 'lower'] as const;
        const bandColors = [
          config.color_upper || '#787B86',
          config.color_mid || '#787B86',
          config.color_lower || '#787B86',
        ];

        for (let i = 0; i < bandKeys.length; i++) {
          const key = bandKeys[i];
          const bandId = `${id}_${key}`;
          let series = indicatorSeriesRefs.current.get(bandId) as ISeriesApi<'Line'> | undefined;

          if (!series) {
            series = chartRef.current.addLineSeries({
              color: bandColors[i],
              lineWidth: 1,
              lineStyle: key === 'middle' ? 2 : 0,
              crosshairMarkerVisible: false,
              priceLineVisible: false,
              lastValueVisible: false,
            });
            indicatorSeriesRefs.current.set(bandId, series);
          }

          const bandData = (indData as { [k: string]: { t: number; v: number }[] })[key];
          if (bandData) {
            const lineData: LineData[] = bandData.map((p) => ({
              time: p.t as Time,
              value: p.v,
            }));
            series.setData(lineData);
          }
        }
      }
    }
  }, [indicatorData, activeIndicators]);

  // Backtest markers
  const { currentResult } = useBacktestStore();
  
  useEffect(() => {
    if (!candleSeriesRef.current) return;
    
    if (!currentResult || !currentResult.trades) {
      candleSeriesRef.current.setMarkers([]);
      return;
    }
    
    const markers: SeriesMarker<Time>[] = [];
    
    currentResult.trades.forEach(trade => {
      // Entry marker
      markers.push({
        time: (new Date(trade.entry_time).getTime() / 1000) as Time,
        position: trade.direction === 'LONG' ? 'belowBar' : 'aboveBar',
        color: trade.direction === 'LONG' ? '#2962FF' : '#9C27B0',
        shape: trade.direction === 'LONG' ? 'arrowUp' : 'arrowDown',
        text: `Entrada ${trade.direction}`,
      });
      
      // Exit marker
      markers.push({
        time: (new Date(trade.exit_time).getTime() / 1000) as Time,
        position: trade.direction === 'LONG' ? 'aboveBar' : 'belowBar',
        color: trade.pnl_usd >= 0 ? '#26A69A' : '#EF5350',
        shape: trade.direction === 'LONG' ? 'arrowDown' : 'arrowUp',
        text: `Salida (${trade.pnl_usd >= 0 ? '+' : ''}${trade.pnl_usd.toFixed(2)})`,
      });
    });
    
    // Sort markers by time as required by lightweight-charts
    markers.sort((a, b) => (a.time as number) - (b.time as number));
    
    candleSeriesRef.current.setMarkers(markers);
  }, [currentResult]);

  return (
    <div className="relative flex-1 bg-bg-primary">
      {/* Loading overlay */}
      {isLoadingData && (
        <div className="absolute inset-0 bg-bg-primary/80 flex items-center justify-center z-10">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="w-8 h-8 text-accent-blue animate-spin" />
            <span className="text-sm text-text-secondary">Cargando datos de {symbol}...</span>
          </div>
        </div>
      )}

      {/* No data state */}
      {!isLoadingData && ohlcvData.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center z-10">
          <div className="text-center">
            <p className="text-text-secondary text-sm">No hay datos disponibles</p>
            <p className="text-text-secondary/60 text-xs mt-1">
              Selecciona un símbolo y rango de fechas válido
            </p>
          </div>
        </div>
      )}

      {/* Chart canvas */}
      <div ref={chartContainerRef} className="w-full h-full" />
    </div>
  );
}
