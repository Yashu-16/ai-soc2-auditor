import type { ScoreBreakdown } from "../types/api";

const PRINCIPLES: { key: keyof ScoreBreakdown; label: string }[] = [
  { key: "security_score", label: "Security" },
  { key: "availability_score", label: "Availability" },
  { key: "confidentiality_score", label: "Confidentiality" },
  { key: "processing_integrity_score", label: "Processing Integrity" },
  { key: "privacy_score", label: "Privacy" },
];

function barColor(score: number): string {
  if (score >= 80) return "var(--risk-none)";
  if (score >= 60) return "var(--risk-medium)";
  return "var(--risk-critical)";
}

export function PrincipleBreakdown({ score }: { score: ScoreBreakdown }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.85rem" }}>
      {PRINCIPLES.map(({ key, label }) => {
        const value = score[key] as number;
        return (
          <div key={key} style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <div
              style={{
                width: "150px",
                fontSize: "0.8rem",
                color: "var(--text-secondary)",
                fontFamily: "var(--font-sans)",
              }}
            >
              {label}
            </div>
            <div
              style={{
                flex: 1,
                height: "6px",
                background: "var(--border-hairline)",
                borderRadius: "3px",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  width: `${Math.max(0, Math.min(100, value))}%`,
                  height: "100%",
                  background: barColor(value),
                  transition: "width 0.5s ease",
                }}
              />
            </div>
            <div
              style={{
                width: "32px",
                textAlign: "right",
                fontFamily: "var(--font-mono)",
                fontSize: "0.8rem",
                color: "var(--text-primary)",
              }}
            >
              {Math.round(value)}
            </div>
          </div>
        );
      })}
    </div>
  );
}