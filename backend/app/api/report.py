"""
/audit-report endpoint.

Accepts the analysis payload the frontend already received from
/analyze-compliance (no second DB lookup — the request body is treated
as the source of truth for what gets rendered), and converts it to a
PDF via ReportLab (pure Python, no native/system library dependencies).
"""

from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel

from app.services.report_generator.pdf_builder import build_audit_report_pdf

router = APIRouter()


class ScoreBreakdownIn(BaseModel):
    overall_score: float
    security_score: float
    availability_score: float
    confidentiality_score: float
    processing_integrity_score: float
    privacy_score: float
    is_soc2_ready: bool
    blocking_issues_count: int


class FindingIn(BaseModel):
    id: str
    control_id: str
    control_title: str
    trust_principle: str
    rule_id: str
    risk_level: str
    evidence_event_ids: list[str]
    ai_explanation: str | None = None
    ai_remediation: str | None = None
    ai_confidence: float | None = None


class AuditReportRequest(BaseModel):
    audit_run_id: str
    company_name: str
    findings_count: int
    ai_summary: str | None = None
    score: ScoreBreakdownIn
    findings: list[FindingIn]


@router.post("/audit-report")
def generate_audit_report(payload: AuditReportRequest):
    pdf_bytes = build_audit_report_pdf(payload)

    filename = f"soc2-audit-report-{payload.audit_run_id[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )