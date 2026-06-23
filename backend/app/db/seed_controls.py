"""
Seeds the `controls` table with a curated SOC2 control catalog.

We intentionally model ~18 controls rather than the full ~150-control
real SOC2 catalog. This is a portfolio/demo system: the goal is to show
correct *mapping methodology* (rule -> control -> trust principle) on a
representative set, not to exhaustively replicate a real auditor's
control library. This is worth saying explicitly in the README.

Run with:
    python -m app.db.seed_controls
"""

from app.db.session import SessionLocal, engine, Base
from app.models.models import Control, TrustPrinciple

CONTROLS = [
    # --- Security (CC6.x) ---
    Control(
        id="CC6.1",
        trust_principle=TrustPrinciple.SECURITY,
        title="Logical Access Controls",
        description=(
            "The entity implements logical access security software, "
            "infrastructure, and architectures over protected information "
            "assets to protect them from security events."
        ),
    ),
    Control(
        id="CC6.2",
        trust_principle=TrustPrinciple.SECURITY,
        title="User Access Provisioning and De-provisioning",
        description=(
            "Prior to issuing system credentials, the entity registers and "
            "authorizes new internal and external users. Access is removed "
            "when no longer required."
        ),
    ),
    Control(
        id="CC6.3",
        trust_principle=TrustPrinciple.SECURITY,
        title="Role-Based Access and Least Privilege",
        description=(
            "The entity authorizes, modifies, or removes access based on "
            "roles, responsibilities, or the system design, applying the "
            "principle of least privilege."
        ),
    ),
    Control(
        id="CC6.6",
        trust_principle=TrustPrinciple.SECURITY,
        title="Multi-Factor Authentication",
        description=(
            "The entity implements multi-factor authentication or "
            "equivalent controls to protect against unauthorized access "
            "from outside system boundaries."
        ),
    ),
    Control(
        id="CC6.7",
        trust_principle=TrustPrinciple.SECURITY,
        title="Restriction of Data Transmission and Removal",
        description=(
            "The entity restricts the transmission, movement, and removal "
            "of information to authorized internal and external users and "
            "processes."
        ),
    ),
    Control(
        id="CC6.8",
        trust_principle=TrustPrinciple.SECURITY,
        title="Prevention of Unauthorized or Malicious Software",
        description=(
            "The entity implements controls to prevent or detect and act "
            "upon the introduction of unauthorized or malicious software."
        ),
    ),

    # --- Availability (A1.x) ---
    Control(
        id="A1.1",
        trust_principle=TrustPrinciple.AVAILABILITY,
        title="Capacity Monitoring",
        description=(
            "The entity monitors current usage of system components and "
            "evaluates capacity demand against thresholds to manage "
            "availability."
        ),
    ),
    Control(
        id="A1.2",
        trust_principle=TrustPrinciple.AVAILABILITY,
        title="Backup and Recovery",
        description=(
            "The entity authorizes, designs, develops, implements, "
            "operates, approves, maintains, and monitors environmental "
            "protections, backup processes, and recovery infrastructure."
        ),
    ),
    Control(
        id="A1.3",
        trust_principle=TrustPrinciple.AVAILABILITY,
        title="Recovery Plan Testing",
        description=(
            "The entity tests recovery plan procedures supporting system "
            "recovery to meet objectives."
        ),
    ),

    # --- Confidentiality (C1.x) ---
    Control(
        id="C1.1",
        trust_principle=TrustPrinciple.CONFIDENTIALITY,
        title="Confidential Information Identification",
        description=(
            "The entity identifies and maintains confidential information "
            "to meet objectives related to confidentiality."
        ),
    ),
    Control(
        id="C1.2",
        trust_principle=TrustPrinciple.CONFIDENTIALITY,
        title="Disposal and Protection of Confidential Information",
        description=(
            "The entity disposes of confidential information and protects "
            "it from unauthorized access during storage and transmission, "
            "including encryption at rest and in transit."
        ),
    ),

    # --- Processing Integrity (PI1.x) ---
    Control(
        id="PI1.1",
        trust_principle=TrustPrinciple.PROCESSING_INTEGRITY,
        title="Change Management Process",
        description=(
            "The entity implements policies and procedures to ensure that "
            "changes to system components are authorized, tested, "
            "approved, and documented prior to deployment."
        ),
    ),
    Control(
        id="PI1.2",
        trust_principle=TrustPrinciple.PROCESSING_INTEGRITY,
        title="Code Review and Branch Protection",
        description=(
            "The entity requires peer review and approval of code changes "
            "via protected branches prior to merging into production "
            "branches."
        ),
    ),
    Control(
        id="PI1.3",
        trust_principle=TrustPrinciple.PROCESSING_INTEGRITY,
        title="System Processing Monitoring",
        description=(
            "The entity monitors system processing for errors, anomalies, "
            "and unauthorized or unexpected changes."
        ),
    ),

    # --- Privacy (P1.x) ---
    Control(
        id="P1.1",
        trust_principle=TrustPrinciple.PRIVACY,
        title="Notice and Data Handling Practices",
        description=(
            "The entity provides notice about its privacy practices and "
            "handles personal information consistent with those practices."
        ),
    ),
    Control(
        id="P4.1",
        trust_principle=TrustPrinciple.PRIVACY,
        title="Access Logging for Personal Information",
        description=(
            "The entity logs and monitors access to systems storing "
            "personal information to detect unauthorized access."
        ),
    ),
    Control(
        id="P5.1",
        trust_principle=TrustPrinciple.PRIVACY,
        title="Data Retention and Disposal",
        description=(
            "The entity retains personal information consistent with its "
            "objectives and disposes of it when no longer required."
        ),
    ),
    Control(
        id="P6.1",
        trust_principle=TrustPrinciple.PRIVACY,
        title="Masking of Sensitive Data in Logs",
        description=(
            "The entity ensures personal information is masked or "
            "redacted in application and infrastructure logs."
        ),
    ),
]


def seed():
    Base.metadata.create_all(bind=engine)  # safety net if tables don't exist yet
    db = SessionLocal()
    try:
        existing_ids = {c.id for c in db.query(Control).all()}
        added = 0
        for control in CONTROLS:
            if control.id not in existing_ids:
                db.add(control)
                added += 1
        db.commit()
        print(f"Seed complete. {added} new controls added, "
              f"{len(CONTROLS) - added} already present.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()