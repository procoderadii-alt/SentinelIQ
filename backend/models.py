import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UUID,
    Table,
    Column,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class Dataset(Base):
    __tablename__ = "datasets"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(String(255))
    uploaded_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    record_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(40), default="Processing")
    
    uploaded_by: Mapped[Optional["User"]] = relationship("User")
    crime_records: Mapped[list["CrimeRecord"]] = relationship("CrimeRecord", back_populates="source_dataset")


# Many-to-many relationship for Roles and Permissions
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

class Permission(Base, TimestampMixin):
    __tablename__ = "permissions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(255), default="")

class Role(Base, TimestampMixin):
    __tablename__ = "roles"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    permissions: Mapped[list[Permission]] = relationship(
        "Permission",
        secondary=role_permissions,
        lazy="joined"
    )
    users: Mapped[list["User"]] = relationship("User", back_populates="role")

class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160))
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("roles.id"), index=True)
    role: Mapped[Role] = relationship("Role", back_populates="users", lazy="joined")

class District(Base, TimestampMixin):
    __tablename__ = "districts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    population: Mapped[int] = mapped_column(Integer)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    polygon_geometry: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # GeoJSON string
    
    stations: Mapped[list["PoliceStation"]] = relationship("PoliceStation", back_populates="district")
    socioeconomic_data: Mapped[list["SocioeconomicData"]] = relationship("SocioeconomicData", back_populates="district")

class PoliceStation(Base, TimestampMixin):
    __tablename__ = "police_stations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(140), index=True)
    district_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("districts.id"), index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    
    district: Mapped[District] = relationship("District", back_populates="stations")

class CrimeCategory(Base, TimestampMixin):
    __tablename__ = "crime_categories"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    severity_weight: Mapped[float] = mapped_column(Float, default=1.0)

class Case(Base, TimestampMixin):
    __tablename__ = "cases"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_number: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), index=True, default="Open")
    assigned_to_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    
    crime_records: Mapped[list["CrimeRecord"]] = relationship("CrimeRecord", back_populates="case")
    notes: Mapped[list["CaseNote"]] = relationship("CaseNote", back_populates="case", cascade="all, delete-orphan")
    suspects: Mapped[list["Suspect"]] = relationship("Suspect", back_populates="case")

class CrimeRecord(Base, TimestampMixin):
    __tablename__ = "crime_records"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crime_id: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    fir: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crime_categories.id"), index=True)
    district_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("districts.id"), index=True)
    police_station_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("police_stations.id"), index=True)
    status: Mapped[str] = mapped_column(String(40), index=True)
    severity: Mapped[str] = mapped_column(String(20), index=True)
    latitude: Mapped[float] = mapped_column(Float, index=True)
    longitude: Mapped[float] = mapped_column(Float, index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    victim_name: Mapped[str] = mapped_column(String(140))
    suspect_name: Mapped[str] = mapped_column(String(140), default="Unknown")
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    narrative: Mapped[str] = mapped_column(Text, default="")
    case_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=True, index=True)
    source_dataset_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=True, index=True)
    
    category: Mapped[CrimeCategory] = relationship("CrimeCategory", lazy="joined")
    district: Mapped[District] = relationship("District", lazy="joined")
    police_station: Mapped[PoliceStation] = relationship("PoliceStation", lazy="joined")
    case: Mapped[Optional[Case]] = relationship("Case", back_populates="crime_records")
    source_dataset: Mapped[Optional["Dataset"]] = relationship("Dataset", back_populates="crime_records")
    victims: Mapped[list["Victim"]] = relationship("Victim", back_populates="crime_record", cascade="all, delete-orphan")
    suspects: Mapped[list["Suspect"]] = relationship("Suspect", back_populates="crime_record", cascade="all, delete-orphan")
    evidences: Mapped[list["Evidence"]] = relationship("Evidence", back_populates="crime_record", cascade="all, delete-orphan")
    vehicles: Mapped[list["Vehicle"]] = relationship("Vehicle", back_populates="suspected_crime")
    phones: Mapped[list["Phone"]] = relationship("Phone", back_populates="suspected_crime")

class Victim(Base, TimestampMixin):
    __tablename__ = "victims"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(140), index=True)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    contact_info: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    crime_record_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("crime_records.id"), nullable=True, index=True)
    
    crime_record: Mapped[Optional[CrimeRecord]] = relationship("CrimeRecord", back_populates="victims")

class Suspect(Base, TimestampMixin):
    __tablename__ = "suspects"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(140), index=True)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    physical_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    crime_record_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("crime_records.id"), nullable=True, index=True)
    case_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=True, index=True)
    
    crime_record: Mapped[Optional[CrimeRecord]] = relationship("CrimeRecord", back_populates="suspects")
    case: Mapped[Optional[Case]] = relationship("Case", back_populates="suspects")

class Gang(Base, TimestampMixin):
    __tablename__ = "gangs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    district_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("districts.id"), index=True)
    risk_score: Mapped[int] = mapped_column(Integer, index=True)
    
    members: Mapped[list["GangMember"]] = relationship("GangMember", back_populates="gang", cascade="all, delete-orphan")

class Offender(Base, TimestampMixin):
    __tablename__ = "offenders"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    offender_id: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(140), index=True)
    gang_name: Mapped[str] = mapped_column(String(120), index=True, default="")
    risk_score: Mapped[int] = mapped_column(Integer, index=True)
    arrests: Mapped[int] = mapped_column(Integer, default=0)
    last_activity: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    area: Mapped[str] = mapped_column(String(120), index=True)
    recidivism_probability: Mapped[int] = mapped_column(Integer)
    
    gang_memberships: Mapped[list["GangMember"]] = relationship("GangMember", back_populates="offender", cascade="all, delete-orphan")

