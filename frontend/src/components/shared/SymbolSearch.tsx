import { useState, useRef, useEffect, useCallback } from 'react';
import { Search, X } from 'lucide-react';
import { searchSymbols } from '../../services/api';
import useChartStore from '../../stores/chartStore';
import type { SymbolInfo } from '../../types';

export default function SymbolSearch() {
  const { symbol, setSymbol } = useChartStore();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SymbolInfo[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<NodeJS.Timeout>();

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Debounced search
  const doSearch = useCallback(async (q: string) => {
    if (q.length < 1) {
      setResults([]);
      return;
    }

    setIsSearching(true);
    try {
      const data = await searchSymbols(q, 15);
      setResults(data.results);
      setSelectedIndex(0);
    } catch {
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  }, []);

  const handleInputChange = (value: string) => {
    setQuery(value);
    setIsOpen(true);

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => doSearch(value), 250);
  };

  const selectSymbol = (sym: SymbolInfo) => {
    setSymbol(sym.symbol);
    setQuery('');
    setIsOpen(false);
    setResults([]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen || results.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      selectSymbol(results[selectedIndex]);
    } else if (e.key === 'Escape') {
      setIsOpen(false);
    }
  };

  const typeColors: Record<string, string> = {
    crypto: 'text-accent-gold',
    forex: 'text-accent-blue',
    stock: 'text-bull-green',
    commodity: 'text-warning',
    index: 'text-accent-purple',
  };

  const typeBgColors: Record<string, string> = {
    crypto: 'bg-accent-gold/10',
    forex: 'bg-accent-blue/10',
    stock: 'bg-bull-green/10',
    commodity: 'bg-warning/10',
    index: 'bg-accent-purple/10',
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Current symbol display + search input */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => {
            setIsOpen(true);
            setTimeout(() => inputRef.current?.focus(), 50);
          }}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded hover:bg-bg-tertiary transition-colors"
        >
          <span className="text-sm font-semibold text-text-primary">{symbol}</span>
        </button>

        {isOpen && (
          <div className="absolute top-full left-0 mt-1 w-[400px] bg-bg-secondary border border-border rounded-lg shadow-2xl z-50 overflow-hidden">
            {/* Search input */}
            <div className="flex items-center gap-2 px-3 py-2.5 border-b border-border">
              <Search className="w-4 h-4 text-text-secondary" />
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => handleInputChange(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Buscar símbolo... (ej: BTC, AAPL, EUR)"
                className="flex-1 bg-transparent text-sm text-text-primary placeholder-text-secondary outline-none"
                autoFocus
              />
              {query && (
                <button onClick={() => { setQuery(''); setResults([]); }}>
                  <X className="w-3.5 h-3.5 text-text-secondary hover:text-text-primary" />
                </button>
              )}
            </div>

            {/* Results */}
            <div className="max-h-[320px] overflow-y-auto">
              {isSearching ? (
                <div className="px-4 py-8 text-center text-text-secondary text-sm">
                  Buscando...
                </div>
              ) : results.length > 0 ? (
                results.map((r, idx) => (
                  <button
                    key={r.symbol}
                    onClick={() => selectSymbol(r)}
                    className={`w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-bg-tertiary transition-colors ${
                      idx === selectedIndex ? 'bg-bg-tertiary' : ''
                    }`}
                  >
                    <span className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded ${typeColors[r.type]} ${typeBgColors[r.type]}`}>
                      {r.type}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-text-primary truncate">
                        {r.symbol}
                      </div>
                      <div className="text-xs text-text-secondary truncate">
                        {r.name}
                      </div>
                    </div>
                    <span className="text-xs text-text-secondary">{r.exchange}</span>
                  </button>
                ))
              ) : query.length > 0 ? (
                <div className="px-4 py-8 text-center text-text-secondary text-sm">
                  Sin resultados para &quot;{query}&quot;
                </div>
              ) : (
                <div className="px-4 py-6 text-center text-text-secondary text-sm">
                  Escribe para buscar un símbolo
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
