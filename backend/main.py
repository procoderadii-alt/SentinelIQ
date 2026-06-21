from __future__ import annotations

import csv
import io
import math
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Response, Request, WebSocket, WebSocketDisconnect, status, UploadFile, File, Form
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

import json

from database import engine, get_db, Base
from models import (
    Role,
    Permission,
    User,
    District,
    PoliceStation,
    CrimeCategory,
    CrimeRecord,
    Offender,
    Gang,
    Alert,
    PatrolUnit,
    Report,
    AuditLog,
    EmergencyCall,
    CctvEvent,
    Case,
    CaseNote,
    Evidence,
    Dataset
)
from schemas import (
    CrimeIn,
    CrimeOut,
    DashboardPayload,
    OffenderOut,
    HotspotOut,
    AlertOut,
    ForecastOut,
    DistrictStatsOut,
    NetworkNodeOut,
    NetworkEdgeOut,
    PatrolRouteOut,
    ReportOut,
    DatasetOut,
    DatasetUploadSummary,
    CaseLinkRequest,
    EvidenceOut
)
from seed import seed_database
import ai_services

# Config and constants
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production-sentinel-key-12345")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "720"))


limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="SentinelIQ API",
    version="2.0.0",
    description="Production-ready crime intelligence FastAPI backend supporting postgres, caching, real-time alerts, and AI models."
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173,http://localhost,http://127.0.0.1:8080,http://localhost:8080").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def audit_logging_middleware(request: Request, call_next):
    # Only log state-mutating requests
    if request.method in ["POST", "PUT", "DELETE"]:
        actor = "System/Anonymous"
        # Extract actor from Authorization header if present
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                actor = payload.get("sub", actor)
            except:
                pass
                
        response = await call_next(request)
        
        # Log to DB asynchronously or using a new session
        # For simplicity, we create a fresh session here.
        with Session(bind=engine) as db:
            log = AuditLog(
                id=uuid.uuid4(),
                actor=actor,
                action=request.method,
                entity=request.url.path,
                entity_id=str(response.status_code)
            )
            db.add(log)
            db.commit()
            
        return response
        
    return await call_next(request)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, data: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception:
                pass

manager = ConnectionManager()

@app.websocket("/api/ws/alerts")
async def websocket_alerts_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # We just hold the connection open.
            # Alerts will be broadcast via manager.broadcast()
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = None
if HAS_REDIS:
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    except Exception as e:
        print(f"Redis connection skipped: {e}")

memory_cache = {}

def get_cached_dashboard():
    if HAS_REDIS and redis_client:
        try:
            return redis_client.get("sentinel_dashboard")
        except Exception:
            pass
    cached = memory_cache.get("sentinel_dashboard")
    if cached:
        val, expiry = cached
        if datetime.now() < expiry:
            return val
    return None

def set_cached_dashboard(payload_json: str, ttl: int = 300):
    if HAS_REDIS and redis_client:
        try:
            redis_client.setex("sentinel_dashboard", ttl, payload_json)
            return
        except Exception:
            pass
    memory_cache["sentinel_dashboard"] = (payload_json, datetime.now() + timedelta(seconds=ttl))

def invalidate_cache():
    if HAS_REDIS and redis_client:
        try:
            redis_client.delete("sentinel_dashboard")
        except Exception:
            pass
    memory_cache.pop("sentinel_dashboard", None)

# Startup event: Schema init & seed checks
@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    with Session(bind=engine) as db:
        # Default seed count
        seed_database(
            db, 
            crimes=int(os.getenv("SEED_CRIMES", "2000")),
            offenders=int(os.getenv("SEED_OFFENDERS", "5000")),
            districts=int(os.getenv("SEED_DISTRICTS", "100")),
            gangs=int(os.getenv("SEED_GANGS", "500")),
            emergency_calls=int(os.getenv("SEED_EMERGENCY_CALLS", "10000")),
            cctv_events=int(os.getenv("SEED_CCTV_EVENTS", "20000"))
        )

# Audit log helper
def log_audit(db: Session, actor: str, action: str, entity: str, entity_id: str):
    log = AuditLog(
        id=uuid.uuid4(),
        actor=actor,
        action=action,
        entity=entity,
        entity_id=str(entity_id)
    )
    db.add(log)
    db.flush()



