"""
Prompt Version 1: Naive Zero-Shot Baseline
A simple, ungrounded prompt without policy details or safety constraints.
Expected failure modes: Hallucinates policies (e.g. 30-day returns, custom discounts), fails to escalate fraud/legal threats.
"""

VERSION_INFO = {
    "version": "v1",
    "name": "Naive Zero-Shot (Baseline)",
    "description": "Minimal system prompt with no policy guidelines or guardrails.",
    "techniques": [
        "Zero-Shot Persona",
        "Ungrounded Output",
        "No Negative Constraints"
    ],
    "known_vulnerabilities": [
        "Hallucinates 30-day return window",
        "Promises unauthorized discounts and cash transfers",
        "Fails to escalate legal and fraud threats",
        "Vulnerable to prompt injection"
    ]
}

SYSTEM_PROMPT = """You are a helpful customer support agent for ShopEase, an online store.
Answer the customer's questions politely and helpfully. Do your best to make the customer happy and resolve their concerns."""
