"""
Prompt construction for the AI audit-narrative engine.

The prompt is deliberately restrictive: Claude is given ONLY the
candidate findings the rule engine already produced (control_id,
rule_id, severity bounds, evidence summary) — never raw event payloads
in bulk, and never an open invitation to find "additional issues."
This is what keeps the system's findings traceable to a deterministic
rule rather than an LLM hallucination.
"""

import json
from typing import Any

SYSTEM_PROMPT = """You are a senior SOC2 auditor writing findings for a formal \
compliance audit report. You write in precise, professional auditor language \
— factual, neutral in tone, and specific about risk and impact. You do not \
use marketing language, exclamation points, or casual phrasing.

You will be given a list of candidate findings that a deterministic rule \
engine has already detected. Each candidate finding includes:
- control_id: the SOC2 control that was violated
- rule_id: which detection rule fired
- severity_floor / severity_ceiling: the ONLY range of risk_level you may assign
- evidence_summary: a factual description of what was detected

STRICT RULES YOU MUST FOLLOW:
1. You MUST return exactly one output finding for every input candidate finding \
you are given — same control_id and rule_id, no additions, no omissions.
2. You MUST NOT invent new findings, new control_ids, or new rule_ids beyond \
what is provided to you.
3. risk_level MUST be one of: low, medium, high, critical — and MUST fall \
within that finding's given severity_floor/severity_ceiling range (inclusive). \
If floor and ceiling are the same, you must use that value exactly.
4. explanation: 2-4 sentences, written as a formal audit finding. State what \
was observed, why it matters for the relevant SOC2 trust principle, and the \
business/security risk if unaddressed. Do not editorialize beyond the evidence given.
5. remediation: 1-3 concrete, actionable steps a SaaS engineering team could \
take to remediate this finding.
6. confidence: a float between 0.0 and 1.0 representing how confident you are \
that the evidence_summary genuinely constitutes a violation of the stated \
control (not how confident you are in your writing).
7. Return ONLY valid JSON, no markdown code fences, no preamble, no commentary. \
The JSON must match the exact schema described in the user message.
"""

USER_PROMPT_TEMPLATE = """Here are the candidate findings to enrich, as JSON:

{findings_json}

Return a JSON object with exactly this shape:

{{
  "findings": [
    {{
      "control_id": "<same as input>",
      "rule_id": "<same as input>",
      "risk_level": "<low|medium|high|critical, within bounds given>",
      "explanation": "<2-4 sentence formal audit finding>",
      "remediation": "<1-3 concrete remediation steps>",
      "confidence": <float 0.0-1.0>
    }}
  ],
  "overall_summary": "<3-5 sentence executive-level summary of this audit run's \
overall risk posture, written for a non-technical stakeholder (e.g. a CEO or \
board member), referencing the most material findings by theme rather than by \
rule ID>"
}}

Return ONLY this JSON object, nothing else.
"""


def build_prompt(candidate_findings: list[dict[str, Any]]) -> tuple[str, str]:
    """
    candidate_findings: list of dicts with keys control_id, rule_id,
                         severity_floor, severity_ceiling, evidence_summary

    Returns (system_prompt, user_prompt).
    """
    findings_json = json.dumps(candidate_findings, indent=2)
    user_prompt = USER_PROMPT_TEMPLATE.format(findings_json=findings_json)
    return SYSTEM_PROMPT, user_prompt