# Current user dependency


# Role permission check dependency


# Mapper helper
def row_to_crime(row: CrimeRecord) -> CrimeOut:
    return CrimeOut(
        id=row.crime_id,
        fir=row.fir,
        type=row.category.name,
        category=row.category.name,
        severity=row.severity,
        status=row.status,
        district=row.district.name,
        station=row.police_station.name,
        lat=row.latitude,
        lng=row.longitude,
        datetime=row.occurred_at,
        victim=row.victim_name,
        suspect=row.suspect_name,
        evidence=row.evidence_count
    )

def build_dashboard(db: Session, limit: int = 420) -> DashboardPayload:
    # Query high volume crimes
    crime_rows = db.scalars(select(CrimeRecord).order_by(CrimeRecord.occurred_at.desc()).limit(limit)).all()
    crimes = [row_to_crime(row) for row in crime_rows]

    # Query repeat offenders using ML risk engine
    offenders = ai_services.get_repeat_offender_list(db, limit=32)

    # Hotspot detection using KMeans and KDE density scoring
    hotspots = ai_services.detect_hotspots(db, limit=300)

    # Watchlist Alerts
    alerts_rows = db.scalars(select(Alert).order_by(Alert.confidence.desc())).all()
    alerts = [
        AlertOut(
            id=a.alert_id,
            title=a.title,
            level=a.level,
            reason=a.reason,
            confidence=a.confidence,
            action=a.action
        ) for a in alerts_rows
    ]

    # Time series prediction & trend analysis
    forecast, monthly_trend = ai_services.forecast_crimes(db)

    # Criminal network analysis using NetworkX graphs
    network_nodes, network_edges = ai_services.analyze_criminal_networks(db, limit=15)

    # District comparisons
    districts = db.scalars(select(District).limit(24)).all()
    district_counts = dict(db.execute(select(District.name, func.count(CrimeRecord.id)).join(CrimeRecord).group_by(District.name)).all())
    
    district_stats = []
    for d in districts:
        count = district_counts.get(d.name, 0)
        rate = round((count / max(d.population, 1)) * 10000, 1)
        
        # Socioeconomic connections
        se_data = d.socioeconomic_data[0] if d.socioeconomic_data else None
        arrest_rate = min(95, round(36 + (100 - (se_data.unemployment_rate if se_data else 10)) / 2))
        patrol_score = min(98, round(54 + (se_data.literacy_rate if se_data else 80) / 2))
        
        district_stats.append(DistrictStatsOut(
            district=d.name,
            crimes=count,
            rate=rate,
            arrestRate=arrest_rate,
            patrol=patrol_score,
            hotspots=max(1, round(count / 80)),
            income=int(28000 + (se_data.literacy_rate if se_data else 80) * 780),
            literacy=int(se_data.literacy_rate if se_data else 80),
            unemployment=float(se_data.unemployment_rate if se_data else 8.5),
            theftIndex=int(count // 10 + (se_data.poverty_rate if se_data else 12) * 2)
        ))

    # Category breakdown aggregates
    category_counts = db.execute(select(CrimeCategory.name, func.count(CrimeRecord.id)).join(CrimeRecord).group_by(CrimeCategory.name)).all()
    category_breakdown = [{"name": r[0], "value": r[1]} for r in category_counts]

    # Live CCTV event notifications feed
    cctv_rows = db.scalars(select(CctvEvent).order_by(CctvEvent.occurred_at.desc()).limit(8)).all()
    cctv_events = [f"{c.event_type}: {c.description} at {c.location}" for c in cctv_rows]
    if not cctv_events:
        cctv_events = [
            "Face match near Viman Nagar camera C-44",
            "Unregistered vehicle convoy detected on Baner Road",
            "Crowd density threshold breached at market junction",
            "Suspicious loitering event matched to open FIR"
        ]

    # Patrol routes optimization
    patrols = db.scalars(select(PatrolUnit).limit(8)).all()
    patrol_routes = [
        PatrolRouteOut(
            route=p.unit_code,
            area=p.area,
            coverage=p.coverage_score,
            eta=f"{p.eta_minutes} min"
        ) for p in patrols
    ]

    # Scales
    scale_dict = {
        "crimeRecords": db.scalar(select(func.count(CrimeRecord.id))) or 0,
        "offenders": db.scalar(select(func.count(Offender.id))) or 0,
        "gangs": db.scalar(select(func.count(Gang.id))) or 0,
        "districts": db.scalar(select(func.count(District.id))) or 0,
        "networkConnections": len(network_edges)
    }

    return DashboardPayload(
        scale=scale_dict,
        incidents=crimes,
        offenders=offenders,
        hotspots=hotspots,
        alerts=alerts,
        monthlyTrend=monthly_trend,
        districtStats=district_stats,
        forecast=forecast,
        networkNodes=network_nodes,
        networkEdges=network_edges,
        categoryBreakdown=category_breakdown,
        cctvEvents=cctv_events,
        patrolRoutes=patrol_routes
    )

# --- ROUTES ---

@app.get("/health")
def health(db: Session = Depends(get_db)):
    return {
        "status": "ok",
        "database": "connected",
        "crime_records": db.scalar(select(func.count(CrimeRecord.id)))
    }



@app.get("/api/dashboard", response_model=DashboardPayload)
def dashboard(db: Session = Depends(get_db)):
    cached = get_cached_dashboard()
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass
            
    payload = build_dashboard(db)
    set_cached_dashboard(payload.model_dump_json(), 300)
    return payload

@app.get("/api/crimes", response_model=List[CrimeOut])
def list_crimes(
    q: str = "",
    district: str = "",
    severity: str = "",
    status: str = "",
    start_date: str = "",
    end_date: str = "",
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    
    db: Session = Depends(get_db)
):
    stmt = select(CrimeRecord).join(CrimeCategory).join(District).join(PoliceStation)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            (CrimeRecord.fir.like(like)) | 
            (CrimeRecord.crime_id.like(like)) | 
            (CrimeCategory.name.like(like)) | 
            (District.name.like(like)) | 
            (CrimeRecord.status.like(like)) |
            (CrimeRecord.victim_name.like(like)) |
            (CrimeRecord.suspect_name.like(like))
        )
    if district:
        stmt = stmt.where(District.name == district)
    if severity:
        stmt = stmt.where(CrimeRecord.severity.in_(severity.split(",")))
    if status:
        stmt = stmt.where(CrimeRecord.status.in_(status.split(",")))
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            stmt = stmt.where(CrimeRecord.occurred_at >= start_dt)
        except ValueError:
            pass
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            stmt = stmt.where(CrimeRecord.occurred_at <= end_dt)
        except ValueError:
            pass
            
    rows = db.scalars(stmt.order_by(CrimeRecord.occurred_at.desc()).offset(offset).limit(limit)).all()
    return [row_to_crime(row) for row in rows]

