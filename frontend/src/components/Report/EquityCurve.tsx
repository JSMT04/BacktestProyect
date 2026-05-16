import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { format } from 'date-fns';
import useBacktestStore from '../../stores/backtestStore';

export default function EquityCurve() {
  const { currentResult } = useBacktestStore();

  if (!currentResult || !currentResult.equity_curve) {
    return null;
  }

  const { equity_curve, metrics } = currentResult;

  const data = equity_curve.map((point) => ({
    time: point.t * 1000,
    equity: point.equity,
    drawdown: point.drawdown_pct,
  }));

  const formatCurrency = (value: number) => `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  const formatPercent = (value: number) => `${value.toFixed(2)}%`;

  return (
    <div className="bg-bg-secondary border border-border rounded-xl p-4 flex flex-col h-[400px]">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-sm font-semibold text-text-primary">Curva de Capital (Equity)</h3>
        <div className="text-xs text-text-secondary">
          Capital Final: <span className="text-text-primary font-bold">{formatCurrency(metrics.final_capital)}</span>
        </div>
      </div>
      
      <div className="flex-1 min-h-0 w-full relative">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorEquity" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#2962FF" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#2962FF" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#363A45" vertical={false} />
            <XAxis 
              dataKey="time" 
              type="number" 
              scale="time" 
              domain={['dataMin', 'dataMax']} 
              tickFormatter={(unixTime) => format(new Date(unixTime), 'MMM dd')}
              stroke="#787B86" 
              fontSize={10} 
              tickMargin={8}
            />
            <YAxis 
              yAxisId="equity"
              domain={['auto', 'auto']} 
              tickFormatter={(value) => `$${value.toLocaleString()}`}
              stroke="#787B86" 
              fontSize={10} 
              width={60}
            />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1E222D', borderColor: '#363A45', borderRadius: '8px' }}
              itemStyle={{ color: '#D1D4DC', fontSize: '12px' }}
              labelStyle={{ color: '#787B86', fontSize: '10px', marginBottom: '4px' }}
              labelFormatter={(label) => format(new Date(label), 'MMM dd, yyyy HH:mm')}
              formatter={(value: number, name: string) => {
                if (name === 'Equity') return [formatCurrency(value), name];
                return [value, name];
              }}
            />
            <ReferenceLine y={metrics.initial_capital} yAxisId="equity" stroke="#787B86" strokeDasharray="3 3" />
            <Area 
              yAxisId="equity"
              type="monotone" 
              dataKey="equity" 
              name="Equity"
              stroke="#2962FF" 
              strokeWidth={2}
              fillOpacity={1} 
              fill="url(#colorEquity)" 
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
