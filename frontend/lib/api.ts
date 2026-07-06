import type { ParseResult, QueryResult, SearchResult, UsersListResponse } from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export async function parseResume(file: File): Promise<ParseResult> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/parse`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    const detail =
      typeof error?.detail === "string"
        ? error.detail
        : "Failed to parse resume";
    throw new Error(detail);
  }

  return response.json();
}

export async function searchResume(
  resumeId: string,
  query: string,
  topK = 3,
): Promise<SearchResult> {
  const response = await fetch(`${API_BASE_URL}/api/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      resume_id: resumeId,
      query,
      top_k: topK,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    const detail =
      typeof error?.detail === "string"
        ? error.detail
        : "Failed to search resume";
    throw new Error(detail);
  }

  return response.json();
}

export async function fetchUsers(): Promise<UsersListResponse> {
  const response = await fetch(`${API_BASE_URL}/api/users`);

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    const detail =
      typeof error?.detail === "string"
        ? error.detail
        : "Failed to load candidates";
    throw new Error(detail);
  }

  return response.json();
}

export async function queryResume(
  resumeId: string,
  query: string,
  userName?: string | null,
  topK = 3,
): Promise<QueryResult> {
  const response = await fetch(`${API_BASE_URL}/api/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      resume_id: resumeId,
      query,
      user_name: userName ?? null,
      top_k: topK,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    const detail =
      typeof error?.detail === "string"
        ? error.detail
        : "Failed to answer question";
    throw new Error(detail);
  }

  return response.json();
}