@app.post("/api/crimes", response_model=CrimeOut, status_code=201)
async def create_crime(
    payload: CrimeIn,
    
    db: Session = Depends(get_db)
):
    district_name = payload.district
    district = db.scalar(select(District).where(District.name == district_name))
    if not district:
        district = District(
            id=uuid.uuid4(),
            name=district_name,
            code=f"DST-{int(datetime.now().timestamp()) % 1000:03d}",
            population=250000,
            latitude=payload.lat,
            longitude=payload.lng
        )
        db.add(district)
        db.flush()

    station = db.scalar(select(PoliceStation).where(PoliceStation.name == payload.station, PoliceStation.district_id == district.id))
    if not station:
        station = PoliceStation(
            id=uuid.uuid4(),
            name=payload.station,
            district_id=district.id,
            latitude=payload.lat,
            longitude=payload.lng
        )
        db.add(station)

    category = db.scalar(select(CrimeCategory).where(CrimeCategory.name == payload.type))
    if not category:
        category = CrimeCategory(
            id=uuid.uuid4(),
            name=payload.type,
            severity_weight=1.0
        )
        db.add(category)
        
    db.flush()

    next_id = (db.scalar(select(func.count(CrimeRecord.id))) or 0) + 240001
    row = CrimeRecord(
        id=uuid.uuid4(),
        crime_id=f"CR-{next_id:06d}",
        fir=payload.fir,
        category_id=category.id,
        district_id=district.id,
        police_station_id=station.id,
        status=payload.status,
        severity=payload.severity,
        latitude=payload.lat,
        longitude=payload.lng,
        occurred_at=payload.datetime,
        victim_name=payload.victim,
        suspect_name=payload.suspect,
        evidence_count=payload.evidence,
        narrative=f"Created incident of {category.name} in district {district.name}."
    )
    
    db.add(row)
    db.flush()
    
    log_audit(db, "system@sentineliq.local", "CREATE", "CrimeRecord", row.crime_id)
    invalidate_cache()
    db.commit()
    db.refresh(row)

    # Real-time WebSockets Alert broadcast
    await manager.broadcast({
        "type": "new_incident",
        "message": f"New FIR registered: {row.fir} ({row.category.name}) in {row.district.name}",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    return row_to_crime(row)

@app.put("/api/crimes/{crime_id}", response_model=CrimeOut)
@limiter.limit(os.getenv("RATE_LIMIT_WRITE", "30/minute"))
def update_crime(
    request: Request,
    crime_id: str,
    payload: CrimeIn,
    
    db: Session = Depends(get_db)
):
    row = db.scalar(select(CrimeRecord).where(CrimeRecord.crime_id == crime_id))
    if not row:
        raise HTTPException(status_code=404, detail="Crime not found")
        
    row.fir = payload.fir
    row.status = payload.status
    row.severity = payload.severity
    row.latitude = payload.lat
    row.longitude = payload.lng
    row.occurred_at = payload.datetime
    row.victim_name = payload.victim
    row.suspect_name = payload.suspect
    row.evidence_count = payload.evidence
    
    log_audit(db, "system@sentineliq.local", "UPDATE", "CrimeRecord", crime_id)
    invalidate_cache()
    db.commit()
    db.refresh(row)
    return row_to_crime(row)

@app.delete("/api/crimes/{crime_id}", status_code=204)
def delete_crime(
    request: Request,
    crime_id: str,
    
    db: Session = Depends(get_db)
):
    row = db.scalar(select(CrimeRecord).where(CrimeRecord.crime_id == crime_id))
    if not row:
        raise HTTPException(status_code=404, detail="Crime not found")
        
    db.delete(row)
    log_audit(db, "system@sentineliq.local", "DELETE", "CrimeRecord", crime_id)
    invalidate_cache()
    db.commit()
    return Response(status_code=204)

@app.post("/api/crimes/{crime_id}/evidence", response_model=EvidenceOut, status_code=201)
async def upload_evidence(
    crime_id: str,
    file: UploadFile,
    description: str = Form("Uploaded evidence"),
    
    db: Session = Depends(get_db)
):
    row = db.scalar(select(CrimeRecord).where(CrimeRecord.crime_id == crime_id))
    if not row:
        raise HTTPException(status_code=404, detail="Crime not found")
        
    os.makedirs("evidence_store", exist_ok=True)
    file_path = f"evidence_store/{uuid.uuid4()}_{file.filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
        
    evidence_rec = Evidence(
        id=uuid.uuid4(),
        evidence_code=f"EVID-{int(datetime.now().timestamp())}",
        crime_record_id=row.id,
        description=description,
        file_path=file_path,
        file_type=file.content_type
    )
    db.add(evidence_rec)
    row.evidence_count += 1
    
    log_audit(db, "system@sentineliq.local", "UPLOAD_EVIDENCE", "CrimeRecord", crime_id)
    db.commit()
    db.refresh(evidence_rec)
    return evidence_rec

@app.post("/api/crimes/{crime_id}/link-case", response_model=CrimeOut)
def link_case(
    crime_id: str,
    payload: CaseLinkRequest,
    
    db: Session = Depends(get_db)
):
    row = db.scalar(select(CrimeRecord).where(CrimeRecord.crime_id == crime_id))
    if not row:
        raise HTTPException(status_code=404, detail="Crime not found")
        
    case_rec = db.scalar(select(Case).where(Case.case_number == payload.case_number))
    if not case_rec:
        case_rec = Case(
            id=uuid.uuid4(),
            case_number=payload.case_number,
            title=f"Investigation {payload.case_number}",
            description=payload.description or "Auto-generated linked case",
            status="Open",
            assigned_to_id=None
        )
        db.add(case_rec)
        db.flush()
        
    row.case_id = case_rec.id
    log_audit(db, "system@sentineliq.local", "LINK_CASE", "CrimeRecord", crime_id)
    db.commit()
    db.refresh(row)
    return row_to_crime(row)

@app.get("/api/gis/geojson")
def geojson(db: Session = Depends(get_db)):
    crimes = db.scalars(select(CrimeRecord).order_by(CrimeRecord.occurred_at.desc()).limit(500)).all()
    features = []
    for c in crimes:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [c.longitude, c.latitude]
            },
            "properties": {
                "id": c.crime_id,
                "fir": c.fir,
                "type": c.category.name,
                "severity": c.severity,
                "status": c.status,
                "district": c.district.name,
                "station": c.police_station.name
            }
        })
    return {"type": "FeatureCollection", "features": features}

