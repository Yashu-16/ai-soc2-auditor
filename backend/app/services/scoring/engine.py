"""
SOC2 Compliance Scoring Engine.

Scoring algorithm:
  - Each of the 5 Trust Principles starts at 100.
  - Every finding under that principle deducts fixed points based on
    risk_level: critical=-40, high=-20, medium=-10, low=-5.
  - Each principle score is floored at 0 (no negatives).
  - Overall score = unweighted average of the 5 principle scores.
    (Unweighted because SOC2 itself doesn't rank Trust Principles —
    an organization chooses which TSCs are in scope, but none is
    inherently "worth more" than another in the standard itself.)

Readiness ("are we SOC2 ready?") logic:
  - ANY finding with risk_level == critical => not ready, regardless
    of the numeric score. This mirrors how real audits work: one
    severe, unaddressed exposure can sink an otherwise strong posture.
  - Otherwise, ready if overall_score >= READINESS_THRESHOLD.

READINESS_THRESHOLD is a named constant specifically so it's not a
buried magic number — it's a defensible, explainable policy choice
that's easy to point to (and easy to change) on its own.
"""

from app.models.models import Finding, Control, TrustPrinciple

SEVERITY_DEDUCTIONS = {
    "critical": 40,
    "high": 20,
    "medium": 10,
    "low": 5,
}

READINESS_THRESHOLD = 80.0

PRINCIPLE_SCORE_FIELD = {
    TrustPrinciple.SECURITY: "security_score",
    TrustPrinciple.AVAILABILITY: "availability_score",
    TrustPrinciple.CONFIDENTIALITY: "confidentiality_score",
    TrustPrinciple.PROCESSING_INTEGRITY: "processing_integrity_score",
    TrustPrinciple.PRIVACY: "privacy_score",
}


def compute_score(findings: list[Finding], controls_by_id: dict[str, Control]) -> dict:
    """
    findings: Finding rows for a single audit run (with .control_id, .risk_level)
    controls_by_id: dict mapping control_id -> Control (for trust_principle lookup)

    Returns a dict with all ScoreSnapshot fields (minus id/audit_run_id/computed_at).
    """
    principle_scores = {p: 100.0 for p in TrustPrinciple}
    blocking_issues_count = 0

    for finding in findings:
        control = controls_by_id.get(finding.control_id)
        if control is None:
            continue  # defensive: shouldn't happen, but don't crash scoring

        risk_value = (
            finding.risk_level.value
            if hasattr(finding.risk_level, "value")
            else finding.risk_level
        )

        deduction = SEVERITY_DEDUCTIONS.get(risk_value, 0)
        principle_scores[control.trust_principle] -= deduction

        if risk_value == "critical":
            blocking_issues_count += 1

    # Floor every principle score at 0
    for principle in principle_scores:
        principle_scores[principle] = max(0.0, principle_scores[principle])

    overall_score = round(
        sum(principle_scores.values()) / len(principle_scores), 1
    )

    is_soc2_ready = blocking_issues_count == 0 and overall_score >= READINESS_THRESHOLD

    result = {
        PRINCIPLE_SCORE_FIELD[p]: round(score, 1)
        for p, score in principle_scores.items()
    }
    result["overall_score"] = overall_score
    result["is_soc2_ready"] = is_soc2_ready
    result["blocking_issues_count"] = blocking_issues_count

    return result