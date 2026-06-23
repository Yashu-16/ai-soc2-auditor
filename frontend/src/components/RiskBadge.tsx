import type { RiskLevel } from "../types/api";

const RISK_CONFIG: Record<RiskLevel, { label: string; color: string }> = {
  critical: { label: "CRITICAL", color: "var(--risk-critical)" },
  high: { label: "HIGH", color: "var(--risk-high)" },
  medium: { label: "MEDIUM", color: "var(--risk-medium)" },
  low: { label: "LOW", color: "var(--risk-low)" },
};

export function RiskBadge({ level }: { level: RiskLevel }) {
  const config = RISK_CONFIG[level];
  return (
    <span
      style={{
        fontFamily: "var(--font-mono)",
        fontSize: "0.7rem",
        fontWeight: 700,
        letterSpacing: "0.06em",
        color: config.color,
        border: `1px solid ${config.color}`,
        borderRadius: "3px",
        padding: "2px 7px",
        whiteSpace: "nowrap",
      }}
    >
      {config.label}
    </span>
  );
}