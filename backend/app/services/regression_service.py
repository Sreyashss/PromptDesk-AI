"""
Prompt Regression Testing Service

Compares two registered prompt versions (baseline vs candidate) across the benchmark
test suite. Reuses run_single_evaluation from eval_service so no metric logic is
duplicated. Results are persisted to a separate timestamped directory and never
overwrite existing benchmark CSVs or the original query dataset.

Regression classification rules:
  - IMPROVED     : both EVALUATED, candidate pqi_score > baseline pqi_score
  - REGRESSION   : both EVALUATED, candidate pqi_score < baseline pqi_score
  - UNCHANGED    : both EVALUATED, candidate pqi_score == baseline pqi_score
  - NOT_COMPARABLE: either side is not EVALUATED (API_ERROR, NOT_EVALUATED, etc.)
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.config import DATA_DIR
from app.prompts import PROMPT_REGISTRY
from app.services.eval_service import run_single_evaluation, load_benchmark_queries

logger = logging.getLogger("promptdesk.regression")

# Regression reports go here - completely separate from existing CSV outputs
REGRESSION_REPORTS_DIR = DATA_DIR / "regression_reports"

PQI_REGRESSION_THRESHOLD = 0.0  # Any drop in PQI counts as regression


def _ensure_reports_dir() -> Path:
    REGRESSION_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return REGRESSION_REPORTS_DIR


def _classify_outcome(
    baseline_result: Dict[str, Any],
    candidate_result: Dict[str, Any],
) -> Dict[str, str]:
    """
    Determines the per-case outcome and a short reason string.
    Returns a dict with keys: outcome, reason
    """
    b_status = baseline_result.get("evaluation_status", "NOT_EVALUATED")
    c_status = candidate_result.get("evaluation_status", "NOT_EVALUATED")

    b_evaluated = b_status == "EVALUATED"
    c_evaluated = c_status == "EVALUATED"

    if not b_evaluated or not c_evaluated:
        parts = []
        if not b_evaluated:
            parts.append(f"baseline={b_status}")
        if not c_evaluated:
            parts.append(f"candidate={c_status}")
        return {
            "outcome": "NOT_COMPARABLE",
            "reason": f"Cannot compare: {', '.join(parts)}",
        }

    b_pqi = baseline_result.get("pqi_score")
    c_pqi = candidate_result.get("pqi_score")

    # Both evaluated but scores somehow missing - treat as not comparable
    if b_pqi is None or c_pqi is None:
        return {
            "outcome": "NOT_COMPARABLE",
            "reason": "PQI score missing despite EVALUATED status",
        }

    b_pqi = float(b_pqi)
    c_pqi = float(c_pqi)
    delta = round(c_pqi - b_pqi, 2)

    if delta > PQI_REGRESSION_THRESHOLD:
        return {
            "outcome": "IMPROVED",
            "reason": f"PQI improved by {delta} pts ({b_pqi} -> {c_pqi})",
        }
    elif delta < 0:
        # Build actionable regression details
        details = []
        b_h = baseline_result.get("has_hallucination")
        c_h = candidate_result.get("has_hallucination")
        if not b_h and c_h:
            details.append("candidate introduced hallucination")

        b_esc = baseline_result.get("correctly_escalated")
        c_esc = candidate_result.get("correctly_escalated")
        if b_esc and not c_esc:
            details.append("escalation accuracy dropped")

        b_c = baseline_result.get("correctness_score", 0)
        c_c = candidate_result.get("correctness_score", 0)
        if c_c is not None and b_c is not None and float(c_c) < float(b_c):
            details.append(f"correctness dropped {round(float(b_c) - float(c_c), 1)} pts")

        detail_str = "; ".join(details) if details else "PQI declined"
        return {
            "outcome": "REGRESSION",
            "reason": f"PQI dropped {abs(delta)} pts ({b_pqi} -> {c_pqi}). {detail_str}.",
        }
    else:
        return {
            "outcome": "UNCHANGED",
            "reason": f"PQI identical ({c_pqi} pts)",
        }


def _safe_float(val) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _compute_aggregate(results: List[Dict[str, Any]], version_label: str) -> Dict[str, Any]:
    """
    Computes aggregate metrics for one version's results.
    Only includes EVALUATED cases in metric averages.
    """
    total = len(results)
    evaluated = [r for r in results if r.get("evaluation_status") == "EVALUATED"]
    api_errors = [r for r in results if r.get("evaluation_status") in ("API_ERROR", "JUDGE_API_ERROR")]
    not_evaluated = total - len(evaluated)

    if not evaluated:
        return {
            "version": version_label,
            "total_cases": total,
            "evaluated_count": 0,
            "api_error_count": len(api_errors),
            "not_comparable_count": not_evaluated,
            "avg_pqi": None,
            "avg_correctness": None,
            "hallucination_rate_pct": None,
            "escalation_accuracy_pct": None,
        }

    pqi_scores = [_safe_float(r.get("pqi_score")) for r in evaluated if _safe_float(r.get("pqi_score")) is not None]
    corr_scores = [_safe_float(r.get("correctness_score")) for r in evaluated if _safe_float(r.get("correctness_score")) is not None]
    hall_flags = [r.get("has_hallucination") for r in evaluated if r.get("has_hallucination") is not None]
    esc_flags = [r.get("correctly_escalated") for r in evaluated if r.get("correctly_escalated") is not None]

    avg_pqi = round(sum(pqi_scores) / len(pqi_scores), 2) if pqi_scores else None
    avg_corr = round(sum(corr_scores) / len(corr_scores), 2) if corr_scores else None
    hall_rate = round((sum(1 for h in hall_flags if h) / len(hall_flags)) * 100, 2) if hall_flags else None
    esc_acc = round((sum(1 for e in esc_flags if e) / len(esc_flags)) * 100, 2) if esc_flags else None

    return {
        "version": version_label,
        "total_cases": total,
        "evaluated_count": len(evaluated),
        "api_error_count": len(api_errors),
        "not_comparable_count": not_evaluated,
        "avg_pqi": avg_pqi,
        "avg_correctness": avg_corr,
        "hallucination_rate_pct": hall_rate,
        "escalation_accuracy_pct": esc_acc,
    }


def run_regression_comparison(
    baseline_version: str,
    candidate_version: str,
    test_case_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Runs both prompt versions against benchmark cases and produces a case-level
    comparison with aggregate summaries.

    Args:
        baseline_version: Registered version key (e.g. 'v1')
        candidate_version: Registered version key (e.g. 'v4')
        test_case_ids: Optional list of TC-xx IDs to restrict the run.
                       Defaults to all 20 benchmark cases.

    Returns:
        Full regression report dict (also persisted to disk).
    """
    baseline_version = baseline_version.lower().strip()
    candidate_version = candidate_version.lower().strip()

    if baseline_version not in PROMPT_REGISTRY:
        raise ValueError(f"Unknown baseline version: '{baseline_version}'")
    if candidate_version not in PROMPT_REGISTRY:
        raise ValueError(f"Unknown candidate version: '{candidate_version}'")

    all_cases = load_benchmark_queries()

    if test_case_ids:
        requested_ids = set(tid.upper() for tid in test_case_ids)
        cases = [tc for tc in all_cases if tc["id"].upper() in requested_ids]
        if not cases:
            raise ValueError(f"No matching test cases found for IDs: {test_case_ids}")
    else:
        cases = all_cases

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    started_at = datetime.now(timezone.utc).isoformat()

    logger.info(
        f"Starting regression run {run_id}: {baseline_version} vs {candidate_version} "
        f"over {len(cases)} test cases."
    )

    baseline_results: List[Dict[str, Any]] = []
    candidate_results: List[Dict[str, Any]] = []

    baseline_quota_reason: Optional[str] = None
    candidate_quota_reason: Optional[str] = None

    for tc in cases:
        # --- Baseline ---
        if baseline_quota_reason:
            b_res = run_single_evaluation(baseline_version, tc, skip_reason=baseline_quota_reason)
        else:
            b_res = run_single_evaluation(baseline_version, tc)
            if b_res.get("evaluation_status") == "API_ERROR":
                r = b_res.get("reasoning", "")
                if "429" in r or "RESOURCE_EXHAUSTED" in r or "quota" in r.lower():
                    baseline_quota_reason = "429 Quota Exhausted"
                    logger.warning(
                        f"Baseline quota exhausted at {tc['id']}. Skipping remaining baseline calls."
                    )

        baseline_results.append(b_res)

        # --- Candidate ---
        if candidate_quota_reason:
            c_res = run_single_evaluation(candidate_version, tc, skip_reason=candidate_quota_reason)
        else:
            c_res = run_single_evaluation(candidate_version, tc)
            if c_res.get("evaluation_status") == "API_ERROR":
                r = c_res.get("reasoning", "")
                if "429" in r or "RESOURCE_EXHAUSTED" in r or "quota" in r.lower():
                    candidate_quota_reason = "429 Quota Exhausted"
                    logger.warning(
                        f"Candidate quota exhausted at {tc['id']}. Skipping remaining candidate calls."
                    )

        candidate_results.append(c_res)

    # Build case-level comparison rows
    case_comparisons: List[Dict[str, Any]] = []
    for b_res, c_res in zip(baseline_results, candidate_results):
        classification = _classify_outcome(b_res, c_res)
        case_comparisons.append({
            "test_id": b_res["test_id"],
            "category": b_res["category"],
            "query": b_res["query"],
            # Baseline
            "baseline_status": b_res.get("evaluation_status"),
            "baseline_pqi": _safe_float(b_res.get("pqi_score")),
            "baseline_correctness": _safe_float(b_res.get("correctness_score")),
            "baseline_hallucination": b_res.get("has_hallucination"),
            "baseline_escalated": b_res.get("correctly_escalated"),
            # Candidate
            "candidate_status": c_res.get("evaluation_status"),
            "candidate_pqi": _safe_float(c_res.get("pqi_score")),
            "candidate_correctness": _safe_float(c_res.get("correctness_score")),
            "candidate_hallucination": c_res.get("has_hallucination"),
            "candidate_escalated": c_res.get("correctly_escalated"),
            # Classification
            "outcome": classification["outcome"],
            "reason": classification["reason"],
        })

    # Aggregate summaries (only over evaluated cases)
    baseline_agg = _compute_aggregate(baseline_results, baseline_version.upper())
    candidate_agg = _compute_aggregate(candidate_results, candidate_version.upper())

    # Count outcomes across all cases
    outcome_counts: Dict[str, int] = {
        "IMPROVED": 0,
        "REGRESSION": 0,
        "UNCHANGED": 0,
        "NOT_COMPARABLE": 0,
    }
    for row in case_comparisons:
        outcome_counts[row["outcome"]] = outcome_counts.get(row["outcome"], 0) + 1

    report = {
        "run_id": run_id,
        "started_at": started_at,
        "baseline_version": baseline_version.upper(),
        "candidate_version": candidate_version.upper(),
        "total_cases_selected": len(cases),
        "outcome_summary": outcome_counts,
        "baseline_aggregate": baseline_agg,
        "candidate_aggregate": candidate_agg,
        "case_comparisons": case_comparisons,
    }

    # Persist report - never touches existing CSVs or benchmark_queries.json
    _save_regression_report(run_id, baseline_version, candidate_version, report)

    logger.info(
        f"Regression run {run_id} complete. "
        f"IMPROVED={outcome_counts['IMPROVED']}, "
        f"REGRESSION={outcome_counts['REGRESSION']}, "
        f"UNCHANGED={outcome_counts['UNCHANGED']}, "
        f"NOT_COMPARABLE={outcome_counts['NOT_COMPARABLE']}"
    )

    return report


