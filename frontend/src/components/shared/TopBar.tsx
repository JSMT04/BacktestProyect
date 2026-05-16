import { Activity } from 'lucide-react';
import SymbolSearch from './SymbolSearch';
import TimeframeSelector from './TimeframeSelector';
import useChartStore from '../../stores/chartStore';

export default function TopBar() {
  const { symbol, dataSource, fromCache, isLoadingData, ohlcvData } = useChartStore();

  return (
    <div className="h-12 flex items-center px-3 gap-3 bg-bg-secondary border-b border-border flex-shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-2 mr-2">
        <Activity className="w-5 h-5 text-accent-blue" />
        <span className="text-sm font-semibold text-text-primary tracking-wide">
          BacktestPro
        </span>
      </div>

      {/* Separator */}
      <div className="w-px h-6 bg-border" />

      {/* Symbol Search */}
      <SymbolSearch />

      {/* Separator */}
      <div className="w-px h-6 bg-border" />

      {/* Timeframe Selector */}
      <TimeframeSelector />

      {/* Separator */}
      <div className="w-px h-6 bg-border" />

      {/* Data info */}
      <div className="flex items-center gap-3 ml-auto text-xs text-text-secondary">
        {isLoadingData ? (
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 bg-accent-blue rounded-full animate-pulse" />
            <span>Cargando datos...</span>
          </div>
        ) : ohlcvData.length > 0 ? (
          <>
            <span>
              {ohlcvData.length.toLocaleString()} velas
            </span>
            <span className="text-text-secondary/60">·</span>
            <span className={fromCache ? 'text-bull-green' : 'text-accent-blue'}>
              {fromCache ? 'Cache' : dataSource}
            </span>
          </>
        ) : null}
      </div>
    </div>
  );
}
