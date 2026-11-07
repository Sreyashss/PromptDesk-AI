import React, { useState, useEffect } from 'react';
import {
  GitCompare,
  Play,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  TrendingDown,
  Minus,
  HelpCircle,
  Info,
  FileText,
  Zap,
  ShieldAlert
} from 'lucide-react';
import { runRegressionTest, fetchRegressionReports, fetchBenchmarkQueries } from '../api/client';

const VERSION_OPTIONS = [
  { value: 'v1', label: 'V1 — Baseline (Naive)' },
  { value: 'v2', label: 'V2 — Policy-Aware' },
  { value: 'v3', label: 'V3 — Few-Shot Guided' },
  { value: 'v4', label: 'V4 — Hardened Guardrails' },
];

const OUTCOME_CONFIG = {
  IMPROVED: {
    label: 'IMPROVED',
    icon: TrendingUp,
    classes: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
    row: 'hover:bg-emerald-950/10',
  },
  REGRESSION: {
    label: 'REGRESSION',
    icon: TrendingDown,
    classes: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
    row: 'hover:bg-rose-950/10',
  },
  UNCHANGED: {
    label: 'UNCHANGED',
    icon: Minus,
    classes: 'bg-slate-700/60 text-slate-300 border-slate-600',
    row: 'hover:bg-slate-800/30',
  },
  NOT_COMPARABLE: {
    label: 'N/A',
    icon: HelpCircle,
    classes: 'bg-amber-500/10 text-amber-400 border-amber-500/25',
    row: 'hover:bg-amber-950/10',
  },
};

function OutcomeBadge({ outcome }) {
  const cfg = OUTCOME_CONFIG[outcome] || OUTCOME_CONFIG.NOT_COMPARABLE;
  const Icon = cfg.icon;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[10px] font-bold whitespace-nowrap ${cfg.classes}`}>
      <Icon className="w-3 h-3" />
      {cfg.label}
    </span>
  );
}

function ScoreCell({ value, status }) {
  if (status !== 'EVALUATED' || value === null || value === undefined) {
    return <span className="text-slate-500 font-mono text-[11px]">N/A</span>;
  }
  return <span className="font-bold text-cyan-300 font-mono text-[12px]">{Number(value).toFixed(1)}</span>;
}

function AggregateCard({ agg, colorClass }) {
  if (!agg) return null;
  const hasData = agg.evaluated_count > 0;
  return (
    <div className={`p-4 rounded-xl border ${colorClass} space-y-3`}>
      <div className="flex items-center justify-between">
        <span className="font-bold text-white text-sm">{agg.version}</span>
        <span className="text-[11px] text-slate-400">
          {agg.evaluated_count} / {agg.total_cases} evaluated
          {agg.api_error_count > 0 && (
            <span className="ml-1.5 text-rose-400">({agg.api_error_count} API errors)</span>
          )}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="p-2 rounded-lg bg-slate-950/60 text-center border border-slate-800">
          <div className="text-slate-400 text-[10px] mb-0.5">Avg PQI</div>
          <div className="font-bold text-white text-base">{hasData ? agg.avg_pqi ?? 'N/A' : '—'}</div>
        </div>
        <div className="p-2 rounded-lg bg-slate-950/60 text-center border border-slate-800">
          <div className="text-slate-400 text-[10px] mb-0.5">Correctness</div>
          <div className="font-bold text-white text-base">{hasData ? agg.avg_correctness ?? 'N/A' : '—'}</div>
        </div>
        <div className="p-2 rounded-lg bg-slate-950/60 text-center border border-slate-800">
          <div className="text-slate-400 text-[10px] mb-0.5">Hallucination</div>
          <div className={`font-bold text-base ${hasData && agg.hallucination_rate_pct === 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
            {hasData ? `${agg.hallucination_rate_pct ?? 'N/A'}%` : '—'}
          </div>
        </div>
        <div className="p-2 rounded-lg bg-slate-950/60 text-center border border-slate-800">
          <div className="text-slate-400 text-[10px] mb-0.5">Escalation Acc.</div>
          <div className="font-bold text-white text-base">{hasData ? `${agg.escalation_accuracy_pct ?? 'N/A'}%` : '—'}</div>
        </div>
      </div>
    </div>
  );
}

