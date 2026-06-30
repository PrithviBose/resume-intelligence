import { apiRequest, endpoints } from "./api";
import type { HealthResponse } from "./types";

export function getHealth(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>(endpoints.health);
}
