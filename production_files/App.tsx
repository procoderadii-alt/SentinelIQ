import {
  Activity,
  AlertTriangle,
  BadgeCheck,
  BarChart3,
  Bot,
  BrainCircuit,
  Camera,
  Car,
  CircleDot,
  Database,
  Download,
  FileSearch,
  Filter,
  Layers,
  MapPin,
  Moon,
  Network,
  Radio,
  Search,
  ShieldAlert,
  Siren,
  Sun,
  Users,
  UploadCloud,
} from "lucide-react";
import { motion } from "framer-motion";
import { CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { alertColor } from "./data";
import { DashboardData, fallbackDashboard, fetchDashboard, naturalLanguageSearch, askCopilot, downloadReport, login, uploadDataset, fetchDatasetHistory, DatasetHistory, DatasetUploadSummary } from "./api";
import { CrimeIncident } from "./types";

const modules = [
  "Overview",
  "Incidents",
  "GIS Map",
  "Hotspots",
  "District Intel",
  "Alerts",
  "Network",
  "Offenders",
  "Socio-Economic",
  "Forecasting",
  "Patterns",
  "Command Center",
  "CCTV",
  "Investigation",
  "Patrol",
  "Search",
  "Reports",
  "AI Copilot",
  "Dataset Management",
];

const colors = ["#38d9c7", "#f4c95d", "#ff5c77", "#7dd3fc", "#a78bfa", "#34d399"];
const DashboardContext = createContext<DashboardData>(fallbackDashboard);

function useDashboard() {
  return useContext(DashboardContext);
}

function fmt(value: number) {
  return new Intl.NumberFormat("en-IN").format(value);
}

function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <section className={`panel ${className}`}>{children}</section>;
}

function ModuleHeader({ icon: Icon, title, subtitle }: { icon: typeof Activity; title: string; subtitle: string }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <div>
        <div className="flex items-center gap-2 text-cyanline">
          <Icon size={18} />
          <span className="text-xs uppercase tracking-[0.24em]">{title}</span>
        </div>
        <h2 className="mt-2 text-xl font-semibold text-slate-50">{subtitle}</h2>
      </div>
      <span className="rounded border border-cyanline/30 px-3 py-1 text-xs text-cyanline">Live model</span>
    </div>
  );
}

function Kpi({ icon: Icon, label, value, delta }: { icon: typeof Activity; label: string; value: string; delta: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="panel min-h-[118px]"
    >
      <div className="flex items-start justify-between">
        <div className="grid size-10 place-items-center rounded border border-cyanline/30 bg-cyanline/10 text-cyanline">
          <Icon size={19} />
        </div>
        <span className="text-xs text-emerald-300">{delta}</span>
      </div>
      <p className="mt-4 text-2xl font-semibold text-white">{value}</p>
      <p className="text-sm text-slate-400">{label}</p>
    </motion.div>
  );
}

