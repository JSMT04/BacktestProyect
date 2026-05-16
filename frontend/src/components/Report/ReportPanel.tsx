import useBacktestStore from '../../stores/backtestStore';
import MetricsCards from './MetricsCards';
import EquityCurve from './EquityCurve';
import TradesList from './TradesList';
import { X } from 'lucide-react';

export default function ReportPanel() {
  const { currentResult, activeJobId, activeJobName, setResult } = useBacktestStore();

  if (!currentResult) return null;

  return (
    <div className="absolute inset-0 bg-bg-primary z-40 overflow-y-auto flex flex-col">
      <div className="flex items-center justify-between p-4 border-b border-border bg-bg-secondary sticky top-0 z-10">
        <h2 className="text-lg font-bold text-text-primary">
          Reporte de Backtest: {activeJobName || 'Estrategia Visual'}
        </h2>
        <div className="flex items-center gap-2">
          <a
            href={`/api/v1/reports/${activeJobId}/pdf`}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-accent-blue/10 text-accent-blue hover:bg-accent-blue/20 rounded transition-colors font-medium"
          >
            PDF
          </a>
          <a
            href={`/api/v1/reports/${activeJobId}/csv`}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-bg-tertiary text-text-secondary hover:text-text-primary hover:bg-border rounded transition-colors"
          >
            CSV
          </a>
          <a
            href={`/api/v1/reports/${activeJobId}/json`}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-bg-tertiary text-text-secondary hover:text-text-primary hover:bg-border rounded transition-colors"
          >
            JSON
          </a>
          <div className="w-px h-6 bg-border mx-1" />
          <button 
            onClick={() => setResult(null)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-bg-tertiary hover:bg-border rounded transition-colors text-text-primary"
          >
            <X className="w-4 h-4" />
            Cerrar Reporte
          </button>
        </div>
      </div>
      
      <div className="p-4 space-y-4 max-w-7xl mx-auto w-full">
        {/* Metrics Overview */}
        <MetricsCards />
        
        {/* Chart & Tables */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          <EquityCurve />
          <TradesList />
        </div>
      </div>
    </div>
  );
}
