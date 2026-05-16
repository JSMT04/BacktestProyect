import { useEffect, useState } from 'react';
import { RefreshCw, PlayCircle } from 'lucide-react';
import { getBacktestHistory, getBacktest } from '../../services/api';
import useBacktestStore from '../../stores/backtestStore';
import type { BacktestSummary } from '../../types';
import { format } from 'date-fns';

export default function HistoryTab() {
  const [history, setHistory] = useState<BacktestSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const { setResult, setIsRunning } = useBacktestStore();

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const response = await getBacktestHistory(20, 0);
      setHistory(response.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleLoadResult = async (jobId: string) => {
    setIsRunning(true);
    try {
      const fullResult = await getBacktest(jobId);
      if (fullResult.result) {
        setResult(fullResult.result, jobId, fullResult.name);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="p-3 border-b border-border flex justify-between items-center">
        <span className="text-xs font-semibold text-text-secondary uppercase">Backtests Anteriores</span>
        <button 
          onClick={fetchHistory} 
          className="p-1.5 text-text-secondary hover:text-accent-blue rounded bg-bg-tertiary/50 hover:bg-bg-tertiary transition-colors"
          title="Refrescar Historial"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {history.length === 0 && !loading && (
          <div className="text-center p-4 text-text-secondary text-xs">
            No hay backtests en el historial
          </div>
        )}

        {history.map((job) => (
          <div key={job.job_id} className="bg-bg-secondary border border-border p-3 rounded flex flex-col gap-2 hover:border-accent-blue/50 transition-colors">
            <div className="flex justify-between items-start">
              <div>
                <h4 className="text-sm font-medium text-text-primary">{job.name}</h4>
                <div className="text-[10px] text-text-secondary mt-0.5">
                  {format(new Date(job.created_at), 'MMM dd, HH:mm')}
                </div>
              </div>
              <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                job.status === 'completed' ? 'bg-bull-green/10 text-bull-green' : 
                job.status === 'failed' ? 'bg-bear-red/10 text-bear-red' : 
                'bg-accent-blue/10 text-accent-blue'
              }`}>
                {job.status}
              </span>
            </div>
            
            <div className="flex gap-2 text-xs">
              <span className="px-2 py-1 bg-bg-tertiary rounded text-text-primary">{job.symbol}</span>
              <span className="px-2 py-1 bg-bg-tertiary rounded text-text-primary">{job.timeframe}</span>
            </div>
            
            {job.status === 'completed' && job.net_profit_pct !== undefined && (
              <div className="flex justify-between items-end mt-1">
                <div className="flex gap-4">
                  <div>
                    <div className="text-[10px] text-text-secondary">PnL</div>
                    <div className={`text-xs font-bold ${job.net_profit_pct >= 0 ? 'text-bull-green' : 'text-bear-red'}`}>
                      {job.net_profit_pct > 0 ? '+' : ''}{job.net_profit_pct.toFixed(2)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] text-text-secondary">Win Rate</div>
                    <div className="text-xs font-bold text-text-primary">
                      {job.win_rate_pct?.toFixed(1)}%
                    </div>
                  </div>
                </div>
                
                <button 
                  onClick={() => handleLoadResult(job.job_id)}
                  className="p-1.5 bg-accent-blue/10 hover:bg-accent-blue/20 text-accent-blue rounded transition-colors"
                  title="Ver Reporte"
                >
                  <PlayCircle className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
