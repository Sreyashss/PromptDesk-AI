"""
Evaluation Service & Benchmark Pipeline
Executes the 20 test cases against V1, V2, V3, V4 prompts, computes scores,
saves CSV logs, and computes aggregated comparative analytics.
Handles API errors (429, 503, timeouts) gracefully by marking them API_ERROR / NOT_EVALUATED
and excluding them from metric averages.
"""

import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from app.config import DATA_DIR
from app.prompts import PROMPT_REGISTRY, get_prompt_by_version
from app.prompts.judge_prompt import JUDGE_SYSTEM_PROMPT
from app.core.llm import generate_llm_response, evaluate_with_judge_llm

logger = logging.getLogger("promptdesk.eval")

BENCHMARK_FILE = DATA_DIR / "benchmark_queries.json"

def load_benchmark_queries() -> List[Dict[str, Any]]:
    if not BENCHMARK_FILE.exists():
        logger.error(f"Benchmark file not found at {BENCHMARK_FILE}")
        return []
    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def run_single_evaluation(
    version: str, 
    test_case: Dict[str, Any], 
    skip_reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes a single test case with the specified prompt version and scores the response.
    Never passes API error messages (429, 503, timeout) to the LLM judge or scores them as valid responses.
    """
    user_query = test_case["query"]
    
    # 1. Check if prior error triggered a circuit breaker skip
    if skip_reason:
        return {
            "test_id": test_case["id"],
            "category": test_case["category"],
            "query": user_query,
            "ground_truth_policy": test_case["ground_truth_policy"],
            "should_escalate": test_case["should_escalate"],
            "prompt_version": version,
            "model_response": f"NOT_EVALUATED: Skipped ({skip_reason})",
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
            "reasoning": f"Skipped evaluation: {skip_reason}"
        }

    system_prompt = get_prompt_by_version(version)
    
    # 2. Generate model response
    gen_result = generate_llm_response(
        system_instruction=system_prompt,
        user_query=user_query,
        temperature=0.2
    )
    
    # Check if API generation failed (429 rate limit, 503 high demand, timeout, etc.)
    if not gen_result.get("success", False):
        err_msg = gen_result.get("error", "API invocation failed")
        err_type = gen_result.get("error_type", "API_ERROR")
        logger.warning(f"Skipping LLM Judge for {test_case['id']} due to API error: {err_type}")
        
        return {
            "test_id": test_case["id"],
            "category": test_case["category"],
            "query": user_query,
            "ground_truth_policy": test_case["ground_truth_policy"],
            "should_escalate": test_case["should_escalate"],
            "prompt_version": version,
            "model_response": gen_result.get("text", f"API_ERROR: {err_msg}"),
            "evaluation_status": "API_ERROR",
            "is_escalated": False,
            "correctly_escalated": None,
            "has_hallucination": None,
            "correctness_score": None,
            "hallucination_score": None,
            "escalation_score": None,
            "tone_score": None,
            "pqi_score": None,
            "latency_ms": gen_result.get("latency_ms", 0),
            "reasoning": f"Not evaluated: Gemini API returned {err_type} ({err_msg}). Response was not scored."
        }
        
    model_response = gen_result["text"]
    latency_ms = gen_result["latency_ms"]
    
    # 3. Evaluate valid response using Judge LLM / Rubric
    judge_result = evaluate_with_judge_llm(
        judge_prompt=JUDGE_SYSTEM_PROMPT,
        user_query=user_query,
        model_response=model_response
    )
    
    if not judge_result.get("success", True):
        # Judge API call failed
        err_msg = judge_result.get("error", "Judge evaluation error")
        return {
            "test_id": test_case["id"],
            "category": test_case["category"],
            "query": user_query,
            "ground_truth_policy": test_case["ground_truth_policy"],
            "should_escalate": test_case["should_escalate"],
            "prompt_version": version,
            "model_response": model_response,
            "evaluation_status": "JUDGE_API_ERROR",
            "is_escalated": False,
            "correctly_escalated": None,
            "has_hallucination": None,
            "correctness_score": None,
            "hallucination_score": None,
            "escalation_score": None,
            "tone_score": None,
            "pqi_score": None,
            "latency_ms": latency_ms,
            "reasoning": f"Not evaluated: Judge LLM API failed ({err_msg})."
        }
    
    c_score = float(judge_result.get("correctness_score", 50))
    h_score = float(judge_result.get("hallucination_score", 50))
    e_score = float(judge_result.get("escalation_score", 50))
    t_score = float(judge_result.get("tone_score", 80))
    
    # Calculate composite Prompt Quality Index (PQI)
    pqi = round((0.35 * c_score) + (0.30 * h_score) + (0.20 * e_score) + (0.15 * t_score), 2)
    
    has_hallucination = bool(judge_result.get("has_hallucination", h_score < 70))
    correctly_escalated = bool(judge_result.get("correctly_escalated", e_score >= 70))
    is_escalated = "[ESCALATE:" in model_response.upper() or "escalat" in model_response.lower()
    
    return {
        "test_id": test_case["id"],
        "category": test_case["category"],
        "query": user_query,
        "ground_truth_policy": test_case["ground_truth_policy"],
        "should_escalate": test_case["should_escalate"],
        "prompt_version": version,
        "model_response": model_response,
        "evaluation_status": "EVALUATED",
        "is_escalated": is_escalated,
        "correctly_escalated": correctly_escalated,
        "has_hallucination": has_hallucination,
        "correctness_score": c_score,
        "hallucination_score": h_score,
        "escalation_score": e_score,
        "tone_score": t_score,
        "pqi_score": pqi,
        "latency_ms": latency_ms,
        "reasoning": judge_result.get("evaluation_reasoning", "Standard evaluation completed.")
    }

def run_benchmark_for_version(version: str, delay_between_calls: float = 0.5) -> List[Dict[str, Any]]:
    """
    Runs test cases for a single prompt version.
    Includes rate pacing and circuit breaker to prevent making more calls than quota allows.
    """
    queries = load_benchmark_queries()
    results = []
    quota_exhausted_reason = None
    
    for i, tc in enumerate(queries):
        if quota_exhausted_reason:
            res = run_single_evaluation(version, tc, skip_reason=quota_exhausted_reason)
        else:
            res = run_single_evaluation(version, tc)
            
            # Check if this query hit 429 quota exhaustion or 503 service unavailable
            eval_status = res.get("evaluation_status")
            reasoning = res.get("reasoning", "")
            if eval_status == "API_ERROR" and ("429" in reasoning or "RESOURCE_EXHAUSTED" in reasoning or "quota" in reasoning.lower()):
                logger.warning(f"Rate limit / quota exhausted at test case {tc['id']}. Activating circuit breaker for remaining queries in {version}.")
                quota_exhausted_reason = "429 Quota Exhausted"
            
            # Pacing delay between queries to avoid exceeding RPM burst limits
            if i < len(queries) - 1 and not quota_exhausted_reason and delay_between_calls > 0:
                time.sleep(delay_between_calls)
                
        results.append(res)
        
    df = pd.DataFrame(results)
    csv_path = DATA_DIR / f"benchmark_{version.lower()}.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8")
    logger.info(f"Saved benchmark results for {version} to {csv_path}")
    
    return results

def run_full_benchmark_suite() -> Dict[str, Any]:
    """
    Runs all 20 test cases across V1, V2, V3, and V4, writes all CSVs,
    creates the consolidated summary CSV, and regenerates charts.
    Safely excludes API_ERROR and NOT_EVALUATED cases from metric averages.
    """
    versions = ["v1", "v2", "v3", "v4"]
    all_version_results = {}
    summary_rows = []
    
    for v in versions:
        res = run_benchmark_for_version(v)
        all_version_results[v] = res
        
        df_v = pd.DataFrame(res)
        
        # Filter only successfully evaluated test cases (where pqi_score is not None/NaN)
        valid_df = df_v[df_v["pqi_score"].notna()]
        
        total_tc = len(df_v)
        evaluated_tc = len(valid_df)
        error_tc = total_tc - evaluated_tc
        
        if evaluated_tc > 0:
            avg_correctness = round(float(valid_df["correctness_score"].mean()), 2)
            avg_hallucination = round(float(valid_df["hallucination_score"].mean()), 2)
            avg_escalation = round(float(valid_df["escalation_score"].mean()), 2)
            avg_tone = round(float(valid_df["tone_score"].mean()), 2)
            avg_pqi = round(float(valid_df["pqi_score"].mean()), 2)
            
            valid_hall = valid_df["has_hallucination"].dropna()
            hallucination_rate = round(float((valid_hall.sum() / len(valid_hall)) * 100), 2) if len(valid_hall) > 0 else 0.0
            
            valid_esc = valid_df["correctly_escalated"].dropna()
            escalation_accuracy = round(float((valid_esc.sum() / len(valid_esc)) * 100), 2) if len(valid_esc) > 0 else 0.0
            
            avg_latency = round(float(valid_df["latency_ms"].mean()), 2)
        else:
            avg_correctness = None
            avg_hallucination = None
            avg_escalation = None
            avg_tone = None
            avg_pqi = None
            hallucination_rate = None
            escalation_accuracy = None
            avg_latency = 0.0
            
        summary_rows.append({
            "version": v.upper(),
            "name": PROMPT_REGISTRY[v]["info"]["name"],
            "avg_correctness": avg_correctness,
            "avg_hallucination_score": avg_hallucination,
            "avg_escalation_score": avg_escalation,
            "avg_tone": avg_tone,
            "composite_pqi": avg_pqi,
            "hallucination_rate_pct": hallucination_rate,
            "escalation_accuracy_pct": escalation_accuracy,
            "avg_latency_ms": avg_latency,
            "total_test_cases": total_tc,
            "evaluated_test_cases": evaluated_tc,
            "api_error_count": error_tc
        })
        
    summary_df = pd.DataFrame(summary_rows)
    summary_csv = DATA_DIR / "evaluation_summary.csv"
    summary_df.to_csv(summary_csv, index=False, encoding="utf-8")
    
    # Regenerate charts
    try:
        from app.services.chart_service import generate_all_charts
        generate_all_charts()
    except Exception as e:
        logger.error(f"Failed to generate evaluation charts: {e}")
        
    return {
        "summary": summary_rows,
        "detail": all_version_results
    }

def get_latest_benchmark_results() -> Dict[str, Any]:
    """
    Reads existing CSV evaluation results from disk or triggers a run if not yet present.
    Replaces NaN with None for clean JSON serialization.
    """
    summary_csv = DATA_DIR / "evaluation_summary.csv"
    if not summary_csv.exists():
        return run_full_benchmark_suite()
        
    summary_df = pd.read_csv(summary_csv)
    summary_df = summary_df.replace({np.nan: None})
    summary_rows = summary_df.to_dict(orient="records")
    
    all_version_results = {}
    for v in ["v1", "v2", "v3", "v4"]:
        v_csv = DATA_DIR / f"benchmark_{v}.csv"
        if v_csv.exists():
            v_df = pd.read_csv(v_csv)
            v_df = v_df.replace({np.nan: None})
            all_version_results[v] = v_df.to_dict(orient="records")
        else:
            all_version_results[v] = []
            
    return {
        "summary": summary_rows,
        "detail": all_version_results
    }
