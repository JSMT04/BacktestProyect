import { useState } from 'react';
import { Plus, X, Eye, EyeOff } from 'lucide-react';
import useChartStore from '../../stores/chartStore';
import type { IndicatorConfig } from '../../types';

const INDICATOR_PRESETS: {
  type: string;
  label: string;
  description: string;
  defaultParams: Record<string, number>;
  panel: string;
  color: string;
}[] = [
  {
    type: 'EMA',
    label: 'EMA',
    description: 'Media Móvil Exponencial',
    defaultParams: { length: 9 },
    panel: 'main',
    color: '#2962FF',
  },
  {
    type: 'SMA',
    label: 'SMA',
    description: 'Media Móvil Simple',
    defaultParams: { length: 20 },
    panel: 'main',
    color: '#FF9800',
  },
  {
    type: 'RSI',
    label: 'RSI',
    description: 'Índice de Fuerza Relativa',
    defaultParams: { length: 14 },
    panel: 'sub_1',
    color: '#9C27B0',
  },
  {
    type: 'MACD',
    label: 'MACD',
    description: 'Convergencia/Divergencia de Medias Móviles',
    defaultParams: { fast: 12, slow: 26, signal: 9 },
    panel: 'sub_2',
    color: '#2962FF',
  },
  {
    type: 'BBANDS',
    label: 'Bollinger Bands',
    description: 'Bandas de Bollinger',
    defaultParams: { length: 20, std: 2 },
    panel: 'main',
    color: '#787B86',
  },
  {
    type: 'ATR',
    label: 'ATR',
    description: 'Rango Verdadero Promedio',
    defaultParams: { length: 14 },
    panel: 'sub_1',
    color: '#F7C948',
  },
  {
    type: 'STOCH',
    label: 'Stochastic',
    description: 'Oscilador Estocástico',
    defaultParams: { k: 14, d: 3 },
    panel: 'sub_1',
    color: '#26A69A',
  },
  {
    type: 'ADX',
    label: 'ADX',
    description: 'Índice Direccional Promedio',
    defaultParams: { length: 14 },
    panel: 'sub_1',
    color: '#EF5350',
  },
  {
    type: 'CCI',
    label: 'CCI',
    description: 'Índice del Canal de Materias Primas',
    defaultParams: { length: 20 },
    panel: 'sub_1',
    color: '#4CAF50',
  },
  {
    type: 'OBV',
    label: 'OBV',
    description: 'Volumen en Balance',
    defaultParams: {},
    panel: 'sub_1',
    color: '#2962FF',
  },
];

