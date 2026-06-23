"""
Rule Engine: loads YAML-defined rules and evaluates them against
NormalizedEvent rows to produce CandidateFinding objects.

This is the deterministic detection layer. The AI engine (Phase 4)
consumes its output but never bypasses it — no finding reaches the
dashboard without having first fired a concrete, inspectable rule.
"""

from pathlib import Path
from typing import Any
from collections import defaultdict

import yaml

from app.schemas.schemas import CandidateFinding

RULES_PATH = Path(__file__).resolve().parents[3] / "rules" / "soc2_rules.yaml"


def _get_path(payload: dict[str, Any], path: str) -> Any:
    """Resolves dot-notation path into a nested dict. Returns None if missing."""
    current: Any = payload
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _evaluate_condition(payload: dict[str, Any], condition: str) -> bool:
    """
    Tiny DSL evaluator. condition format: "<path> <operator> <value>"
    e.g. "mfa_enabled is_false", "permissions contains *:*"
    """
    parts = condition.split(" ", 2)
    if len(parts) < 2:
        return False
    path, operator = parts[0], parts[1]
    value = parts[2] if len(parts) > 2 else None
    actual = _get_path(payload, path)

    if operator == "is_false":
        return actual is False
    if operator == "is_true":
        return actual is True
    if operator == "is_empty":
        return actual in (None, "", [], {})
    if operator == "eq":
        return str(actual) == value
    if operator == "neq":
        return str(actual) != value
    if operator == "contains":
        if isinstance(actual, list):
            return any(value in str(item) for item in actual)
        if isinstance(actual, str):
            return value in actual
        return False
    if operator == "ends_with_any":
        if isinstance(actual, list):
            return any(str(item).endswith(value) for item in actual)
        return False
    if operator == "in":
        return actual in (value.split(",") if value else [])
    if operator == "gt":
        try:
            return float(actual) > float(value)
        except (TypeError, ValueError):
            return False
    if operator == "lt":
        try:
            return float(actual) < float(value)
        except (TypeError, ValueError):
            return False
    return False


def load_rules() -> list[dict[str, Any]]:
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["rules"]


def run_rule_engine(events: list[dict[str, Any]]) -> list[CandidateFinding]:
    """
    events: list of dicts shaped like NormalizedEvent rows, each must have
            at minimum: id, source_type (str value, e.g. "iam_log"),
            raw_payload (dict)

    Returns one CandidateFinding per (rule_id) that fired, aggregating
    all matching events as evidence for that rule.
    """
    rules = load_rules()
    # group matches by rule_id so multiple violating events become one finding
    matches: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for rule in rules:
        for event in events:
            if event["source_type"] != rule["source_type"]:
                continue
            if _evaluate_condition(event["raw_payload"], rule["condition"]):
                matches[rule["id"]].append(event)

    findings: list[CandidateFinding] = []
    rules_by_id = {r["id"]: r for r in rules}

    for rule_id, matched_events in matches.items():
        rule = rules_by_id[rule_id]
        findings.append(
            CandidateFinding(
                control_id=rule["control_id"],
                rule_id=rule_id,
                severity_floor=rule["severity_floor"],
                severity_ceiling=rule["severity_ceiling"],
                evidence_event_ids=[e["id"] for e in matched_events],
                evidence_summary=(
                    f"{rule['description']} — {len(matched_events)} "
                    f"matching event(s) detected."
                ),
            )
        )

    return findings