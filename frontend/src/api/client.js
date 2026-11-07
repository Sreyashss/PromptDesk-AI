/**
 * API Client for PromptDesk AI FastAPI Backend
 */

const API_BASE_URL = 'http://127.0.0.1:8000';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE_URL}/api/health`);
  if (!res.ok) throw new Error('Backend health check failed');
  return res.json();
}

export async function sendChatQuery(query, promptVersion = 'v4', compareWith = null) {
  const res = await fetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      prompt_version: promptVersion,
      compare_with: compareWith
    })
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to process chat query');
  }
  return res.json();
}

export async function fetchPrompts() {
  const res = await fetch(`${API_BASE_URL}/api/prompts`);
  if (!res.ok) throw new Error('Failed to load system prompts');
  return res.json();
}

export async function fetchBenchmarkQueries() {
  const res = await fetch(`${API_BASE_URL}/api/benchmarks/queries`);
  if (!res.ok) throw new Error('Failed to load benchmark test cases');
  return res.json();
}

export async function fetchBenchmarkResults() {
  const res = await fetch(`${API_BASE_URL}/api/benchmarks/results`);
  if (!res.ok) throw new Error('Failed to load benchmark results');
  return res.json();
}

export async function runBenchmarkSuite(version = null) {
  const res = await fetch(`${API_BASE_URL}/api/benchmarks/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ version })
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Benchmark suite execution failed');
  }
  return res.json();
}

export function getChartUrl(chartName) {
  return `${API_BASE_URL}/api/charts/${chartName}?t=${Date.now()}`;
}

export function getCsvDownloadUrl(version) {
  return `${API_BASE_URL}/api/benchmarks/csv/${version}`;
}

export async function runRegressionTest(baselineVersion, candidateVersion, testCaseIds = null) {
  const res = await fetch(`${API_BASE_URL}/api/benchmarks/regression`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      baseline_version: baselineVersion,
      candidate_version: candidateVersion,
      test_case_ids: testCaseIds
    })
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Regression test execution failed');
  }
  return res.json();
}

export async function fetchRegressionReports() {
  const res = await fetch(`${API_BASE_URL}/api/benchmarks/regression/reports`);
  if (!res.ok) throw new Error('Failed to load regression reports');
  return res.json();
}