export default function IndicatorsTab() {
  const { activeIndicators, addIndicator, removeIndicator } = useChartStore();
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState<typeof INDICATOR_PRESETS[0] | null>(null);
  const [customParams, setCustomParams] = useState<Record<string, number>>({});

  const handleAddIndicator = () => {
    if (!selectedPreset) return;

    const params = { ...selectedPreset.defaultParams, ...customParams };
    const paramStr = Object.entries(params)
      .map(([, v]) => v)
      .join('_');

    const config: IndicatorConfig = {
      id: `${selectedPreset.type.toLowerCase()}_${paramStr}`,
      type: selectedPreset.type,
      params,
      panel: selectedPreset.panel,
      color: selectedPreset.color,
      line_width: 1,
    };

    addIndicator(config);
    setShowAddModal(false);
    setSelectedPreset(null);
    setCustomParams({});
  };

  return (
    <div className="p-3">
      {/* Active indicators */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
          Indicadores Activos
        </span>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-1 px-2 py-1 text-xs font-medium text-accent-blue hover:bg-accent-blue/10 rounded transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          Agregar
        </button>
      </div>

      {activeIndicators.length === 0 ? (
        <div className="py-8 text-center">
          <p className="text-text-secondary text-sm">Sin indicadores activos</p>
          <p className="text-text-secondary/60 text-xs mt-1">
            Haz clic en &quot;Agregar&quot; para añadir indicadores al gráfico
          </p>
        </div>
      ) : (
        <div className="space-y-1.5">
          {activeIndicators.map((ind) => (
            <div
              key={ind.id}
              className="flex items-center gap-2 px-2.5 py-2 bg-bg-tertiary/50 rounded-lg group"
            >
              <div
                className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                style={{ backgroundColor: ind.color || '#2962FF' }}
              />
              <div className="flex-1 min-w-0">
                <div className="text-xs font-medium text-text-primary">
                  {ind.type}
                  <span className="text-text-secondary ml-1">
                    ({Object.values(ind.params).join(', ')})
                  </span>
                </div>
                <div className="text-[10px] text-text-secondary">
                  Panel: {ind.panel === 'main' ? 'Principal' : ind.panel}
                </div>
              </div>
              <button
                onClick={() => removeIndicator(ind.id)}
                className="opacity-0 group-hover:opacity-100 p-1 hover:bg-bear-red/20 rounded transition-all"
              >
                <X className="w-3 h-3 text-bear-red" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Add indicator modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-bg-secondary border border-border rounded-xl w-[420px] max-h-[80vh] overflow-hidden shadow-2xl">
            <div className="flex items-center justify-between px-4 py-3 border-b border-border">
              <h3 className="text-sm font-semibold text-text-primary">Agregar Indicador</h3>
              <button
                onClick={() => {
                  setShowAddModal(false);
                  setSelectedPreset(null);
                }}
                className="p-1 hover:bg-bg-tertiary rounded"
              >
                <X className="w-4 h-4 text-text-secondary" />
              </button>
            </div>

            <div className="p-4 overflow-y-auto max-h-[60vh]">
              {!selectedPreset ? (
                // Indicator list
                <div className="space-y-1">
                  {INDICATOR_PRESETS.map((preset) => {
                    const isActive = activeIndicators.some(
                      (i) => i.type === preset.type
                    );
                    return (
                      <button
                        key={preset.type}
                        onClick={() => {
                          setSelectedPreset(preset);
                          setCustomParams({ ...preset.defaultParams });
                        }}
                        className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-bg-tertiary transition-colors text-left"
                      >
                        <div
                          className="w-3 h-3 rounded-full flex-shrink-0"
                          style={{ backgroundColor: preset.color }}
                        />
                        <div className="flex-1">
                          <div className="text-sm font-medium text-text-primary">
                            {preset.label}
                            {isActive && (
                              <span className="ml-2 text-[10px] text-accent-blue">ACTIVO</span>
                            )}
                          </div>
                          <div className="text-xs text-text-secondary">
                            {preset.description}
                          </div>
                        </div>
                        <span className="text-[10px] text-text-secondary uppercase">
                          {preset.panel === 'main' ? 'Overlay' : 'Sub-panel'}
                        </span>
                      </button>
                    );
                  })}
                </div>
              ) : (
                // Parameter configuration
                <div>
                  <button
                    onClick={() => setSelectedPreset(null)}
                    className="text-xs text-accent-blue hover:underline mb-3"
                  >
                    ← Volver a la lista
                  </button>

                  <div className="mb-4">
                    <h4 className="text-sm font-semibold text-text-primary mb-1">
                      {selectedPreset.label}
                    </h4>
                    <p className="text-xs text-text-secondary">{selectedPreset.description}</p>
                  </div>

                  <div className="space-y-3">
                    {Object.entries(selectedPreset.defaultParams).map(([key, defaultVal]) => (
                      <div key={key}>
                        <label className="block text-xs text-text-secondary mb-1 capitalize">
                          {key}
                        </label>
                        <input
                          type="number"
                          value={customParams[key] ?? defaultVal}
                          onChange={(e) =>
                            setCustomParams({
                              ...customParams,
                              [key]: parseFloat(e.target.value) || 0,
                            })
                          }
                          className="w-full bg-bg-tertiary border border-border rounded px-3 py-1.5 text-sm text-text-primary outline-none focus:border-accent-blue transition-colors"
                        />
                      </div>
                    ))}
                  </div>

                  <button
                    onClick={handleAddIndicator}
                    className="w-full mt-4 py-2 bg-accent-blue text-white text-sm font-medium rounded-lg hover:bg-accent-blue/90 transition-colors"
                  >
                    Agregar {selectedPreset.label}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
