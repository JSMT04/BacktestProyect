import { useMemo, useState } from 'react';
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  SortingState,
} from '@tanstack/react-table';
import { format } from 'date-fns';
import { ArrowUpDown } from 'lucide-react';
import useBacktestStore from '../../stores/backtestStore';
import type { Trade } from '../../types';

const columnHelper = createColumnHelper<Trade>();

export default function TradesList() {
  const { currentResult } = useBacktestStore();
  const [sorting, setSorting] = useState<SortingState>([]);

  const data = useMemo(() => currentResult?.trades || [], [currentResult]);

  const columns = useMemo(
    () => [
      columnHelper.accessor('trade_id', {
        header: 'ID',
        cell: (info) => <span className="text-text-secondary">#{info.getValue()}</span>,
      }),
      columnHelper.accessor('direction', {
        header: 'Lado',
        cell: (info) => {
          const val = info.getValue();
          return (
            <span className={`font-medium ${val === 'LONG' ? 'text-bull-green' : 'text-bear-red'}`}>
              {val}
            </span>
          );
        },
      }),
      columnHelper.accessor('entry_time', {
        header: 'Entrada',
        cell: (info) => format(new Date(info.getValue()), 'MMM dd, HH:mm'),
      }),
      columnHelper.accessor('entry_price', {
        header: 'Precio Ent.',
        cell: (info) => `$${info.getValue().toFixed(2)}`,
      }),
      columnHelper.accessor('exit_time', {
        header: 'Salida',
        cell: (info) => format(new Date(info.getValue()), 'MMM dd, HH:mm'),
      }),
      columnHelper.accessor('exit_price', {
        header: 'Precio Sal.',
        cell: (info) => `$${info.getValue().toFixed(2)}`,
      }),
      columnHelper.accessor('pnl_usd', {
        header: 'PnL ($)',
        cell: (info) => {
          const val = info.getValue();
          return (
            <span className={`font-medium ${val >= 0 ? 'text-bull-green' : 'text-bear-red'}`}>
              {val > 0 ? '+' : ''}{val.toFixed(2)}
            </span>
          );
        },
      }),
      columnHelper.accessor('pnl_pct', {
        header: 'PnL (%)',
        cell: (info) => {
          const val = info.getValue();
          return (
            <span className={val >= 0 ? 'text-bull-green' : 'text-bear-red'}>
              {val > 0 ? '+' : ''}{val.toFixed(2)}%
            </span>
          );
        },
      }),
    ],
    []
  );

  const table = useReactTable({
    data,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  if (!currentResult || data.length === 0) return null;

  return (
    <div className="bg-bg-secondary border border-border rounded-xl flex flex-col h-[400px] overflow-hidden">
      <div className="p-4 border-b border-border flex justify-between items-center">
        <h3 className="text-sm font-semibold text-text-primary">Lista de Operaciones ({data.length})</h3>
      </div>
      
      <div className="flex-1 overflow-auto">
        <table className="w-full text-xs text-left">
          <thead className="sticky top-0 bg-bg-secondary border-b border-border z-10">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    onClick={header.column.getToggleSortingHandler()}
                    className="p-3 font-semibold text-text-secondary cursor-pointer hover:text-text-primary select-none whitespace-nowrap group"
                  >
                    <div className="flex items-center gap-1">
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      <ArrowUpDown className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-border/50">
            {table.getRowModel().rows.map((row) => (
              <tr key={row.id} className="hover:bg-bg-tertiary/30 transition-colors">
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="p-3 text-text-primary whitespace-nowrap">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