function Overview() {
  const { incidents, scale, hotspots, monthlyTrend, alerts } = useDashboard();
  const solved = incidents.filter((item) => item.status === "Solved").length;
  const active = incidents.length - solved;
  const kpis = [
    [Database, "Total Crimes", fmt(scale.crimeRecords), "+4.8%"],
    [FileSearch, "Active Cases", fmt(active * 118), "+312"],
    [BadgeCheck, "Solved Cases", fmt(solved * 124), "+7.1%"],
    [MapPin, "High-Risk Areas", String(hotspots.filter((h) => h.category !== "Low").length), "+2"],
    [Siren, "Emergency Calls", fmt(12480), "+9.6%"],
    [Users, "Repeat Offenders", fmt(scale.offenders), "+81"],
    [BrainCircuit, "AI Alerts Generated", fmt(1482), "+18%"],
    [Activity, "Crime Trend Score", "82.4", "+3.2"],
  ] as const;

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {kpis.map(([icon, label, value, delta]) => (
          <Kpi key={label} icon={icon} label={label} value={value} delta={delta} />
        ))}
      </div>
      <div className="grid gap-4 xl:grid-cols-[1.45fr_0.9fr]">
        <Card>
          <ModuleHeader icon={BarChart3} title="Crime Tempo" subtitle="Monthly trend, solved load, and category velocity" />
          <div className="mt-5 h-80">
            <ResponsiveContainer>
              <AreaChart data={monthlyTrend}>
                <defs>
                  <linearGradient id="theft" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stopColor="#38d9c7" stopOpacity={0.52} />
                    <stop offset="100%" stopColor="#38d9c7" stopOpacity={0.04} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#1f3a40" strokeDasharray="3 3" />
                <XAxis dataKey="month" stroke="#7f949b" />
                <YAxis stroke="#7f949b" />
                <Tooltip contentStyle={{ background: "#091519", border: "1px solid #1f3a40" }} />
                <Area dataKey="theft" stroke="#38d9c7" fill="url(#theft)" />
                <Line dataKey="cyber" stroke="#f4c95d" strokeWidth={2} />
                <Line dataKey="solved" stroke="#7dd3fc" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>
        <Card>
          <ModuleHeader icon={ShieldAlert} title="AI Alerts" subtitle="Highest priority watchlist" />
          <div className="mt-5 space-y-3">
            {alerts.map((alert) => (
              <div key={alert.id} className={`rounded border p-3 ${alertColor[alert.level]}`}>
                <div className="flex items-center justify-between gap-3">
                  <strong className="text-sm">{alert.title}</strong>
                  <span className="text-xs">{alert.confidence}%</span>
                </div>
                <p className="mt-1 text-xs text-slate-300">{alert.reason}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

function IncidentManagement() {
  const { incidents } = useDashboard();
  const [query, setQuery] = useState("");
  const rows = useMemo(
    () =>
      incidents
        .filter((incident) =>
          `${incident.id} ${incident.fir} ${incident.type} ${incident.district} ${incident.status}`.toLowerCase().includes(query.toLowerCase()),
        )
        .slice(0, 18),
    [query],
  );

  return (
    <Card>
      <ModuleHeader icon={FileSearch} title="Incident Management" subtitle="FIR records, evidence, filters, and exports" />
      <div className="mt-5 grid gap-3 lg:grid-cols-[1fr_auto_auto_auto]">
        <label className="control">
          <Search size={16} />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search FIR, case, district, status" />
        </label>
        <button className="btn"><Filter size={16} /> Filters</button>
        <button className="btn"><Download size={16} /> PDF</button>
        <button className="btn"><Download size={16} /> CSV / Excel</button>
      </div>
      <div className="mt-5 overflow-auto">
        <table className="data-table">
          <thead>
            <tr>
              {["Crime ID", "FIR", "Type", "Date & Time", "District", "Police Station", "Severity", "Status", "Evidence"].map((head) => (
                <th key={head}>{head}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((incident) => (
              <tr key={incident.id}>
                <td>{incident.id}</td>
                <td>{incident.fir}</td>
                <td>{incident.type}</td>
                <td>{new Date(incident.datetime).toLocaleString()}</td>
                <td>{incident.district}</td>
                <td>{incident.station}</td>
                <td><span className={`pill ${alertColor[incident.severity]}`}>{incident.severity}</span></td>
                <td>{incident.status}</td>
                <td>{incident.evidence} files</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function CrimeMap({ compact = false }: { compact?: boolean }) {
  const { incidents } = useDashboard();
  const visible = incidents.slice(0, compact ? 80 : 180);
  return (
    <Card className={compact ? "h-full" : ""}>
      <ModuleHeader icon={Layers} title="Interactive GIS" subtitle="Crime markers, heat intensity, stations, and emergency layers" />
      <div className="mt-4 grid gap-3 md:grid-cols-6">
        {["Theft", "Assault", "Robbery", "Cybercrime", "Drug Cases", "Missing Persons"].map((layer) => (
          <button key={layer} className="btn justify-center">{layer}</button>
        ))}
      </div>
      <div className="map-shell mt-4">
        <MapContainer center={[18.5204, 73.8567]} zoom={11} scrollWheelZoom className="h-full w-full">
          <TileLayer attribution="&copy; OpenStreetMap" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          {visible.map((incident: CrimeIncident) => (
            <CircleMarker
              key={incident.id}
              center={[incident.lat, incident.lng]}
              radius={incident.severity === "Critical" ? 8 : 5}
              color={incident.severity === "Critical" ? "#ff5c77" : incident.severity === "High" ? "#f4c95d" : "#38d9c7"}
              fillOpacity={0.55}
            >
              <Popup>
                <strong>{incident.type}</strong>
                <br />
                {incident.district}
                <br />
                {incident.status}
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        {["Draw area", "Radius search", "Area statistics"].map((item) => (
          <div key={item} className="metric-row"><CircleDot size={15} /> {item}</div>
        ))}
      </div>
    </Card>
  );
}

function HotspotDetection() {
  const { hotspots } = useDashboard();
  return (
    <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
      <CrimeMap compact />
      <Card>
        <ModuleHeader icon={BrainCircuit} title="AI Hotspot Detection" subtitle="Risk zones with confidence and explanation" />
        <div className="mt-5 space-y-3">
          {hotspots.slice(0, 8).map((spot) => (
            <div key={spot.id} className="rounded border border-white/10 bg-white/[0.03] p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <strong>{spot.name}</strong>
                  <p className="text-xs text-slate-400">{spot.incidents} recent incidents</p>
                </div>
                <span className={`pill ${alertColor[spot.category]}`}>{spot.category}</span>
              </div>
              <div className="mt-3 h-2 rounded bg-slate-800">
                <div className="h-full rounded bg-cyanline" style={{ width: `${spot.score}%` }} />
              </div>
              <p className="mt-2 text-xs text-slate-300">Score {spot.score} · Confidence {spot.confidence}% · {spot.why}</p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

function DistrictCenter() {
  const { districtStats } = useDashboard();
  return (
    <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
      <Card>
        <ModuleHeader icon={BarChart3} title="District Intelligence" subtitle="Crime rates, patrol coverage, hotspots, and arrests" />
        <div className="mt-5 h-80">
          <ResponsiveContainer>
            <BarChart data={districtStats.slice(0, 10)}>
              <CartesianGrid stroke="#1f3a40" strokeDasharray="3 3" />
              <XAxis dataKey="district" stroke="#7f949b" angle={-20} height={72} textAnchor="end" />
              <YAxis stroke="#7f949b" />
              <Tooltip contentStyle={{ background: "#091519", border: "1px solid #1f3a40" }} />
              <Bar dataKey="crimes" fill="#38d9c7" />
              <Bar dataKey="patrol" fill="#f4c95d" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>
      <Card>
        <ModuleHeader icon={Users} title="Compare" subtitle="District drilldown summary" />
        <div className="mt-5 space-y-3">
          {districtStats.slice(0, 7).map((item) => (
            <div key={item.district} className="metric-row">
              <span>{item.district}</span>
              <span>{item.rate} / 10k · {item.arrestRate}% arrests</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

function AlertsView() {
  const { alerts } = useDashboard();
  return (
    <Card>
      <ModuleHeader icon={AlertTriangle} title="Anomaly Detection" subtitle="Spike, repeat incident, location, and night-activity monitors" />
      <div className="mt-5 grid gap-4 md:grid-cols-2">
        {alerts.map((alert) => (
          <div key={alert.id} className={`rounded border p-5 ${alertColor[alert.level]}`}>
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">{alert.title}</h3>
              <span className="text-sm">{alert.level}</span>
            </div>
            <p className="mt-3 text-sm text-slate-300">{alert.reason}</p>
            <p className="mt-3 text-sm text-slate-200">Suggested action: {alert.action}</p>
            <p className="mt-2 text-xs text-slate-400">Confidence {alert.confidence}%</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function NetworkAnalysis() {
  const { networkNodes, networkEdges } = useDashboard();
  return (
    <Card>
      <ModuleHeader icon={Network} title="Criminal Network Analysis" subtitle="Relationship graph, hidden links, centrality, and clusters" />
      <div className="mt-5 grid gap-5 xl:grid-cols-[1fr_340px]">
        <svg viewBox="-180 -150 460 360" className="h-[520px] w-full rounded border border-white/10 bg-[#061114]">
          {networkEdges.map((edge, index) => {
            const source = networkNodes.find((node) => node.id === edge.source)!;
            const target = networkNodes.find((node) => node.id === edge.target)!;
            return <line key={`${edge.source}-${edge.target}-${index}`} x1={source.x} y1={source.y} x2={target.x} y2={target.y} stroke="#2e5d64" strokeWidth={edge.strength / 28} opacity={0.72} />;
          })}
          {networkNodes.map((node) => (
            <g key={node.id}>
              <circle cx={node.x} cy={node.y} r={5 + node.weight / 3} fill={node.type === "Criminal" ? "#ff5c77" : node.type === "Gang" ? "#f4c95d" : "#38d9c7"} />
              <text x={node.x + 10} y={node.y + 4} fill="#cbd5e1" fontSize="8">{node.label}</text>
            </g>
          ))}
        </svg>
        <div className="space-y-3">
          {["Mastermind: Arjun Kale 1", "Coordinator: Cell-C", "Hidden phone bridge: Phone 19", "Community: Vehicle theft network", "Centrality leader: Rafiq Shaikh 2"].map((item) => (
            <div key={item} className="metric-row"><BrainCircuit size={15} /> {item}</div>
          ))}
        </div>
      </div>
    </Card>
  );
}

function OffenderTracking() {
  const { offenders } = useDashboard();
  return (
    <Card>
      <ModuleHeader icon={Users} title="Repeat Offender Tracking" subtitle="Profiles, associates, operating areas, and reoffending probability" />
      <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {offenders.slice(0, 8).map((offender) => (
          <div key={offender.id} className="rounded border border-white/10 bg-white/[0.03] p-4">
            <div className="flex items-center justify-between">
              <strong>{offender.name}</strong>
              <span className="text-xs text-cyanline">{offender.id}</span>
            </div>
            <p className="mt-1 text-sm text-slate-400">{offender.gang} · {offender.area}</p>
            <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
              <span>Arrests<br /><b>{offender.arrests}</b></span>
              <span>Risk<br /><b>{offender.riskScore}</b></span>
              <span>Reoffend<br /><b>{offender.probability}%</b></span>
              <span>Associates<br /><b>{Math.round(offender.arrests * 1.8)}</b></span>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function SocioEconomic() {
  const { districtStats } = useDashboard();
  return (
    <div className="grid gap-4 xl:grid-cols-2">
      <Card>
        <ModuleHeader icon={Activity} title="Socio-Economic Correlation" subtitle="Literacy, unemployment, income, and theft index" />
        <div className="mt-5 h-80">
          <ResponsiveContainer>
            <ScatterChart>
              <CartesianGrid stroke="#1f3a40" />
              <XAxis dataKey="unemployment" name="Unemployment" stroke="#7f949b" />
              <YAxis dataKey="theftIndex" name="Theft" stroke="#7f949b" />
              <Tooltip cursor={{ strokeDasharray: "3 3" }} contentStyle={{ background: "#091519", border: "1px solid #1f3a40" }} />
              <Scatter data={districtStats} fill="#38d9c7" />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </Card>
      <Card>
        <ModuleHeader icon={BrainCircuit} title="AI Insight" subtitle="Regression and correlation summary" />
        <p className="mt-5 text-slate-300">
          Areas with lower literacy and higher unemployment show elevated theft incidents. The model flags bus terminals, market perimeters, and low lighting corridors as the strongest co-factors.
        </p>
        <div className="mt-5 grid grid-cols-2 gap-3">
          {["Population", "Literacy", "Income", "Employment", "Poverty", "Infrastructure"].map((item, index) => (
            <div key={item} className="metric-row"><span>{item}</span><b>{Math.round(42 + index * 7 + Math.random() * 12)}%</b></div>
          ))}
        </div>
      </Card>
    </div>
  );
}

function Forecasting() {
  const { forecast, monthlyTrend } = useDashboard();
  return (
    <Card>
      <ModuleHeader icon={BrainCircuit} title="Predictive Risk Scoring" subtitle="Random Forest, XGBoost, and time-series forecast outputs" />
      <div className="mt-5 grid gap-4 md:grid-cols-3">
        {forecast.map((item) => (
          <div key={item.horizon} className="rounded border border-white/10 bg-white/[0.03] p-5">
            <p className="text-sm text-slate-400">{item.horizon}</p>
            <p className="mt-2 text-3xl font-semibold">{fmt(item.predicted)}</p>
            <p className="mt-2 text-sm text-slate-300">CI {fmt(item.low)} - {fmt(item.high)}</p>
            <p className="mt-1 text-sm text-cyanline">{item.confidence}% confidence</p>
          </div>
        ))}
      </div>
      <div className="mt-5 h-72">
        <ResponsiveContainer>
          <LineChart data={monthlyTrend}>
            <CartesianGrid stroke="#1f3a40" strokeDasharray="3 3" />
            <XAxis dataKey="month" stroke="#7f949b" />
            <YAxis stroke="#7f949b" />
            <Tooltip contentStyle={{ background: "#091519", border: "1px solid #1f3a40" }} />
            <Line dataKey="theft" stroke="#38d9c7" strokeWidth={2} />
            <Line dataKey="assault" stroke="#ff5c77" strokeWidth={2} />
            <Line dataKey="cyber" stroke="#f4c95d" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

function Patterns() {
  return (
    <Card>
      <ModuleHeader icon={BrainCircuit} title="AI Pattern Detection" subtitle="Serial patterns, MOs, crime chains, and organized activity" />
      <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {["Serial two-wheeler theft MO", "Payment-wallet cyber chain", "Night market assault cluster", "Organized narcotics route"].map((pattern, index) => (
          <div key={pattern} className="rounded border border-cyanline/20 bg-cyanline/5 p-4">
            <p className="font-semibold">{pattern}</p>
            <p className="mt-2 text-sm text-slate-300">{82 + index * 4}% similarity · {12 + index * 5} linked FIRs</p>
            <p className="mt-3 text-xs text-slate-400">Generated from clustering, association rules, and graph analytics.</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function CommandCenter() {
  const { hotspots } = useDashboard();
  return (
    <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
      <CrimeMap compact />
      <Card>
        <ModuleHeader icon={Radio} title="Real-Time Command Center" subtitle="Emergency calls, patrol vehicles, AI alerts, hotspot updates, and weather" />
        <div className="mt-5 space-y-3">
          {["Incoming emergency call: Wakad junction", "Patrol V-24 rerouted to hotspot HS-03", "Weather: heavy rain reducing visibility", "Hotspot HS-01 intensity increased 12%", "Active incident: robbery response in progress"].map((event, index) => (
            <div key={event} className="metric-row"><span>{event}</span><span>T+{index * 4}s</span></div>
          ))}
        </div>
      </Card>
    </div>
  );
}

function CCTV() {
  const { cctvEvents } = useDashboard();
  return (
    <Card>
      <ModuleHeader icon={Camera} title="CCTV & Surveillance" subtitle="Camera locations, face match, vehicle tracking, crowd detection, and timeline" />
      <div className="mt-5 grid gap-4 md:grid-cols-2">
        {cctvEvents.map((event, index) => (
          <div key={event} className="rounded border border-white/10 bg-white/[0.03] p-4">
            <p className="text-xs text-cyanline">Camera event {index + 1}</p>
            <h3 className="mt-2 font-semibold">{event}</h3>
            <p className="mt-2 text-sm text-slate-400">Confidence {86 + index * 3}% · linked timeline marker created</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function Investigation() {
  return (
    <Card>
      <ModuleHeader icon={FileSearch} title="Case Investigation Workspace" subtitle="Evidence board, timeline reconstruction, notes, and AI summary" />
      <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_1fr]">
        <div className="grid grid-cols-2 gap-3">
          {["Evidence board", "Timeline reconstruction", "Suspect graph", "Case notes"].map((item) => (
            <div key={item} className="rounded border border-white/10 bg-white/[0.03] p-5 min-h-[130px]">{item}</div>
          ))}
        </div>
        <div className="rounded border border-cyanline/25 bg-cyanline/5 p-5">
          <p className="text-xs uppercase tracking-[0.22em] text-cyanline">AI-generated investigation summary</p>
          <p className="mt-4 text-lg text-slate-100">Potential suspect linked to 4 incidents across 3 districts through shared vehicle sightings, phone proximity, and repeated market-access timing.</p>
        </div>
      </div>
    </Card>
  );
}

function Patrol() {
  const { patrolRoutes } = useDashboard();
  return (
    <div className="grid gap-4 xl:grid-cols-[1fr_0.8fr]">
      <CrimeMap compact />
      <Card>
        <ModuleHeader icon={Car} title="Patrol Optimization" subtitle="Routes, coverage score, resource allocation, and risk inputs" />
        <div className="mt-5 space-y-3">
          {patrolRoutes.map((route) => (
            <div key={route.route} className="metric-row">
              <span>{route.route} · {route.area}</span>
              <span>{route.coverage}% · {route.eta}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

function SearchAndReports({ reports = false }: { reports?: boolean }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<CrimeIncident[]>([]);
  const [status, setStatus] = useState("");

  async function runSearch() {
    setStatus("Searching live records...");
    try {
      const response = await naturalLanguageSearch(query || "Show robbery cases in Pune");
      setResults(response.results);
      setStatus(`${response.results.length} matching records`);
    } catch {
      setStatus("Search service offline");
    }
  }

  return (
    <Card>
      <ModuleHeader icon={reports ? Download : Search} title={reports ? "Reporting Center" : "Advanced Search"} subtitle={reports ? "Daily, weekly, district, and predictive reports" : "Natural language search across cases, criminals, vehicles, locations, and FIRs"} />
      <label className="control mt-5">
        <Search size={16} />
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={reports ? "Generate weekly intelligence report for Pune Central" : "Show robbery cases involving repeat offenders in Pune during last 30 days"} />
      </label>
      <div className="mt-5 grid gap-3 md:grid-cols-4">
        {(reports ? ["Daily Crime Report", "Weekly Intelligence", "District Report", "Predictive Risk"] : ["Cases", "Criminals", "Vehicles", "Locations"]).map((item) => (
          <button key={item} className="btn justify-center" onClick={runSearch}>{item}</button>
        ))}
      </div>
            {reports && (
        <div className="mt-4 flex flex-wrap gap-3">
          <button className="btn" onClick={() => downloadReport("pdf")}><Download size={16} /> PDF</button>
          <button className="btn" onClick={() => downloadReport("xlsx")}><Download size={16} /> Excel</button>
          <button className="btn" onClick={() => downloadReport("csv")}><Download size={16} /> CSV</button>
        </div>
      )}
      {status && <p className="mt-4 text-sm text-cyanline">{status}</p>}
      {results.length > 0 && (
        <div className="mt-5 overflow-auto">
          <table className="data-table">
            <thead><tr><th>Crime ID</th><th>FIR</th><th>Type</th><th>District</th><th>Status</th></tr></thead>
            <tbody>{results.slice(0, 8).map((item) => <tr key={item.id}><td>{item.id}</td><td>{item.fir}</td><td>{item.type}</td><td>{item.district}</td><td>{item.status}</td></tr>)}</tbody>
          </table>
        </div>
      )}
    </Card>
  );
}

function Copilot() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([
    "Why did theft increase in District A?",
    "Theft rose after 20:00 near transit corridors. Three repeat offenders and two market cameras overlap with recent FIRs.",
    "Predict next week's risk areas.",
    "Critical risk: Shivajinagar Corridor and Viman Nagar exits. Recommended patrol overlap: 19:30-01:00.",
  ]);

  async function send() {
    const question = input.trim();
    if (!question) return;
    setMessages((items) => [...items, question]);
    setInput("");
    try {
      const response = await askCopilot(question);
      setMessages((items) => [...items, response.answer]);
    } catch {
      setMessages((items) => [...items, "The copilot service is offline. Local fallback data is still available across the dashboard."]);
    }
  }

  return (
    <Card>
      <ModuleHeader icon={Bot} title="AI Copilot" subtitle="Crime analytics Q&A, summaries, anomaly explanations, and patrol planning" />
      <div className="mt-5 grid gap-4 lg:grid-cols-[1fr_360px]">
        <div className="rounded border border-white/10 bg-[#061114] p-4">
          {messages.map((text, index) => (
            <div key={index} className={`mb-3 max-w-[80%] rounded p-3 text-sm ${index % 2 ? "ml-auto bg-cyanline/15 text-slate-100" : "bg-white/8 text-slate-300"}`}>{text}</div>
          ))}
          <label className="control mt-4"><Bot size={16} /><input value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") void send(); }} placeholder="Ask SentinelIQ..." /></label>
        </div>
        <div className="space-y-3">
          {["Generate case summary", "Explain anomaly", "Suggest patrol plan", "Identify hotspots"].map((item) => (
            <button key={item} className="btn w-full justify-center">{item}</button>
          ))}
        </div>
      </div>
    </Card>
  );
}

function CategoryPie() {
  const { categoryBreakdown } = useDashboard();
  return (
    <Card>
      <ModuleHeader icon={BarChart3} title="Categories" subtitle="Crime category distribution" />
      <div className="mt-5 h-72">
        <ResponsiveContainer>
          <PieChart>
            <Pie data={categoryBreakdown} dataKey="value" nameKey="name" outerRadius={92} innerRadius={48}>
              {categoryBreakdown.map((_, index) => <Cell key={index} fill={colors[index % colors.length]} />)}
            </Pie>
            <Tooltip contentStyle={{ background: "#091519", border: "1px solid #1f3a40" }} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

function DatasetManagement({ setTrigger }: { setTrigger: (t: number) => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [summary, setSummary] = useState<DatasetUploadSummary | null>(null);
  const [history, setHistory] = useState<DatasetHistory[]>([]);

  useEffect(() => {
    fetchDatasetHistory().then(setHistory).catch(console.error);
  }, []);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    try {
      const result = await uploadDataset(file);
      setSummary(result);
      setFile(null);
      fetchDatasetHistory().then(setHistory).catch(console.error);
      setTrigger(Date.now());
    } catch (e: any) {
      alert("Error uploading dataset: " + e.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="flex h-full flex-col gap-6 p-6">
      <ModuleHeader icon={UploadCloud} title="Data Ingestion" subtitle="Dataset Management" />
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 flex-1 min-h-0">
        <div className="xl:col-span-1 flex flex-col gap-6">
          <Card className="p-6">
            <h3 className="text-lg font-medium text-slate-200 mb-4">Upload New Dataset</h3>
            <div
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${file ? 'border-cyanline bg-cyanline/10' : 'border-slate-700 hover:border-slate-500'}`}
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => document.getElementById("file-upload")?.click()}
            >
              <input id="file-upload" type="file" accept=".csv" className="hidden" onChange={(e) => setFile(e.target.files?.[0] || null)} />
              <UploadCloud className="mx-auto h-12 w-12 text-slate-400 mb-4" />
              <p className="text-slate-300 font-medium">{file ? file.name : "Drag and drop a CSV file here"}</p>
              <p className="text-slate-500 text-sm mt-2">{file ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : "or click to browse"}</p>
            </div>
            <div className="mt-6 flex justify-end gap-3">
              {file && (
                <button onClick={(e) => { e.stopPropagation(); setFile(null); }} disabled={uploading} className="px-4 py-2 text-sm text-slate-300 hover:text-white transition-colors">
                  Cancel
                </button>
              )}
              <button
                onClick={(e) => { e.stopPropagation(); handleUpload(); }}
                disabled={!file || uploading}
                className="px-6 py-2 bg-cyanline text-slate-900 rounded-md font-medium text-sm hover:bg-cyanline/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                {uploading ? "Processing..." : "Upload & Process"}
              </button>
            </div>
          </Card>
          
          {summary && (
            <Card className="p-6 border-green-500/30 bg-green-500/5">
              <div className="flex items-center gap-3 mb-4">
                <BadgeCheck className="text-green-500" />
                <h3 className="text-lg font-medium text-green-500">Dataset Imported Successfully</h3>
              </div>
              <ul className="space-y-3 text-sm text-slate-300">
                <li className="flex justify-between"><span>Records Uploaded:</span> <span className="font-mono text-white">{fmt(summary.records_uploaded)}</span></li>
                <li className="flex justify-between"><span>Valid Records:</span> <span className="font-mono text-white">{fmt(summary.valid_records)}</span></li>
                <li className="flex justify-between"><span>Duplicates Removed:</span> <span className="font-mono text-red-400">{fmt(summary.duplicates_removed)}</span></li>
                <li className="flex justify-between"><span>Districts Updated:</span> <span className="font-mono text-cyanline">{fmt(summary.districts_updated)}</span></li>
                <li className="flex justify-between"><span>Hotspots Recalculated:</span> <span className="font-mono text-yellow-400">{fmt(summary.hotspots_recalculated)}</span></li>
              </ul>
              <div className="mt-4 pt-4 border-t border-slate-700 text-xs text-slate-500">Processing Time: {summary.processing_time}</div>
            </Card>
          )}
        </div>
        
        <div className="xl:col-span-2">
          <Card className="p-6 h-[600px] flex flex-col">
            <h3 className="text-lg font-medium text-slate-200 mb-6">Upload History</h3>
            <div className="flex-1 overflow-auto pr-2 custom-scrollbar">
              <table className="w-full text-sm text-left">
                <thead className="text-xs uppercase text-slate-400 border-b border-slate-700/50 sticky top-0 bg-[#0c1a1f]">
                  <tr>
                    <th className="px-4 py-3">Filename</th>
                    <th className="px-4 py-3">Date</th>
                    <th className="px-4 py-3">Uploaded By</th>
                    <th className="px-4 py-3 text-right">Records</th>
                    <th className="px-4 py-3">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((h) => (
                    <tr key={h.id} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                      <td className="px-4 py-3 font-medium text-slate-300">{h.filename}</td>
                      <td className="px-4 py-3 text-slate-500">{new Date(h.uploaded_at).toLocaleString()}</td>
                      <td className="px-4 py-3 text-slate-400">{h.uploaded_by_name}</td>
                      <td className="px-4 py-3 text-right font-mono text-cyanline">{fmt(h.record_count)}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded text-xs ${h.status === 'Completed' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
                          {h.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {history.length === 0 && (
                    <tr>
                      <td colSpan={5} className="px-4 py-8 text-center text-slate-500">No datasets uploaded yet.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

function ModuleBody({ active, setTrigger }: { active: string, setTrigger: (t: number) => void }) {
  if (active === "Overview") return <><Overview /><div className="mt-4 grid gap-4 xl:grid-cols-2"><CategoryPie /><DistrictCenter /></div></>;
  if (active === "Incidents") return <IncidentManagement />;
  if (active === "GIS Map") return <CrimeMap />;
  if (active === "Hotspots") return <HotspotDetection />;
  if (active === "District Intel") return <DistrictCenter />;
  if (active === "Alerts") return <AlertsView />;
  if (active === "Network") return <NetworkAnalysis />;
  if (active === "Offenders") return <OffenderTracking />;
  if (active === "Socio-Economic") return <SocioEconomic />;
  if (active === "Forecasting") return <Forecasting />;
  if (active === "Patterns") return <Patterns />;
  if (active === "Command Center") return <CommandCenter />;
  if (active === "CCTV") return <CCTV />;
  if (active === "Investigation") return <Investigation />;
  if (active === "Patrol") return <Patrol />;
  if (active === "Search") return <SearchAndReports />;
  if (active === "Reports") return <SearchAndReports reports />;
  if (active === "Dataset Management") return <DatasetManagement setTrigger={setTrigger} />;
  return <Copilot />;
}

export function App() {
  const [active, setActive] = useState("Overview");
  const [dark, setDark] = useState(true);
  const [dashboard, setDashboard] = useState<DashboardData>(fallbackDashboard);
  const [connection, setConnection] = useState("Connecting");
  
  // Auth states
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem("sentineliq.token"));
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authError, setAuthError] = useState("");
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  useEffect(() => {
    if (!isAuthenticated) return;
    let cancelled = false;
    fetchDashboard()
      .then((data) => {
        if (!cancelled) {
          setDashboard(data);
          setConnection(data === fallbackDashboard ? "Offline demo" : "Live API");
        }
      })
      .catch(() => {
        if (!cancelled) setConnection("Offline demo");
      });
    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, refreshTrigger]);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setAuthError("");
    try {
      await login(email || "admin@sentineliq.local", password || "SentinelIQ@123");
      setIsAuthenticated(true);
    } catch (err) {
      setAuthError("Invalid username or password");
    }
  }

  function handleLogout() {
    localStorage.removeItem("sentineliq.token");
    setIsAuthenticated(false);
    setEmail("");
    setPassword("");
    setAuthError("");
  }

  if (!isAuthenticated) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900 text-slate-100 dark:bg-ink">
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="w-full max-w-md rounded-lg border border-cyanline/30 bg-[#071114] p-8 shadow-2xl"
        >
          <div className="flex flex-col items-center border-b border-white/10 pb-6">
            <div className="grid size-12 place-items-center rounded border border-cyanline bg-cyanline/10 text-cyanline">
              <ShieldAlert size={28} />
            </div>
            <h1 className="mt-4 text-2xl font-bold tracking-tight text-white">SentinelIQ</h1>
            <p className="text-sm text-slate-400">Crime Intelligence Platform Auth</p>
          </div>
          
          <form onSubmit={handleLogin} className="mt-6 space-y-4">
            {authError && (
              <div className="rounded border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-300">
                {authError}
              </div>
            )}
            <div>
              <label className="block text-xs uppercase tracking-wider text-slate-400">Email Address</label>
              <input 
                type="email" 
                className="mt-1 w-full rounded border border-white/10 bg-slate-950/60 p-3 text-slate-100 outline-none focus:border-cyanline"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@sentineliq.local"
                required
              />
            </div>
            <div>
              <label className="block text-xs uppercase tracking-wider text-slate-400">Password</label>
              <input 
                type="password" 
                className="mt-1 w-full rounded border border-white/10 bg-slate-950/60 p-3 text-slate-100 outline-none focus:border-cyanline"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
            </div>
            <button 
              type="submit" 
              className="mt-2 w-full rounded bg-cyanline py-3 font-semibold text-slate-900 transition hover:bg-cyanline/80"
            >
              Sign In
            </button>
          </form>
        </motion.div>
      </div>
    );
  }

  return (
    <DashboardContext.Provider value={dashboard}>
    <div className={dark ? "dark" : ""}>
      <main className="min-h-screen bg-slate-100 text-slate-950 dark:bg-ink dark:text-slate-100">
        <aside className="fixed inset-y-0 left-0 z-20 hidden w-72 border-r border-white/10 bg-[#071114]/95 p-4 lg:block">
          <div className="flex items-center gap-3 border-b border-white/10 pb-4">
            <div className="grid size-11 place-items-center rounded border border-cyanline/40 bg-cyanline/10 text-cyanline"><ShieldAlert /></div>
            <div>
              <h1 className="text-xl font-semibold">SentinelIQ</h1>
              <p className="text-xs text-slate-400">AI Crime Intelligence Platform</p>
            </div>
          </div>
          <nav className="mt-4 h-[calc(100vh-108px)] space-y-1 overflow-auto pr-1">
            {modules.map((module) => (
              <button key={module} onClick={() => setActive(module)} className={`nav-item ${active === module ? "active" : ""}`}>
                {module}
              </button>
            ))}
          </nav>
        </aside>
        <div className="lg:pl-72">
          <header className="sticky top-0 z-10 border-b border-white/10 bg-[#071114]/90 px-4 py-3 backdrop-blur md:px-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.28em] text-cyanline">Operational Intelligence · {connection}</p>
                <h2 className="text-2xl font-semibold text-white">{active}</h2>
              </div>
              <div className="flex items-center gap-2">
                <label className="control hidden min-w-[280px] md:flex"><Search size={16} /><input placeholder="Global smart search" /></label>
                <button className="icon-btn" onClick={() => setDark(!dark)} aria-label="Toggle theme">{dark ? <Sun size={18} /> : <Moon size={18} />}</button>
                <button className="btn text-xs px-3 py-1.5 border border-cyanline/40 text-cyanline hover:bg-cyanline/10" onClick={handleLogout}>Sign Out</button>
              </div>
            </div>
            <div className="mt-3 flex gap-2 overflow-auto lg:hidden">
              {modules.map((module) => <button key={module} onClick={() => setActive(module)} className={`mobile-tab ${active === module ? "active" : ""}`}>{module}</button>)}
            </div>
          </header>
          <section className="p-4 md:p-6">
            <ModuleBody active={active} setTrigger={setRefreshTrigger} />
          </section>
        </div>
      </main>
    </div>
    </DashboardContext.Provider>
  );
}
