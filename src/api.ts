import { Alert, CrimeIncident, Hotspot, NetworkEdge, NetworkNode, Offender } from "./types";

export interface DashboardData {
  scale: { crimeRecords: number; offenders: number; alerts: number };
  incidents: CrimeIncident[];
  offenders: Offender[];
  hotspots: Hotspot[];
  alerts: Alert[];
  monthlyTrend: { month: string; theft: number; cyber: number; solved: number }[];
  districtStats: { district: string; crimes: number; rate: number; patrol: number; arrestRate: number }[];
  forecast: { area: string; risk: string; predicted: number; trend: string; horizon: string; low: number; high: number; confidence: number }[];
  networkNodes: NetworkNode[];
  networkEdges: NetworkEdge[];
  categoryBreakdown: { name: string; value: number }[];
  cctvEvents: string[];
  patrolRoutes: { route: string; area: string; coverage: number; eta: string }[];
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`SentinelIQ API ${response.status}: ${await response.text()}`);
  }
  return response.json() as Promise<T>;
}

export async function fetchDashboard(): Promise<DashboardData> {
  return request<DashboardData>("/api/dashboard");
}

export async function fetchIncidents(query: string = ""): Promise<CrimeIncident[]> {
  const url = query ? `/api/crimes?q=${encodeURIComponent(query)}&limit=100` : `/api/crimes?limit=100`;
  return request<CrimeIncident[]>(url);
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
  missing_values: number;
  anomalies_detected: number;
  data_quality_score: number;
  districts_updated: number;
  hotspots_recalculated: number;
  processing_time: string;
}

export async function uploadDataset(file: File): Promise<DatasetUploadSummary> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/api/datasets/upload`, {
    method: "POST",
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

export async function downloadReport(format: string): Promise<Blob> {
  const response = await fetch(`${API_BASE}/api/reports/export.${format}`);
  if (!response.ok) throw new Error("Report download failed");
  return response.blob();
}
