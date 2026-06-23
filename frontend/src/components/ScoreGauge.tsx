interface ScoreGaugeProps {
    score: number;
    isReady: boolean;
  }
  
  export function ScoreGauge({ score, isReady }: ScoreGaugeProps) {
    const radius = 70;
    const circumference = Math.PI * radius; // semicircle arc length
    const pct = Math.max(0, Math.min(100, score)) / 100;
    const dashOffset = circumference * (1 - pct);
  
    const arcColor =
      score >= 80 ? "var(--risk-none)" : score >= 60 ? "var(--risk-medium)" : "var(--risk-critical)";
  
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "0.5rem" }}>
        <svg width="180" height="100" viewBox="0 0 180 100">
          <path
            d="M 20 90 A 70 70 0 0 1 160 90"
            fill="none"
            stroke="var(--border-hairline)"
            strokeWidth="10"
            strokeLinecap="round"
          />
          <path
            d="M 20 90 A 70 70 0 0 1 160 90"
            fill="none"
            stroke={arcColor}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            style={{ transition: "stroke-dashoffset 0.6s ease, stroke 0.6s ease" }}
          />
          <text
            x="90"
            y="78"
            textAnchor="middle"
            fontFamily="var(--font-mono)"
            fontSize="34"
            fontWeight="700"
            fill="var(--text-primary)"
          >
            {Math.round(score)}
          </text>
        </svg>
        <div
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "0.75rem",
            letterSpacing: "0.08em",
            color: isReady ? "var(--risk-none)" : "var(--risk-critical)",
            fontWeight: 600,
          }}
        >
          {isReady ? "SOC2 READY" : "NOT READY"}
        </div>
      </div>
    );
  }