export default function RegressionTester() {
  const [baseline, setBaseline] = useState('v1');
  const [candidate, setCandidate] = useState('v4');
  const [allQueries, setAllQueries] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]); // empty = all 20
  const [useSubset, setUseSubset] = useState(false);
  const [report, setReport] = useState(null);
  const [pastReports, setPastReports] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState('');
  const [showConfirm, setShowConfirm] = useState(false);
  const [expandedRows, setExpandedRows] = useState({});
  const [showPastReports, setShowPastReports] = useState(false);

  useEffect(() => {
    fetchBenchmarkQueries()
      .then(d => setAllQueries(d.queries || []))
      .catch(() => {});
    fetchRegressionReports()
      .then(d => setPastReports(d.reports || []))
      .catch(() => {});
  }, []);

  const effectiveIds = useSubset && selectedIds.length > 0 ? selectedIds : null;
  const caseCount = effectiveIds ? effectiveIds.length : 20;
  const estimatedCalls = caseCount * 4; // 2 versions × 2 calls (gen + judge) each

  const handleRequestRun = () => {
    if (baseline === candidate) {
      setError('Baseline and candidate must be different versions.');
      return;
    }
    setError('');
    setShowConfirm(true);
  };

  const handleConfirmRun = async () => {
    setShowConfirm(false);
    setIsRunning(true);
    setReport(null);
    setError('');
    try {
      const result = await runRegressionTest(baseline, candidate, effectiveIds);
      setReport(result.report);
      // Refresh past reports list
      fetchRegressionReports()
        .then(d => setPastReports(d.reports || []))
        .catch(() => {});
    } catch (err) {
      setError(err.message || 'Regression run failed');
    } finally {
      setIsRunning(false);
    }
  };

  const toggleRow = (testId) => {
    setExpandedRows(prev => ({ ...prev, [testId]: !prev[testId] }));
  };

  const toggleCaseId = (id) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const outcomeSummary = report?.outcome_summary || {};
  const regressionCount = outcomeSummary.REGRESSION || 0;
  const hasRegressions = regressionCount > 0;

  return (
    <div className="space-y-5">

      {/* Header */}
      <div className="p-5 rounded-2xl glass-panel border border-slate-800 bg-gradient-to-r from-slate-900 via-slate-900/60 to-violet-950/20">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <div className="flex items-center space-x-2">
              <span className="p-2 rounded-lg bg-violet-500/10 text-violet-400 border border-violet-500/20">
                <GitCompare className="w-5 h-5" />
              </span>
              <h3 className="text-lg font-bold text-white tracking-tight">
                Prompt Regression Testing
              </h3>
            </div>
            <p className="mt-1 text-xs text-slate-400 max-w-xl">
              Compare two prompt versions case-by-case across the benchmark suite to detect regressions
              before deployment. Reports are saved separately and never overwrite existing evaluation data.
            </p>
          </div>
        </div>

        {/* Version Selectors */}
        <div className="mt-5 flex flex-col sm:flex-row items-start sm:items-end gap-4">
          <div className="flex-1 min-w-[160px]">
            <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
              Baseline Version
            </label>
            <select
              value={baseline}
              onChange={e => setBaseline(e.target.value)}
              disabled={isRunning}
              className="w-full bg-slate-900 border border-slate-700 text-xs text-slate-200 rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-violet-500"
            >
              {VERSION_OPTIONS.map(o => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center pt-5 sm:pt-0">
            <span className="text-slate-500 font-mono text-lg">vs</span>
          </div>

          <div className="flex-1 min-w-[160px]">
            <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
              Candidate Version
            </label>
            <select
              value={candidate}
              onChange={e => setCandidate(e.target.value)}
              disabled={isRunning}
              className="w-full bg-slate-900 border border-slate-700 text-xs text-slate-200 rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-violet-500"
            >
              {VERSION_OPTIONS.map(o => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>

          <button
            onClick={handleRequestRun}
            disabled={isRunning}
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-purple-700 hover:from-violet-500 hover:to-purple-600 text-white font-semibold text-xs flex items-center space-x-2 shadow-lg shadow-violet-500/20 disabled:opacity-50 transition-all whitespace-nowrap self-end"
          >
            {isRunning ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Running…</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                <span>Run Regression Test</span>
              </>
            )}
          </button>
        </div>

        {/* Subset selector */}
        <div className="mt-4 border-t border-slate-800 pt-4">
          <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-300 font-medium select-none">
            <input
              type="checkbox"
              checked={useSubset}
              onChange={e => setUseSubset(e.target.checked)}
              className="rounded border-slate-600 bg-slate-900 accent-violet-500"
            />
            Use a smaller subset (select individual test cases)
          </label>
          {useSubset && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {allQueries.map(q => (
                <button
                  key={q.id}
                  onClick={() => toggleCaseId(q.id)}
                  className={`px-2 py-1 rounded text-[10px] font-mono font-bold border transition-all ${
                    selectedIds.includes(q.id)
                      ? 'bg-violet-500 text-white border-violet-400'
                      : 'bg-slate-900 text-slate-400 border-slate-700 hover:border-slate-500'
                  }`}
                >
                  {q.id}
                </button>
              ))}
              {selectedIds.length > 0 && (
                <button
                  onClick={() => setSelectedIds([])}
                  className="px-2 py-1 rounded text-[10px] text-slate-400 border border-slate-700 hover:text-slate-200"
                >
                  Clear
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Confirmation dialog */}
      {showConfirm && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center space-x-2">
              <ShieldAlert className="w-5 h-5 text-amber-400" />
              <h4 className="font-bold text-white text-base">Confirm Gemini API Usage</h4>
            </div>
            <div className="p-3 rounded-xl bg-amber-500/5 border border-amber-500/20 text-xs text-amber-200 space-y-1.5">
              <p>
                This will compare <strong className="text-amber-300">{baseline.toUpperCase()}</strong> (baseline)
                vs <strong className="text-amber-300">{candidate.toUpperCase()}</strong> (candidate)
                across <strong className="text-amber-300">{caseCount} test cases</strong>.
              </p>
              <p>
                Estimated Gemini API calls: <strong className="text-amber-300">up to ~{estimatedCalls}</strong>
                {' '}(generation + judge for each version × each case).
              </p>
              <p>
                If the Gemini quota is exhausted (429), the run will stop early and partial results will be saved.
                No automatic retries are made.
              </p>
            </div>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowConfirm(false)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmRun}
                className="px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-500 text-white text-xs font-bold"
              >
                Confirm & Run
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Error banner */}
      {error && (
        <div className="flex items-center gap-2 p-3 rounded-xl border border-rose-500/30 bg-rose-500/5 text-rose-300 text-xs">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      {/* Running state */}
      {isRunning && (
        <div className="p-5 rounded-2xl glass-panel border border-violet-500/20 bg-violet-950/10 flex items-center gap-3 text-sm text-violet-200">
          <RefreshCw className="w-5 h-5 animate-spin text-violet-400" />
          <span>
            Running regression comparison: <strong>{baseline.toUpperCase()}</strong> vs{' '}
            <strong>{candidate.toUpperCase()}</strong> over {caseCount} cases…
          </span>
        </div>
      )}

      {/* Report */}
      {report && !isRunning && (
        <div className="space-y-4">

          {/* Run metadata */}
          <div className="p-4 rounded-2xl glass-panel border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="space-y-0.5">
              <div className="text-xs text-slate-400">
                Run ID: <span className="font-mono text-slate-200">{report.run_id}</span>
              </div>
              <div className="text-xs text-slate-400">
                {report.baseline_version} vs {report.candidate_version} •{' '}
                {report.total_cases_selected} cases
              </div>
            </div>
            {/* Outcome summary pills */}
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(OUTCOME_CONFIG).map(([k, cfg]) => {
                const Icon = cfg.icon;
                const count = outcomeSummary[k] ?? 0;
                return (
                  <span key={k} className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg border text-[11px] font-bold ${cfg.classes}`}>
                    <Icon className="w-3 h-3" />
                    {count} {cfg.label}
                  </span>
                );
              })}
            </div>
          </div>

          {/* Regression alert */}
          {hasRegressions && (
            <div className="flex items-center gap-2 p-3 rounded-xl border border-rose-500/30 bg-rose-500/5 text-rose-300 text-xs font-medium">
              <TrendingDown className="w-4 h-4 shrink-0" />
              <span>
                {regressionCount} regression{regressionCount !== 1 ? 's' : ''} detected.
                Review the case table below for details.
              </span>
            </div>
          )}

          {/* Aggregate comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <AggregateCard
              agg={report.baseline_aggregate}
              colorClass="border-slate-700 bg-slate-900/30"
            />
            <AggregateCard
              agg={report.candidate_aggregate}
              colorClass="border-violet-500/25 bg-violet-950/10"
            />
          </div>

          {/* Case-level table */}
          <div className="rounded-2xl glass-panel border border-slate-800 overflow-hidden">
            <div className="p-4 border-b border-slate-800 flex items-center gap-2">
              <FileText className="w-4 h-4 text-violet-400" />
              <h4 className="font-bold text-white text-sm">Case-Level Comparison</h4>
              <span className="text-xs text-slate-400 ml-auto">
                Click a row to expand the model responses
              </span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-slate-300">
                <thead className="bg-slate-900/80 text-slate-400 uppercase text-[10px] font-bold tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="px-3 py-2.5 text-left">ID</th>
                    <th className="px-3 py-2.5 text-left">Category</th>
                    <th className="px-3 py-2.5 text-left">
                      {report.baseline_version} PQI
                    </th>
                    <th className="px-3 py-2.5 text-left">
                      {report.candidate_version} PQI
                    </th>
                    <th className="px-3 py-2.5 text-left">Outcome</th>
                    <th className="px-3 py-2.5 text-left w-56">Reason</th>
                    <th className="px-3 py-2.5"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {(report.case_comparisons || []).map((row) => {
                    const cfg = OUTCOME_CONFIG[row.outcome] || OUTCOME_CONFIG.NOT_COMPARABLE;
                    const expanded = expandedRows[row.test_id];
                    return (
                      <React.Fragment key={row.test_id}>
                        <tr
                          className={`cursor-pointer transition-colors ${cfg.row}`}
                          onClick={() => toggleRow(row.test_id)}
                        >
                          <td className="px-3 py-2.5 font-mono font-bold text-slate-400 whitespace-nowrap">
                            {row.test_id}
                          </td>
                          <td className="px-3 py-2.5 text-slate-300 whitespace-nowrap">
                            {row.category}
                          </td>
                          <td className="px-3 py-2.5">
                            <ScoreCell value={row.baseline_pqi} status={row.baseline_status} />
                          </td>
                          <td className="px-3 py-2.5">
                            <ScoreCell value={row.candidate_pqi} status={row.candidate_status} />
                          </td>
                          <td className="px-3 py-2.5">
                            <OutcomeBadge outcome={row.outcome} />
                          </td>
                          <td className="px-3 py-2.5 text-slate-400 max-w-[220px]">
                            <span className={row.outcome === 'REGRESSION' ? 'text-rose-300' : ''}>
                              {row.reason}
                            </span>
                          </td>
                          <td className="px-3 py-2.5 text-slate-500">
                            {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                          </td>
                        </tr>
                        {expanded && (
                          <tr className="bg-slate-950/60">
                            <td colSpan={7} className="px-4 py-3 text-xs">
                              <p className="mb-2 text-slate-300 italic">"{row.query}"</p>
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                <div className="space-y-1">
                                  <span className="text-[10px] font-bold uppercase text-slate-400">
                                    {report.baseline_version} status
                                  </span>
                                  <p className="font-mono text-[11px] text-slate-400">
                                    {row.baseline_status} •{' '}
                                    {row.baseline_hallucination ? '⚠ Hallucination' : '✓ Clean'} •{' '}
                                    Esc: {row.baseline_escalated === null ? 'N/A' : row.baseline_escalated ? 'Correct' : 'Missed'}
                                  </p>
                                </div>
                                <div className="space-y-1">
                                  <span className="text-[10px] font-bold uppercase text-slate-400">
                                    {report.candidate_version} status
                                  </span>
                                  <p className="font-mono text-[11px] text-slate-400">
                                    {row.candidate_status} •{' '}
                                    {row.candidate_hallucination ? '⚠ Hallucination' : '✓ Clean'} •{' '}
                                    Esc: {row.candidate_escalated === null ? 'N/A' : row.candidate_escalated ? 'Correct' : 'Missed'}
                                  </p>
                                </div>
                              </div>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Past regression reports */}
      {pastReports.length > 0 && (
        <div className="rounded-2xl glass-panel border border-slate-800">
          <button
            onClick={() => setShowPastReports(p => !p)}
            className="w-full p-4 flex items-center justify-between text-left"
          >
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-slate-400" />
              <span className="font-semibold text-sm text-slate-300">
                Saved Regression Reports ({pastReports.length})
              </span>
            </div>
            {showPastReports ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
          </button>
          {showPastReports && (
            <div className="px-4 pb-4 space-y-2">
              {pastReports.map(r => (
                <div
                  key={r.run_id}
                  className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2"
                >
                  <div className="text-xs space-y-0.5">
                    <div className="font-mono text-slate-300">{r.run_id}</div>
                    <div className="text-slate-400">
                      {r.baseline_version} vs {r.candidate_version} — {r.total_cases_selected} cases
                    </div>
                  </div>
                  <div className="flex gap-1.5 flex-wrap">
                    {Object.entries(OUTCOME_CONFIG).map(([k, cfg]) => {
                      const count = r.outcome_summary?.[k] ?? 0;
                      if (count === 0) return null;
                      return (
                        <span key={k} className={`px-2 py-0.5 rounded border text-[10px] font-bold ${cfg.classes}`}>
                          {count} {k}
                        </span>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Info note */}
      <div className="flex items-start gap-2 p-3 rounded-xl bg-slate-900/50 border border-slate-800 text-xs text-slate-400">
        <Info className="w-3.5 h-3.5 mt-0.5 shrink-0 text-violet-400" />
        <span>
          Results are classified as <strong className="text-rose-400">REGRESSION</strong> only when both versions
          were successfully evaluated and the candidate scored lower under the existing PQI rubric.
          API errors and unevaluated cases are always <strong className="text-amber-400">NOT_COMPARABLE</strong> and
          excluded from all aggregate averages.
          Reports are saved to <code className="font-mono">data/regression_reports/</code> and never touch
          existing benchmark CSV files.
        </span>
      </div>

    </div>
  );
}