@app.get("/api/gis/districts")
def get_geojson_districts(db: Session = Depends(get_db)):
    # Load district polygon bounds
    districts = db.scalars(select(District)).all()
    features = []
    for d in districts:
        geom = json_loads_safe(d.polygon_geometry)
        if geom:
            features.append({
                "type": "Feature",
                "geometry": geom,
                "properties": {
                    "id": str(d.id),
                    "name": d.name,
                    "code": d.code,
                    "population": d.population
                }
            })
    return {"type": "FeatureCollection", "features": features}

@app.get("/api/gis/patrols")
def get_geojson_patrols(db: Session = Depends(get_db)):
    # Rough approximation of patrol areas as polygon buffers around their center lat/lng
    patrols = db.scalars(select(PatrolUnit)).all()
    features = []
    for p in patrols:
        radius_deg = (p.coverage_score / 100.0) * 0.02 # up to ~2km radius depending on score
        coords = []
        for i in range(8):
            angle = i * (math.pi / 4)
            clat = p.latitude + radius_deg * math.sin(angle)
            clng = p.longitude + radius_deg * math.cos(angle)
            coords.append([clng, clat])
        coords.append(coords[0])
        
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [coords]
            },
            "properties": {
                "id": str(p.id),
                "code": p.unit_code,
                "area": p.area,
                "score": p.coverage_score,
                "status": p.status
            }
        })
    return {"type": "FeatureCollection", "features": features}

