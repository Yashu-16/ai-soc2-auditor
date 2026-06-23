"""
/analyze-compliance endpoint.

Runs the deterministic rule engine against all NormalizedEvent rows for
a given audit run, persists the results as Finding rows, and returns
them. AI enrichment (explanation/remediation/confidence, and any
AI-assisted severity adjustment within the rule's floor/ceiling bounds)
happens in a later step (Phase 4) — this endpoint intentionally works
correctly without it, defaulting risk_level to each rule's severity_floor.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import AuditRun, NormalizedEvent, RawLog, Finding, Control
from app.services.rule_engine.engine import run_rule_engine

router = APIRouter()


@router.post("/analyze-compliance/{audit_run_id}")
def analyze_compliance(audit_run_id: str, db: Session = Depends(get_db)):
    audit_run = db.query(AuditRun).filter(AuditRun.id == audit_run_id).first()
    if not audit_run:
        raise HTTPException(status_code=404, detail="Audit run not found.")

    # Pull all normalized events belonging to this run via its raw_logs
    events = (
        db.query(NormalizedEvent)
        .join(RawLog, NormalizedEvent.raw_log_id == RawLog.id)
        .filter(RawLog.audit_run_id == audit_run_id)
        .all()
    )

    if not events:
        raise HTTPException(
            status_code=400,
            detail="No normalized events found for this audit run. Upload logs first.",
        )

    event_dicts = [
        {"id": e.id, "source_type": e.source_type.value, "raw_payload": e.raw_payload}
        for e in events
    ]

    candidate_findings = run_rule_engine(event_dicts)

    # Clear any prior findings for this run (re-analysis should be idempotent)
    db.query(Finding).filter(Finding.audit_run_id == audit_run_id).delete()

    created_findings = []
    for cf in candidate_findings:
        control = db.query(Control).filter(Control.id == cf.control_id).first()
        if not control:
            # Should never happen if rules.yaml control_ids match seeded controls,
            # but skip defensively rather than crash the whole analysis.
            continue

        finding = Finding(
            audit_run_id=audit_run_id,
            control_id=cf.control_id,
            rule_id=cf.rule_id,
            risk_level=cf.severity_floor,  # AI engine may raise this in Phase 4
            evidence_event_ids=cf.evidence_event_ids,
        )
        db.add(finding)
        created_findings.append(finding)

    audit_run.status = "analyzed"
    db.commit()

    return {
        "audit_run_id": audit_run_id,
        "findings_count": len(created_findings),
        "findings": [
            {
                "id": f.id,
                "control_id": f.control_id,
                "rule_id": f.rule_id,
                "risk_level": f.risk_level.value,
                "evidence_event_ids": f.evidence_event_ids,
            }
            for f in created_findings
        ],
    }