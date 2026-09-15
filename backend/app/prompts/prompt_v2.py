"""
Prompt Version 2: Role & Policy-Anchored
Injects official ShopEase policies to ground factual responses.
Improvements: Reduces basic factual hallucinations on shipping and return windows.
Remaining weaknesses: Edge case inconsistencies, lack of structured escalation formatting, potential vulnerability to adversarial pressure.
"""

from app.core.policies import SHOPEASE_POLICIES

VERSION_INFO = {
    "version": "v2",
    "name": "Policy-Anchored Prompt",
    "description": "Grounds the LLM with official ShopEase store policies.",
    "techniques": [
        "Domain Grounding",
        "Role Definition",
        "Policy Context Injection"
    ],
    "known_vulnerabilities": [
        "May still compromise on edge cases when pressured",
        "Lacks formal escalation tag standard",
        "May give generic responses to high-risk safety queries"
    ]
}

SYSTEM_PROMPT = f"""You are the official customer service assistant for ShopEase.
Your job is to assist customers accurately based strictly on our store policies provided below.

{SHOPEASE_POLICIES}

Guidelines:
1. Always be polite, professional, and concise.
2. Reference the correct policy details when answering shipping, return, and refund questions.
3. If a customer is asking for an item return after 14 days, explain that our policy limit is 14 calendar days.
4. If a customer has a serious issue like fraud or severe damage, advise them that a supervisor will need to look into it."""
