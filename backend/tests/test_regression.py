"""
Tests for Prompt Regression Testing Service

All tests use mocked Gemini calls - zero live API requests are made.
Covers all 9 required scenarios:
  1. Correct comparison of two fully evaluated versions
  2. Detecting a candidate regression
  3. Detecting a candidate improvement
  4. Identical results classified as unchanged
  5. API failures classified as NOT_COMPARABLE
  6. Unevaluated cases excluded from aggregate averages
  7. Partial reports saved safely without overwriting original benchmark files
  8. A quota error does not trigger repeated requests
  9. Baseline and candidate use the same test case IDs
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.services.regression_service import (
    _classify_outcome,
    _compute_aggregate,
    run_regression_comparison,
    list_regression_reports,
    REGRESSION_REPORTS_DIR,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_eval_result(
    test_id="TC-01",
    category="Standard Policy",
    query="Test query?",
    status="EVALUATED",
    pqi=85.0,
    correctness=90.0,
    hallucination_score=80.0,
    escalation_score=75.0,
    tone_score=95.0,
    has_hallucination=False,
    correctly_escalated=True,
    prompt_version="v1",
):
    """
    Returns a minimal eval result dictionary matching the schema produced by
    run_single_evaluation.
    """
    return {
        "test_id": test_id,
        "category": category,
        "query": query,
        "ground_truth_policy": "Policy text",
        "should_escalate": False,
        "prompt_version": prompt_version,
        "model_response": "Some response",
        "evaluation_status": status,
        "is_escalated": False,
        "correctly_escalated": correctly_escalated if status == "EVALUATED" else None,
        "has_hallucination": has_hallucination if status == "EVALUATED" else None,
        "correctness_score": correctness if status == "EVALUATED" else None,
        "hallucination_score": hallucination_score if status == "EVALUATED" else None,
        "escalation_score": escalation_score if status == "EVALUATED" else None,
        "tone_score": tone_score if status == "EVALUATED" else None,
        "pqi_score": pqi if status == "EVALUATED" else None,
        "latency_ms": 300,
        "reasoning": "Test reasoning.",
    }


def _make_api_error_result(test_id="TC-01", error_type="429_RESOURCE_EXHAUSTED"):
    return {
        "test_id": test_id,
        "category": "Standard Policy",
        "query": "Test query?",
        "ground_truth_policy": "Policy text",
        "should_escalate": False,
        "prompt_version": "v1",
        "model_response": "Gemini API quota exhausted. Please try again after the quota resets.",
        "evaluation_status": "API_ERROR",
        "is_escalated": False,
        "correctly_escalated": None,
        "has_hallucination": None,
        "correctness_score": None,
        "hallucination_score": None,
        "escalation_score": None,
        "tone_score": None,
        "pqi_score": None,
        "latency_ms": 100,
        "reasoning": f"Not evaluated: Gemini API returned {error_type}. Response was not scored.",
    }


def _make_not_evaluated_result(test_id="TC-01"):
    return {
        "test_id": test_id,
        "category": "Standard Policy",
        "query": "Test query?",
        "ground_truth_policy": "Policy text",
        "should_escalate": False,
        "prompt_version": "v1",
        "model_response": "NOT_EVALUATED: Skipped (429 Quota Exhausted)",
        "evaluation_status": "NOT_EVALUATED",
        "is_escalated": False,
        "correctly_escalated": None,
        "has_hallucination": None,
        "correctness_score": None,
        "hallucination_score": None,
        "escalation_score": None,
        "tone_score": None,
        "pqi_score": None,
        "latency_ms": 0,
        "reasoning": "Skipped evaluation: 429 Quota Exhausted",
    }


# ---------------------------------------------------------------------------
# Unit tests for _classify_outcome
# ---------------------------------------------------------------------------

class TestClassifyOutcome:

    def test_improvement_classified_correctly(self):
        baseline = _make_eval_result(pqi=75.0)
        candidate = _make_eval_result(pqi=90.0)
        result = _classify_outcome(baseline, candidate)
        assert result["outcome"] == "IMPROVED"
        assert "90.0" in result["reason"]

    def test_regression_classified_correctly(self):
        baseline = _make_eval_result(pqi=90.0, has_hallucination=False)
        candidate = _make_eval_result(pqi=70.0, has_hallucination=True)
        result = _classify_outcome(baseline, candidate)
        assert result["outcome"] == "REGRESSION"
        assert "hallucination" in result["reason"].lower()

    def test_unchanged_classified_correctly(self):
        baseline = _make_eval_result(pqi=85.0)
        candidate = _make_eval_result(pqi=85.0)
        result = _classify_outcome(baseline, candidate)
        assert result["outcome"] == "UNCHANGED"
        assert "85.0" in result["reason"]

    def test_api_error_baseline_is_not_comparable(self):
        baseline = _make_api_error_result()
        candidate = _make_eval_result(pqi=85.0)
        result = _classify_outcome(baseline, candidate)
        assert result["outcome"] == "NOT_COMPARABLE"
        assert "API_ERROR" in result["reason"]

    def test_api_error_candidate_is_not_comparable(self):
        baseline = _make_eval_result(pqi=85.0)
        candidate = _make_api_error_result()
        result = _classify_outcome(baseline, candidate)
        assert result["outcome"] == "NOT_COMPARABLE"
        assert "API_ERROR" in result["reason"]

    def test_not_evaluated_is_not_comparable(self):
        baseline = _make_not_evaluated_result()
        candidate = _make_eval_result(pqi=85.0)
        result = _classify_outcome(baseline, candidate)
        assert result["outcome"] == "NOT_COMPARABLE"

    def test_both_api_errors_is_not_comparable(self):
        baseline = _make_api_error_result("TC-01")
        candidate = _make_api_error_result("TC-01")
        result = _classify_outcome(baseline, candidate)
        assert result["outcome"] == "NOT_COMPARABLE"

    def test_regression_escalation_detail(self):
        baseline = _make_eval_result(pqi=90.0, correctly_escalated=True)
        candidate = _make_eval_result(pqi=75.0, correctly_escalated=False)
        result = _classify_outcome(baseline, candidate)
        assert result["outcome"] == "REGRESSION"
        assert "escalation" in result["reason"].lower()

    def test_regression_correctness_detail(self):
        baseline = _make_eval_result(pqi=90.0, correctness=95.0)
        candidate = _make_eval_result(pqi=70.0, correctness=60.0)
        result = _classify_outcome(baseline, candidate)
        assert result["outcome"] == "REGRESSION"
        assert "correctness" in result["reason"].lower()


# ---------------------------------------------------------------------------
# Unit tests for _compute_aggregate
# ---------------------------------------------------------------------------

class TestComputeAggregate:

    def test_all_evaluated(self):
        results = [
            _make_eval_result(pqi=80.0, correctness=85.0, has_hallucination=False, correctly_escalated=True),
            _make_eval_result(pqi=90.0, correctness=95.0, has_hallucination=False, correctly_escalated=True),
        ]
        agg = _compute_aggregate(results, "V1")
        assert agg["evaluated_count"] == 2
        assert agg["api_error_count"] == 0
        assert agg["avg_pqi"] == 85.0
        assert agg["avg_correctness"] == 90.0
        assert agg["hallucination_rate_pct"] == 0.0
        assert agg["escalation_accuracy_pct"] == 100.0

    def test_api_errors_excluded_from_averages(self):
        """Unevaluated cases must not contaminate aggregate averages."""
        results = [
            _make_eval_result(pqi=80.0),
            _make_api_error_result("TC-02"),
            _make_not_evaluated_result("TC-03"),
        ]
        agg = _compute_aggregate(results, "V1")
        assert agg["evaluated_count"] == 1
        assert agg["api_error_count"] == 1
        # avg_pqi should only include TC-01's score
        assert agg["avg_pqi"] == 80.0

    def test_all_api_errors_returns_none_averages(self):
        results = [_make_api_error_result("TC-01"), _make_api_error_result("TC-02")]
        agg = _compute_aggregate(results, "V1")
        assert agg["evaluated_count"] == 0
        assert agg["avg_pqi"] is None
        assert agg["hallucination_rate_pct"] is None

    def test_mixed_hallucination_rate(self):
        results = [
            _make_eval_result(pqi=80.0, has_hallucination=True),
            _make_eval_result(pqi=90.0, has_hallucination=False),
            _make_eval_result(pqi=70.0, has_hallucination=False),
        ]
        agg = _compute_aggregate(results, "V1")
        # 1 hallucination out of 3 = 33.33%
        assert agg["hallucination_rate_pct"] == pytest.approx(33.33, abs=0.1)


# ---------------------------------------------------------------------------
# Integration tests for run_regression_comparison (all mocked)
# ---------------------------------------------------------------------------

def _build_mock_run_single(results_map: dict):
    """
    Returns a side_effect function that dispatches mock eval results
    based on (version, tc_id).
    """
    def side_effect(version, tc, skip_reason=None):
        version_key = version.lower()
        tc_id = tc["id"]

        if skip_reason:
            return _make_not_evaluated_result(tc_id)

        key = (version_key, tc_id)
        if key in results_map:
            return results_map[key]

        # Default: return a successful evaluation
        return _make_eval_result(test_id=tc_id, prompt_version=version_key, pqi=85.0)

    return side_effect


class TestRunRegressionComparison:

    @patch("app.services.regression_service.load_benchmark_queries")
    @patch("app.services.regression_service.run_single_evaluation")
    def test_full_comparison_two_evaluated_versions(
        self, mock_eval, mock_load_queries, tmp_path, monkeypatch
    ):
        """Test 1: Correct comparison of two fully evaluated versions."""
        monkeypatch.setattr(
            "app.services.regression_service.REGRESSION_REPORTS_DIR", tmp_path
        )
        mock_load_queries.return_value = [
            {"id": "TC-01", "category": "Standard Policy", "query": "Q1",
             "ground_truth_policy": "P1", "should_escalate": False},
        ]
        mock_eval.side_effect = _build_mock_run_single({
            ("v1", "TC-01"): _make_eval_result("TC-01", pqi=75.0, prompt_version="v1"),
            ("v4", "TC-01"): _make_eval_result("TC-01", pqi=90.0, prompt_version="v4"),
        })

        report = run_regression_comparison("v1", "v4")

        assert report["baseline_version"] == "V1"
        assert report["candidate_version"] == "V4"
        assert len(report["case_comparisons"]) == 1
        assert report["case_comparisons"][0]["outcome"] == "IMPROVED"
        assert report["outcome_summary"]["IMPROVED"] == 1
        assert report["outcome_summary"]["REGRESSION"] == 0

    @patch("app.services.regression_service.load_benchmark_queries")
    @patch("app.services.regression_service.run_single_evaluation")
    def test_detects_regression(self, mock_eval, mock_load_queries, tmp_path, monkeypatch):
        """Test 2: Detecting a candidate regression."""
        monkeypatch.setattr(
            "app.services.regression_service.REGRESSION_REPORTS_DIR", tmp_path
        )
        mock_load_queries.return_value = [
            {"id": "TC-01", "category": "Standard Policy", "query": "Q1",
             "ground_truth_policy": "P1", "should_escalate": False},
        ]
        mock_eval.side_effect = _build_mock_run_single({
            ("v3", "TC-01"): _make_eval_result("TC-01", pqi=90.0, prompt_version="v3"),
            ("v4", "TC-01"): _make_eval_result("TC-01", pqi=70.0, has_hallucination=True, prompt_version="v4"),
        })

        report = run_regression_comparison("v3", "v4")

        assert report["outcome_summary"]["REGRESSION"] == 1
        assert report["case_comparisons"][0]["outcome"] == "REGRESSION"
        assert "hallucination" in report["case_comparisons"][0]["reason"].lower()

    @patch("app.services.regression_service.load_benchmark_queries")
    @patch("app.services.regression_service.run_single_evaluation")
    def test_detects_improvement(self, mock_eval, mock_load_queries, tmp_path, monkeypatch):
        """Test 3: Detecting a candidate improvement."""
        monkeypatch.setattr(
            "app.services.regression_service.REGRESSION_REPORTS_DIR", tmp_path
        )
        mock_load_queries.return_value = [
            {"id": "TC-02", "category": "Standard Policy", "query": "Q2",
             "ground_truth_policy": "P2", "should_escalate": False},
        ]
        mock_eval.side_effect = _build_mock_run_single({
            ("v1", "TC-02"): _make_eval_result("TC-02", pqi=60.0, prompt_version="v1"),
            ("v4", "TC-02"): _make_eval_result("TC-02", pqi=95.0, prompt_version="v4"),
        })

        report = run_regression_comparison("v1", "v4")
        assert report["outcome_summary"]["IMPROVED"] == 1
        assert report["outcome_summary"]["REGRESSION"] == 0

    @patch("app.services.regression_service.load_benchmark_queries")
    @patch("app.services.regression_service.run_single_evaluation")
    def test_identical_scores_are_unchanged(self, mock_eval, mock_load_queries, tmp_path, monkeypatch):
        """Test 4: Identical results classified as unchanged."""
        monkeypatch.setattr(
            "app.services.regression_service.REGRESSION_REPORTS_DIR", tmp_path
        )
        mock_load_queries.return_value = [
            {"id": "TC-03", "category": "Standard Policy", "query": "Q3",
             "ground_truth_policy": "P3", "should_escalate": False},
        ]
        mock_eval.side_effect = _build_mock_run_single({
            ("v2", "TC-03"): _make_eval_result("TC-03", pqi=85.0, prompt_version="v2"),
            ("v3", "TC-03"): _make_eval_result("TC-03", pqi=85.0, prompt_version="v3"),
        })

        report = run_regression_comparison("v2", "v3")
        assert report["outcome_summary"]["UNCHANGED"] == 1
        assert report["outcome_summary"]["REGRESSION"] == 0
        assert report["outcome_summary"]["IMPROVED"] == 0

    @patch("app.services.regression_service.load_benchmark_queries")
    @patch("app.services.regression_service.run_single_evaluation")
    def test_api_failures_classified_not_comparable(
        self, mock_eval, mock_load_queries, tmp_path, monkeypatch
    ):
        """Test 5: API failures classified as NOT_COMPARABLE."""
        monkeypatch.setattr(
            "app.services.regression_service.REGRESSION_REPORTS_DIR", tmp_path
        )
        mock_load_queries.return_value = [
            {"id": "TC-04", "category": "Standard Policy", "query": "Q4",
             "ground_truth_policy": "P4", "should_escalate": False},
        ]
        mock_eval.side_effect = _build_mock_run_single({
            ("v1", "TC-04"): _make_api_error_result("TC-04"),
            ("v4", "TC-04"): _make_eval_result("TC-04", pqi=90.0, prompt_version="v4"),
        })

        report = run_regression_comparison("v1", "v4")
        assert report["outcome_summary"]["NOT_COMPARABLE"] == 1
        assert report["outcome_summary"]["REGRESSION"] == 0
        assert report["case_comparisons"][0]["outcome"] == "NOT_COMPARABLE"

    @patch("app.services.regression_service.load_benchmark_queries")
    @patch("app.services.regression_service.run_single_evaluation")
    def test_unevaluated_cases_excluded_from_aggregates(
        self, mock_eval, mock_load_queries, tmp_path, monkeypatch
    ):
        """Test 6: Unevaluated cases excluded from aggregate averages."""
        monkeypatch.setattr(
            "app.services.regression_service.REGRESSION_REPORTS_DIR", tmp_path
        )
        mock_load_queries.return_value = [
            {"id": "TC-01", "category": "Standard Policy", "query": "Q1",
             "ground_truth_policy": "P1", "should_escalate": False},
            {"id": "TC-02", "category": "Standard Policy", "query": "Q2",
             "ground_truth_policy": "P2", "should_escalate": False},
        ]
        mock_eval.side_effect = _build_mock_run_single({
            ("v1", "TC-01"): _make_eval_result("TC-01", pqi=80.0, prompt_version="v1"),
            ("v1", "TC-02"): _make_api_error_result("TC-02"),
            ("v4", "TC-01"): _make_eval_result("TC-01", pqi=80.0, prompt_version="v4"),
            ("v4", "TC-02"): _make_api_error_result("TC-02"),
        })

        report = run_regression_comparison("v1", "v4")

        # Only TC-01 was evaluated; avg_pqi must not include TC-02's None score
        b_agg = report["baseline_aggregate"]
        assert b_agg["evaluated_count"] == 1
        assert b_agg["api_error_count"] == 1
        assert b_agg["avg_pqi"] == 80.0  # only from evaluated case

    @patch("app.services.regression_service.load_benchmark_queries")
    @patch("app.services.regression_service.run_single_evaluation")
    def test_partial_report_saved_without_overwriting_csvs(
        self, mock_eval, mock_load_queries, tmp_path, monkeypatch
    ):
        """Test 7: Partial reports saved safely without overwriting original benchmark files."""
        monkeypatch.setattr(
            "app.services.regression_service.REGRESSION_REPORTS_DIR", tmp_path
        )
        mock_load_queries.return_value = [
            {"id": "TC-01", "category": "Standard Policy", "query": "Q1",
             "ground_truth_policy": "P1", "should_escalate": False},
        ]
        mock_eval.side_effect = _build_mock_run_single({
            ("v1", "TC-01"): _make_api_error_result("TC-01"),
            ("v4", "TC-01"): _make_eval_result("TC-01", pqi=85.0, prompt_version="v4"),
        })

        # Guard: none of the protected CSV filenames should be produced in tmp_path
        protected = ["benchmark_v1.csv", "benchmark_v2.csv", "benchmark_v3.csv",
                     "benchmark_v4.csv", "evaluation_summary.csv", "benchmark_queries.json"]

        report = run_regression_comparison("v1", "v4")

        produced_files = [f.name for f in tmp_path.iterdir()]
        for protected_file in protected:
            assert protected_file not in produced_files, f"Protected file '{protected_file}' was produced!"

        # One JSON report should exist
        json_files = [f for f in tmp_path.iterdir() if f.suffix == ".json"]
        assert len(json_files) == 1
        saved = json.loads(json_files[0].read_text())
        assert saved["run_id"] == report["run_id"]

    @patch("app.services.regression_service.load_benchmark_queries")
    @patch("app.services.regression_service.run_single_evaluation")
    def test_quota_error_stops_further_requests_no_retry(
        self, mock_eval, mock_load_queries, tmp_path, monkeypatch
    ):
        """Test 8: A quota error does not trigger repeated requests (circuit breaker)."""
        monkeypatch.setattr(
            "app.services.regression_service.REGRESSION_REPORTS_DIR", tmp_path
        )
        # Three test cases; quota hits on TC-02 for baseline
        cases = [
            {"id": "TC-01", "category": "Standard Policy", "query": "Q1",
             "ground_truth_policy": "P1", "should_escalate": False},
            {"id": "TC-02", "category": "Standard Policy", "query": "Q2",
             "ground_truth_policy": "P2", "should_escalate": False},
            {"id": "TC-03", "category": "Standard Policy", "query": "Q3",
             "ground_truth_policy": "P3", "should_escalate": False},
        ]
        mock_load_queries.return_value = cases

        quota_error_result = {
            "test_id": "TC-02",
            "category": "Standard Policy",
            "query": "Q2",
            "ground_truth_policy": "P2",
            "should_escalate": False,
            "prompt_version": "v1",
            "model_response": "Gemini API quota exhausted. Please try again after the quota resets.",
            "evaluation_status": "API_ERROR",
            "is_escalated": False,
            "correctly_escalated": None,
            "has_hallucination": None,
            "correctness_score": None,
            "hallucination_score": None,
            "escalation_score": None,
            "tone_score": None,
            "pqi_score": None,
            "latency_ms": 100,
            "reasoning": "Not evaluated: Gemini API returned 429_RESOURCE_EXHAUSTED (429 RESOURCE_EXHAUSTED). Response was not scored.",
        }

        call_tracker = {"count": 0}

        def tracked_eval(version, tc, skip_reason=None):
            if skip_reason:
                return _make_not_evaluated_result(tc["id"])
            call_tracker["count"] += 1
            if version == "v1" and tc["id"] == "TC-02":
                return quota_error_result
            return _make_eval_result(tc["id"], prompt_version=version, pqi=85.0)

        mock_eval.side_effect = tracked_eval

        report = run_regression_comparison("v1", "v4")

        # TC-03 baseline should be skipped (circuit breaker active after TC-02 quota error)
        tc03_comparison = next(c for c in report["case_comparisons"] if c["test_id"] == "TC-03")
        assert tc03_comparison["baseline_status"] == "NOT_EVALUATED"

        # The service must NOT call generate on TC-03 baseline again
        # (call_tracker["count"] would be higher if it did)
        # Exact: TC-01 baseline + TC-02 baseline(quota) + TC-01 candidate + TC-02 candidate + TC-03 candidate = 5
        assert call_tracker["count"] == 5

    @patch("app.services.regression_service.load_benchmark_queries")
    @patch("app.services.regression_service.run_single_evaluation")
    def test_baseline_and_candidate_share_same_test_case_ids(
        self, mock_eval, mock_load_queries, tmp_path, monkeypatch
    ):
        """Test 9: Baseline and candidate use the same test case IDs."""
        monkeypatch.setattr(
            "app.services.regression_service.REGRESSION_REPORTS_DIR", tmp_path
        )
        cases = [
            {"id": "TC-01", "category": "Standard Policy", "query": "Q1",
             "ground_truth_policy": "P1", "should_escalate": False},
            {"id": "TC-02", "category": "Standard Policy", "query": "Q2",
             "ground_truth_policy": "P2", "should_escalate": False},
        ]
        mock_load_queries.return_value = cases
        mock_eval.side_effect = _build_mock_run_single({})

        report = run_regression_comparison("v1", "v4")

        baseline_ids = [c["test_id"] for c in report["case_comparisons"]]
        assert baseline_ids == ["TC-01", "TC-02"]
        # Both sides must have same IDs (zip ensures this, but verify column data)
        for row in report["case_comparisons"]:
            assert row["test_id"] in ["TC-01", "TC-02"]


# ---------------------------------------------------------------------------
# API endpoint integration tests
# ---------------------------------------------------------------------------

@patch("app.services.regression_service.load_benchmark_queries")
@patch("app.services.regression_service.run_single_evaluation")
def test_regression_api_endpoint_valid(mock_eval, mock_load_queries, tmp_path, monkeypatch):
    """Regression API endpoint returns 200 with a valid report for known versions."""
    from fastapi.testclient import TestClient
    from app.main import app

    monkeypatch.setattr(
        "app.services.regression_service.REGRESSION_REPORTS_DIR", tmp_path
    )
    mock_load_queries.return_value = [
        {"id": "TC-01", "category": "Standard Policy", "query": "Q1",
         "ground_truth_policy": "P1", "should_escalate": False},
    ]
    mock_eval.return_value = _make_eval_result("TC-01", pqi=85.0)

    client = TestClient(app)
    response = client.post(
        "/api/benchmarks/regression",
        json={"baseline_version": "v1", "candidate_version": "v4"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "report" in data
    assert data["report"]["baseline_version"] == "V1"
    assert data["report"]["candidate_version"] == "V4"


def test_regression_api_endpoint_invalid_version():
    """Regression API endpoint returns 400 for unknown version."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.post(
        "/api/benchmarks/regression",
        json={"baseline_version": "v99", "candidate_version": "v4"}
    )
    assert response.status_code == 400


def test_regression_reports_listing_endpoint():
    """Regression reports listing endpoint returns 200."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/benchmarks/regression/reports")
    assert response.status_code == 200
    data = response.json()
    assert "reports" in data
