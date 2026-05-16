import useChartStore from '../../stores/chartStore';
import type { Timeframe } from '../../types';

const TIMEFRAMES: { value: Timeframe; label: string }[] = [
  { value: '1m', label: '1m' },
  { value: '5m', label: '5m' },
  { value: '15m', label: '15m' },
  { value: '30m', label: '30m' },
  { value: '1h', label: '1H' },
  { value: '4h', label: '4H' },
  { value: '1d', label: '1D' },
  { value: '1w', label: '1S' },
  { value: '1M', label: '1M' },
];

export default function TimeframeSelector() {
  const { timeframe, setTimeframe } = useChartStore();

  return (
    <div className="flex items-center gap-0.5">
      {TIMEFRAMES.map((tf) => (
        <button
          key={tf.value}
          onClick={() => setTimeframe(tf.value)}
          className={`px-2 py-1 text-xs font-medium rounded transition-all ${
            timeframe === tf.value
              ? 'bg-accent-blue text-white'
              : 'text-text-secondary hover:text-text-primary hover:bg-bg-tertiary'
          }`}
        >
          {tf.label}
        </button>
      ))}
    </div>
  );
}
