"""
Support Service for Interactive Live Support Desk and Prompt Battles
"""

from typing import Dict, Any, Optional
from app.prompts import PROMPT_REGISTRY, get_prompt_by_version
from app.core.llm import generate_llm_response, is_api_error_text
from app.services.validator_service import guard_and_correct_response

def process_support_chat(
    query: str,
    prompt_version: str = "v4",
    compare_with: Optional[str] = None
) -> Dict[str, Any]:
    """
    Processes a customer query with the primary prompt version and optionally compares with a second version.
    Validates output with deterministic rule-based checks and applies single-turn correction or safe fallback if flagged.
    Guarantees that API error failures bypass validator, correction flow, and escalation tags.
    """
    v_primary = prompt_version.lower().strip()
    primary_prompt = get_prompt_by_version(v_primary)
    
    # 1. Execute Primary LLM generation
    primary_res = generate_llm_response(
        system_instruction=primary_prompt,
        user_query=query,
        temperature=0.2
    )
    raw_primary_text = primary_res["text"]
    
    # 2. Validate response with AI Response Validator ONLY if API call succeeded
    if not primary_res.get("success", False) or is_api_error_text(raw_primary_text):
        final_primary_text = raw_primary_text
        primary_val = {
            "final_response": final_primary_text,
            "status": "NOT_EVALUATED",
            "was_corrected": False,
            "fallback_used": False,
            "original_response": raw_primary_text,
            "checks_performed": [],
            "failed_rules": [],
            "reasons": ["Generation failed due to API error. Skipped validation."],
            "summary": "Validation skipped due to API error in generation.",
            "policy_trace": []
        }
        primary_is_escalated = False
        primary_tag = None
    else:
        primary_val = guard_and_correct_response(query, raw_primary_text)
        final_primary_text = primary_val["final_response"]
        primary_is_escalated = "[ESCALATE:" in final_primary_text.upper() or "escalat" in final_primary_text.lower()
        primary_tag = None
        if "[ESCALATE:" in final_primary_text:
            try:
                primary_tag = final_primary_text.split("[ESCALATE:")[1].split("]")[0].strip()
            except Exception:
                primary_tag = "FLAGGED"
            
    response_payload = {
        "primary": {
            "version": v_primary,
            "name": PROMPT_REGISTRY.get(v_primary, {}).get("info", {}).get("name", v_primary.upper()),
            "response": final_primary_text,
            "raw_response": raw_primary_text,
            "is_escalated": primary_is_escalated,
            "escalation_tag": primary_tag,
            "latency_ms": primary_res["latency_ms"],
            "model": primary_res["model"],
            "success": primary_res["success"],
            "error_type": primary_res.get("error_type"),
            "finish_reason": primary_res.get("finish_reason", "STOP"),
            "truncated": primary_res.get("truncated", False),
            "error": primary_res.get("error"),
            "validation": primary_val
        },
        "comparison": None
    }
    
    # 3. Execute Comparison if requested (e.g. Prompt Battle)
    if compare_with:
        v_comp = compare_with.lower().strip()
        comp_prompt = get_prompt_by_version(v_comp)
        comp_res = generate_llm_response(
            system_instruction=comp_prompt,
            user_query=query,
            temperature=0.2
        )
        raw_comp_text = comp_res["text"]
        
        if not comp_res.get("success", False) or is_api_error_text(raw_comp_text):
            final_comp_text = raw_comp_text
            comp_val = {
                "final_response": final_comp_text,
                "status": "NOT_EVALUATED",
                "was_corrected": False,
                "fallback_used": False,
                "original_response": raw_comp_text,
                "checks_performed": [],
                "failed_rules": [],
                "reasons": ["Generation failed due to API error. Skipped validation."],
                "summary": "Validation skipped due to API error in generation.",
                "policy_trace": []
            }
            comp_is_escalated = False
            comp_tag = None
        else:
            comp_val = guard_and_correct_response(query, raw_comp_text)
            final_comp_text = comp_val["final_response"]
            comp_is_escalated = "[ESCALATE:" in final_comp_text.upper() or "escalat" in final_comp_text.lower()
            comp_tag = None
            if "[ESCALATE:" in final_comp_text:
                try:
                    comp_tag = final_comp_text.split("[ESCALATE:")[1].split("]")[0].strip()
                except Exception:
                    comp_tag = "FLAGGED"
                
        response_payload["comparison"] = {
            "version": v_comp,
            "name": PROMPT_REGISTRY.get(v_comp, {}).get("info", {}).get("name", v_comp.upper()),
            "response": final_comp_text,
            "raw_response": raw_comp_text,
            "is_escalated": comp_is_escalated,
            "escalation_tag": comp_tag,
            "latency_ms": comp_res["latency_ms"],
            "model": comp_res["model"],
            "success": comp_res["success"],
            "error_type": comp_res.get("error_type"),
            "finish_reason": comp_res.get("finish_reason", "STOP"),
            "truncated": comp_res.get("truncated", False),
            "error": comp_res.get("error"),
            "validation": comp_val
        }
        
    return response_payload
