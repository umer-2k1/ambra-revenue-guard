"""Extraction agent - a small LangGraph workflow.

    START -> identify -> [per-cluster loop] -> finalize -> END

* ``identify``  groups the seed denials into clusters and emits the opening
  progress events.
* ``process_cluster`` handles one cluster per step (LLM extraction with a
  single retry, then store rule + embeddings) and loops back until every
  cluster is done - sequential, so the SSE live feed stays readable.
* ``finalize`` emits the completion event.

Progress is pushed with LangGraph's custom stream writer, so
:func:`run_analysis` is a thin ``async for`` over ``astream(stream_mode="custom")``.
"""
from __future__ import annotations

import asyncio
import json
import operator
from typing import Annotated, Any, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from database import get_all_denials, get_denials_by_cluster, get_status, insert_rule
from llm import ainvoke_json
from models import AnalysisProgress, ExtractedRule, RuleDraft
from prompts import EXTRACTION_SYSTEM_PROMPT, EXTRACTION_USER_PROMPT_TEMPLATE, render
from vector_store import add_denial_embedding, add_rule_embedding, get_collection_counts


class AnalysisState(TypedDict, total=False):
    clusters: list[dict]  # [{"cluster_name": str, "cases": [...]}]
    idx: int
    total: int
    rules: Annotated[list, operator.add]  # accumulated ExtractedRule dicts


def _emit(payload: dict[str, Any]) -> None:
    """Push a progress event to the SSE stream (no-op if not streaming)."""
    try:
        from langgraph.config import get_stream_writer

        writer = get_stream_writer()
    except Exception:
        writer = None
    if writer:
        writer(payload)


# ── LLM extraction for a single cluster ──────────────────────────────────────
async def extract_rule_from_cluster(
    cluster_name: str, cases: list[dict], rule_number: int
) -> Optional[ExtractedRule]:
    """Extract one prevention rule from a cluster, retrying once on failure."""
    user_prompt = render(
        EXTRACTION_USER_PROMPT_TEMPLATE,
        n=len(cases),
        cases_json=json.dumps(cases, indent=2, default=str),
    )

    draft: Optional[RuleDraft] = None
    for _attempt in range(2):  # retry once
        try:
            draft = await ainvoke_json(EXTRACTION_SYSTEM_PROMPT, user_prompt, RuleDraft)
            break
        except Exception as exc:  # noqa: BLE001 - we retry, then skip
            print(f"[extraction] {cluster_name}: attempt failed: {exc}")
            draft = None

    if draft is None:
        return None

    return ExtractedRule(
        rule_id=f"R-{rule_number:03d}",
        source_denials=[c["id"] for c in cases],
        source_count=len(cases),
        **draft.model_dump(),
    )


def _store_cluster(rule: dict, cases: list[dict]) -> None:
    """Blocking storage work, run off the event loop via ``asyncio.to_thread``."""
    insert_rule(rule)
    for case in cases:
        add_denial_embedding(case)
    add_rule_embedding(rule)


# ── Graph nodes ──────────────────────────────────────────────────────────────
async def identify_node(state: AnalysisState) -> dict:
    denials = get_all_denials()
    _emit(
        {
            "step": "starting",
            "cluster_name": "",
            "message": f"Loaded {len(denials)} denial cases",
            "progress": 0.0,
        }
    )

    clusters = [
        {"cluster_name": name, "cases": cases}
        for name, cases in get_denials_by_cluster().items()
    ]
    _emit(
        {
            "step": "clustering",
            "cluster_name": "",
            "message": f"Identified {len(clusters)} denial patterns",
            "progress": 0.1,
        }
    )
    return {"clusters": clusters, "idx": 0, "total": len(clusters)}


async def process_cluster_node(state: AnalysisState) -> dict:
    idx = state["idx"]
    total = state["total"]
    cluster = state["clusters"][idx]
    name = cluster["cluster_name"]
    cases = cluster["cases"]

    _emit(
        {
            "step": "extracting",
            "cluster_name": name,
            "message": f"Analyzing cluster {idx + 1}/{total}: {name} ({len(cases)} cases)",
            "progress": 0.1 + 0.7 * idx / max(total, 1),
        }
    )

    rule = await extract_rule_from_cluster(name, cases, idx + 1)
    done_progress = 0.1 + 0.7 * (idx + 1) / max(total, 1)

    if rule is None:
        _emit(
            {
                "step": "error",
                "cluster_name": name,
                "message": f"Could not extract a rule from {name} - skipping",
                "progress": done_progress,
            }
        )
        return {"idx": idx + 1}

    # Storage (SQLite + embeddings + Qdrant) is blocking I/O - keep it off the
    # event loop so status polls and other requests stay responsive.
    await asyncio.to_thread(_store_cluster, rule.model_dump(), cases)

    _emit(
        {
            "step": "stored",
            "cluster_name": name,
            "message": f"Extracted rule: {rule.rule_title}",
            "progress": done_progress,
            "rule": rule.model_dump(),
        }
    )
    return {"idx": idx + 1, "rules": [rule.model_dump()]}


async def finalize_node(state: AnalysisState) -> dict:
    status = get_status()
    counts = get_collection_counts()
    _emit(
        {
            "step": "complete",
            "cluster_name": "",
            "message": (
                f"Analysis complete. {status['total_rules']} rules learned, "
                f"{counts['denial_narratives']} denial embeddings, "
                f"{counts['rule_embeddings']} rule embeddings stored."
            ),
            "progress": 1.0,
        }
    )
    return {}


def _route(state: AnalysisState) -> str:
    return "process_cluster" if state.get("idx", 0) < state.get("total", 0) else "finalize"


def _build_graph():
    builder = StateGraph(AnalysisState)
    builder.add_node("identify", identify_node)
    builder.add_node("process_cluster", process_cluster_node)
    builder.add_node("finalize", finalize_node)

    builder.add_edge(START, "identify")
    builder.add_conditional_edges(
        "identify", _route, {"process_cluster": "process_cluster", "finalize": "finalize"}
    )
    builder.add_conditional_edges(
        "process_cluster", _route, {"process_cluster": "process_cluster", "finalize": "finalize"}
    )
    builder.add_edge("finalize", END)
    return builder.compile()


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = _build_graph()
    return _graph


async def run_analysis():
    """Async generator of :class:`AnalysisProgress` events, driven by the graph."""
    initial: AnalysisState = {"clusters": [], "idx": 0, "total": 0, "rules": []}
    async for event in get_graph().astream(initial, stream_mode="custom"):
        yield AnalysisProgress(**event)
