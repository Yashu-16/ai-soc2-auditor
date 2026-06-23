export function AiSummaryPanel({ summary }: { summary: string | null }) {
    if (!summary) return null;
  
    return (
      <div
        style={{
          background: "var(--bg-panel)",
          border: "1px solid var(--border-hairline)",
          borderLeft: "3px solid var(--ai-accent)",
          borderRadius: "6px",
          padding: "1.25rem 1.5rem",
        }}
      >
        <div
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "0.7rem",
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            color: "var(--ai-accent)",
            marginBottom: "0.6rem",
          }}
        >
          AI Audit Summary
        </div>
        <p
          style={{
            margin: 0,
            fontSize: "0.92rem",
            lineHeight: 1.65,
            color: "var(--text-primary)",
          }}
        >
          {summary}
        </p>
      </div>
    );
  }