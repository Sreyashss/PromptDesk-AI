import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  Play, 
  RefreshCw, 
  CheckCircle2, 
  AlertTriangle, 
  Flame, 
  ExternalLink, 
  Filter, 
  Search,
  Layers,
  ArrowRight
} from 'lucide-react';
import { fetchBenchmarkQueries, runBenchmarkSuite } from '../api/client';

export default function BenchmarkRunner({ onSelectQueryForPlayground, onBenchmarkCompleted }) {
  const [queries, setQueries] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [searchFilter, setSearchFilter] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [runProgress, setRunProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');
  const [selectedVersion, setSelectedVersion] = useState('all');

  useEffect(() => {
    fetchBenchmarkQueries()
      .then(data => setQueries(data.queries || []))
      .catch(err => console.error('Failed to load benchmark queries:', err));
  }, []);

  const categories = ['All', 'Standard Policy', 'Boundary & Edge Cases', 'Adversarial & Hallucination Traps', 'Escalation & High-Risk'];

  const filteredQueries = queries.filter(q => {
    const matchesCategory = selectedCategory === 'All' || q.category === selectedCategory;
    const matchesSearch = q.query.toLowerCase().includes(searchFilter.toLowerCase()) || 
                          q.id.toLowerCase().includes(searchFilter.toLowerCase()) ||
                          q.ground_truth_policy.toLowerCase().includes(searchFilter.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const handleRunSuite = async () => {
    setIsRunning(true);
    setRunProgress(10);
    setStatusMessage('Initializing evaluation pipeline...');

    try {
      const timer = setInterval(() => {
        setRunProgress(prev => {
          if (prev >= 90) return prev;
          return prev + 15;
        });
      }, 400);

      const targetVersion = selectedVersion === 'all' ? null : selectedVersion;
      await runBenchmarkSuite(targetVersion);
      
      clearInterval(timer);
      setRunProgress(100);
      setStatusMessage('Evaluation complete! CSV logs & charts updated.');
      
      if (onBenchmarkCompleted) {
        onBenchmarkCompleted();
      }
    } catch (err) {
      console.error('Benchmark execution error:', err);
      setStatusMessage(`Error: ${err.message || 'Execution failed'}`);
    } finally {
      setTimeout(() => {
        setIsRunning(false);
        setRunProgress(0);
        setStatusMessage('');
      }, 2500);
    }
  };

  const getCategoryBadge = (category) => {
    switch (category) {
      case 'Standard Policy':
        return 'bg-sky-500/15 text-sky-400 border-sky-500/30';
      case 'Boundary & Edge Cases':
        return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
      case 'Adversarial & Hallucination Traps':
        return 'bg-purple-500/15 text-purple-400 border-purple-500/30';
      case 'Escalation & High-Risk':
        return 'bg-rose-500/15 text-rose-400 border-rose-500/30';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Header & Benchmark Controls */}
      <div className="p-6 rounded-2xl glass-panel border border-slate-800 bg-gradient-to-r from-slate-900 via-slate-900/60 to-emerald-950/30">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <ShieldCheck className="w-5 h-5" />
              </span>
              <h2 className="text-xl font-bold text-white tracking-tight">
                ShopEase 20-Query Benchmark Test Suite
              </h2>
            </div>
            <p className="mt-1 text-sm text-slate-400">
              The standardized ground-truth benchmark containing 20 curated customer queries covering routine policy, boundary edges, hallucination traps, and critical escalation triggers.
            </p>
          </div>

          {/* Action Trigger */}
          <div className="flex items-center space-x-3 self-start md:self-auto">
            <select
              value={selectedVersion}
              onChange={(e) => setSelectedVersion(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-xs text-slate-200 rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="all">Run All (V1 - V4 Suite)</option>
              <option value="v1">Run V1 (Baseline Only)</option>
              <option value="v2">Run V2 (Policy Only)</option>
              <option value="v3">Run V3 (Few-Shot Only)</option>
              <option value="v4">Run V4 (Hardened Only)</option>
            </select>

            <button
              onClick={handleRunSuite}
              disabled={isRunning}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white font-semibold text-xs sm:text-sm flex items-center space-x-2 shadow-lg shadow-emerald-500/20 disabled:opacity-50 transition-all whitespace-nowrap"
            >
              {isRunning ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Evaluating Suite...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-white" />
                  <span>Run Benchmark Suite</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Live Progress Bar */}
        {isRunning && (
          <div className="mt-5 space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-300">
              <span className="font-medium flex items-center">
                <RefreshCw className="w-3.5 h-3.5 mr-1.5 animate-spin text-emerald-400" />
                {statusMessage}
              </span>
              <span className="font-mono font-bold text-emerald-400">{runProgress}%</span>
            </div>
            <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500 transition-all duration-300"
                style={{ width: `${runProgress}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        {/* Category Pills */}
        <div className="flex flex-wrap gap-1.5 w-full sm:w-auto">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                selectedCategory === cat
                  ? 'bg-slate-100 text-slate-900 shadow-sm'
                  : 'bg-slate-900/80 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Search Input */}
        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            placeholder="Search test cases..."
            className="w-full pl-9 pr-3 py-1.5 bg-slate-900/90 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>
      </div>

      {/* Test Case Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredQueries.map((tc) => (
          <div
            key={tc.id}
            className="p-5 rounded-2xl glass-panel border border-slate-800/90 hover:border-slate-700 transition-all flex flex-col justify-between space-y-4"
          >
            <div>
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-xs font-bold text-slate-400">
                  {tc.id}
                </span>
                <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${getCategoryBadge(tc.category)}`}>
                  {tc.category}
                </span>
              </div>

              {/* Query Text */}
              <p className="mt-3 text-sm font-semibold text-white leading-relaxed">
                "{tc.query}"
              </p>

              {/* Ground Truth Policy Expectation */}
              <div className="mt-3 p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1.5 text-xs">
                <div className="flex items-center text-slate-400 font-semibold">
                  <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-emerald-400" />
                  <span>Ground Truth Expectation:</span>
                </div>
                <p className="text-slate-300 pl-4 leading-relaxed">
                  {tc.ground_truth_policy}
                </p>
              </div>

              {/* Escalation or Hallucination Traps */}
              <div className="mt-2.5 flex items-center justify-between text-xs">
                {tc.should_escalate ? (
                  <span className="px-2 py-0.5 rounded bg-rose-500/15 text-rose-400 border border-rose-500/30 font-bold flex items-center">
                    <AlertTriangle className="w-3 h-3 mr-1" />
                    Must Escalate: {tc.escalation_type}
                  </span>
                ) : (
                  <span className="text-slate-400 text-[11px]">
                    Standard Resolution (No Escalation)
                  </span>
                )}
                
                {tc.hallucination_risk && (
                  <span className="text-[11px] text-amber-400/90 italic truncate max-w-[200px]" title={tc.hallucination_risk}>
                    Trap: {tc.hallucination_risk}
                  </span>
                )}
              </div>
            </div>

            {/* Test in Playground Button */}
            <div className="pt-3 border-t border-slate-800/80 flex justify-end">
              <button
                onClick={() => onSelectQueryForPlayground && onSelectQueryForPlayground(tc.query)}
                className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 flex items-center space-x-1 group"
              >
                <span>Test in Live Playground</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </button>
            </div>

          </div>
        ))}
      </div>

    </div>
  );
}
