"""
ORM models for the AI SOC2 Auditor.

Design notes:
- AuditRun is the anchor entity. Every upload, finding, and score is
  scoped to a run, which gives us "compliance over time" for free.
- Control is reference data (seeded once, not per-run) representing the
  static catalog of SOC2 controls this system knows how to check.
- Finding links a violation back to both its Control and the specific
  NormalizedEvent rows that constitute evidence — this traceability is
  the difference between "an AI said so" and an auditable finding.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    Text,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    Float,
    Integer,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class TrustPrinciple(str, enum.Enum):
    SECURITY = "security"
    AVAILABILITY = "availability"
    CONFIDENTIALITY = "confidentiality"
    PROCESSING_INTEGRITY = "processing_integrity"
    PRIVACY = "privacy"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SourceType(str, enum.Enum):
    IAM_LOG = "iam_log"
    CLOUDTRAIL_LOG = "cloudtrail_log"
    CLOUD_CONFIG = "cloud_config"
    GITHUB_ACTIVITY = "github_activity"


class AuditRun(Base):
    """One end-to-end analysis run: upload -> rule engine -> AI -> score."""

    __tablename__ = "audit_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    company_name: Mapped[str] = mapped_column(String, default="Demo SaaS Co")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String, default="pending")
    # pending -> ingested -> analyzed -> scored -> reported

    raw_logs: Mapped[list["RawLog"]] = relationship(
        back_populates="audit_run", cascade="all, delete-orphan"
    )
    findings: Mapped[list["Finding"]] = relationship(
        back_populates="audit_run", cascade="all, delete-orphan"
    )
    score_snapshot: Mapped["ScoreSnapshot"] = relationship(
        back_populates="audit_run", uselist=False, cascade="all, delete-orphan"
    )


class RawLog(Base):
    """An uploaded file, stored as-is, tied to a run."""

    __tablename__ = "raw_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    audit_run_id: Mapped[str] = mapped_column(ForeignKey("audit_runs.id"))
    source_type: Mapped[SourceType] = mapped_column(SAEnum(SourceType))
    original_filename: Mapped[str] = mapped_column(String)
    storage_path: Mapped[str] = mapped_column(String)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    audit_run: Mapped["AuditRun"] = relationship(back_populates="raw_logs")
    events: Mapped[list["NormalizedEvent"]] = relationship(
        back_populates="raw_log", cascade="all, delete-orphan"
    )


class NormalizedEvent(Base):
    """
    A single log entry normalized into a common schema, regardless of
    whether it originated from IAM, CloudTrail, GitHub, or config files.
    """

    __tablename__ = "normalized_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    raw_log_id: Mapped[str] = mapped_column(ForeignKey("raw_logs.id"))
    source_type: Mapped[SourceType] = mapped_column(SAEnum(SourceType))
    event_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    actor: Mapped[str] = mapped_column(String, nullable=True)
    action: Mapped[str] = mapped_column(String, nullable=True)
    resource: Mapped[str] = mapped_column(String, nullable=True)
    # Full original entry, preserved for evidence/audit trail purposes
    raw_payload: Mapped[dict] = mapped_column(JSON)

    raw_log: Mapped["RawLog"] = relationship(back_populates="events")


class Control(Base):
    """
    Static reference catalog of SOC2 controls this system can check.
    Seeded once (see backend/app/db/seed_controls.py in a later step),
    not created per-run.
    """

    __tablename__ = "controls"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # e.g. "CC6.1"
    trust_principle: Mapped[TrustPrinciple] = mapped_column(SAEnum(TrustPrinciple))
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)

    findings: Mapped[list["Finding"]] = relationship(back_populates="control")


class Finding(Base):
    """
    A detected violation within a specific audit run, linked to the
    control it violates and (via evidence_event_ids) the normalized
    events that constitute proof.
    """

    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    audit_run_id: Mapped[str] = mapped_column(ForeignKey("audit_runs.id"))
    control_id: Mapped[str] = mapped_column(ForeignKey("controls.id"))
    rule_id: Mapped[str] = mapped_column(String)  # which rule_engine rule fired
    risk_level: Mapped[RiskLevel] = mapped_column(SAEnum(RiskLevel))

    # Evidence trail: IDs of NormalizedEvent rows that triggered this finding
    evidence_event_ids: Mapped[list] = mapped_column(JSON, default=list)

    # Filled in by the AI layer (Phase 4); nullable until that step runs
    ai_explanation: Mapped[str] = mapped_column(Text, nullable=True)
    ai_remediation: Mapped[str] = mapped_column(Text, nullable=True)
    ai_confidence: Mapped[float] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    audit_run: Mapped["AuditRun"] = relationship(back_populates="findings")
    control: Mapped["Control"] = relationship(back_populates="findings")


class ScoreSnapshot(Base):
    """The computed compliance score for a given audit run."""

    __tablename__ = "score_snapshots"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    audit_run_id: Mapped[str] = mapped_column(ForeignKey("audit_runs.id"), unique=True)

    overall_score: Mapped[float] = mapped_column(Float)
    security_score: Mapped[float] = mapped_column(Float)
    availability_score: Mapped[float] = mapped_column(Float)
    confidentiality_score: Mapped[float] = mapped_column(Float)
    processing_integrity_score: Mapped[float] = mapped_column(Float)
    privacy_score: Mapped[float] = mapped_column(Float)

    is_soc2_ready: Mapped[bool] = mapped_column(default=False)
    blocking_issues_count: Mapped[int] = mapped_column(Integer, default=0)

    computed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    audit_run: Mapped["AuditRun"] = relationship(back_populates="score_snapshot")