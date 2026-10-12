"""Scoring agent.

Takes a new PCR narrative and returns a risk score plus specific flags, using
the rules learned during analysis.

Retrieval is deliberately **soft**:

1. vector similarity over *all* learned rules (semantic candidates), and
2. a deterministic merge of every rule whose payer/CPT pattern matches the
   claim ("always look at these").

The two are unioned, so the claim is judged against cross-payer rules that
describe the same failure mode, and a payer-specific rule can never be missed
just because its embedding drifted.

After the LLM responds, :func:`_normalize` applies a deterministic guard:
the overall risk can never be *lower* than what the flags imply, and the score
is floored for HIGH/MEDIUM results. Nothing is fabricated - flags only ever
come from the model, and only reference rules that were actually retrieved.
"""
from __future__ import annotations

import fnmatch
import json
from typing import Any
from uuid import uuid4

from database import get_all_rules, get_rule, get_status, insert_score
from llm import ainvoke_json
from models import ClaimFlag, ClaimScoreResult, ScoreDraft
from prompts import SCORING_SYSTEM_PROMPT, SCORING_USER_PROMPT_TEMPLATE, render
from vector_store import query_similar_rules

_RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


def generate_score_id() -> str:
    return f"S-{uuid4().hex[:8]}"


# ── Retrieval ────────────────────────────────────────────────────────────────
def _payer_match(pattern: str | None, payer: str | None) -> bool:
    if not pattern:
        return False
    pattern = pattern.strip().lower()
    if pattern in ("*", ""):
        return True
    return pattern == (payer or "").strip().lower()


def _cpt_match(pattern: str | None, cpt: str | None) -> bool:
    if not pattern:
        return False
    pattern = pattern.strip()
    if pattern in ("*", "") or pattern == cpt:
        return True
    return fnmatch.fnmatch(cpt or "", pattern)


def retrieve_matching_rules(
    claim_text: str, payer: str | None, cpt_code: str | None, top_k: int = 5
) -> list[dict]:
    """Union of vector-similar rules and exact payer/CPT matches, full detail."""
    by_id: dict[str, dict] = {}

    # Layer 1 - semantic candidates.
    for hit in query_similar_rules(claim_text, n_results=top_k):
        rule_id = hit.get("rule_id")
        if not rule_id or rule_id in by_id:
            continue
        rule = get_rule(rule_id)
        if rule:
            rule = dict(rule)
            rule["similarity_score"] = (
                round(hit["similarity_score"], 4)
                if hit.get("similarity_score") is not None
                else None
            )
            rule["matched_by"] = "vector"
            by_id[rule_id] = rule

    # Layer 2 - deterministic payer/CPT matches (never miss a targeted rule).
    for rule in get_all_rules():
        rule_id = rule["rule_id"]
        if rule_id in by_id:
            continue
        if _payer_match(rule.get("payer_pattern"), payer) or _cpt_match(
            rule.get("cpt_pattern"), cpt_code
        ):
            rule = dict(rule)
            rule["similarity_score"] = None
            rule["matched_by"] = "filter"
            by_id[rule_id] = rule

    return list(by_id.values())


# ── Guard / result assembly ──────────────────────────────────────────────────
def _normalize(draft: ScoreDraft, matching: list[dict]) -> ClaimScoreResult:
    rules_by_id = {r["rule_id"]: r for r in matching}

    flags: list[ClaimFlag] = []
    for f in draft.flags:
        rule = rules_by_id.get(f.rule_id)
        est = f.estimated_denial_risk
        if (not est) and rule:
            est = rule.get("avg_denied_amount") or 0.0
        flags.append(
            ClaimFlag(
                rule_id=f.rule_id,
                rule_title=f.rule_title,
                risk_level=(f.risk_level or "low").lower(),
                missing_element=f.missing_element,
                suggestion=f.suggestion,
                estimated_denial_risk=float(est or 0.0),
                similar_denial_count=(rule.get("source_count") if rule else 0) or 0,
            )
        )

    # Deterministic guard: overall risk must be at least what the flags imply.
    derived = max((_RISK_ORDER.get(fl.risk_level, 0) for fl in flags), default=0)
    llm_rank = _RISK_ORDER.get((draft.overall_risk or "").strip().lower(), 0)
    rank = max(derived, llm_rank)
    overall = {0: "LOW", 1: "MEDIUM", 2: "HIGH"}[rank]

    score = max(0, min(100, int(draft.risk_score or 0)))
    if overall == "HIGH":
        score = max(score, 65)
    elif overall == "MEDIUM":
        score = max(score, 35)

    top = (draft.top_recommendation or "").strip()
    if not top and flags:
        top = flags[0].suggestion

    return ClaimScoreResult(
        score_id=generate_score_id(),
        overall_risk=overall,
        risk_score=score,
        flags=flags,
        rules_checked=len(matching),
        rules_matched=len(flags),
        top_recommendation=top,
        plain_recommendation=(draft.plain_recommendation or "").strip(),
    )


def _persist(
    result: ClaimScoreResult, narrative: str, service_type: str, cpt_code: str, payer: str
) -> None:
    insert_score(
        {
            "score_id": result.score_id,
            "claim_narrative": narrative,
            "service_type": service_type,
            "cpt_code": cpt_code,
            "payer": payer,
            "overall_risk": result.overall_risk,
            "risk_score": result.risk_score,
            "flags_found": len(result.flags),
            "flags_detail": [f.model_dump() for f in result.flags],
            "rules_matched": [f.rule_id for f in result.flags],
        }
    )


# ── Main entry point ─────────────────────────────────────────────────────────
async def score_claim(
    narrative: str, service_type: str, cpt_code: str, payer: str
) -> ClaimScoreResult:
    """Score one claim narrative against the learned rules."""
    if get_status()["total_rules"] == 0:
        raise ValueError("No rules in memory. Run analysis first.")

    matching = retrieve_matching_rules(narrative, payer, cpt_code)

    if not matching:
        result = ClaimScoreResult(
            score_id=generate_score_id(),
            overall_risk="LOW",
            risk_score=0,
            flags=[],
            rules_checked=0,
            rules_matched=0,
            top_recommendation="No matching denial patterns found. Claim appears safe.",
        )
        _persist(result, narrative, service_type, cpt_code, payer)
        return result

    user_prompt = render(
        SCORING_USER_PROMPT_TEMPLATE,
        service_type=service_type,
        cpt_code=cpt_code,
        payer=payer,
        claim_narrative=narrative,
        rules_json=json.dumps(matching, indent=2),
    )

    draft: ScoreDraft | None = None
    for _attempt in range(2):  # retry once
        try:
            draft = await ainvoke_json(SCORING_SYSTEM_PROMPT, user_prompt, ScoreDraft)
            break
        except Exception as exc:  # noqa: BLE001
            print(f"[scoring] attempt failed: {exc}")
            draft = None

    if draft is None:
        raise ValueError("Scoring model failed to return valid JSON. Please retry.")

    result = _normalize(draft, matching)
    _persist(result, narrative, service_type, cpt_code, payer)
    return result
