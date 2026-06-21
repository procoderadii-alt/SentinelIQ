import sys
import requests
import time
import os
import subprocess

BASE_URL = "http://127.0.0.1:8000"

def test():
    print("Starting uvicorn server in background...")
    proc = subprocess.Popen(["python", "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"])
    
    # Wait for server
    for i in range(30):
        try:
            requests.get(f"{BASE_URL}/health")
            break
        except:
            time.sleep(1)
    else:
        print("Server failed to start")
        proc.kill()
        sys.exit(1)

    print("\n--- RUNNING TESTS ---\n")
    
    # 1. Health
    print("GET /health")
    r = requests.get(f"{BASE_URL}/health")
    print(r.status_code)
    print(r.text)
    
    # 2. Dashboard
    print("\nGET /api/dashboard")
    r = requests.get(f"{BASE_URL}/api/dashboard")
    print(r.status_code)
    print(r.text[:200] + "...") # truncate
    
    # 3. POST Crime
    print("\nPOST /api/crimes")
    payload = {
        "fir": "TEST-123",
        "crime_type": "Theft",
        "category": "Theft",
        "severity": "High",
        "status": "Open",
        "district": "Pune Central",
        "station": "Pune Central PS 1",
        "lat": 18.5204,
        "lng": 73.8567,
        "datetime": "2026-06-20T12:00:00Z",
        "victim": "John Doe",
        "suspect": "Unknown"
    }
    r = requests.post(f"{BASE_URL}/api/crimes", json=payload)
    print(r.status_code)
    print(r.text)
    crime_id = r.json().get("id")
    
    # GET Crime
    print(f"\nGET /api/crimes (to find {crime_id})")
    r = requests.get(f"{BASE_URL}/api/crimes")
    crimes = r.json()
    found = any(c.get("id") == crime_id for c in crimes)
    print(r.status_code, "Found newly posted crime:", found)
    
    # DELETE Crime
    print(f"\nDELETE /api/crimes/{crime_id}")
    r = requests.delete(f"{BASE_URL}/api/crimes/{crime_id}")
    print(r.status_code)
    print(r.text)
    
    # GET Crime again
    print(f"\nGET /api/crimes (to confirm {crime_id} is hidden)")
    r = requests.get(f"{BASE_URL}/api/crimes")
    crimes = r.json()
    found = any(c.get("id") == crime_id for c in crimes)
    print(r.status_code, "Found crime after delete:", found)
    
    # Check DB directly
    print("\nCheck DB for soft delete")
    import sqlite3
    db_path = os.path.join(os.getcwd(), "backend", "sentineliq.db")
    if not os.path.exists(db_path):
        db_path = os.path.join(os.getcwd(), "sentineliq.db")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT is_deleted FROM crime_records WHERE id=?", (crime_id,))
    row = c.fetchone()
    print("DB raw is_deleted:", row[0] if row else "Not Found")
    
    # POST Upload
    print("\nPOST /api/datasets/upload")
    with open("dummy.csv", "w") as f:
        f.write("crime_id,crime_type,district,status,latitude,longitude,date\n")
        f.write("FIR-999,Theft,Pune Central,Open,18.5204,73.8567,2026-06-20\n")
    with open("dummy.csv", "rb") as f:
        r = requests.post(f"{BASE_URL}/api/datasets/upload", files={"file": f})
    print(r.status_code)
    print(r.text)
    
    # Exports
    print("\nEXPORTS")
    for fmt in ["csv", "json", "excel"]:
        print(f"GET /api/reports/export.{fmt}")
        r = requests.get(f"{BASE_URL}/api/reports/export.{fmt}")
        print(r.status_code)
        print(r.headers.get("content-type"), "Size:", len(r.content))
        
    # Copilot
    print("\nPOST /api/copilot")
    r = requests.post(f"{BASE_URL}/api/copilot", json={"query": "hotspots"})
    print(r.status_code)
    print(r.text)
    
    print("\nShutting down server...")
    proc.terminate()
    proc.wait()

if __name__ == "__main__":
    test()
