import { TrendingUp, TrendingDown, Activity, DollarSign, Percent } from 'lucide-react';
import useBacktestStore from '../../stores/backtestStore';

export default function MetricsCards() {
  const { currentResult } = useBacktestStore();

  if (!currentResult || !currentResult.metrics) {
    return null;
  }

  const { metrics } = currentResult;

  const cards = [
    {
      label: 'Beneficio Neto',
      value: `$${metrics.net_profit_usd.toFixed(2)}`,
      subValue: `${metrics.net_profit_pct > 0 ? '+' : ''}${metrics.net_profit_pct.toFixed(2)}%`,
      isPositive: metrics.net_profit_usd >= 0,
      icon: DollarSign,
    },
    {
      label: 'Tasa de Acierto',
      value: `${metrics.win_rate_pct.toFixed(1)}%`,
      subValue: `${metrics.winning_trades} / ${metrics.total_trades} trades`,
      isPositive: metrics.win_rate_pct > 50,
      icon: Activity,
    },
    {
      label: 'Profit Factor',
      value: metrics.profit_factor.toFixed(2),
      subValue: 'Relación Ganancia/Pérdida',
      isPositive: metrics.profit_factor > 1,
      icon: TrendingUp,
    },
    {
      label: 'Max Drawdown',
      value: `${metrics.max_drawdown_pct.toFixed(2)}%`,
      subValue: `Derrumbe máximo`,
      isPositive: false, // Drawdown is generally negative context but we color it red
      icon: TrendingDown,
    },
  ];

  return (
    <div className="grid grid-cols-4 gap-4 p-4">
      {cards.map((card, i) => {
        const Icon = card.icon;
        const colorClass = card.isPositive ? 'text-bull-green' : 'text-bear-red';
        const bgColorClass = card.isPositive ? 'bg-bull-green/10' : 'bg-bear-red/10';

        return (
          <div key={i} className="bg-bg-secondary border border-border rounded-xl p-4 flex items-center gap-4">
            <div className={`p-3 rounded-lg ${bgColorClass} ${colorClass}`}>
              <Icon className="w-6 h-6" />
            </div>
            <div>
              <div className="text-xs text-text-secondary mb-1">{card.label}</div>
              <div className={`text-lg font-bold ${colorClass}`}>
                {card.value}
              </div>
              <div className="text-[10px] text-text-secondary/70 mt-0.5">
                {card.subValue}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
