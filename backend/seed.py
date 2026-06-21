import json
import math
import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine
from models import (
    Role,
    Permission,
    User,
    District,
    PoliceStation,
    CrimeCategory,
    CrimeRecord,
    Victim,
    Suspect,
    Offender,
    Gang,
    GangMember,
    Vehicle,
    Phone,
    Evidence,
    Case,
    CaseNote,
    PatrolUnit,
    EmergencyCall,
    CctvEvent,
    Alert,
    RiskPrediction,
    SocioeconomicData,
    CriminalRelationship,
    AuditLog,
    role_permissions
)
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def make_polygon_geojson(lat: float, lng: float, radius: float = 0.015) -> str:
    coords = []
    # Create an octagon geometry
    for i in range(8):
        angle = i * (math.pi / 4)
        clat = lat + radius * math.sin(angle) + random.uniform(-0.002, 0.002)
        clng = lng + radius * math.cos(angle) + random.uniform(-0.002, 0.002)
        coords.append([clng, clat])
    coords.append(coords[0]) # close polygon
    return json.dumps({
        "type": "Polygon",
        "coordinates": [coords]
    })

def seed_database(db: Session, crimes: int = 50000, offenders: int = 5000, districts: int = 100, gangs: int = 500, emergency_calls: int = 10000, cctv_events: int = 20000) -> None:
    print("Initiating PostgreSQL Database Seeding...")
    
    # Check if database has been seeded already
    existing_users = db.scalar(select(User))
    if existing_users is not None:
        print("Database already seeded. Skipping seeder.")
        return

    # 1. Create Permissions
    permission_names = [
        ("View Data", "Can view all dashboards, maps, and crime data"),
        ("Edit Data", "Can add/modify crime records and incidents"),
        ("Delete Data", "Can delete crime records"),
        ("Generate Reports", "Can compile and export data reports"),
        ("Manage Users", "Can configure administration settings and roles"),
        ("Access AI Services", "Can access copilot and predictive intelligence models")
    ]
    permission_dict = {}
    for name, desc in permission_names:
        perm = Permission(name=name, description=desc)
        db.add(perm)
        permission_dict[name] = perm
    db.flush()

    # 2. Create Roles
    role_permissions_map = {
        "Admin": ["View Data", "Edit Data", "Delete Data", "Generate Reports", "Manage Users", "Access AI Services"],
        "Commissioner": ["View Data", "Generate Reports", "Access AI Services"],
        "SP": ["View Data", "Generate Reports", "Access AI Services"],
        "Inspector": ["View Data", "Edit Data", "Generate Reports"],
        "Officer": ["View Data", "Edit Data"],
        "Analyst": ["View Data", "Generate Reports", "Access AI Services"],
        "Viewer": ["View Data"]
    }
    
    role_dict = {}
    for role_name, perms in role_permissions_map.items():
        role = Role(name=role_name)
        role.permissions = [permission_dict[p] for p in perms]
        db.add(role)
        role_dict[role_name] = role
    db.flush()

    # 3. Create Users
    users_to_create = [
        ("admin@sentineliq.local", "SentinelIQ Administrator", "Admin"),
        ("commissioner@sentineliq.local", "Commissioner of Police", "Commissioner"),
        ("sp@sentineliq.local", "Superintendent of Police", "SP"),
        ("inspector@sentineliq.local", "Station Inspector", "Inspector"),
        ("officer@sentineliq.local", "Patrol Officer", "Officer"),
        ("analyst@sentineliq.local", "SentinelIQ Analyst", "Analyst"),
        ("viewer@sentineliq.local", "Dashboard Viewer", "Viewer"),
    ]
    
    for email, full_name, role_name in users_to_create:
        u = User(
            email=email,
            full_name=full_name,
            hashed_password=hash_password("SentinelIQ@123"),
            role=role_dict[role_name],
            failed_login_attempts=0,
            mfa_enabled=False
        )
        if role_name == "Admin":
            admin_user = u
        db.add(u)
        
    db.flush()

    # 4. Create Districts (100)
    base_districts = [
        "Pune Central", "Shivajinagar", "Kothrud", "Hadapsar", "Hinjawadi", 
        "Wakad", "Kondhwa", "Aundh", "Viman Nagar", "Yerawada", "Baner", "Swargate"
    ]
    
    print(f"Generating {districts} Districts...")
    districts_list = []
    for i in range(districts):
        name = base_districts[i % len(base_districts)] if i < len(base_districts) else f"District Beat {i + 1}"
        if i >= len(base_districts):
            name = f"{name} ({random.choice(['East', 'West', 'North', 'South', 'Outer'])})"
        
        # Center around Pune (18.5204, 73.8567)
        lat = 18.5204 + random.uniform(-0.15, 0.15)
        lng = 73.8567 + random.uniform(-0.15, 0.15)
        
        d = District(
            id=uuid.uuid4(),
            name=name,
            code=f"DST-{i + 1:03d}",
            population=random.randint(100000, 950000),
            latitude=lat,
            longitude=lng,
            polygon_geometry=make_polygon_geojson(lat, lng, radius=random.uniform(0.008, 0.02))
        )
        districts_list.append(d)
        db.add(d)
    db.flush()

    # 5. Create Police Stations
    print("Generating Police Stations...")
    stations_list = []
    for d in districts_list:
        for j in range(2):
            station = PoliceStation(
                id=uuid.uuid4(),
                name=f"{d.name} PS {j + 1}",
                district_id=d.id,
                latitude=d.latitude + random.uniform(-0.005, 0.005),
                longitude=d.longitude + random.uniform(-0.005, 0.005)
            )
            stations_list.append(station)
            db.add(station)
    db.flush()

    # 6. Create Crime Categories
    print("Generating Crime Categories...")
    crime_types = [
        ("Theft", 1.0),
        ("Assault", 1.5),
        ("Robbery", 2.0),
        ("Cybercrime", 1.2),
        ("Drug Case", 1.8),
        ("Missing Person", 1.0),
        ("Fraud", 1.1),
        ("Extortion", 1.6)
    ]
    categories_list = []
    for name, weight in crime_types:
        cat = CrimeCategory(id=uuid.uuid4(), name=name, severity_weight=weight)
        categories_list.append(cat)
        db.add(cat)
    db.flush()

    # 7. Create Gangs (500)
    print(f"Generating {gangs} Gangs...")
    gangs_list = []
    for i in range(gangs):
        g = Gang(
            id=uuid.uuid4(),
            name=f"Cell-{random.choice(['Alpha', 'Beta', 'Gamma', 'Delta', 'Sigma', 'Zeta'])}-{i+1:03d}",
            district_id=random.choice(districts_list).id,
            risk_score=random.randint(30, 99)
        )
        gangs_list.append(g)
        db.add(g)
    db.flush()

    # 8. Create Offenders (5000)
    print(f"Generating {offenders} Offenders...")
    offenders_data = []
    first_names = ["Arjun", "Rafiq", "Nilesh", "Vikram", "Sameer", "Prakash", "Karan", "Rahul", "Aarav", "Amit"]
    last_names = ["Kale", "Shaikh", "Pawar", "Joshi", "Khan", "More", "Sharma", "Patil", "Deshmukh", "Kulkarni"]
    
    offenders_objs = []
    for i in range(offenders):
        o_id = uuid.uuid4()
        off_code = f"OF-{i + 1:04d}"
        name = f"{random.choice(first_names)} {random.choice(last_names)} {i + 1}"
        gang = random.choice(gangs_list) if random.random() > 0.4 else None
        gang_name = gang.name if gang else ""
        
        off = Offender(
            id=o_id,
            offender_id=off_code,
            name=name,
            gang_name=gang_name,
            risk_score=random.randint(35, 100),
            arrests=random.randint(1, 25),
            last_activity=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 90)),
            area=random.choice(districts_list).name,
            recidivism_probability=random.randint(28, 98)
        )
        offenders_objs.append(off)
        db.add(off)
        
        if gang:
            # Associate in gang_members table
            member = GangMember(
                id=uuid.uuid4(),
                gang_id=gang.id,
                offender_id=o_id,
                role_in_gang=random.choices(["Leader", "Lieutenant", "Member"], weights=[5, 15, 80], k=1)[0]
            )
            db.add(member)
            
    db.flush()

    # 9. Create Patrol Units (12)
    print("Generating Patrol Units...")
    patrol_units_list = []
    for i in range(12):
        p = PatrolUnit(
            id=uuid.uuid4(),
            unit_code=f"V-{i + 1:02d}",
            area=districts_list[i % len(districts_list)].name,
            coverage_score=random.randint(68, 96),
            eta_minutes=random.randint(8, 31),
            latitude=districts_list[i % len(districts_list)].latitude,
            longitude=districts_list[i % len(districts_list)].longitude,
            status="Active"
        )
        patrol_units_list.append(p)
        db.add(p)
    db.flush()

    # 10. Generate 50,000 Crime Records, Cases, Victims, Suspects
    print(f"Bulk Seeding {crimes:,} Crime Records (this may take a moment)...")
    
    # Pre-generate some Case containers
    cases_list = []
    for i in range(1000): # 1000 cases containing multiple crimes
        c = Case(
            id=uuid.uuid4(),
            case_number=f"CASE-2026-{i+1:04d}",
            title=f"Complex Organized {random.choice(categories_list).name} Investigation",
            description="Multi-district intelligence tracking, vehicle overlays, and cell phone records check.",
            status=random.choice(["Open", "Under Investigation", "Solved"]),
            assigned_to_id=admin_user.id
        )
        cases_list.append(c)
        db.add(c)
    db.flush()

    crimes_to_insert = []
    victims_to_insert = []
    suspects_to_insert = []
    evidence_to_insert = []
    vehicles_to_insert = []
    phones_to_insert = []
    
    statuses = ["Open", "Under Investigation", "Solved", "Escalated"]
    severities = ["Low", "Medium", "High", "Critical"]
    victim_first_names = ["Priya", "Anjali", "Suresh", "Ramesh", "Deepa", "Sunita", "Vijay", "Anand"]
    victim_last_names = ["Deshpande", "Joshi", "Bhosale", "Kadam", "Shinde", "Deshmukh", "Nair", "Rao"]
    
    now = datetime.now(timezone.utc)
    
    for i in range(crimes):
        c_id = uuid.uuid4()
        district = random.choice(districts_list)
        # Filter stations in this district
        stations = [s for s in stations_list if s.district_id == district.id]
        station = random.choice(stations) if stations else random.choice(stations_list)
        category = random.choice(categories_list)
        occurred = now - timedelta(
            days=random.randint(0, 365),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        # Link some crimes to cases
        case = random.choice(cases_list) if random.random() > 0.88 else None
        
        crime_rec = CrimeRecord(
            id=c_id,
            crime_id=f"CR-{240000 + i:06d}",
            fir=f"FIR/2026/{1000 + i}",
            category_id=category.id,
            district_id=district.id,
            police_station_id=station.id,
            status=random.choice(statuses),
            severity=random.choices(severities, weights=[35, 35, 22, 8], k=1)[0],
            latitude=district.latitude + random.uniform(-0.06, 0.06),
            longitude=district.longitude + random.uniform(-0.06, 0.06),
            occurred_at=occurred,
            victim_name=f"{random.choice(victim_first_names)} {random.choice(victim_last_names)} {i + 1}",
            suspect_name=random.choice(offenders_objs).name if random.random() > 0.3 else "Unknown",
            evidence_count=random.randint(0, 6),
            narrative=f"Reported incident of {category.name} in the beats of {district.name}. Followed up by {station.name}.",
            case_id=case.id if case else None
        )
        db.add(crime_rec)
        
        # 11. Relational Entities (Victims, Suspects, Evidence, Vehicles, Phones)
        # Create corresponding Victim record
        v_id = uuid.uuid4()
        victim = Victim(
            id=v_id,
            name=crime_rec.victim_name,
            age=random.randint(18, 75),
            gender=random.choice(["Male", "Female"]),
            contact_info=f"+91 98230 {random.randint(10000, 99999)}",
            crime_record_id=c_id
        )
        db.add(victim)
        
        # Create corresponding Suspect record if not Unknown
        if crime_rec.suspect_name != "Unknown":
            s_id = uuid.uuid4()
            suspect = Suspect(
                id=s_id,
                name=crime_rec.suspect_name,
                age=random.randint(18, 55),
                gender="Male",
                physical_description="Identified by matching CCTV footprint or repeat offender catalog.",
                crime_record_id=c_id,
                case_id=case.id if case else None
            )
            db.add(suspect)
            
        # Add Evidence records
        if crime_rec.evidence_count > 0:
            for ev_idx in range(crime_rec.evidence_count):
                evidence = Evidence(
                    id=uuid.uuid4(),
                    evidence_code=f"EVID-{i:06d}-{ev_idx}",
                    crime_record_id=c_id,
                    description=f"CCTV footage / physical evidence for {category.name}",
                    file_path=f"/evidence/CR-{240000 + i:06d}_{ev_idx}.jpg",
                    file_type="image/jpeg"
                )
                db.add(evidence)
                
        # Link Phone/Vehicle
        if random.random() > 0.9:
            vehicle = Vehicle(
                id=uuid.uuid4(),
                plate_number=f"MH-12-{"".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=2))}-{random.randint(1000, 9999)}",
                model=random.choice(["Honda Activa", "Maruti Swift", "Hyundai i20", "Bajaj Pulsar"]),
                color=random.choice(["Black", "White", "Silver", "Red"]),
                owner_name=f"Owner {i}",
                suspected_crime_id=c_id
            )
            db.add(vehicle)
            
        if random.random() > 0.9:
            phone = Phone(
                id=uuid.uuid4(),
                phone_number=f"+91 99220 {random.randint(10000, 99999)}",
                imei=f"86100704{random.randint(1000000, 9999999)}",
                owner_name=f"Owner {i}",
                suspected_crime_id=c_id
            )
            db.add(phone)
            
        # Commit in batches of 5000 to keep memory low
        if i > 0 and i % 5000 == 0:
            db.flush()
            print(f"  Flushed {i} crimes...")
            
    db.flush()
    print("Crime Records seeded successfully.")

    # 12. Create Emergency Calls (10,000)
    print(f"Generating {emergency_calls:,} Emergency Calls...")
    for i in range(emergency_calls):
        call_district = random.choice(districts_list)
        c = EmergencyCall(
            id=uuid.uuid4(),
            call_id=f"EC-{100000 + i:06d}",
            caller_number=f"+91 90110 {random.randint(10000, 99999)}",
            latitude=call_district.latitude + random.uniform(-0.04, 0.04),
            longitude=call_district.longitude + random.uniform(-0.04, 0.04),
            description=random.choice([
                "Suspicious noise near residential building.",
                "Two-wheeler collision on main crossing.",
                "Report of purse snatching near bus terminal.",
                "Assault report inside commercial area.",
                "Siren heard/alarm system triggered."
            ]),
            status=random.choice(["Pending", "Dispatched", "Resolved"]),
            dispatch_unit_id=random.choice(patrol_units_list).id if random.random() > 0.5 else None
        )
        db.add(c)
        if i % 5000 == 0:
            db.flush()

    # 13. Create CCTV Events (20,000)
    print(f"Generating {cctv_events:,} CCTV Events...")
    cctv_logs = [
        "Face match near transit junction",
        "Unregistered vehicle convoy detected",
        "Crowd density threshold breached at crossing",
        "Suspicious loitering event matched to open FIR",
        "Speed limit breach in narrow lane"
    ]
    for i in range(cctv_events):
        e_district = random.choice(districts_list)
        c = CctvEvent(
            id=uuid.uuid4(),
            event_id=f"CCTV-{200000 + i:06d}",
            camera_code=f"C-{random.randint(10, 99):02d}",
            location=f"{e_district.name} Junction {random.randint(1, 5)}",
            event_type=random.choice(["Face Recognition", "Vehicle Analytics", "Crowd Sensing", "Intrusion Detection"]),
            description=random.choice(cctv_logs) + f" #{i}",
            confidence_score=round(random.uniform(70.0, 99.8), 2),
            occurred_at=now - timedelta(days=random.randint(0, 30), minutes=random.randint(0, 1440))
        )
        db.add(c)
        if i % 5000 == 0:
            db.flush()

    # 14. Create Alerts (4)
    print("Generating Watchlist Alerts...")
    db.add(Alert(alert_id="AL-01", title="Robbery spike near transit exits", level="Red", reason="7-day robbery volume is above district baseline after 21:00.", confidence=94, action="Deploy two mobile patrol units and query repeat offenders within 3 km.", resolved=False))
    db.add(Alert(alert_id="AL-02", title="Cyber fraud cluster emerging", level="Orange", reason="Common phone and payment handles appear across FIR narratives.", confidence=88, action="Prioritize cyber-cell triage and issue public advisory.", resolved=False))
    db.add(Alert(alert_id="AL-03", title="Drug case displacement", level="Yellow", reason="Incidents moved from a known hotspot into adjacent residential beat.", confidence=81, action="Shift patrol window and inspect CCTV routes.", resolved=False))
    db.add(Alert(alert_id="AL-04", title="Assault activity normalizing", level="Green", reason="Weekend assault count returned within expected confidence interval.", confidence=73, action="Maintain baseline coverage.", resolved=True))

    # 15. Create District Socioeconomic Data & predictions
    print("Generating Socioeconomic Data and Predictions...")
    for index, district in enumerate(districts_list):
        lit = round(random.uniform(61.0, 95.0), 2)
        pov = round(random.uniform(3.0, 28.0), 2)
        unemp = round(random.uniform(3.0, 17.0), 2)
        income = round(28000.0 + lit * 780.0, 2)
        
        se = SocioeconomicData(
            id=uuid.uuid4(),
            district_id=district.id,
            literacy_rate=lit,
            poverty_rate=pov,
            unemployment_rate=unemp,
            average_income=income
        )
        db.add(se)
        
        # Risk predictions (7, 30, 90 days)
        for horizon, days in [("7 Days", 7), ("30 Days", 30), ("90 Days", 90)]:
            pred_count = random.randint(10, 80) * (days // 7)
            db.add(RiskPrediction(
                id=uuid.uuid4(),
                district_id=district.id,
                horizon=horizon,
                predicted_crime_count=pred_count,
                low_confidence_boundary=max(1, round(pred_count * 0.85)),
                high_confidence_boundary=round(pred_count * 1.15),
                confidence_score=random.randint(70, 95)
            ))
            
    # 16. Criminal Relationships
    print("Generating Criminal Relationships...")
    for idx in range(1000):
        o1 = random.choice(offenders_objs)
        o2 = random.choice(offenders_objs)
        if o1.id != o2.id:
            rel = CriminalRelationship(
                id=uuid.uuid4(),
                source_offender_id=o1.id,
                target_offender_id=o2.id,
                relationship_type=random.choice(["Gang Associate", "Co-arrestee", "Phone Contact", "Family"]),
                strength=random.randint(10, 100)
            )
            db.add(rel)

    db.commit()
    print("Database seeding completed successfully.")

def run() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        # Seeding high-volume target data
        seed_database(db, crimes=50000, offenders=5000, districts=100, gangs=500, emergency_calls=10000, cctv_events=20000)

if __name__ == "__main__":
    run()
