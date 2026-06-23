// Mirrors backend/app/schemas/schemas.py — keep these in sync manually
// for this MVP scope (no codegen pipeline; documented as a known
// improvement opportunity for a v2).

export type RiskLevel = "low" | "medium" | "high" | "critical";

export type SourceType =
  | "iam_log"
  | "cloudtrail_log"
  | "cloud_config"
  | "github_activity";

export interface UploadResponse {
  audit_run_id: string;
  files_received: number;
  events_normalized: number;
  source_types: string[];
}

export interface ScoreBreakdown {
  overall_score: number;
  security_score: number;
  availability_score: number;
  confidentiality_score: number;
  processing_integrity_score: number;
  privacy_score: number;
  is_soc2_ready: boolean;
  blocking_issues_count: number;
}

export interface FindingResponse {
  id: string;
  control_id: string;
  control_title: string;
  trust_principle: string;
  rule_id: string;
  risk_level: RiskLevel;
  evidence_event_ids: string[];
  ai_explanation: string | null;
  ai_remediation: string | null;
  ai_confidence: number | null;
}

export interface AnalysisResponse {
  audit_run_id: string;
  company_name: string;
  findings_count: number;
  ai_summary: string | null;
  score: ScoreBreakdown;
  findings: FindingResponse[];
}