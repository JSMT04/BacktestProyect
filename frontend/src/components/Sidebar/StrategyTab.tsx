import { useState, useEffect } from 'react';
import { Play, Plus, X, Settings2, Code, LayoutTemplate, Save } from 'lucide-react';
import Editor from '@monaco-editor/react';
import useStrategyStore from '../../stores/strategyStore';
import useChartStore from '../../stores/chartStore';
import useBacktestStore from '../../stores/backtestStore';
import { runBacktest, listStrategies, createStrategy, getStrategy } from '../../services/api';

const OPERATOR_OPTIONS = [
  { value: 'greater_than', label: '>' },
  { value: 'less_than', label: '<' },
  { value: 'crosses_above', label: 'Cruza Arriba' },
  { value: 'crosses_below', label: 'Cruza Abajo' },
  { value: 'equal', label: '=' },
];

export default function StrategyTab() {
  const strategy = useStrategyStore();
  const { symbol, timeframe, dateRange } = useChartStore();
  const { isRunning, setIsRunning, setActiveJob, setResult } = useBacktestStore();
  
  const [showConfig, setShowConfig] = useState(false);
  const [savedStrategies, setSavedStrategies] = useState<any[]>([]);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    fetchStrategies();
  }, []);

  const fetchStrategies = async () => {
    try {
      const data = await listStrategies();
      setSavedStrategies(data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSave = async () => {
    const name = prompt("Nombre de la estrategia:");
    if (!name) return;
    setIsSaving(true);
    try {
      await createStrategy({
        name,
        strategy_data: {
          mode: strategy.editorMode,
          code: strategy.code,
          initialCapital: strategy.initialCapital,
          positionValue: strategy.positionValue,
          positionType: strategy.positionType,
          commissionValue: strategy.commissionValue,
          commissionType: strategy.commissionType,
          stopLossValue: strategy.stopLossValue,
          takeProfitValue: strategy.takeProfitValue,
          entryLong: strategy.entryLong,
          exitLong: strategy.exitLong,
        }
      });
      await fetchStrategies();
    } catch (e) {
      console.error(e);
    } finally {
      setIsSaving(false);
    }
  };

  const handleLoad = async (id: string) => {
    try {
      const data = await getStrategy(id);
      if (data && data.versions && data.versions.length > 0) {
        const sData = data.versions[0].strategy_data;
        if (sData.mode) strategy.setEditorMode(sData.mode);
        if (sData.code) strategy.setCode(sData.code);
        if (sData.initialCapital) strategy.setCapital(sData.initialCapital);
        if (sData.positionValue) strategy.setPosition(sData.positionValue, sData.positionType);
        if (sData.commissionValue) strategy.setCommission(sData.commissionValue, sData.commissionType);
        if (sData.stopLossValue) strategy.setStops(sData.stopLossValue, sData.takeProfitValue);
        
        // Cargar condiciones
        strategy.entryLong.forEach(c => strategy.removeEntryCondition(c.id));
        strategy.exitLong.forEach(c => strategy.removeExitCondition(c.id));
        
        if (sData.entryLong) sData.entryLong.forEach((c: any) => strategy.addEntryCondition(c));
        if (sData.exitLong) sData.exitLong.forEach((c: any) => strategy.addExitCondition(c));
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleRun = async () => {
    setIsRunning(true);
    setResult(null);

    try {
      const response = await runBacktest({
        name: strategy.editorMode === 'code' ? 'Estrategia Python' : 'Estrategia Visual',
        symbol,
        timeframe,
        start: dateRange.start.toISOString(),
        end: dateRange.end.toISOString(),
        initial_capital: strategy.initialCapital,
        position_config: { type: strategy.positionType, value: strategy.positionValue },
        commission: { type: strategy.commissionType, value: strategy.commissionValue },
        slippage_pips: 0,
        strategy: {
          mode: strategy.editorMode,
          entry_long: strategy.entryLong.map(({ id, ...rest }) => rest),
          exit_long: strategy.exitLong.map(({ id, ...rest }) => rest),
          entry_short: [],
          exit_short: [],
          stop_loss: { type: 'percent', value: strategy.stopLossValue },
          take_profit: { type: 'percent', value: strategy.takeProfitValue },
          trailing_stop: { enabled: false, value: 0, type: 'percent' },
          code: strategy.code
        }
      });
      
      setActiveJob({
        job_id: response.job_id,
        status: response.status,
        websocket_url: response.websocket_url,
        created_at: response.created_at
      });
      
    } catch (error) {
      console.error(error);
      setIsRunning(false);
    }
  };

  const renderConditionBuilder = (title: string, conditions: any[], addFn: any, removeFn: any) => (
    <div className="mb-4">
      <div className="flex justify-between items-center mb-2">
        <span className="text-xs font-semibold text-text-secondary uppercase">{title}</span>
        <button onClick={() => addFn({ indicator_a: { type: 'SMA', params: { length: 20 } }, operator: 'greater_than', indicator_b: { type: 'SMA', params: { length: 50 } } })} className="p-1 text-accent-blue hover:bg-accent-blue/10 rounded">
          <Plus className="w-3.5 h-3.5" />
        </button>
      </div>
      
      {conditions.length === 0 ? (
        <p className="text-[10px] text-text-secondary italic">Sin condiciones</p>
      ) : (
        <div className="space-y-2">
          {conditions.map((cond: any) => (
            <div key={cond.id} className="bg-bg-tertiary/50 p-2 rounded relative flex flex-col gap-1.5 text-xs">
              <button onClick={() => removeFn(cond.id)} className="absolute top-1 right-1 text-text-secondary hover:text-bear-red">
                <X className="w-3 h-3" />
              </button>
              
              <div className="flex items-center gap-1">
                <span className="text-accent-blue font-medium">{cond.indicator_a.type}</span>
                <span className="text-text-secondary">({cond.indicator_a.params.length || 'close'})</span>
              </div>
              
              <div className="text-warning text-[10px] font-bold">
                {OPERATOR_OPTIONS.find(o => o.value === cond.operator)?.label}
              </div>
              
              <div className="flex items-center gap-1">
                <span className="text-accent-purple font-medium">{cond.indicator_b.type}</span>
                <span className="text-text-secondary">({cond.indicator_b.params.length || 'close'})</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  return (
    <div className="flex flex-col h-full relative">
      <div className="flex-1 overflow-y-auto p-3 flex flex-col">
        
        {/* Load / Save */}
        <div className="flex items-center gap-2 mb-4">
          <select 
            className="flex-1 bg-bg-tertiary text-xs rounded px-2 py-1.5 border border-border outline-none text-text-secondary hover:text-text-primary transition-colors"
            onChange={(e) => {
              if(e.target.value) handleLoad(e.target.value);
            }}
            defaultValue=""
          >
            <option value="" disabled>Cargar Estrategia...</option>
            {savedStrategies.map(s => (
              <option key={s.strategy_id} value={s.strategy_id}>{s.name}</option>
            ))}
          </select>
          <button 
            onClick={handleSave}
            disabled={isSaving}
            className="px-2.5 py-1.5 bg-accent-blue/10 text-accent-blue rounded hover:bg-accent-blue/20 transition-colors flex items-center gap-1"
            title="Guardar Estrategia"
          >
            <Save className="w-4 h-4" />
          </button>
        </div>

        {/* Toggle Config */}
        <div className="flex gap-2 mb-4">
          <button 
            onClick={() => strategy.setEditorMode('visual')}
            className={`flex-1 py-1.5 text-xs font-medium rounded flex items-center justify-center gap-1.5 transition-colors ${strategy.editorMode === 'visual' ? 'bg-accent-blue text-white' : 'bg-bg-tertiary text-text-secondary hover:text-text-primary'}`}
          >
            <LayoutTemplate className="w-3.5 h-3.5" /> Visual
          </button>
          <button 
            onClick={() => strategy.setEditorMode('code')}
            className={`flex-1 py-1.5 text-xs font-medium rounded flex items-center justify-center gap-1.5 transition-colors ${strategy.editorMode === 'code' ? 'bg-accent-blue text-white' : 'bg-bg-tertiary text-text-secondary hover:text-text-primary'}`}
          >
            <Code className="w-3.5 h-3.5" /> Código
          </button>
        </div>
        
        <button onClick={() => setShowConfig(!showConfig)} className="w-full flex items-center justify-between p-2 mb-4 bg-bg-tertiary/50 rounded text-xs text-text-primary hover:bg-bg-tertiary">
          <span className="flex items-center gap-1.5"><Settings2 className="w-3.5 h-3.5" /> Parámetros y Riesgo</span>
          <span className="text-[10px]">{showConfig ? 'Ocultar' : 'Ver'}</span>
        </button>
        
        {showConfig && (
          <div className="mb-4 space-y-3 bg-bg-tertiary/30 p-2 rounded">
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-[10px] text-text-secondary">Capital Inicial</label>
                <input type="number" value={strategy.initialCapital} onChange={e => strategy.setCapital(Number(e.target.value))} className="w-full bg-bg-secondary border border-border rounded px-2 py-1 text-xs" />
              </div>
              <div>
                <label className="text-[10px] text-text-secondary">Riesgo / Posición</label>
                <input type="number" value={strategy.positionValue} onChange={e => strategy.setPosition(Number(e.target.value), strategy.positionType)} className="w-full bg-bg-secondary border border-border rounded px-2 py-1 text-xs" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-[10px] text-text-secondary">Stop Loss (%)</label>
                <input type="number" value={strategy.stopLossValue} onChange={e => strategy.setStops(Number(e.target.value), strategy.takeProfitValue)} className="w-full bg-bg-secondary border border-border rounded px-2 py-1 text-xs" />
              </div>
              <div>
                <label className="text-[10px] text-text-secondary">Take Profit (%)</label>
                <input type="number" value={strategy.takeProfitValue} onChange={e => strategy.setStops(strategy.stopLossValue, Number(e.target.value))} className="w-full bg-bg-secondary border border-border rounded px-2 py-1 text-xs" />
              </div>
            </div>
          </div>
        )}
        
        {strategy.editorMode === 'visual' ? (
          <>
            {renderConditionBuilder("Condiciones de Entrada (Long)", strategy.entryLong, strategy.addEntryCondition, strategy.removeEntryCondition)}
            <div className="h-px bg-border my-4" />
            {renderConditionBuilder("Condiciones de Salida (Long)", strategy.exitLong, strategy.addExitCondition, strategy.removeExitCondition)}
          </>
        ) : (
          <div className="flex-1 border border-border rounded overflow-hidden min-h-[300px]">
            <Editor
              height="100%"
              defaultLanguage="python"
              theme="vs-dark"
              value={strategy.code}
              onChange={(val) => strategy.setCode(val || '')}
              options={{
                minimap: { enabled: false },
                fontSize: 12,
                wordWrap: 'on',
                padding: { top: 10 }
              }}
            />
          </div>
        )}
        
      </div>
      
      {/* Footer / Run Button */}
      <div className="p-3 border-t border-border bg-bg-secondary">
        <button
          onClick={handleRun}
          disabled={isRunning}
          className={`w-full flex items-center justify-center gap-2 py-2 rounded font-medium text-sm transition-colors ${
            isRunning ? 'bg-bg-tertiary text-text-secondary cursor-not-allowed' : 'bg-accent-blue text-white hover:bg-accent-blue/90'
          }`}
        >
          <Play className="w-4 h-4 fill-current" />
          {isRunning ? 'Ejecutando...' : 'Correr Backtest'}
        </button>
      </div>
    </div>
  );
}
