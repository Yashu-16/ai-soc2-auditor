"""
PDF report generation using ReportLab (pure Python, no native/system
library dependencies — chosen specifically for cross-platform
portability after WeasyPrint's Pango/Cairo dependency proved unreliable
on Windows, including in this project's own development environment).

This module builds the SOC2 audit report as a ReportLab Platypus
document: a cover page, executive summary, per-Trust-Principle score
table, detailed findings, and an evidence appendix.
"""

import io
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable,
)

# --- Color palette (mirrors the dashboard's risk semantics) ---
COLOR_INK = colors.HexColor("#0b0e14")
COLOR_BODY = colors.HexColor("#1a1d24")
COLOR_MUTED = colors.HexColor("#5c6478")
COLOR_HAIRLINE = colors.HexColor("#d8dbe2")
COLOR_PANEL = colors.HexColor("#f4f5f7")
COLOR_READY = colors.HexColor("#1f9d63")
COLOR_NOT_READY = colors.HexColor("#c43d32")
COLOR_RISK = {
    "critical": colors.HexColor("#c43d32"),
    "high": colors.HexColor("#c43d32"),
    "medium": colors.HexColor("#a36a1a"),
    "low": colors.HexColor("#8a7a1f"),
}

_styles = getSampleStyleSheet()

STYLE_EYEBROW = ParagraphStyle(
    "Eyebrow", parent=_styles["Normal"], fontName="Courier-Bold",
    fontSize=9, textColor=COLOR_MUTED, spaceAfter=4, leading=11,
)
STYLE_COVER_TITLE = ParagraphStyle(
    "CoverTitle", parent=_styles["Normal"], fontName="Helvetica-Bold",
    fontSize=28, textColor=COLOR_INK, spaceAfter=4, leading=32,
)
STYLE_COVER_COMPANY = ParagraphStyle(
    "CoverCompany", parent=_styles["Normal"], fontName="Helvetica",
    fontSize=15, textColor=colors.HexColor("#3a4254"), spaceAfter=24,
)
STYLE_COVER_SCORE = ParagraphStyle(
    "CoverScore", parent=_styles["Normal"], fontName="Courier-Bold",
    fontSize=48, textColor=COLOR_INK, leading=52,
)
STYLE_COVER_META = ParagraphStyle(
    "CoverMeta", parent=_styles["Normal"], fontName="Courier",
    fontSize=9, textColor=COLOR_MUTED, leading=14,
)
STYLE_SECTION = ParagraphStyle(
    "Section", parent=_styles["Normal"], fontName="Helvetica-Bold",
    fontSize=14, textColor=COLOR_INK, spaceBefore=4, spaceAfter=10,
)
STYLE_BODY = ParagraphStyle(
    "Body", parent=_styles["Normal"], fontName="Helvetica",
    fontSize=10, textColor=COLOR_BODY, leading=15,
)
STYLE_SUMMARY_BOX = ParagraphStyle(
    "SummaryBox", parent=STYLE_BODY, backColor=COLOR_PANEL,
    borderPadding=10, leading=15,
)
STYLE_LABEL = ParagraphStyle(
    "Label", parent=_styles["Normal"], fontName="Courier-Bold",
    fontSize=8, textColor=colors.HexColor("#4a5570"), spaceBefore=8, spaceAfter=2,
)
STYLE_FINDING_HEADER = ParagraphStyle(
    "FindingHeader", parent=_styles["Normal"], fontName="Courier-Bold",
    fontSize=11, textColor=COLOR_BODY, spaceAfter=2,
)
STYLE_FINDING_RULE = ParagraphStyle(
    "FindingRule", parent=_styles["Normal"], fontName="Courier",
    fontSize=8, textColor=COLOR_MUTED, spaceAfter=4,
)
STYLE_EVIDENCE = ParagraphStyle(
    "Evidence", parent=_styles["Normal"], fontName="Courier",
    fontSize=8, textColor=COLOR_BODY, backColor=COLOR_PANEL,
    borderPadding=8, leading=12,
)
STYLE_DISCLAIMER = ParagraphStyle(
    "Disclaimer", parent=_styles["Normal"], fontName="Helvetica-Oblique",
    fontSize=8, textColor=COLOR_MUTED, leading=12, spaceBefore=20,
)


def _risk_tag_html(risk_level: str) -> str:
    color = COLOR_RISK.get(risk_level, COLOR_MUTED).hexval()
    return (
        f'<font color="{color}"><b>[{risk_level.upper()}]</b></font>'
    )


