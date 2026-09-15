"""
Support Service for Interactive Live Support Desk and Prompt Battles
"""

from typing import Dict, Any, Optional
from app.prompts import PROMPT_REGISTRY, get_prompt_by_version
from app.core.llm import generate_llm_response

def process_support_chat(
    query: str,
    prompt_version: str = "v4",
    compare_with: Optional[str] = None
) -> Dict[str, Any]:
    """
    Processes a customer query with the primary prompt version and optionally compares with a second version.
    """
    v_primary = prompt_version.lower().strip()
    primary_prompt = get_prompt_by_version(v_primary)
    
    # 1. Execute Primary
    primary_res = generate_llm_response(
        system_instruction=primary_prompt,
        user_query=query,
        temperature=0.2
    )
    
    primary_text = primary_res["text"]
    primary_is_escalated = "[ESCALATE:" in primary_text.upper() or "escalat" in primary_text.lower()
    
    # Extract escalation tag if present
    primary_tag = None
    if "[ESCALATE:" in primary_text:
        try:
            primary_tag = primary_text.split("[ESCALATE:")[1].split("]")[0].strip()
        except Exception:
            primary_tag = "FLAGGED"
            
    response_payload = {
        "primary": {
            "version": v_primary,
            "name": PROMPT_REGISTRY.get(v_primary, {}).get("info", {}).get("name", v_primary.upper()),
            "response": primary_text,
            "is_escalated": primary_is_escalated,
            "escalation_tag": primary_tag,
            "latency_ms": primary_res["latency_ms"],
            "model": primary_res["model"],
            "success": primary_res["success"]
        },
        "comparison": None
    }
    
    # 2. Execute Comparison if requested (e.g. Prompt Battle)
    if compare_with:
        v_comp = compare_with.lower().strip()
        comp_prompt = get_prompt_by_version(v_comp)
        comp_res = generate_llm_response(
            system_instruction=comp_prompt,
            user_query=query,
            temperature=0.2
        )
        comp_text = comp_res["text"]
        comp_is_escalated = "[ESCALATE:" in comp_text.upper() or "escalat" in comp_text.lower()
        comp_tag = None
        if "[ESCALATE:" in comp_text:
            try:
                comp_tag = comp_text.split("[ESCALATE:")[1].split("]")[0].strip()
            except Exception:
                comp_tag = "FLAGGED"
                
        response_payload["comparison"] = {
            "version": v_comp,
            "name": PROMPT_REGISTRY.get(v_comp, {}).get("info", {}).get("name", v_comp.upper()),
            "response": comp_text,
            "is_escalated": comp_is_escalated,
            "escalation_tag": comp_tag,
            "latency_ms": comp_res["latency_ms"],
            "model": comp_res["model"],
            "success": comp_res["success"]
        }
        
    return response_payload
