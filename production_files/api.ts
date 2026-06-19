import * as fallback from "./data";
import { Alert, CrimeIncident, Hotspot, NetworkEdge, NetworkNode, Offender } from "./types";

export interface DashboardData {
  scale: typeof fallback.scale;
  incidents: CrimeIncident[];
  offenders: Offender[];
  hotspots: Hotspot[];
  alerts: Alert[];
  monthlyTrend: typeof fallback.monthlyTrend;
  districtStats: typeof fallback.districtStats;
  forecast: typeof fallback.forecast;
  networkNodes: NetworkNode[];
  networkEdges: NetworkEdge[];
  categoryBreakdown: typeof fallback.categoryBreakdown;
  cctvEvents: string[];
  patrolRoutes: typeof fallback.patrolRoutes;
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8001";
const TOKEN_KEY = "sentineliq.token";

export const fallbackDashboard: DashboardData = {
  scale: fallback.scale,
  incidents: fallback.incidents,
  offenders: fallback.offenders,
  hotspots: fallback.hotspots,
  alerts: fallback.alerts,
  monthlyTrend: fallback.monthlyTrend,
  districtStats: fallback.districtStats,
  forecast: fallback.forecast,
  networkNodes: fallback.networkNodes,
  networkEdges: fallback.networkEdges,
  categoryBreakdown: fallback.categoryBreakdown,
  cctvEvents: fallback.cctvEvents,
  patrolRoutes: fallback.patrolRoutes,
};

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem(TOKEN_KEY);
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  });
  if (!response.ok) {
    throw new Error(`SentinelIQ API ${response.status}: ${await response.text()}`);
  }
  return response.json() as Promise<T>;
}

export async function login(email = "admin@sentineliq.local", password = "SentinelIQ@123") {
  const params = new URLSearchParams();
  params.append("username", email);
  params.append("password", password);

  const response = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: params.toString(),
  });
  if (!response.ok) {
    throw new Error("Login failed");
  }
  const payload = await response.json() as { access_token: string; user: any };
  localStorage.setItem(TOKEN_KEY, payload.access_token);
  return payload.user;
}

export async function fetchDashboard(): Promise<DashboardData> {
  try {
    if (!localStorage.getItem(TOKEN_KEY)) {
      await login();
    }
    return await request<DashboardData>("/api/dashboard");
  } catch (error) {
    console.warn("Using SentinelIQ offline fallback data.", error);
    return fallbackDashboard;
  }
}

export async function naturalLanguageSearch(query: string) {
  return request<{ results: CrimeIncident[]; filters: Record<string, string> }>("/api/search", {
    method: "POST",
    body: JSON.stringify({ query }),
  });
}

export async function askCopilot(query: string) {
  return request<{ answer: string; sources: string[] }>("/api/copilot", {
    method: "POST",
    body: JSON.stringify({ query }),
  });
}

export async function downloadReport(format: "pdf" | "csv" | "xlsx") {
  const token = localStorage.getItem(TOKEN_KEY);
  const response = await fetch(`${API_BASE}/api/reports/export.${format}`, {
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
  if (!response.ok) throw new Error("Export failed");
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `sentineliq-crimes.${format === "xlsx" ? "xlsx" : format}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
}

export interface DatasetHistory {
  id: string;
  filename: string;
  uploaded_at: string;
  record_count: number;
  status: string;
  uploaded_by_name: string;
}

export interface DatasetUploadSummary {
  records_uploaded: number;
  valid_records: number;
  duplicates_removed: number;
  districts_updated: number;
  hotspots_recalculated: number;
  processing_time: string;
}

export async function uploadDataset(file: File): Promise<DatasetUploadSummary> {
  const token = localStorage.getItem(TOKEN_KEY);
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/api/datasets/upload`, {
    method: "POST",
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: formData,
  });
  if (!response.ok) {
    throw new Error(`Upload failed: ${await response.text()}`);
  }
  return response.json();
}

export async function fetchDatasetHistory(): Promise<DatasetHistory[]> {
  return request<DatasetHistory[]>("/api/datasets/history");
}
