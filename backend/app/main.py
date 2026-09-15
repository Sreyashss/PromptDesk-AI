"""
PromptDesk AI - FastAPI Main Application
Real-Time Prompt Engineering Support Desk & Evaluation Benchmark Engine
"""

import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.config import PORT, HOST, ENVIRONMENT, GEMINI_MODEL, DATA_DIR, STATIC_DIR, CHARTS_DIR
from app.prompts import PROMPT_REGISTRY
from app.services.support_service import process_support_chat
from app.services.eval_service import (
    load_benchmark_queries,
    run_full_benchmark_suite,
    run_benchmark_for_version,
    get_latest_benchmark_results
)
from app.services.chart_service import generate_all_charts

# Request / Response Models
class ChatRequest(BaseModel):
    query: str = Field(..., description="Customer support query")
    prompt_version: str = Field("v4", description="Prompt version (v1, v2, v3, v4)")
    compare_with: Optional[str] = Field(None, description="Optional second version to compare with")

class BenchmarkRunRequest(BaseModel):
    version: Optional[str] = Field(None, description="Specific version to run, or None for all")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure baseline benchmark evaluation and charts are initialized on server boot."""
    summary_file = DATA_DIR / "evaluation_summary.csv"
    if not summary_file.exists():
        try:
            run_full_benchmark_suite()
        except Exception as e:
            print(f"Initial benchmark run deferred: {e}")
    yield

app = FastAPI(
    title="PromptDesk AI API",
    description="Real-Time Scenario: Prompt Engineering a Support Desk for ShopEase",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local React/Vite development and all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory for charts
if not CHARTS_DIR.exists():
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/api/health")
def get_health():
    """Returns system status, active model, and configuration."""
    from app.config import GEMINI_API_KEY
    return {
        "status": "healthy",
        "app": "PromptDesk AI",
        "model": GEMINI_MODEL,
        "has_api_key": bool(GEMINI_API_KEY),
        "environment": ENVIRONMENT
    }

@app.get("/api/prompts")
def get_prompts():
    """Returns metadata and full prompt texts for V1, V2, V3, and V4."""
    prompts_data = []
    for k, v in PROMPT_REGISTRY.items():
        prompts_data.append({
            "key": k,
            "info": v["info"],
            "prompt_text": v["prompt"]
        })
    return {"prompts": prompts_data}

@app.post("/api/chat")
def handle_chat(payload: ChatRequest):
    """Processes customer query with selected prompt version and optional comparison."""
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    result = process_support_chat(
        query=payload.query.strip(),
        prompt_version=payload.prompt_version,
        compare_with=payload.compare_with
    )
    return result

@app.get("/api/benchmarks/queries")
def get_benchmark_queries():
    """Returns the 20 curated customer support test queries with ground-truth labels."""
    queries = load_benchmark_queries()
    return {
        "total_queries": len(queries),
        "queries": queries
    }

@app.get("/api/benchmarks/results")
def get_benchmark_results():
    """Returns the latest benchmark summary and per-query results."""
    return get_latest_benchmark_results()

@app.post("/api/benchmarks/run")
def run_benchmark_suite(payload: BenchmarkRunRequest = None):
    """Runs the 20-query evaluation benchmark suite across V1-V4 or a specific version."""
    if payload and payload.version:
        v = payload.version.lower().strip()
        if v not in PROMPT_REGISTRY:
            raise HTTPException(status_code=400, detail=f"Invalid version: {payload.version}")
        results = run_benchmark_for_version(v)
        return {"status": "success", "version": v, "results": results}
    else:
        results = run_full_benchmark_suite()
        return {"status": "success", "suite_results": results}

@app.get("/api/benchmarks/csv/{version}")
def download_csv(version: str):
    """Downloads raw CSV evaluation logs for a given prompt version or the summary."""
    v = version.lower().strip()
    if v == "summary":
        csv_path = DATA_DIR / "evaluation_summary.csv"
    elif v in ["v1", "v2", "v3", "v4"]:
        csv_path = DATA_DIR / f"benchmark_{v}.csv"
    else:
        raise HTTPException(status_code=404, detail="CSV file not found")
        
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail=f"Benchmark CSV for {version} not yet generated")
        
    return FileResponse(
        path=str(csv_path),
        filename=csv_path.name,
        media_type="text/csv"
    )

@app.get("/api/charts/{chart_name}")
def get_chart_image(chart_name: str):
    """Serves generated Matplotlib visualization PNG charts."""
    clean_name = os.path.basename(chart_name)
    chart_path = CHARTS_DIR / clean_name
    if not chart_path.exists():
        generate_all_charts()
        
    if not chart_path.exists():
        raise HTTPException(status_code=404, detail=f"Chart {chart_name} not found")
        
    return FileResponse(
        path=str(chart_path),
        media_type="image/png"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)
