import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { Dashboard } from './pages/Dashboard';
import { NewAnalysis } from './pages/NewAnalysis';
import { LiveProgress } from './pages/LiveProgress';
import { AnalysisResults } from './pages/AnalysisResults';
import { CodeExplorer } from './pages/CodeExplorer';
import { History } from './pages/History';
import { Settings } from './pages/Settings';
import { Observability } from './pages/Observability';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col font-sans">
        <Navbar />
        <main className="flex-1 pb-16">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/new" element={<NewAnalysis />} />
            <Route path="/live/:sessionId" element={<LiveProgress />} />
            <Route path="/report/:sessionId" element={<AnalysisResults />} />
            <Route path="/explorer/:sessionId" element={<CodeExplorer />} />
            <Route path="/history" element={<History />} />
            <Route path="/observability" element={<Observability />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>

        <footer className="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500 font-mono">
          <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
            <span>ChangeLens Agentic AI Platform &copy; 2026. All rights reserved.</span>
            <span>Powered by Groq High-Speed Inference Engine &middot; Multi-Agent Architecture</span>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  );
};

export default App;
