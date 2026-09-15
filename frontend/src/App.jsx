import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import LivePlayground from './components/LivePlayground';
import EvaluationDashboard from './components/EvaluationDashboard';
import PromptInspector from './components/PromptInspector';
import BenchmarkRunner from './components/BenchmarkRunner';
import JuryDemoMode from './components/JuryDemoMode';
import { fetchHealth } from './api/client';

export default function App() {
  const [activeTab, setActiveTab] = useState('playground');
  const [healthData, setHealthData] = useState(null);
  const [prefilledQuery, setPrefilledQuery] = useState('');

  useEffect(() => {
    fetchHealth()
      .then(data => setHealthData(data))
      .catch(err => console.error('Failed to connect to backend:', err));
  }, []);

  const handleSelectQueryForPlayground = (queryText) => {
    setPrefilledQuery(queryText);
    setActiveTab('playground');
  };

  return (
    <div className="min-h-screen bg-[#0B0F19] text-slate-100 flex flex-col font-sans">
      
      {/* Navigation Header */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        healthData={healthData}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'playground' && (
          <LivePlayground initialQuery={prefilledQuery} />
        )}

        {activeTab === 'dashboard' && (
          <EvaluationDashboard />
        )}

        {activeTab === 'prompts' && (
          <PromptInspector />
        )}

        {activeTab === 'benchmarks' && (
          <BenchmarkRunner
            onSelectQueryForPlayground={handleSelectQueryForPlayground}
            onBenchmarkCompleted={() => {}}
          />
        )}

        {activeTab === 'jury' && (
          <JuryDemoMode
            onNavigateToPlayground={handleSelectQueryForPlayground}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-[#0B0F19]/80 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>PromptDesk AI — Generative AI Prompt Engineering Support Desk Project</span>
          <span className="font-mono text-slate-400">ShopEase Support Architecture • {healthData?.model || 'gemini-3.6-flash'}</span>
        </div>
      </footer>

    </div>
  );
}
