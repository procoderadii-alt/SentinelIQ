export type Risk = "Low" | "Medium" | "High" | "Critical";
export type AlertLevel = "Green" | "Yellow" | "Orange" | "Red";

export interface CrimeIncident {
  id: string;
  fir: string;
  type: string;
  category: string;
  severity: Risk;
  status: "Open" | "Under Investigation" | "Solved" | "Escalated";
  district: string;
  station: string;
  lat: number;
  lng: number;
  datetime: string;
  victim: string;
  suspect: string;
  evidence: number;
}

export interface Offender {
  id: string;
  name: string;
  gang: string;
  riskScore: number;
  arrests: number;
  lastActivity: string;
  area: string;
  probability: number;
}

export interface Alert {
  id: string;
  title: string;
  level: AlertLevel;
  reason: string;
  confidence: number;
  action: string;
}

export interface Hotspot {
  id: string;
  name: string;
  district: string;
  lat: number;
  lng: number;
  score: number;
  confidence: number;
  category: Risk;
  why: string;
  incidents: number;
}

export interface NetworkNode {
  id: string;
  label: string;
  type: "Criminal" | "Gang" | "Vehicle" | "Phone" | "Location" | "Case";
  x: number;
  y: number;
  weight: number;
}

export interface NetworkEdge {
  source: string;
  target: string;
  strength: number;
}
