import { useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import TopBar from './components/shared/TopBar';
import ChartContainer from './components/Chart/ChartContainer';
import Sidebar from './components/Sidebar/Sidebar';
import ProgressBar from './components/shared/ProgressBar';
import ReportPanel from './components/Report/ReportPanel';
import useChartStore from './stores/chartStore';

function App() {
  const loadData = useChartStore((s) => s.loadData);

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-bg-primary relative">
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#1E222D',
            color: '#D1D4DC',
            border: '1px solid #363A45',
            fontSize: '14px',
          },
          success: {
            iconTheme: { primary: '#4CAF50', secondary: '#1E222D' },
          },
          error: {
            iconTheme: { primary: '#F44336', secondary: '#1E222D' },
          },
        }}
      />

      <ProgressBar />

      {/* Top Bar */}
      <TopBar />

      {/* Main Content: Chart + Sidebar */}
      <div className="flex flex-1 overflow-hidden relative">
        <ReportPanel />
        
        {/* Chart Section — 75% */}
        <div className="flex-1 flex flex-col min-w-0">
          <ChartContainer />
        </div>

        {/* Sidebar — 25% */}
        <div className="w-[380px] flex-shrink-0 border-l border-border">
          <Sidebar />
        </div>
      </div>
    </div>
  );
}

export default App;
