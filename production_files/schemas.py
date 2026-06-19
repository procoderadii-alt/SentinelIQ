from __future__ import annotations
from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict[str, Any]

class LoginRequest(BaseModel):
    email: str
    password: str

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: str
    full_name: str
    is_active: bool
    role: str

class PermissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: str

class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    permissions: list[PermissionOut]

class CrimeIn(BaseModel):
    fir: str
    type: str = Field(alias="crime_type")
    district: str
    station: str
    severity: Literal["Low", "Medium", "High", "Critical"]
    status: Literal["Open", "Under Investigation", "Solved", "Escalated"]
    lat: float
    lng: float
    datetime: datetime
    victim: str
    suspect: str = "Unknown"
    evidence: int = 0

class CrimeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str  # maps to crime_id in DB (e.g. CR-123456)
    fir: str
    type: str
    category: str
    severity: str
    status: str
    district: str
    station: str
    lat: float
    lng: float
    datetime: datetime
    victim: str
    suspect: str
    evidence: int

class OffenderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str # offender_id
    name: str
    gang: str
    riskScore: int
    arrests: int
    lastActivity: str
    area: str
    probability: int

class HotspotOut(BaseModel):
    id: str
    name: str
    district: str
    lat: float
    lng: float
    score: int
    confidence: int
    category: str
    why: str
    incidents: int

class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str # alert_id
    title: str
    level: str
    reason: str
    confidence: int
    action: str

class ForecastOut(BaseModel):
    horizon: str
    predicted: int
    low: int
    high: int
    confidence: int

class DistrictStatsOut(BaseModel):
    district: str
    crimes: int
    rate: float
    arrestRate: int
    patrol: int
    hotspots: int
    income: int
    literacy: int
    unemployment: float
    theftIndex: int

class NetworkNodeOut(BaseModel):
    id: str
    label: str
    type: str
    x: float
    y: float
    weight: int

class NetworkEdgeOut(BaseModel):
    source: str
    target: str
    strength: int

class PatrolRouteOut(BaseModel):
    route: str
    area: str
    coverage: int
    eta: str

class DashboardPayload(BaseModel):
    scale: dict[str, int]
    incidents: list[CrimeOut]
    offenders: list[OffenderOut]
    hotspots: list[HotspotOut]
    alerts: list[AlertOut]
    monthlyTrend: list[dict[str, Any]]
    districtStats: list[DistrictStatsOut]
    forecast: list[ForecastOut]
    networkNodes: list[NetworkNodeOut]
    networkEdges: list[NetworkEdgeOut]
    categoryBreakdown: list[dict[str, Any]]
    cctvEvents: list[str]
    patrolRoutes: list[PatrolRouteOut]

class SearchResult(BaseModel):
    query: str
    filters: dict[str, str]
    results: list[CrimeOut]

class CopilotResult(BaseModel):
    answer: str
    sources: list[str]

class ReportOut(BaseModel):
    id: UUID
    title: str
    reportType: str
    createdAt: str

class DatasetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    filename: str
    uploaded_at: datetime
    record_count: int
    status: str
    uploaded_by_name: str = "System"

class DatasetUploadSummary(BaseModel):
    records_uploaded: int
    valid_records: int
    duplicates_removed: int
    districts_updated: int
    hotspots_recalculated: int
    processing_time: str
