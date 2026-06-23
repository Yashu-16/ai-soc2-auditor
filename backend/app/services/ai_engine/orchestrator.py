"""
AI enrichment orchestration.

Takes CandidateFinding objects (from the rule engine) and returns
AIEnrichedFinding objects (explanation, remediation, confidence, and a
validated risk_level). This is the ONLY place in the codebase that
calls the LLM for finding enrichment, and it enforces three guarantees
regardless of what the model returns:

  1. Every candidate finding gets exactly one enriched output — the AI
     cannot add or drop findings.
  2. risk_level is clamped to [severity_floor, severity_ceiling] even if
     the model's returned value falls outside that range.
  3. If the model call fails, returns malformed JSON, or omits a finding,
     we fall back to a templated (non-AI) explanation for that finding
     rather than leaving the API response incomplete or erroring out.
"""

from app.schemas.schemas import CandidateFinding, AIEnrichedFinding
from app.services.ai_engine.claude_client import call_claude_json
from app.services.ai_engine.prompts import build_prompt

RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def _clamp_risk(risk_level: str, floor: str, ceiling: str) -> str:
    """Forces risk_level into [floor, ceiling], defaulting to floor if invalid."""
    if risk_level not in RISK_ORDER:
        return floor
    lo, hi, val = RISK_ORDER[floor], RISK_ORDER[ceiling], RISK_ORDER[risk_level]
    if val < lo:
        return floor
    if val > hi:
        return ceiling
    return risk_level


def _fallback_finding(cf: CandidateFinding) -> AIEnrichedFinding:
    """Templated, non-AI enrichment used when the LLM call fails entirely."""
    return AIEnrichedFinding(
        control_id=cf.control_id,
        rule_id=cf.rule_id,
        risk_level=cf.severity_floor,
        explanation=(
            f"Automated detection rule {cf.rule_id} identified a control "
            f"violation: {cf.evidence_summary} AI-generated narrative "
            f"enrichment was unavailable for this finding; this is a "
            f"system-generated fallback description."
        ),
        remediation=(
            "Review the underlying evidence for this finding and consult "
            "the relevant SOC2 control description to determine appropriate "
            "remediation steps."
        ),
        confidence=0.5,
    )


def enrich_findings(
    candidate_findings: list[CandidateFinding],
) -> tuple[list[AIEnrichedFinding], str | None]:
    """
    Returns (enriched_findings, overall_summary).
    overall_summary is None if the AI call fails entirely.
    """
    if not candidate_findings:
        return [], None

    candidates_by_key = {
        (cf.control_id, cf.rule_id): cf for cf in candidate_findings
    }

    payload = [
        {
            "control_id": cf.control_id,
            "rule_id": cf.rule_id,
            "severity_floor": cf.severity_floor,
            "severity_ceiling": cf.severity_ceiling,
            "evidence_summary": cf.evidence_summary,
        }
        for cf in candidate_findings
    ]

    system_prompt, user_prompt = build_prompt(payload)

    parsed = None
    for attempt in range(2):  # one initial attempt + one retry
        try:
            parsed = call_claude_json(system_prompt, user_prompt)
            break
        except (ValueError, RuntimeError):
            if attempt == 1:
                parsed = None

    if not parsed or "findings" not in parsed:
        # Total failure: fall back for every candidate finding.
        return [_fallback_finding(cf) for cf in candidate_findings], None

    enriched_by_key: dict[tuple[str, str], AIEnrichedFinding] = {}

    for item in parsed.get("findings", []):
        key = (item.get("control_id"), item.get("rule_id"))
        cf = candidates_by_key.get(key)
        if cf is None:
            # Model returned a finding we never asked about — discard it.
            # This is the concrete enforcement of "AI cannot invent findings."
            continue

        risk_level = _clamp_risk(
            item.get("risk_level", cf.severity_floor),
            cf.severity_floor,
            cf.severity_ceiling,
        )

        enriched_by_key[key] = AIEnrichedFinding(
            control_id=cf.control_id,
            rule_id=cf.rule_id,
            risk_level=risk_level,
            explanation=item.get("explanation") or "No explanation provided.",
            remediation=item.get("remediation") or "No remediation provided.",
            confidence=float(item.get("confidence", 0.5)),
        )

    # Guarantee 1: every candidate gets an output, even if the model
    # skipped it — fall back individually for any gaps.
    results = []
    for cf in candidate_findings:
        key = (cf.control_id, cf.rule_id)
        results.append(enriched_by_key.get(key) or _fallback_finding(cf))

    overall_summary = parsed.get("overall_summary")
    return results, overall_summary