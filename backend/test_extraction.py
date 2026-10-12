"""Offline smoke test for the extraction graph - NO API keys required.

Stubs the LLM call and the embedding call, then runs the real LangGraph
workflow end to end and asserts that 5 rules get extracted, stored, and that
the SSE progress stream looks right. Run: ``python3 backend/test_extraction.py``
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import extraction_agent
import vector_store
from database import get_all_rules, reset_analysis
from models import RuleDraft
from vector_store import close_client, get_collection_counts, init_vector_store, reset_vectors

FAKE_DRAFT = RuleDraft(
    rule_title="Test prevention rule",
    payer_pattern="*",
    cpt_pattern="A0427",
    carc_pattern="CO-16",
    service_pattern="ALS-1 Emergency",
    risk_description="Stub rule used to exercise the graph without an LLM.",
    required_elements=["documented transport necessity", "documented vital signs"],
    recommended_phrases=["Patient required ALS-level transport because ..."],
    confidence=0.9,
    severity="high",
    avg_denied_amount=1850.0,
)


async def _fake_ainvoke_json(system, user, schema):
    return FAKE_DRAFT


# Stub the LLM and the embedder; everything else (graph, storage, Qdrant) is real.
extraction_agent.ainvoke_json = _fake_ainvoke_json
vector_store.embed_text = lambda text, task_type=None: [0.01] * 768

init_vector_store()
reset_analysis()
reset_vectors()


async def _run():
    return [event async for event in extraction_agent.run_analysis()]


events = asyncio.run(_run())

# Test 1: five rules extracted and stored
rules = get_all_rules()
assert len(rules) == 5, f"Expected 5 rules, got {len(rules)}"
print(f"✓ {len(rules)} rules extracted via the LangGraph workflow")

# Test 2: rule ids and cluster order are deterministic
assert [r["rule_id"] for r in rules] == ["R-001", "R-002", "R-003", "R-004", "R-005"]
assert rules[0]["source_count"] == 6, "R-001 should be the 6-case UHC cluster"
print("✓ rule ids deterministic (R-001..R-005, UHC cluster first)")

# Test 3: progress stream shape
steps = [e.step for e in events]
assert steps[0] == "starting" and steps[1] == "clustering"
assert steps[-1] == "complete"
assert steps.count("stored") == 5
assert events[-1].progress == 1.0
assert events[-1].rule is None
print(f"✓ progress stream: {steps[0]} -> {steps[1]} -> 5x stored -> {steps[-1]}")

# Test 4: a stored event carries the full rule payload for the UI
stored = [e for e in events if e.step == "stored"]
assert stored[0].rule is not None and stored[0].rule.rule_id == "R-001"
print(f"✓ stored event carries rule payload: {stored[0].rule.rule_title}")

# Test 5: embeddings written (rule + denial points)
counts = get_collection_counts()
assert counts["rule_embeddings"] == 5
assert counts["denial_narratives"] == 24, counts
print(f"✓ vector store: {counts}")

# Clean up runtime state
reset_analysis()
reset_vectors()
close_client()

print("\n=== Extraction workflow tests passed (offline, stubbed LLM) ===")
