import { useEffect } from 'react';
import { XCircle, Activity } from 'lucide-react';
import useBacktestStore from '../../stores/backtestStore';
import { cancelBacktest, getBacktest } from '../../services/api';

export default function ProgressBar() {
  const { activeJob, isRunning, progress, setProgress, setIsRunning, setResult } = useBacktestStore();

  useEffect(() => {
    if (activeJob && isRunning) {
      // Connect to WebSocket using native WebSocket since backend uses FastAPI WebSocket
      const wsUrl = `ws://${window.location.host}${activeJob.websocket_url}`;
      const ws = new WebSocket(wsUrl);

      ws.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.event === 'progress') {
            setProgress(data.progress || data.progress_pct);
          } else if (data.event === 'completed') {
            setIsRunning(false);
            setProgress(100);
            
            // Fetch final result
            try {
              const fullResult = await getBacktest(activeJob.job_id);
              if (fullResult.result) {
                setResult(fullResult.result, activeJob.job_id, fullResult.name);
              }
            } catch (err) {
              console.error("Failed to fetch final results", err);
            }
          } else if (data.event === 'failed' || data.event === 'cancelled') {
            setIsRunning(false);
            setProgress(0);
          }
        } catch (e) {
          console.error("Error parsing WS message", e);
        }
      };

      return () => {
        ws.close();
      };
    }
  }, [activeJob, isRunning, setProgress, setIsRunning, setResult]);

  if (!isRunning || !activeJob) return null;

  const handleCancel = async () => {
    try {
      await cancelBacktest(activeJob.job_id);
    } catch (e) {
      console.error("Failed to cancel backtest", e);
    }
  };

  return (
    <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-bg-secondary border border-border shadow-2xl rounded-xl p-4 w-96 z-50 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-accent-blue animate-pulse" />
          <span className="text-sm font-semibold text-text-primary">Ejecutando Backtest...</span>
        </div>
        <span className="text-xs font-mono text-accent-blue">{Math.round(progress)}%</span>
      </div>
      
      <div className="h-2 w-full bg-bg-tertiary rounded-full overflow-hidden">
        <div 
          className="h-full bg-accent-blue transition-all duration-300 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>
      
      <button 
        onClick={handleCancel}
        className="flex items-center justify-center gap-1.5 py-1.5 mt-1 rounded bg-bg-tertiary/50 hover:bg-bear-red/20 text-xs font-medium text-text-secondary hover:text-bear-red transition-colors"
      >
        <XCircle className="w-3.5 h-3.5" />
        Cancelar Ejecución
      </button>
    </div>
  );
}