def json_loads_safe(data: Optional[str]) -> Optional[dict]:
    if not data:
        return None
    try:
        import json
        return json.loads(data)
    except Exception:
        return None

@app.get("/api/gis/radius")
def radius_search(
    lat: float,
    lng: float,
    radius_km: float = Query(2.0, ge=0.1, le=50.0),
    
    db: Session = Depends(get_db)
):
    # Search crimes within bounding circle using rough degrees (1 deg lat = 111km)
    deg_offset = radius_km / 111.0
    stmt = select(CrimeRecord).where(
        (CrimeRecord.latitude >= lat - deg_offset) &
        (CrimeRecord.latitude <= lat + deg_offset) &
        (CrimeRecord.longitude >= lng - deg_offset) &
        (CrimeRecord.longitude <= lng + deg_offset)
    )
    rows = db.scalars(stmt).all()
    
    # Accurate distance calculations
    results = []
    for r in rows:
        dist = math.sqrt((r.latitude - lat)**2 + (r.longitude - lng)**2) * 111.0
        if dist <= radius_km:
            results.append(row_to_crime(r))
    return results

@app.get("/api/analytics/hotspots")
def hotspots(db: Session = Depends(get_db)):
    return ai_services.detect_hotspots(db, limit=300)

@app.get("/api/analytics/anomalies")
def anomalies(db: Session = Depends(get_db)):
    return ai_services.detect_anomalies(db, limit=300)

@app.post("/api/search")
def natural_language_search(payload: dict, db: Session = Depends(get_db)):
    query = payload.get("query", "")
    crimes, filters = ai_services.natural_language_search(db, query)
    return {
        "query": query,
        "filters": filters,
        "results": [row_to_crime(c) for c in crimes]
    }

@app.post("/api/copilot")
@limiter.limit(os.getenv("RATE_LIMIT_COPILOT", "10/minute"))
def copilot_chat(request: Request, payload: dict, db: Session = Depends(get_db)):
    query = payload.get("query", "")
    return ai_services.ask_copilot_assistant(db, query)

# --- REPORT GENERATION & EXPORTS ---

