"""Offline smoke test for the scoring agent - NO API keys required.

Verifies retrieval (including the deterministic payer/CPT layer), the
normalization guard, flag enrichment, and the "no rules yet" error - all with
a stubbed LLM and embedder. Run: ``python3 backend/test_scoring.py``
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import scoring_agent
import vector_store
from database import insert_rule, reset_analysis
from models import FlagDraft, ScoreDraft
from scoring_agent import retrieve_matching_rules, score_claim
from vector_store import close_client, init_vector_store, reset_vectors

RULE = {
    "rule_id": "R-001",
    "source_denials": ["D-001", "D-002", "D-003", "D-004", "D-005", "D-006"],
    "source_count": 6,
    "payer_pattern": "UnitedHealthcare",
    "cpt_pattern": "A0427",
    "carc_pattern": "CO-16",
    "service_pattern": "ALS-1 Emergency",
    "rule_title": "UHC ALS-1 requires transport necessity language",
    "risk_description": "UHC denies ALS-1 claims lacking explicit transport necessity.",
    "required_elements": [
        "explicit transport necessity statement",
        "why BLS / private vehicle was insufficient",
    ],
    "recommended_phrases": ["Patient required ALS-level transport because ..."],
    "confidence": 0.95,
    "severity": "high",
    "avg_denied_amount": 1850.0,
}

NARRATIVE = "Dispatched for chest pain. Administered aspirin 324mg PO. Transported to hospital."

vector_store.embed_text = lambda text, task_type=None: [0.01] * 768

init_vector_store()
reset_analysis()
reset_vectors()
insert_rule(RULE)  # SQL only - no embeddings, to prove the filter layer works alone

# Test 1: deterministic payer/CPT match, even with an empty vector index
matching = retrieve_matching_rules(NARRATIVE, "UnitedHealthcare", "A0427")
assert len(matching) == 1 and matching[0]["rule_id"] == "R-001"
assert matching[0]["matched_by"] == "filter"
print("✓ retrieval found R-001 via payer/CPT filter (no embeddings needed)")


# Test 2: the guard - LLM says LOW with a high flag -> result must be HIGH
async def _fake_low_but_high_flag(system, user, schema):
    return ScoreDraft(
        overall_risk="LOW",
        risk_score=0,
        flags=[
            FlagDraft(
                rule_id="R-001",
                rule_title=RULE["rule_title"],
                risk_level="high",
                missing_element="no transport necessity statement",
                suggestion="Add: Patient required ALS-level transport because ...",
                estimated_denial_risk=0,  # left blank -> should be filled from rule
            )
        ],
        top_recommendation="",
    )


scoring_agent.ainvoke_json = _fake_low_but_high_flag
result = asyncio.run(score_claim(NARRATIVE, "ALS-1 Emergency", "A0427", "UnitedHealthcare"))

assert result.overall_risk == "HIGH", result.overall_risk
assert result.risk_score >= 65, result.risk_score
assert result.flags[0].risk_level == "high"
assert result.flags[0].estimated_denial_risk == 1850.0, "est risk should fall back to rule avg"
assert result.flags[0].similar_denial_count == 6, "should pull source_count from the rule"
assert result.top_recommendation, "top recommendation should fall back to the first flag"
print(f"✓ guard: LLM 'LOW' + high flag -> normalized to {result.overall_risk} ({result.risk_score}/100)")
print(f"✓ flag enriched: est risk ${result.flags[0].estimated_denial_risk:.0f}, {result.flags[0].similar_denial_count} similar denials")

# Test 3: scoring with no rules raises a clear error
reset_analysis()
try:
    asyncio.run(score_claim(NARRATIVE, "ALS-1 Emergency", "A0427", "UnitedHealthcare"))
    raise AssertionError("expected ValueError when no rules exist")
except ValueError as exc:
    assert "analysis" in str(exc).lower()
    print(f"✓ no-rules guard: {exc}")

# Clean up
reset_analysis()
reset_vectors()
close_client()

print("\n=== Scoring agent tests passed (offline, stubbed LLM) ===")