def build_audit_report_pdf(payload) -> bytes:
    """
    payload: an object (e.g. the Pydantic AuditReportRequest) exposing
             audit_run_id, company_name, findings_count, ai_summary,
             score (with .overall_score, .security_score, etc.,
             .is_soc2_ready, .blocking_issues_count), and findings
             (list of objects with control_id, control_title,
             trust_principle, rule_id, risk_level, evidence_event_ids,
             ai_explanation, ai_remediation, ai_confidence).

    Returns raw PDF bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        topMargin=2.2 * cm,
        bottomMargin=2 * cm,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        title=f"SOC2 Audit Report — {payload.company_name}",
    )

    elements = []
    generated_at = datetime.now(timezone.utc).strftime("%B %d, %Y %H:%M UTC")

    # --- Cover page ---
    elements.append(Spacer(1, 5 * cm))
    elements.append(Paragraph("SOC 2 COMPLIANCE AUDIT REPORT — SIMULATED", STYLE_EYEBROW))
    elements.append(Paragraph("Compliance Audit Report", STYLE_COVER_TITLE))
    elements.append(Paragraph(payload.company_name, STYLE_COVER_COMPANY))

    score = payload.score
    ready_color = "#1f9d63" if score.is_soc2_ready else "#c43d32"
    ready_label = "SOC2 READY" if score.is_soc2_ready else "NOT READY"
    elements.append(
        Paragraph(
            f'{round(score.overall_score)} '
            f'<font color="{ready_color}" size="13"><b> {ready_label}</b></font>',
            STYLE_COVER_SCORE,
        )
    )
    elements.append(Spacer(1, 1 * cm))
    elements.append(
        Paragraph(
            f"Audit Run ID: {payload.audit_run_id}<br/>"
            f"Report Generated: {generated_at}<br/>"
            f"Findings Identified: {payload.findings_count}",
            STYLE_COVER_META,
        )
    )
    elements.append(PageBreak())

    # --- Executive Summary ---
    elements.append(Paragraph("Executive Summary", STYLE_SECTION))
    summary_text = payload.ai_summary or "No summary available for this audit run."
    elements.append(Paragraph(summary_text, STYLE_SUMMARY_BOX))
    elements.append(Spacer(1, 0.4 * cm))

    score_rows = [
        ["TRUST SERVICE CRITERION", "SCORE"],
        ["Security", f"{round(score.security_score)} / 100"],
        ["Availability", f"{round(score.availability_score)} / 100"],
        ["Confidentiality", f"{round(score.confidentiality_score)} / 100"],
        ["Processing Integrity", f"{round(score.processing_integrity_score)} / 100"],
        ["Privacy", f"{round(score.privacy_score)} / 100"],
    ]
    score_table = Table(score_rows, colWidths=[11 * cm, 4 * cm])
    score_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Courier-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_MUTED),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTNAME", (1, 1), (1, -1), "Courier"),
                ("FONTSIZE", (0, 1), (-1, -1), 9.5),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LINEBELOW", (0, 0), (-1, -2), 0.5, COLOR_HAIRLINE),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    elements.append(score_table)
    elements.append(Spacer(1, 0.3 * cm))

    if score.blocking_issues_count > 0:
        plural = "s" if score.blocking_issues_count > 1 else ""
        verb = "were" if score.blocking_issues_count > 1 else "was"
        elements.append(
            Paragraph(
                f'<font color="#c43d32">{score.blocking_issues_count} critical-severity '
                f"finding{plural} {verb} identified during this audit run. Per audit "
                f'policy, any open critical finding precludes a "SOC2 Ready" '
                f"determination regardless of the overall numeric score.</font>",
                STYLE_SUMMARY_BOX,
            )
        )

    # --- Detailed Findings ---
    elements.append(PageBreak())
    elements.append(Paragraph("Detailed Findings", STYLE_SECTION))

    for f in payload.findings:
        elements.append(
            Paragraph(
                f"{f.control_id} &nbsp; {f.control_title} &nbsp; {_risk_tag_html(f.risk_level)}",
                STYLE_FINDING_HEADER,
            )
        )
        principle_label = f.trust_principle.replace("_", " ").title()
        elements.append(Paragraph(f"{f.rule_id} &middot; {principle_label}", STYLE_FINDING_RULE))
        elements.append(Paragraph("AUDITOR FINDING", STYLE_LABEL))
        elements.append(Paragraph(f.ai_explanation or "No explanation available.", STYLE_BODY))
        elements.append(Paragraph("REMEDIATION", STYLE_LABEL))
        elements.append(Paragraph(f.ai_remediation or "No remediation guidance available.", STYLE_BODY))
        elements.append(Spacer(1, 0.45 * cm))
        elements.append(HRFlowable(width="100%", color=COLOR_HAIRLINE, thickness=0.5))
        elements.append(Spacer(1, 0.3 * cm))

    # --- Evidence Appendix ---
    elements.append(PageBreak())
    elements.append(Paragraph("Appendix: Evidence Log References", STYLE_SECTION))
    elements.append(
        Paragraph(
            "The following evidence event identifiers correspond to normalized log "
            "entries that triggered each finding above. Full raw evidence is "
            "retained in the system's audit trail and available upon request.",
            STYLE_BODY,
        )
    )
    elements.append(Spacer(1, 0.3 * cm))

    for f in payload.findings:
        evidence_lines = "<br/>".join(f"- {eid}" for eid in f.evidence_event_ids) or "- (none)"
        elements.append(
            Paragraph(
                f"{f.control_id} ({f.rule_id}) — Evidence Event ID(s):<br/>{evidence_lines}",
                STYLE_EVIDENCE,
            )
        )
        elements.append(Spacer(1, 0.25 * cm))

    elements.append(
        Paragraph(
            "This report was generated by an automated SOC2 audit simulation system "
            "combining deterministic rule-based detection with AI-assisted narrative "
            "enrichment (Anthropic Claude). It is intended as a demonstration/portfolio "
            "artifact and does not constitute a formal SOC2 Type I or Type II audit "
            "opinion issued by a licensed CPA firm.",
            STYLE_DISCLAIMER,
        )
    )

    doc.build(elements)
    return buffer.getvalue()