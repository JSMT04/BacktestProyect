import { create } from 'zustand';
import type { BacktestJob, BacktestResultData, BacktestSummary, BacktestConfig } from '../types';

interface BacktestStore {
  activeJob: BacktestJob | null;
  currentResult: BacktestResultData | null;
  activeJobId: string | null;
  activeJobName: string | null;
  history: BacktestSummary[];
  isRunning: boolean;
  progress: number;
  // Actions
  setActiveJob: (job: BacktestJob | null) => void;
  setResult: (result: BacktestResultData | null, jobId?: string, name?: string) => void;
  setProgress: (p: number) => void;
  setIsRunning: (running: boolean) => void;
  setHistory: (history: BacktestSummary[]) => void;
  reset: () => void;
}

const useBacktestStore = create<BacktestStore>((set) => ({
  activeJob: null,
  currentResult: null,
  activeJobId: null,
  activeJobName: null,
  history: [],
  isRunning: false,
  progress: 0,

  setActiveJob: (job) => set({ activeJob: job }),
  setResult: (result, jobId, name) => set({ currentResult: result, activeJobId: jobId ?? null, activeJobName: name ?? null }),
  setProgress: (progress) => set({ progress }),
  setIsRunning: (isRunning) => set({ isRunning }),
  setHistory: (history) => set({ history }),
  reset: () => set({
    activeJob: null,
    currentResult: null,
    activeJobId: null,
    activeJobName: null,
    isRunning: false,
    progress: 0,
  }),
}));

export default useBacktestStore;
