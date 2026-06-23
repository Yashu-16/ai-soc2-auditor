import { useState } from "react";
import type { SourceType } from "../types/api";
import type { UploadFileEntry } from "../api/client";

const SOURCE_LABELS: { key: SourceType; label: string }[] = [
  { key: "iam_log", label: "IAM / Access Logs" },
  { key: "cloudtrail_log", label: "CloudTrail Logs" },
  { key: "cloud_config", label: "Cloud Config (Terraform-like JSON)" },
  { key: "github_activity", label: "GitHub Activity" },
];

interface LogUploaderProps {
  onSubmit: (entries: UploadFileEntry[], companyName: string) => void;
  isLoading: boolean;
}

export function LogUploader({ onSubmit, isLoading }: LogUploaderProps) {
  const [files, setFiles] = useState<Partial<Record<SourceType, File>>>({});
  const [companyName, setCompanyName] = useState("Demo SaaS Co");

  const handleFileChange = (sourceType: SourceType, file: File | null) => {
    setFiles((prev) => {
      const next = { ...prev };
      if (file) next[sourceType] = file;
      else delete next[sourceType];
      return next;
    });
  };

  const entries: UploadFileEntry[] = Object.entries(files).map(([sourceType, file]) => ({
    sourceType: sourceType as SourceType,
    file: file as File,
  }));

  return (
    <div
      style={{
        background: "var(--bg-panel)",
        border: "1px solid var(--border-hairline)",
        borderRadius: "6px",
        padding: "1.5rem",
      }}
    >
      <div style={{ marginBottom: "1.25rem" }}>
        <label style={fieldLabelStyle}>Company Name</label>
        <input
          type="text"
          value={companyName}
          onChange={(e) => setCompanyName(e.target.value)}
          style={textInputStyle}
        />
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "0.9rem" }}>
        {SOURCE_LABELS.map(({ key, label }) => (
          <div key={key}>
            <label style={fieldLabelStyle}>{label}</label>
            <input
              type="file"
              accept=".json"
              onChange={(e) => handleFileChange(key, e.target.files?.[0] ?? null)}
              style={fileInputStyle}
            />
          </div>
        ))}
      </div>

      <button
        onClick={() => onSubmit(entries, companyName)}
        disabled={entries.length === 0 || isLoading}
        style={{
          marginTop: "1.5rem",
          width: "100%",
          padding: "0.75rem",
          background: entries.length === 0 || isLoading ? "var(--border-hairline)" : "var(--ai-accent)",
          color: entries.length === 0 || isLoading ? "var(--text-tertiary)" : "#0b0e14",
          border: "none",
          borderRadius: "4px",
          fontFamily: "var(--font-mono)",
          fontSize: "0.85rem",
          fontWeight: 600,
          letterSpacing: "0.03em",
          cursor: entries.length === 0 || isLoading ? "not-allowed" : "pointer",
        }}
      >
        {isLoading ? "UPLOADING…" : "UPLOAD & RUN AUDIT"}
      </button>
    </div>
  );
}

const fieldLabelStyle: React.CSSProperties = {
  display: "block",
  fontFamily: "var(--font-mono)",
  fontSize: "0.7rem",
  letterSpacing: "0.06em",
  textTransform: "uppercase",
  color: "var(--text-secondary)",
  marginBottom: "0.4rem",
};

const textInputStyle: React.CSSProperties = {
  width: "100%",
  padding: "0.55rem 0.7rem",
  background: "var(--bg-panel-raised)",
  border: "1px solid var(--border-hairline)",
  borderRadius: "4px",
  color: "var(--text-primary)",
  fontFamily: "var(--font-sans)",
  fontSize: "0.85rem",
};

const fileInputStyle: React.CSSProperties = {
  width: "100%",
  padding: "0.4rem",
  background: "var(--bg-panel-raised)",
  border: "1px solid var(--border-hairline)",
  borderRadius: "4px",
  color: "var(--text-secondary)",
  fontSize: "0.8rem",
};