def _save_regression_report(
    run_id: str,
    baseline: str,
    candidate: str,
    report: Dict[str, Any],
) -> Path:
    """
    Saves regression report to:
      data/regression_reports/<run_id>_<baseline>_vs_<candidate>.json
    Never overwrites existing files; uses a unique run_id timestamp.
    """
    reports_dir = _ensure_reports_dir()
    filename = f"{run_id}_{baseline}_vs_{candidate}.json"
    report_path = reports_dir / filename

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"Regression report saved to {report_path}")
    return report_path


def list_regression_reports() -> List[Dict[str, Any]]:
    """
    Returns metadata for all persisted regression reports, newest first.
    """
    reports_dir = _ensure_reports_dir()
    report_files = sorted(reports_dir.glob("*.json"), reverse=True)

    listing = []
    for rf in report_files:
        try:
            with open(rf, "r", encoding="utf-8") as f:
                data = json.load(f)
            listing.append({
                "run_id": data.get("run_id"),
                "started_at": data.get("started_at"),
                "baseline_version": data.get("baseline_version"),
                "candidate_version": data.get("candidate_version"),
                "total_cases_selected": data.get("total_cases_selected"),
                "outcome_summary": data.get("outcome_summary"),
                "filename": rf.name,
            })
        except Exception as e:
            logger.warning(f"Could not read regression report {rf.name}: {e}")

    return listing
