import { Alert, AlertLevel, CrimeIncident, Hotspot, NetworkEdge, NetworkNode, Offender, Risk } from "./types";

const crimeTypes = ["Theft", "Assault", "Robbery", "Cybercrime", "Drug Case", "Missing Person", "Fraud", "Extortion"];
const statuses: CrimeIncident["status"][] = ["Open", "Under Investigation", "Solved", "Escalated"];
const risks: Risk[] = ["Low", "Medium", "High", "Critical"];
const districts = [
  "Pune Central",
  "Shivajinagar",
  "Kothrud",
  "Hadapsar",
  "Hinjawadi",
  "Wakad",
  "Kondhwa",
  "Aundh",
  "Viman Nagar",
  "Yerawada",
  "Baner",
  "Swargate",
];
const stations = ["Alpha PS", "Market PS", "Cyber Cell", "East Division", "Metro Unit", "Special Branch"];

function mulberry32(seed: number) {
  return () => {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const random = mulberry32(42);
const pick = <T,>(items: T[]) => items[Math.floor(random() * items.length)];
const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(max, value));

export const scale = {
  crimeRecords: 50000,
  offenders: 5000,
  gangs: 500,
  districts: 100,
  networkConnections: 100000,
};

export const incidents: CrimeIncident[] = Array.from({ length: 420 }, (_, index) => {
  const district = pick(districts);
  const type = pick(crimeTypes);
  const severity = pick(risks);
  const dayOffset = Math.floor(random() * 120);
  const date = new Date(Date.now() - dayOffset * 86400000 - random() * 86400000);
  const centerLat = 18.5204 + (districts.indexOf(district) - 5) * 0.012;
  const centerLng = 73.8567 + (districts.indexOf(district) % 5) * 0.018;
  return {
    id: `CR-${String(240000 + index).padStart(6, "0")}`,
    fir: `FIR/${2026}/${String(1000 + index)}`,
    type,
    category: type,
    severity,
    status: pick(statuses),
    district,
    station: pick(stations),
    lat: centerLat + (random() - 0.5) * 0.08,
    lng: centerLng + (random() - 0.5) * 0.08,
    datetime: date.toISOString(),
    victim: `Victim ${index + 1}`,
    suspect: random() > 0.28 ? `Suspect ${Math.floor(random() * 5000)}` : "Unknown",
    evidence: Math.floor(random() * 8),
  };
});

export const offenders: Offender[] = Array.from({ length: 32 }, (_, index) => ({
  id: `OF-${String(index + 1).padStart(4, "0")}`,
  name: ["Arjun Kale", "Rafiq Shaikh", "Nilesh Pawar", "Vikram Joshi", "Sameer Khan", "Prakash More"][index % 6] + ` ${index + 1}`,
  gang: `Cell-${String.fromCharCode(65 + (index % 9))}`,
  riskScore: clamp(Math.round(48 + random() * 55), 1, 100),
  arrests: Math.floor(1 + random() * 18),
  lastActivity: new Date(Date.now() - random() * 45 * 86400000).toISOString(),
  area: pick(districts),
  probability: clamp(Math.round(35 + random() * 64), 1, 99),
}));

export const hotspots: Hotspot[] = districts.slice(0, 10).map((district, index) => {
  const score = Math.round(42 + random() * 57);
  return {
    id: `HS-${index + 1}`,
    name: `${district} Corridor`,
    district,
    lat: 18.5204 + (index - 4) * 0.018,
    lng: 73.8567 + (index % 5) * 0.023,
    score,
    confidence: Math.round(74 + random() * 22),
    category: score > 86 ? "Critical" : score > 72 ? "High" : score > 55 ? "Medium" : "Low",
    why: "Night activity, repeat FIR geography, and unresolved suspect overlap increased the zone score.",
    incidents: Math.round(90 + random() * 420),
  };
});

export const alerts: Alert[] = [
  {
    id: "AL-01",
    title: "Robbery spike near transit exits",
    level: "Red",
    reason: "7-day robbery volume is 2.8x the district baseline after 21:00.",
    confidence: 94,
    action: "Deploy two mobile patrol units and query repeat offenders within 3 km.",
  },
  {
    id: "AL-02",
    title: "Cyber fraud cluster emerging",
    level: "Orange",
    reason: "Common phone and payment handles appear across 18 FIR narratives.",
    confidence: 88,
    action: "Freeze linked accounts, prioritize cyber-cell triage, and issue public advisory.",
  },
  {
    id: "AL-03",
    title: "Drug case displacement",
    level: "Yellow",
    reason: "Incidents moved from known hotspot into adjacent residential beat.",
    confidence: 81,
    action: "Shift patrol window by 90 minutes and inspect CCTV routes.",
  },
  {
    id: "AL-04",
    title: "Assault activity normalizing",
    level: "Green",
    reason: "Weekend assault count returned within expected confidence interval.",
    confidence: 73,
    action: "Maintain baseline coverage and monitor event venues.",
  },
];

export const monthlyTrend = Array.from({ length: 12 }, (_, index) => ({
  month: new Date(2025, index, 1).toLocaleString("en", { month: "short" }),
  theft: Math.round(420 + Math.sin(index / 1.6) * 90 + random() * 95),
  assault: Math.round(260 + Math.cos(index / 1.7) * 60 + random() * 70),
  cyber: Math.round(180 + index * 18 + random() * 65),
  solved: Math.round(520 + index * 12 + random() * 80),
}));

export const districtStats = districts.map((district, index) => ({
  district,
  crimes: Math.round(2400 + random() * 7200),
  rate: Number((22 + random() * 61).toFixed(1)),
  arrestRate: Math.round(36 + random() * 46),
  patrol: Math.round(58 + random() * 38),
  hotspots: Math.round(2 + random() * 12),
  income: Math.round(28000 + random() * 72000),
  literacy: Math.round(62 + random() * 33),
  unemployment: Number((3 + random() * 15).toFixed(1)),
  theftIndex: Math.round(40 + random() * 58 + index * 1.8),
}));

export const forecast = [
  { horizon: "7 Days", predicted: 824, low: 760, high: 892, confidence: 91 },
  { horizon: "30 Days", predicted: 3510, low: 3220, high: 3844, confidence: 86 },
  { horizon: "90 Days", predicted: 10580, low: 9700, high: 11720, confidence: 79 },
];

const nodeTypes: NetworkNode["type"][] = ["Criminal", "Gang", "Vehicle", "Phone", "Location", "Case"];
export const networkNodes: NetworkNode[] = Array.from({ length: 34 }, (_, index) => ({
  id: `N-${index}`,
  label: index < 8 ? offenders[index].name.split(" ").slice(0, 2).join(" ") : `${pick(nodeTypes)} ${index}`,
  type: index < 8 ? "Criminal" : pick(nodeTypes),
  x: 50 + Math.cos(index * 0.83) * (95 + (index % 5) * 20),
  y: 50 + Math.sin(index * 0.83) * (72 + (index % 7) * 18),
  weight: Math.round(3 + random() * 17),
}));

export const networkEdges: NetworkEdge[] = Array.from({ length: 54 }, (_, index) => ({
  source: networkNodes[index % networkNodes.length].id,
  target: networkNodes[(index * 7 + 5) % networkNodes.length].id,
  strength: Math.round(20 + random() * 78),
}));

export const categoryBreakdown = crimeTypes.slice(0, 6).map((name) => ({
  name,
  value: incidents.filter((incident) => incident.type === name).length + Math.round(random() * 500),
}));

export const cctvEvents = [
  "Face match near Viman Nagar camera C-44",
  "Unregistered vehicle convoy detected on Baner Road",
  "Crowd density threshold breached at market junction",
  "Suspicious loitering event matched to open FIR",
];

export const patrolRoutes = hotspots.slice(0, 5).map((hotspot, index) => ({
  route: `Route ${index + 1}`,
  area: hotspot.name,
  coverage: Math.round(72 + random() * 24),
  eta: `${Math.round(12 + random() * 18)} min`,
}));

export const alertColor: Record<AlertLevel | Risk, string> = {
  Green: "text-emerald-300 bg-emerald-400/12 border-emerald-400/30",
  Yellow: "text-yellow-200 bg-yellow-400/12 border-yellow-400/30",
  Orange: "text-orange-200 bg-orange-400/12 border-orange-400/30",
  Red: "text-rose-200 bg-rose-400/12 border-rose-400/30",
  Low: "text-emerald-300 bg-emerald-400/12 border-emerald-400/30",
  Medium: "text-yellow-200 bg-yellow-400/12 border-yellow-400/30",
  High: "text-orange-200 bg-orange-400/12 border-orange-400/30",
  Critical: "text-rose-200 bg-rose-400/12 border-rose-400/30",
};
