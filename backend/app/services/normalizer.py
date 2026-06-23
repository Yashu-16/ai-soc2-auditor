"""
Log normalization: converts source-specific log entries (IAM, CloudTrail,
cloud config, GitHub activity) into a common NormalizedEvent shape.

Each normalize_* function takes one raw JSON object (as parsed from the
uploaded file) and returns a dict matching the NormalizedEvent columns:
    source_type, event_timestamp, actor, action, resource, raw_payload

raw_payload always preserves the FULL original entry, regardless of
source — this is what lets findings later cite verbatim evidence rather
than a lossy summary.
"""

from datetime import datetime
from typing import Any, Optional

from app.models.models import SourceType


def _parse_ts(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def normalize_iam_log(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_type": SourceType.IAM_LOG,
        "event_timestamp": _parse_ts(entry.get("timestamp")),
        "actor": entry.get("user"),
        "action": entry.get("event_type"),
        "resource": entry.get("role"),
        "raw_payload": entry,
    }


def normalize_cloudtrail_log(entry: dict[str, Any]) -> dict[str, Any]:
    user_identity = entry.get("userIdentity", {})
    request_params = entry.get("requestParameters", {})
    resource = (
        request_params.get("bucketName")
        or request_params.get("resourceName")
        or request_params.get("instanceId")
    )
    return {
        "source_type": SourceType.CLOUDTRAIL_LOG,
        "event_timestamp": _parse_ts(entry.get("eventTime")),
        "actor": user_identity.get("arn"),
        "action": entry.get("eventName"),
        "resource": resource,
        "raw_payload": entry,
    }


def normalize_cloud_config(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_type": SourceType.CLOUD_CONFIG,
        "event_timestamp": None,  # config snapshots aren't time-bound events
        "actor": None,
        "action": "config_snapshot",
        "resource": entry.get("resource_id"),
        "raw_payload": entry,
    }


def normalize_github_activity(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_type": SourceType.GITHUB_ACTIVITY,
        "event_timestamp": _parse_ts(entry.get("timestamp")),
        "actor": entry.get("actor"),
        "action": entry.get("event"),
        "resource": entry.get("branch"),
        "raw_payload": entry,
    }


NORMALIZERS = {
    SourceType.IAM_LOG: normalize_iam_log,
    SourceType.CLOUDTRAIL_LOG: normalize_cloudtrail_log,
    SourceType.CLOUD_CONFIG: normalize_cloud_config,
    SourceType.GITHUB_ACTIVITY: normalize_github_activity,
}


def normalize_entries(
    source_type: SourceType, entries: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Normalizes a list of raw entries for a given source type.
    Entries that fail normalization are skipped, not fatal — one bad
    line in a 500-line log file shouldn't kill the whole upload.
    """
    normalizer = NORMALIZERS[source_type]
    normalized = []
    for entry in entries:
        try:
            normalized.append(normalizer(entry))
        except (KeyError, AttributeError, TypeError):
            continue
    return normalized