import { useState } from 'react';
import { BarChart3, LineChart, History } from 'lucide-react';
import IndicatorsTab from './IndicatorsTab';
import StrategyTab from './StrategyTab';
import HistoryTab from './HistoryTab';

type TabId = 'strategy' | 'indicators' | 'history';

export default function Sidebar() {
  const [activeTab, setActiveTab] = useState<TabId>('indicators');

  const tabs = [
    { id: 'strategy' as TabId, label: 'Estrategia', icon: BarChart3 },
    { id: 'indicators' as TabId, label: 'Indicadores', icon: LineChart },
    { id: 'history' as TabId, label: 'Historial', icon: History },
  ];

  return (
    <div className="h-full flex flex-col bg-bg-secondary">
      {/* Tabs */}
      <div className="flex border-b border-border flex-shrink-0">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 text-xs font-medium transition-all border-b-2 ${
                activeTab === tab.id
                  ? 'text-accent-blue border-accent-blue bg-accent-blue/5'
                  : 'text-text-secondary border-transparent hover:text-text-primary hover:bg-bg-tertiary/30'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {tab.label}
            </button>
          );
        })}
      </div>

        {activeTab === 'strategy' && <StrategyTab />}

        {activeTab === 'indicators' && <IndicatorsTab />}

        {activeTab === 'history' && <HistoryTab />}
      </div>
    </div>
  );
}
