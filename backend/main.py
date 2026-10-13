"""FastAPI application - the Ambra denial-prevention demo backend.

Run from the ``backend/`` directory:

    uvicorn main:app --reload --port 8000
"""
from __future__ import annotations

import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from database import (
    get_all_denials,
    get_all_rules,
    get_rule,
    get_status,
    reset_analysis,
)
from extraction_agent import run_analysis
from demo_claim import DEMO_CLAIM
from models import ScoreRequest
from scoring_agent import score_claim
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from vector_store import cached_counts, init_vector_store, refresh_counts, reset_vectors, store_mode

app = FastAPI(title="Ambra - Denial-to-Prevention Feedback Loop")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_vector_store()
    refresh_counts()
    print(f"[startup] vector store: {store_mode()} | LLM: {config.LLM_PROVIDER} | embeddings: {config.EMBEDDING_PROVIDER}")


@app.get("/health")
def health() -> dict:
    """Liveness probe for hosting platforms (Render/Vercel health checks)."""
    return {"status": "ok"}


# ── Denials ──────────────────────────────────────────────────────────────────
@app.get("/api/denials")
def list_denials() -> list[dict]:
    return get_all_denials()


@app.get("/api/denials/stats")
def denial_stats() -> dict:
    denials = get_all_denials()
    by_payer: Counter = Counter()
    by_carc: Counter = Counter()
    by_outcome: Counter = Counter()
    total_denied = 0.0
    days: list[int] = []

    for case in denials:
        by_payer[case["payer"]] += 1
        by_carc[case["carc_code"]] += 1
        by_outcome[case["appeal_outcome"]] += 1
        total_denied += case["denied_amount"] or 0
        if case["days_to_appeal"] is not None:
            days.append(case["days_to_appeal"])

    return {
        "total_cases": len(denials),
        "total_denied_amount": round(total_denied, 2),
        "by_payer": dict(by_payer),
        "by_carc": dict(by_carc),
        "by_outcome": dict(by_outcome),
        "avg_days_to_appeal": round(sum(days) / len(days), 1) if days else 0,
    }


# ── Analysis (SSE) ───────────────────────────────────────────────────────────
@app.post("/api/analyze")
async def analyze_denials():
    if get_status()["total_rules"] > 0:
        return JSONResponse(
            status_code=400,
            content={"error": "Analysis already complete. Call /api/reset first."},
        )

    async def event_generator():
        async for progress in run_analysis():
            yield {"event": "progress", "data": progress.model_dump_json()}
        refresh_counts()

    return EventSourceResponse(event_generator())


# ── Rules ────────────────────────────────────────────────────────────────────
@app.get("/api/rules")
def list_rules() -> list[dict]:
    return get_all_rules()


@app.get("/api/rules/{rule_id}")
def read_rule(rule_id: str):
    rule = get_rule(rule_id)
    if rule is None:
        return JSONResponse(status_code=404, content={"error": f"Rule {rule_id} not found"})
    return rule


# ── Scoring ──────────────────────────────────────────────────────────────────
@app.get("/api/demo-claim")
def get_demo_claim() -> dict:
    return DEMO_CLAIM


@app.post("/api/score")
async def score_claim_endpoint(request: ScoreRequest):
    try:
        return await score_claim(
            narrative=request.narrative,
            service_type=request.service_type,
            cpt_code=request.cpt_code,
            payer=request.payer,
        )
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})


# ── Status / reset ───────────────────────────────────────────────────────────
@app.get("/api/status")
def system_status() -> dict:
    db = get_status()
    counts = cached_counts()  # cached: no store round-trip on this hot path
    return {
        "total_denials": db["total_denials"],
        "total_rules": db["total_rules"],
        "total_scores": db["total_scores"],
        "denial_embeddings": counts["denial_narratives"],
        "rule_embeddings": counts["rule_embeddings"],
        "analysis_complete": db["total_rules"] > 0,
        "llm_provider": config.LLM_PROVIDER,
        "embedding_provider": config.EMBEDDING_PROVIDER,
        "vector_store": store_mode(),
        "vector_store_error": None,
    }


@app.post("/api/reset")
def reset() -> dict:
    reset_analysis()
    reset_vectors()
    refresh_counts()
    return {"status": "reset", "message": "All rules, scores, and embeddings cleared."}
