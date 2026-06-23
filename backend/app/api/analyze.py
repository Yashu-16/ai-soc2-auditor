"""
/analyze-compliance endpoint.

Runs the deterministic rule engine against all NormalizedEvent rows for
a given audit run, enriches each resulting finding via the AI engine
(explanation, remediation, confidence, severity-bounded risk_level),
persists the results as Finding rows, computes the weighted SOC2
compliance score, and persists it as a ScoreSnapshot.

If the AI engine fails entirely, findings still persist correctly with
templated fallback explanations rather than the request failing.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import (
    AuditRun,
    NormalizedEvent,
    RawLog,
    Finding,
    Control,
    ScoreSnapshot,
)
from app.services.rule_engine.engine import run_rule_engine
from app.services.ai_engine.orchestrator import enrich_findings
from app.services.scoring.engine import compute_score

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

    # Clear any prior findings + score for this run (re-analysis is idempotent)
    db.query(Finding).filter(Finding.audit_run_id == audit_run_id).delete()
    db.query(ScoreSnapshot).filter(ScoreSnapshot.audit_run_id == audit_run_id).delete()

    enriched_findings, overall_summary = enrich_findings(candidate_findings)
    enriched_by_key = {(ef.control_id, ef.rule_id): ef for ef in enriched_findings}

    all_controls = db.query(Control).all()
    controls_by_id = {c.id: c for c in all_controls}

    created_findings = []
    for cf in candidate_findings:
        control = controls_by_id.get(cf.control_id)
        if not control:
            # Should never happen if rules.yaml control_ids match seeded controls,
            # but skip defensively rather than crash the whole analysis.
            continue

        ef = enriched_by_key.get((cf.control_id, cf.rule_id))

        finding = Finding(
            audit_run_id=audit_run_id,
            control_id=cf.control_id,
            rule_id=cf.rule_id,
            risk_level=ef.risk_level if ef else cf.severity_floor,
            evidence_event_ids=cf.evidence_event_ids,
            ai_explanation=ef.explanation if ef else None,
            ai_remediation=ef.remediation if ef else None,
            ai_confidence=ef.confidence if ef else None,
        )
        db.add(finding)
        created_findings.append(finding)

    db.flush()  # ensure created_findings have risk_level set as Enum for scoring

    score_fields = compute_score(created_findings, controls_by_id)
    score_snapshot = ScoreSnapshot(audit_run_id=audit_run_id, **score_fields)
    db.add(score_snapshot)

    audit_run.status = "scored"
    db.commit()

    return {
        "audit_run_id": audit_run_id,
        "findings_count": len(created_findings),
        "ai_summary": overall_summary,
        "score": score_fields,
        "findings": [
            {
                "id": f.id,
                "control_id": f.control_id,
                "control_title": controls_by_id[f.control_id].title,
                "trust_principle": controls_by_id[f.control_id].trust_principle.value,
                "rule_id": f.rule_id,
                "risk_level": f.risk_level.value,
                "evidence_event_ids": f.evidence_event_ids,
                "ai_explanation": f.ai_explanation,
                "ai_remediation": f.ai_remediation,
                "ai_confidence": f.ai_confidence,
            }
            for f in created_findings
        ],
    }