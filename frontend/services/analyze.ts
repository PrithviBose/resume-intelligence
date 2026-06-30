import { apiRequest, endpoints } from "./api";
import type { AnalysisResult } from "./types";

export function analyzeResume(file: File): Promise<AnalysisResult> {
  const formData = new FormData();
  formData.append("file", file);

  return apiRequest<AnalysisResult>(endpoints.analyze, {
    method: "POST",
    body: formData,
  });
}