def generate_simple_pdf(title: str, lines: list[str]) -> bytes:
    # Manual PDF generator to avoid dependencies on PDF build systems
    pdf_template = (
        "%PDF-1.4\n"
        "1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
        "2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
        "3 0 obj <</Type /Page /Parent 2 0 R /Resources <</Font <</F1 4 0 R>> >> /MediaBox [0 0 595 842] /Contents 5 0 R>> endobj\n"
        "4 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold>> endobj\n"
    )
    
    content_stream = "BT /F1 16 Tf 50 800 Td (" + title + ") Tj 0 -30 Td /F1 10 Tf\n"
    content_stream += "0 -10 Td (Generated at: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ") Tj 0 -25 Td\n"
    for line in lines:
        escaped_line = line.replace("(", "\\(").replace(")", "\\)")
        content_stream += f"0 -16 Td ({escaped_line}) Tj\n"
    content_stream += "ET"
    
    content_bytes = content_stream.encode("utf-8")
    
    pdf_template += f"5 0 obj <</Length {len(content_bytes)}>> stream\n"
    pdf_template += content_stream + "\nendstream\nendobj\n"
    
    pdf_template += (
        "xref\n"
        "0 6\n"
        "0000000000 65535 f \n"
        "trailer <</Size 6 /Root 1 0 R>>\n"
        "startxref 500\n"
        "%%EOF"
    )
    return pdf_template.encode("utf-8")

@app.post("/api/reports/generate")
def create_report_record(payload: dict, db: Session = Depends(get_db)):
    report_type = payload.get("type", "weekly")
    dash = build_dashboard(db, 300)
    
    report = Report(
        id=uuid.uuid4(),
        title=f"{report_type.title()} Intelligence Report",
        report_type=report_type,
        payload=dash.model_dump_json()
    )
    db.add(report)
    db.commit()
    return {"id": report.id, "title": report.title, "reportType": report.report_type}

@app.get("/api/reports/export.csv")
def export_csv(db: Session = Depends(get_db)):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["crime_id", "fir", "type", "district", "severity", "status", "occurred_at"])
    
    crimes = db.scalars(select(CrimeRecord).order_by(CrimeRecord.occurred_at.desc()).limit(1000)).all()
    for c in crimes:
        writer.writerow([c.crime_id, c.fir, c.category.name, c.district.name, c.severity, c.status, c.occurred_at.isoformat()])
        
    return Response(
        buffer.getvalue(), 
        media_type="text/csv", 
        headers={"Content-Disposition": "attachment; filename=sentineliq-crimes.csv"}
    )

@app.get("/api/reports/export.xlsx")
def export_excel(db: Session = Depends(get_db)):
    if not HAS_PANDAS:
        # Fallback if pandas is not installed (e.g. Python 3.14 build issues)
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["Crime ID", "FIR", "Type", "District", "Severity", "Status", "Date & Time"])
        crimes = db.scalars(select(CrimeRecord).order_by(CrimeRecord.occurred_at.desc()).limit(1000)).all()
        for c in crimes:
            writer.writerow([c.crime_id, c.fir, c.category.name, c.district.name, c.severity, c.status, c.occurred_at.strftime("%Y-%m-%d %H:%M:%S")])
        return Response(
            buffer.getvalue().encode("utf-8"),
            media_type="application/vnd.ms-excel",
            headers={"Content-Disposition": "attachment; filename=sentineliq-crimes.xls"}
        )

    # Export using Pandas and IO stream
    crimes = db.scalars(select(CrimeRecord).order_by(CrimeRecord.occurred_at.desc()).limit(1000)).all()
    data = [{
        "Crime ID": c.crime_id,
        "FIR": c.fir,
        "Type": c.category.name,
        "District": c.district.name,
        "Severity": c.severity,
        "Status": c.status,
        "Date & Time": c.occurred_at.strftime("%Y-%m-%d %H:%M:%S")
    } for c in crimes]
    
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Crimes Log", index=False)
        
    return Response(
        output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=sentineliq-crimes.xlsx"}
    )

@app.get("/api/reports/export.pdf")
def export_pdf(db: Session = Depends(get_db)):
    crimes = db.scalars(select(CrimeRecord).order_by(CrimeRecord.occurred_at.desc()).limit(20)).all()
    lines = []
    for c in crimes:
        lines.append(f"{c.crime_id} | {c.fir} | {c.category.name[:12]} | {c.district.name[:15]} | {c.severity} | {c.status}")
        
    pdf_bytes = generate_simple_pdf("SentinelIQ Crime Analytics Report", lines)
    return Response(
        pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=sentineliq-crimes.pdf"}
    )

