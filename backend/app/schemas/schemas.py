"""
Pydantic schemas: the API's request/response contracts.

These are intentionally decoupled from the ORM models (app/models/models.py).
ORM models describe how data is stored; schemas describe how data is
exchanged over the API. Keeping them separate means we can change the
DB schema without breaking the API contract, and vice versa.
"""

from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

class UploadResponse(BaseModel):
    audit_run_id: str
    files_received: int
    events_normalized: int
    source_types: list[str]


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------

class EvidenceItem(BaseModel):
    """A single piece of evidence backing a finding, for display in the UI."""

    event_id: str
    actor: Optional[str] = None
    action: Optional[str] = None
    resource: Optional[str] = None
    timestamp: Optional[datetime] = None
    raw_payload: dict[str, Any]


class FindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    control_id: str
    control_title: str
    trust_principle: str
    rule_id: str
    risk_level: str
    ai_explanation: Optional[str] = None
    ai_remediation: Optional[str] = None
    ai_confidence: Optional[float] = None
    evidence: list[EvidenceItem] = []


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

class ScoreBreakdown(BaseModel):
    overall_score: float
    security_score: float
    availability_score: float
    confidentiality_score: float
    processing_integrity_score: float
    privacy_score: float
    is_soc2_ready: bool
    blocking_issues_count: int


# ---------------------------------------------------------------------------
# Analysis (the main /analyze-compliance response)
# ---------------------------------------------------------------------------

class AnalysisResponse(BaseModel):
    audit_run_id: str
    company_name: str
    analyzed_at: datetime
    score: ScoreBreakdown
    findings: list[FindingResponse]
    ai_summary: Optional[str] = None
    risk_counts: dict[str, int]  # {"low": 2, "medium": 3, "high": 1, "critical": 0}


# ---------------------------------------------------------------------------
# AI Engine internal contract (used between rule_engine -> ai_engine)
# ---------------------------------------------------------------------------

class CandidateFinding(BaseModel):
    """
    Output of the rule engine, input to the AI engine.
    The AI engine must not invent new control_id or rule_id values —
    it only enriches what's here with explanation/remediation/confidence.
    """

    control_id: str
    rule_id: str
    severity_floor: str  # minimum risk_level the AI can assign
    severity_ceiling: str  # maximum risk_level the AI can assign
    evidence_event_ids: list[str]
    evidence_summary: str  # short factual description for the AI prompt


class AIEnrichedFinding(BaseModel):
    """Strict schema the AI engine's LLM call must conform to."""

    control_id: str
    rule_id: str
    risk_level: str
    explanation: str
    remediation: str
    confidence: float