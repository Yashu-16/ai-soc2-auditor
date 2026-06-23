import { useState } from "react";
import type { AnalysisResponse } from "./types/api";
import type { UploadFileEntry } from "./api/client";
import { uploadLogs, analyzeCompliance, downloadAuditReport, ApiError } from "./api/client";
import { LogUploader } from "./components/LogUploader";
import { ScoreGauge } from "./components/ScoreGauge";
import { PrincipleBreakdown } from "./components/PrincipleBreakdown";
import { AiSummaryPanel } from "./components/AiSummaryPanel";
import { FindingRow } from "./components/FindingRow";

type Phase = "idle" | "uploading" | "analyzing" | "done" | "error";

function App() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);

  const handleSubmit = async (entries: UploadFileEntry[], companyName: string) => {
    setErrorMsg(null);
    try {
      setPhase("uploading");
      const uploadRes = await uploadLogs(entries, companyName);

      setPhase("analyzing");
      const analysis = await analyzeCompliance(uploadRes.audit_run_id);

      setResult(analysis);
      setPhase("done");
    } catch (err) {
      setPhase("error");
      setErrorMsg(err instanceof ApiError ? err.message : "Unexpected error occurred.");
    }
  };

  const handleDownloadReport = async () => {
    if (!result) return;
    setIsDownloading(true);
    try {
      await downloadAuditReport(result);
    } catch (err) {
      setErrorMsg(err instanceof ApiError ? err.message : "Failed to generate report.");
    } finally {
      setIsDownloading(false);
    }
  };

  const sortedFindings = result
    ? [...result.findings].sort((a, b) => riskRank(b.risk_level) - riskRank(a.risk_level))
    : [];

  return (
    <div style={{ minHeight: "100vh", padding: "2.5rem 2rem" }}>
      <div style={{ maxWidth: "880px", margin: "0 auto" }}>
        <Masthead />

        {phase !== "done" && (
          <div style={{ marginTop: "2rem" }}>
            <LogUploader onSubmit={handleSubmit} isLoading={phase === "uploading" || phase === "analyzing"} />
            {phase === "analyzing" && (
              <p style={statusTextStyle}>Running rule engine and AI enrichment…</p>
            )}
            {phase === "error" && errorMsg && (
              <p style={{ ...statusTextStyle, color: "var(--risk-critical)" }}>{errorMsg}</p>
            )}
          </div>
        )}

        {phase === "done" && result && (
          <div style={{ marginTop: "2rem", display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <div
              style={{
                display: "flex",
                gap: "2.5rem",
                background: "var(--bg-panel)",
                border: "1px solid var(--border-hairline)",
                borderRadius: "6px",
                padding: "1.75rem",
                alignItems: "center",
              }}
            >
              <ScoreGauge score={result.score.overall_score} isReady={result.score.is_soc2_ready} />
              <div style={{ flex: 1 }}>
                <PrincipleBreakdown score={result.score} />
              </div>
            </div>

            {result.score.blocking_issues_count > 0 && (
              <div
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.8rem",
                  color: "var(--risk-critical)",
                  background: "rgba(232, 72, 60, 0.08)",
                  border: "1px solid var(--risk-critical)",
                  borderRadius: "4px",
                  padding: "0.7rem 1rem",
                }}
              >
                {result.score.blocking_issues_count} blocking critical finding
                {result.score.blocking_issues_count > 1 ? "s" : ""} preventing SOC2 readiness,
                regardless of overall score.
              </div>
            )}

            <AiSummaryPanel summary={result.ai_summary} />

            <div>
              <div
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.7rem",
                  letterSpacing: "0.08em",
                  textTransform: "uppercase",
                  color: "var(--text-secondary)",
                  marginBottom: "0.75rem",
                }}
              >
                Findings ({result.findings_count})
              </div>
              {sortedFindings.map((f) => (
                <FindingRow key={f.id} finding={f} />
              ))}
            </div>

            <div style={{ display: "flex", gap: "0.75rem" }}>
              <button
                onClick={handleDownloadReport}
                disabled={isDownloading}
                style={{
                  background: isDownloading ? "var(--border-hairline)" : "var(--ai-accent)",
                  color: isDownloading ? "var(--text-tertiary)" : "#0b0e14",
                  border: "none",
                  borderRadius: "4px",
                  padding: "0.6rem 1.1rem",
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.78rem",
                  fontWeight: 600,
                  cursor: isDownloading ? "not-allowed" : "pointer",
                }}
              >
                {isDownloading ? "GENERATING…" : "↓ Generate Audit Report"}
              </button>

              <button
                onClick={() => {
                  setPhase("idle");
                  setResult(null);
                }}
                style={{
                  background: "none",
                  border: "1px solid var(--border-hairline)",
                  color: "var(--text-secondary)",
                  borderRadius: "4px",
                  padding: "0.6rem 1.1rem",
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.78rem",
                  cursor: "pointer",
                }}
              >
                ← Run another audit
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Masthead() {
  return (
    <div style={{ borderBottom: "1px solid var(--border-hairline)", paddingBottom: "1.25rem" }}>
      <div
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: "0.7rem",
          letterSpacing: "0.1em",
          color: "var(--text-tertiary)",
          textTransform: "uppercase",
        }}
      >
        AI SOC2 Auditor
      </div>
      <h1
        style={{
          margin: "0.35rem 0 0",
          fontFamily: "var(--font-sans)",
          fontSize: "1.6rem",
          fontWeight: 700,
          color: "var(--text-primary)",
        }}
      >
        Compliance Audit Console
      </h1>
    </div>
  );
}

const statusTextStyle: React.CSSProperties = {
  marginTop: "1rem",
  fontFamily: "var(--font-mono)",
  fontSize: "0.8rem",
  color: "var(--text-secondary)",
};

function riskRank(level: string): number {
  const order: Record<string, number> = { critical: 3, high: 2, medium: 1, low: 0 };
  return order[level] ?? 0;
}

export default App;