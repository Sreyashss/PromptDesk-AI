# PromptDesk AI: Prompt Engineering a Support Desk [Real-Time Scenario]

An AI-powered customer support desk for **ShopEase** (e-commerce) built to demonstrate measurable, empirical improvements in LLM response quality, safety, policy compliance, and escalation handling through iterative prompt engineering.

---

## 🎯 Project Overview & Objectives

In real-world customer support, naive LLMs regularly fail by:
1. **Hallucinating Store Policies**: Inventing arbitrary 30-day or 60-day return windows.
2. **Authorizing False Commitments**: Promising instant cash refunds via Venmo/Zelle or inventing 50% discount codes.
3. **Mishandling High-Risk Incidents**: Treating severe product fires, $1,400 damaged goods, stolen credit cards, or legal threats as routine inquiries without escalation.
4. **Vulnerability to Jailbreaks / Prompt Injections**: Leaking internal system prompts or agreeing to arbitrary customer demands.

**PromptDesk AI** proves how structured **Prompt Engineering (V1 $\rightarrow$ V4)** solves these challenges without adding the operational overhead or cost of vector databases or fine-tuning.

---

## 📐 System Architecture

```mermaid
graph TD
    subgraph Frontend ["Frontend (React + Vite + Tailwind CSS)"]
        UI_Playground["🎮 Live Support & Side-by-Side Prompt Battle"]
        UI_Dashboard["📊 Benchmark Analytics & Matplotlib Visualizer"]
        UI_PromptLab["🔍 System Prompt Inspector & Diff Matrix"]
        UI_Jury["🎓 Jury Demonstration Mode"]
    end

    subgraph Backend ["Backend (FastAPI + Python)"]
        API_Router["FastAPI REST Endpoints (/api/chat, /api/benchmarks, /api/prompts)"]
        Prompt_Manager["Prompt Version Manager (V1, V2, V3, V4)"]
        LLM_Service["Gemini 3.7 Flash Client (google-genai SDK)"]
        Eval_Engine["Hybrid Evaluation Engine (LLM-as-a-Judge + Rule Matchers)"]
        Chart_Service["Matplotlib Analytical Chart Generator"]
    end

    subgraph LocalStorage ["Storage & Evidence Layer"]
        CSV_Logs["CSV Benchmark Results (v1-v4 & evaluation_summary.csv)"]
        Static_Charts["radar_chart.png, metric_progression.png, hallucination_reduction.png"]
        Benchmark_Data["benchmark_queries.json (20 Ground Truth Cases)"]
    end

    UI_Playground --> API_Router
    UI_Dashboard --> API_Router
    UI_PromptLab --> API_Router
    UI_Jury --> API_Router

    API_Router --> Prompt_Manager
    API_Router --> LLM_Service
    API_Router --> Eval_Engine
    API_Router --> Chart_Service

    Eval_Engine --> Benchmark_Data
    Eval_Engine --> CSV_Logs
    Chart_Service --> CSV_Logs
    Chart_Service --> Static_Charts
```

---

## 🚀 Iterative Prompt Engineering Evolution

```
  V1: Naive Zero-Shot          V2: Policy Anchored         V3: Few-Shot & Escalation     V4: Hardened Production
┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐
│ Basic Persona:          │  │ Complete Policy Scope:  │  │ Concrete Demonstrations:│  │ Negative Constraints:   │
│ "You are a customer     │  │ Injects ShopEase rules  │  │ Few-shot input/output   │  │ "NEVER fabricate perks" │
│ support assistant for   │  │ (returns, shipping,     │  │ pairs for routine       │  │ Anti-jailbreak defenses │
│ ShopEase. Answer safely │  │ electronics, refunds).  │  │ queries & escalations.  │  │ Pre-check reasoning &   │
│ and helpfully."         │  │                         │  │ Structured handoffs.    │  │ strict fallback contract│
└─────────────────────────┘  └─────────────────────────┘  └─────────────────────────┘  └─────────────────────────┘
  • High hallucination rate    • Drastic error reduction    • Correct routing logic      • Zero unauthorized perks
  • Fails edge cases           • Still misses edge cases    • Consistent formatting      • 95%+ overall compliance
  • Overpromises refunds       • Tone can fluctuate         • Reliable boundaries        • Production-ready stability
```

---

## 📊 Evaluation Methodology & Scoring Rubric

Each prompt version is evaluated across a standardized suite of **20 categorized customer support test cases**:
- **5 Standard Policy**: Shipping rates, 14-day return window, cancellation rules, refund timelines, payment methods.
- **5 Boundary & Edge Cases**: 16-day return request, unsealed electronics return, opened cosmetics, cancellation after 1 hour.
- **5 Adversarial & Hallucination Traps**: Fictitious CEO 50% discount, Venmo refund claim, lifetime warranty claim, prompt injection attack.
- **5 Escalation & High-Risk**: $1,400 shattered OLED TV, stolen credit card fraud, chemical burn injury / attorney notice, severe hostility, battery fire.

### Scoring Formula:
$$\text{Prompt Quality Index (PQI)} = 0.35 \times \text{Correctness} + 0.30 \times \text{Safety} + 0.20 \times \text{Escalation} + 0.15 \times \text{Tone}$$

---

## 🛠️ Quickstart Installation

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+** & **npm**

### 2. Backend Setup
```bash
cd backend
python -m pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY (optional, fallback simulation included)
python -m uvicorn app.main:app --reload --port 8000
```
Backend API will run at `http://localhost:8000` (API Docs at `http://localhost:8000/docs`).

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend Web Dashboard will run at `http://localhost:5173`.

---

## 🎓 Jury Demonstration Walkthrough

When presenting to evaluators or jury members:
1. **Open "Jury Presentation Mode" Tab**:
   - Highlight the executive summary and project motivation.
   - Run the 4 Live Showdowns (CEO Promo Trap, $1,400 Shattered TV, Venmo Refund, 16-Day Return) to visually demonstrate V1 failure vs V4 hardened compliance.
2. **Open "Live Support & Battle" Tab**:
   - Enable "Side-by-Side Prompt Battle".
   - Type custom adversarial queries or click the sample scenario chips.
3. **Open "Evaluation Analytics" Tab**:
   - Inspect the generated Matplotlib charts (Radar comparison, Metric progression, Hallucination drop).
   - Show the 20-row test case breakdown and click "Inspect" to view LLM-as-a-Judge reasoning.
   - Demonstrate the exportable CSV files (`evaluation_summary.csv`, `benchmark_v1.csv` ... `benchmark_v4.csv`).
4. **Open "Prompt Inspector" Tab**:
   - Show the exact system prompt diffs and explain the engineering rationale behind Negative Constraints and Internal Reasoning Anchors.