@app.post("/api/datasets/upload", response_model=DatasetUploadSummary)
@limiter.limit(os.getenv("RATE_LIMIT_UPLOAD", "5/minute"))
async def upload_dataset(
    request: Request,
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    try:
        ext = file.filename.split(".")[-1].lower()
        if ext not in ["csv", "xlsx", "json", "geojson"]:
            raise HTTPException(status_code=400, detail="Unsupported file format.")

        MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 10 * 1024 * 1024))
        content = await file.read()
        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=400, detail="File too large. Max 10MB allowed.")
        import io
        buffer = io.BytesIO(content)

        import time
        start_time = time.time()

        # Phase 10: Pandas Parsing
        import pandas as pd
        try:
            if ext == "csv":
                df = pd.read_csv(buffer)
            elif ext == "xlsx":
                df = pd.read_excel(buffer)
            elif ext == "json":
                df = pd.read_json(buffer)
            elif ext == "geojson":
                import json
                gj = json.loads(content.decode("utf-8"))
                feats = [f["properties"] | {"longitude": f["geometry"]["coordinates"][0], "latitude": f["geometry"]["coordinates"][1]} for f in gj["features"]]
                df = pd.DataFrame(feats)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")

        required_cols = {"crime_id", "date", "district", "crime_type", "latitude", "longitude", "status"}
        if not required_cols.issubset(set(df.columns)):
            raise HTTPException(status_code=400, detail=f"Missing required columns. Required: {required_cols}")

        dataset = Dataset(
            id=uuid.uuid4(),
            filename=file.filename,
            record_count=0,
            status="Processing"
        )
        db.add(dataset)
        db.flush()

        records_uploaded = len(df)
        
        missing_count = df[list(required_cols)].isnull().any(axis=1).sum()
        df = df.dropna(subset=list(required_cols)) 

        df = df.drop_duplicates(subset=["crime_id"])
        
        anomalies_mask = (df["latitude"] < -90) | (df["latitude"] > 90) | (df["longitude"] < -180) | (df["longitude"] > 180)
        anomalies_count = anomalies_mask.sum()
        df = df[~anomalies_mask] 

        valid_records = 0
        duplicates_removed = (records_uploaded - len(df)) - missing_count - anomalies_count
        
        districts = {d.name: d for d in db.scalars(select(District)).all()}
        categories = {c.name: c for c in db.scalars(select(CrimeCategory)).all()}
        existing_crimes = set(db.scalars(select(CrimeRecord.crime_id)).all())

        from datetime import datetime, timezone

        for _, row in df.iterrows():
            cid = str(row["crime_id"]).strip()
            if not cid or cid in existing_crimes:
                duplicates_removed += 1
                continue

            d_name = str(row.get("district", "Unknown District")).strip()
            c_type = str(row.get("crime_type", "Other")).strip()
            
            try:
                lat = float(row.get("latitude", 0.0))
                lng = float(row.get("longitude", 0.0))
                if isinstance(row["date"], str):
                    dt = datetime.fromisoformat(row["date"].replace("Z", "+00:00"))
                else:
                    dt = pd.to_datetime(row["date"]).to_pydatetime()
            except Exception:
                anomalies_count += 1
                continue

            if d_name not in districts:
                districts[d_name] = District(id=uuid.uuid4(), name=d_name, code=f"DST-{uuid.uuid4().hex[:6].upper()}", population=250000, latitude=lat, longitude=lng)
                db.add(districts[d_name])
                db.flush()
            
            if c_type not in categories:
                categories[c_type] = CrimeCategory(id=uuid.uuid4(), name=c_type, severity_weight=1.0)
                db.add(categories[c_type])
                db.flush()

            station = db.scalar(select(PoliceStation).where(PoliceStation.district_id == districts[d_name].id).limit(1))
            if not station:
                station = PoliceStation(id=uuid.uuid4(), name=f"{d_name} HQ", district_id=districts[d_name].id, latitude=lat, longitude=lng)
                db.add(station)
                db.flush()

            cr = CrimeRecord(
                id=uuid.uuid4(),
                crime_id=cid,
                fir=f"FIR-{cid}",
                category_id=categories[c_type].id,
                district_id=districts[d_name].id,
                police_station_id=station.id,
                status=str(row.get("status", "Open")),
                severity="Medium",
                latitude=lat,
                longitude=lng,
                occurred_at=dt,
                victim_name="Unknown",
                suspect_name="Unknown",
                source_dataset_id=dataset.id
            )
            db.add(cr)
            existing_crimes.add(cid)
            valid_records += 1

        dataset.record_count = valid_records
        dataset.status = "Completed"
        db.commit()
        
        invalidate_cache()
        elapsed = time.time() - start_time
        
        data_quality_score = max(0.0, 100.0 - ((missing_count + anomalies_count) / records_uploaded * 100)) if records_uploaded > 0 else 0.0

        await manager.broadcast({
            "type": "dataset_imported",
            "message": f"Dataset processed. Q-Score: {data_quality_score:.1f}%",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        return DatasetUploadSummary(
            records_uploaded=records_uploaded,
            valid_records=valid_records,
            duplicates_removed=int(duplicates_removed),
            anomalies_detected=int(anomalies_count),
            missing_values=int(missing_count),
            data_quality_score=data_quality_score,
            districts_updated=len(districts),
            hotspots_recalculated=0,
            processing_time=f"{elapsed:.2f}s"
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        print("UPLOAD ERROR:", err_msg)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/api/datasets/history", response_model=List[DatasetOut])
def dataset_history(db: Session = Depends(get_db)):
    datasets = db.scalars(select(Dataset).order_by(Dataset.uploaded_at.desc())).all()
    out = []
    for d in datasets:
        out.append(DatasetOut(
            id=d.id,
            filename=d.filename,
            uploaded_at=d.uploaded_at,
            record_count=d.record_count,
            status=d.status,
            uploaded_by_name=d.uploaded_by.full_name if d.uploaded_by else "System"
        ))
    return out

@app.get("/api/{resource}")
def generic_resource(
    resource: str, 
    limit: int = Query(100, ge=1, le=1000), 
    
    db: Session = Depends(get_db)
):
    # Maps generic routes to exact database tables
    if resource == "offenders":
        return ai_services.get_repeat_offender_list(db, limit)
    elif resource == "gangs":
        gangs = db.scalars(select(Gang).order_by(Gang.risk_score.desc()).limit(limit)).all()
        return [{"id": str(g.id), "name": g.name, "district": g.district_id, "riskScore": g.risk_score} for g in gangs]
    elif resource == "districts":
        districts = db.scalars(select(District).limit(limit)).all()
        return [{"id": str(d.id), "name": d.name, "code": d.code, "population": d.population} for d in districts]
    elif resource == "patrols":
        patrols = db.scalars(select(PatrolUnit).limit(limit)).all()
        return [{"route": p.unit_code, "area": p.area, "coverage": p.coverage_score, "eta": f"{p.eta_minutes} min"} for p in patrols]
    elif resource == "alerts":
        alerts = db.scalars(select(Alert).order_by(Alert.confidence.desc()).limit(limit)).all()
        return [{"id": a.alert_id, "title": a.title, "level": a.level, "reason": a.reason, "confidence": a.confidence, "action": a.action} for a in alerts]
    elif resource == "reports":
        reports = db.scalars(select(Report).order_by(Report.created_at.desc()).limit(limit)).all()
        return [{"id": str(r.id), "title": r.title, "reportType": r.report_type, "createdAt": r.created_at.isoformat()} for r in reports]
    elif resource == "cases":
        cases = db.scalars(select(Case).order_by(Case.created_at.desc()).limit(limit)).all()
        return [{"id": str(c.id), "case_number": c.case_number, "title": c.title, "status": c.status} for c in cases]
    else:
        raise HTTPException(status_code=404, detail="Resource not found")

# WebSocket Live feed
@app.websocket("/ws/live")
async def live_updates(socket: WebSocket):
    await manager.connect(socket)
    try:
        while True:
            # Periodic heartbeats
            await socket.send_json({
                "type": "heartbeat",
                "message": "SentinelIQ live channel active",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            # Wait for client input (keeps connection alive)
            await socket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(socket)