class GangMember(Base, TimestampMixin):
    __tablename__ = "gang_members"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gang_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("gangs.id"), index=True)
    offender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("offenders.id"), index=True)
    role_in_gang: Mapped[str] = mapped_column(String(60), default="Member")
    
    gang: Mapped[Gang] = relationship("Gang", back_populates="members")
    offender: Mapped[Offender] = relationship("Offender", back_populates="gang_memberships")

class Vehicle(Base, TimestampMixin):
    __tablename__ = "vehicles"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plate_number: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    model: Mapped[str] = mapped_column(String(120))
    color: Mapped[str] = mapped_column(String(40))
    owner_name: Mapped[str] = mapped_column(String(140))
    suspected_crime_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("crime_records.id"), nullable=True, index=True)
    
    suspected_crime: Mapped[Optional[CrimeRecord]] = relationship("CrimeRecord", back_populates="vehicles")

class Phone(Base, TimestampMixin):
    __tablename__ = "phones"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    imei: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    owner_name: Mapped[str] = mapped_column(String(140))
    suspected_crime_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("crime_records.id"), nullable=True, index=True)
    
    suspected_crime: Mapped[Optional[CrimeRecord]] = relationship("CrimeRecord", back_populates="phones")

class Evidence(Base, TimestampMixin):
    __tablename__ = "evidence"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evidence_code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    crime_record_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crime_records.id"), index=True)
    description: Mapped[str] = mapped_column(Text)
    file_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_type: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    
    crime_record: Mapped[CrimeRecord] = relationship("CrimeRecord", back_populates="evidences")

class CaseNote(Base, TimestampMixin):
    __tablename__ = "case_notes"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cases.id"), index=True)
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    note: Mapped[str] = mapped_column(Text)
    
    case: Mapped[Case] = relationship("Case", back_populates="notes")
    author: Mapped[User] = relationship("User", lazy="joined")

class PatrolUnit(Base, TimestampMixin):
    __tablename__ = "patrol_units"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    unit_code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    area: Mapped[str] = mapped_column(String(120), index=True)
    coverage_score: Mapped[int] = mapped_column(Integer)
    eta_minutes: Mapped[int] = mapped_column(Integer)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(40), default="Active")

class EmergencyCall(Base, TimestampMixin):
    __tablename__ = "emergency_calls"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_id: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    caller_number: Mapped[str] = mapped_column(String(40), index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), index=True, default="Pending")
    dispatch_unit_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("patrol_units.id"), nullable=True, index=True)
    
    dispatch_unit: Mapped[Optional[PatrolUnit]] = relationship("PatrolUnit")

class CctvEvent(Base, TimestampMixin):
    __tablename__ = "cctv_events"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    camera_code: Mapped[str] = mapped_column(String(40), index=True)
    location: Mapped[str] = mapped_column(String(160))
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    description: Mapped[str] = mapped_column(Text)
    confidence_score: Mapped[float] = mapped_column(Float)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

class Alert(Base, TimestampMixin):
    __tablename__ = "alerts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    level: Mapped[str] = mapped_column(String(20), index=True)
    reason: Mapped[str] = mapped_column(Text)
    confidence: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(Text)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)

class RiskPrediction(Base, TimestampMixin):
    __tablename__ = "risk_predictions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    district_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("districts.id"), index=True)
    horizon: Mapped[str] = mapped_column(String(40), index=True)
    predicted_crime_count: Mapped[int] = mapped_column(Integer)
    low_confidence_boundary: Mapped[int] = mapped_column(Integer)
    high_confidence_boundary: Mapped[int] = mapped_column(Integer)
    confidence_score: Mapped[int] = mapped_column(Integer)
    
    district: Mapped[District] = relationship("District")

class SocioeconomicData(Base, TimestampMixin):
    __tablename__ = "socioeconomic_data"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    district_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("districts.id"), index=True)
    literacy_rate: Mapped[float] = mapped_column(Float)
    poverty_rate: Mapped[float] = mapped_column(Float)
    unemployment_rate: Mapped[float] = mapped_column(Float)
    average_income: Mapped[float] = mapped_column(Float)
    
    district: Mapped[District] = relationship("District", back_populates="socioeconomic_data")

class CriminalRelationship(Base, TimestampMixin):
    __tablename__ = "criminal_relationships"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_offender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("offenders.id"), index=True)
    target_offender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("offenders.id"), index=True)
    relationship_type: Mapped[str] = mapped_column(String(80))
    strength: Mapped[int] = mapped_column(Integer)
    
    source: Mapped[Offender] = relationship("Offender", foreign_keys=[source_offender_id])
    target: Mapped[Offender] = relationship("Offender", foreign_keys=[target_offender_id])

class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor: Mapped[str] = mapped_column(String(160), index=True)
    action: Mapped[str] = mapped_column(String(80), index=True)
    entity: Mapped[str] = mapped_column(String(80), index=True)
    entity_id: Mapped[str] = mapped_column(String(80), index=True)

class Report(Base, TimestampMixin):
    __tablename__ = "reports"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200), index=True)
    report_type: Mapped[str] = mapped_column(String(60), index=True)
    payload: Mapped[str] = mapped_column(Text)
    generated_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    generated_by: Mapped[Optional[User]] = relationship("User")
