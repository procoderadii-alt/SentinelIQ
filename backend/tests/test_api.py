import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set test environment variables
os.environ["DATABASE_URL"] = "sqlite:///./test_sentinel.db"
os.environ["SECRET_KEY"] = "test-secret-key-12345"

from database import Base, get_db
from main import app
from seed import seed_database

# Create testing engine and session
test_engine = create_engine("sqlite:///./test_sentinel.db", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    # Setup test database schema and seed initial role/users
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        # Seed database with minimal counts for fast test speed
        seed_database(db, crimes=50, offenders=5, districts=2, gangs=2, emergency_calls=5, cctv_events=5)
    finally:
        db.close()
    yield
    # Cleanup after tests
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists("./test_sentinel.db"):
        try:
            os.remove("./test_sentinel.db")
        except PermissionError:
            pass

# Override db session dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_dashboard():
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "scale" in data
    assert "incidents" in data
    assert "offenders" in data
    assert "hotspots" in data
    assert "alerts" in data

def test_crimes_crud():
    # 1. Create Crime
    crime_payload = {
        "fir": "FIR/2026/TEST001",
        "crime_type": "Theft",
        "district": "Pune Central",
        "station": "Market PS",
        "severity": "High",
        "status": "Open",
        "lat": 18.5204,
        "lng": 73.8567,
        "datetime": "2026-06-18T10:00:00Z",
        "victim": "Test Victim",
        "suspect": "Unknown",
        "evidence": 2
    }
    create_resp = client.post("/api/crimes", json=crime_payload)
    assert create_resp.status_code == 201
    created_crime = create_resp.json()
    assert created_crime["fir"] == "FIR/2026/TEST001"
    crime_id = created_crime["id"]
    
    # 2. List Crimes
    list_resp = client.get(f"/api/crimes?q=TEST001")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1
    
    # 3. Update Crime
    crime_payload["status"] = "Under Investigation"
    update_resp = client.put(f"/api/crimes/{crime_id}", json=crime_payload)
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "Under Investigation"
    
    # 4. Delete Crime
    delete_resp = client.delete(f"/api/crimes/{crime_id}")
    assert delete_resp.status_code == 204

def test_analytics():
    hotspots_resp = client.get("/api/analytics/hotspots")
    assert hotspots_resp.status_code == 200
    assert isinstance(hotspots_resp.json(), list)
    
    anomalies_resp = client.get("/api/analytics/anomalies")
    assert anomalies_resp.status_code == 200
    assert isinstance(anomalies_resp.json(), list)

def test_search_and_copilot():
    search_resp = client.post("/api/search", json={"query": "Show Theft cases in Pune"})
    assert search_resp.status_code == 200
    assert "results" in search_resp.json()
    
    copilot_resp = client.post("/api/copilot", json={"query": "Identify active hotspots"})
    assert copilot_resp.status_code == 200
    assert "answer" in copilot_resp.json()

def test_reports_exports():
    csv_resp = client.get("/api/reports/export.csv")
    assert csv_resp.status_code == 200
    assert csv_resp.headers["content-type"] == "text/csv; charset=utf-8"
    
    pdf_resp = client.get("/api/reports/export.pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    
    xlsx_resp = client.get("/api/reports/export.xlsx")
    assert xlsx_resp.status_code == 200
    assert xlsx_resp.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
