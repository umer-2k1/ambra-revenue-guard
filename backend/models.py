"""Pydantic models shared across the backend (API + agents + storage)."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class DenialCase(BaseModel):
    """A resolved denial case (maps to the ``denial_cases`` table / seed JSON)."""

    id: str
    cluster: Optional[str] = None
    payer: str
    payer_id: Optional[str] = None
    claim_date: Optional[str] = None
    denial_date: Optional[str] = None
    resolution_date: Optional[str] = None
    service_type: str
    cpt_code: str
    billed_amount: float
    denied_amount: float
    paid_after_appeal: Optional[float] = None
    carc_code: str
    rarc_code: Optional[str] = None
    denial_reason: str
    pcr_excerpt: str
    missing_element: str
    appeal_strategy: str
    appeal_outcome: str
    days_to_appeal: Optional[int] = None
    region: Optional[str] = None


class ExtractedRule(BaseModel):
    """A prevention rule learned by the extraction agent (``prevention_rules``)."""

    rule_id: str
    source_denials: list[str]
    source_count: int
    plain_title: str
    plain_summary: str
    payer_pattern: str
    cpt_pattern: str
    carc_pattern: str
    service_pattern: str
    rule_title: str
    risk_description: str
    required_elements: list[str]
    recommended_phrases: list[str]
    confidence: float
    severity: str  # "high" | "medium" | "low"
    avg_denied_amount: float


class ClaimFlag(BaseModel):
    """A single documentation gap found while scoring a claim."""

    rule_id: str
    rule_title: str
    risk_level: str  # "high" | "medium" | "low"
    missing_element: str
    suggestion: str
    estimated_denial_risk: float
    similar_denial_count: int = 0


class ClaimScoreResult(BaseModel):
    """The result of scoring one claim narrative (``claim_scores``)."""

    score_id: str
    overall_risk: str  # "HIGH" | "MEDIUM" | "LOW"
    risk_score: int  # 0-100
    flags: list[ClaimFlag]
    rules_checked: int
    rules_matched: int
    top_recommendation: str = ""


class ScoreRequest(BaseModel):
    """Request body for ``POST /api/score``."""

    narrative: str
    service_type: str
    cpt_code: str
    payer: str


class AnalysisProgress(BaseModel):
    """One Server-Sent-Event payload emitted during analysis."""

    step: str  # "starting" | "clustering" | "extracting" | "stored" | "complete" | "error"
    cluster_name: str = ""
    message: str
    progress: float  # 0.0 - 1.0
    rule: Optional[ExtractedRule] = None


# ── LLM output schemas (what the model returns, before we add IDs) ────────────
class RuleDraft(BaseModel):
    """The LLM's raw extraction output for one cluster."""

    plain_title: str
    plain_summary: str
    rule_title: str
    payer_pattern: str
    cpt_pattern: str
    carc_pattern: str
    service_pattern: str
    risk_description: str
    required_elements: list[str]
    recommended_phrases: list[str]
    confidence: float
    severity: str
    avg_denied_amount: float


class FlagDraft(BaseModel):
    """One flag as returned by the scoring LLM."""

    rule_id: str
    rule_title: str
    risk_level: str
    missing_element: str
    suggestion: str
    estimated_denial_risk: float = 0.0


class ScoreDraft(BaseModel):
    """The LLM's raw scoring output."""

    overall_risk: str
    risk_score: int
    flags: list[FlagDraft] = []
    top_recommendation: str = ""
