# SentinelIQ

SentinelIQ is a production-style AI-driven crime analytics and visualization prototype built with React, TypeScript, Tailwind CSS, Recharts, Leaflet, Framer Motion, and a FastAPI service scaffold.

## Run the frontend

```bash
npm install
npm run dev -- --port 5173
```

Open `http://127.0.0.1:5173`.

## Build

```bash
npm run build
```

## Backend scaffold

```bash
cd backend
pip install fastapi uvicorn pydantic
uvicorn main:app --reload --port 8000
```

Available endpoints:

- `GET /health`
- `GET /api/incidents?limit=100`
- `GET /api/insights`

## Prototype coverage

- Command-center dashboard with animated KPI cards and live-style operational metrics
- Crime incident management with FIR fields, filters, search, evidence counts, and export actions
- Leaflet GIS crime map with marker layers, severity styling, area tools, and emergency context
- AI hotspot detection with risk score, confidence, risk category, recent incidents, and rationale
- District intelligence center with comparisons, charts, patrol coverage, and arrest rates
- Trend alerts and anomaly detection with color-coded confidence and actions
- Criminal network graph showing entities, connection strengths, clusters, and AI findings
- Repeat offender profiles with risk scoring, associates, operating areas, and reoffending probability
- Socio-economic correlation, forecasting, pattern detection, command center, CCTV, investigation workspace, patrol optimization, global search, reporting center, and AI copilot screens
- Seeded synthetic operating scale: 50,000 crime records, 5,000 offenders, 500 gangs, 100 districts, and 100,000 network connections
