import { useState } from "react";
import type { FindingResponse } from "../types/api";
import { RiskBadge } from "./RiskBadge";

const RISK_BORDER: Record<string, string> = {
  critical: "var(--risk-critical)",
  high: "var(--risk-high)",
  medium: "var(--risk-medium)",
  low: "var(--risk-low)",
};

export function FindingRow({ finding }: { finding: FindingResponse }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      style={{
        display: "flex",
        borderLeft: `3px solid ${RISK_BORDER[finding.risk_level]}`,
        background: "var(--bg-panel)",
        marginBottom: "0.6rem",
      }}
    >
      <button
        onClick={() => setExpanded((e) => !e)}
        style={{
          width: "100%",
          textAlign: "left",
          background: "none",
          border: "none",
          color: "inherit",
          cursor: "pointer",
          padding: "0.9rem 1.1rem",
        }}
        aria-expanded={expanded}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.85rem" }}>
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "0.78rem",
              color: "var(--text-secondary)",
              minWidth: "58px",
            }}
          >
            {finding.control_id}
          </span>
          <RiskBadge level={finding.risk_level} />
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "0.72rem",
              color: "var(--text-tertiary)",
            }}
          >
            {finding.rule_id}
          </span>
          <span
            style={{
              marginLeft: "auto",
              fontSize: "0.75rem",
              color: "var(--text-tertiary)",
              fontFamily: "var(--font-mono)",
            }}
          >
            {expanded ? "▾ hide" : "▸ details"}
          </span>
        </div>

        {expanded && (
          <div style={{ marginTop: "0.9rem", display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            <div>
              <Label aiSourced>Auditor Finding</Label>
              <p style={{ margin: "0.3rem 0 0", fontSize: "0.88rem", lineHeight: 1.55, color: "var(--text-primary)" }}>
                {finding.ai_explanation ?? "No explanation available."}
              </p>
            </div>
            <div>
              <Label aiSourced>Remediation</Label>
              <p style={{ margin: "0.3rem 0 0", fontSize: "0.88rem", lineHeight: 1.55, color: "var(--text-primary)" }}>
                {finding.ai_remediation ?? "No remediation guidance available."}
              </p>
            </div>
            <div style={{ display: "flex", gap: "1.5rem", fontSize: "0.75rem", color: "var(--text-tertiary)", fontFamily: "var(--font-mono)" }}>
              {finding.ai_confidence !== null && (
                <span>confidence: {(finding.ai_confidence * 100).toFixed(0)}%</span>
              )}
              <span>evidence: {finding.evidence_event_ids.length} event(s)</span>
            </div>
          </div>
        )}
      </button>
    </div>
  );
}

function Label({ children, aiSourced }: { children: React.ReactNode; aiSourced?: boolean }) {
  return (
    <span
      style={{
        fontFamily: "var(--font-mono)",
        fontSize: "0.68rem",
        letterSpacing: "0.08em",
        textTransform: "uppercase",
        color: aiSourced ? "var(--ai-accent)" : "var(--text-secondary)",
      }}
    >
      {children}
    </span>
  );
}