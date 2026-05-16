import { create } from 'zustand';
import type { PositionType, CommissionType, ConditionOperator } from '../types';

export interface StrategyCondition {
  id: string;
  indicator_a: { type: string; params: Record<string, any>; source?: string };
  operator: ConditionOperator;
  indicator_b?: { type: string; params: Record<string, any>; source?: string };
  value?: number;
}

interface StrategyStore {
  // Config
  editorMode: 'visual' | 'code';
  code: string;
  initialCapital: number;
  positionValue: number;
  positionType: PositionType;
  commissionValue: number;
  commissionType: CommissionType;
  stopLossValue: number;
  takeProfitValue: number;
  
  // Conditions
  entryLong: StrategyCondition[];
  exitLong: StrategyCondition[];

  // Actions
  setEditorMode: (mode: 'visual' | 'code') => void;
  setCode: (code: string) => void;
  setCapital: (v: number) => void;
  setPosition: (v: number, t: PositionType) => void;
  setCommission: (v: number, t: CommissionType) => void;
  setStops: (sl: number, tp: number) => void;
  addEntryCondition: (cond: Omit<StrategyCondition, 'id'>) => void;
  removeEntryCondition: (id: string) => void;
  addExitCondition: (cond: Omit<StrategyCondition, 'id'>) => void;
  removeExitCondition: (id: string) => void;
}

const generateId = () => Math.random().toString(36).substr(2, 9);

const useStrategyStore = create<StrategyStore>((set) => ({
  editorMode: 'visual',
  code: '# Escribe tu estrategia en Python aquí\n# Usa df, pd, np, ta\n# Define entries, exits, short_entries, short_exits\n\nfast = ta.sma(df["close"], length=10)\nslow = ta.sma(df["close"], length=50)\n\nentries = (fast > slow) & (fast.shift(1) <= slow.shift(1))\nexits = (fast < slow) & (fast.shift(1) >= slow.shift(1))\n',
  initialCapital: 10000,
  positionValue: 100,
  positionType: 'percent_capital',
  commissionValue: 0.1,
  commissionType: 'percent',
  stopLossValue: 2,
  takeProfitValue: 2,
  entryLong: [],
  exitLong: [],

  setEditorMode: (mode) => set({ editorMode: mode }),
  setCode: (code) => set({ code }),
  setCapital: (v) => set({ initialCapital: v }),
  setPosition: (v, t) => set({ positionValue: v, positionType: t }),
  setCommission: (v, t) => set({ commissionValue: v, commissionType: t }),
  setStops: (sl, tp) => set({ stopLossValue: sl, takeProfitValue: tp }),
  
  addEntryCondition: (cond) => set((state) => ({ 
    entryLong: [...state.entryLong, { ...cond, id: generateId() }] 
  })),
  removeEntryCondition: (id) => set((state) => ({ 
    entryLong: state.entryLong.filter((c) => c.id !== id) 
  })),
  
  addExitCondition: (cond) => set((state) => ({ 
    exitLong: [...state.exitLong, { ...cond, id: generateId() }] 
  })),
  removeExitCondition: (id) => set((state) => ({ 
    exitLong: state.exitLong.filter((c) => c.id !== id) 
  })),
}));

export default useStrategyStore;
