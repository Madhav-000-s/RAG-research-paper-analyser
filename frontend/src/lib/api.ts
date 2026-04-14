import type { Paper, QueryRequest, QueryResponse, Conversation } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res.json();
}

export async function uploadPaper(file: File): Promise<Paper> {
  const formData = new FormData();
  formData.append("file", file);
  return fetchJSON<Paper>(`${BASE}/papers`, {
    method: "POST",
    body: formData,
  });
}

export async function fetchPapers(status?: string): Promise<Paper[]> {
  const params = status ? `?status=${status}` : "";
  return fetchJSON<Paper[]>(`${BASE}/papers${params}`);
}

export async function fetchPaper(paperId: string): Promise<Paper> {
  return fetchJSON<Paper>(`${BASE}/papers/${paperId}`);
}

export function getPaperPdfUrl(paperId: string): string {
  return `${BASE}/papers/${paperId}/pdf`;
}

export async function askQuestion(req: QueryRequest): Promise<QueryResponse> {
  return fetchJSON<QueryResponse>(`${BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
}

export async function fetchConversation(id: string): Promise<Conversation> {
  return fetchJSON<Conversation>(`${BASE}/conversations/${id}`);
}
