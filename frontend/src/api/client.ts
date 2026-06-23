import type { UploadResponse, AnalysisResponse, SourceType } from "../types/api";

const API_BASE = "http://127.0.0.1:8001";

export class ApiError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
    this.name = "ApiError";
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // response wasn't JSON; keep statusText
    }
    throw new ApiError(detail, res.status);
  }
  return res.json();
}

export interface UploadFileEntry {
  file: File;
  sourceType: SourceType;
}

export async function uploadLogs(
  entries: UploadFileEntry[],
  companyName: string
): Promise<UploadResponse> {
  const formData = new FormData();
  for (const entry of entries) {
    formData.append("files", entry.file);
    formData.append("source_types", entry.sourceType);
  }
  formData.append("company_name", companyName);

  const res = await fetch(`${API_BASE}/upload-logs`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<UploadResponse>(res);
}

export async function analyzeCompliance(
  auditRunId: string
): Promise<AnalysisResponse> {
  const res = await fetch(`${API_BASE}/analyze-compliance/${auditRunId}`, {
    method: "POST",
  });
  return handleResponse<AnalysisResponse>(res);
}