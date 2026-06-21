import requests
import sqlite3
import json

base_url = "http://localhost:8088"

print("--- 1. GET /health ---")
r = requests.get(f"{base_url}/health")
print(r.status_code, r.text)

print("\n--- 2. GET /api/dashboard ---")
r = requests.get(f"{base_url}/api/dashboard")
try:
    print(r.status_code, "Items returned:", len(r.json().get('recent_crimes', [])))
except Exception as e:
    print("Failed to decode JSON:", r.text)

print("\n--- 3. CRUD Soft Delete ---")
crime_data = {
    "title": "Test Crime for Deletion",
    "description": "Will be soft deleted",
    "category": "Theft",
    "latitude": 18.5,
    "longitude": 73.8,
    "occurred_at": "2026-06-20T10:00:00",
    "status": "Open",
    "district": "Central"
}
r = requests.post(f"{base_url}/api/crimes", json=crime_data)
crime_id = r.json().get("id")
print("Created crime:", crime_id)

requests.delete(f"{base_url}/api/crimes/{crime_id}")
print("Deleted crime:", crime_id)

r = requests.get(f"{base_url}/api/crimes")
found = any(c['id'] == crime_id for c in r.json())
print("Crime found in GET /api/crimes?", found)

conn = sqlite3.connect('backend/sentineliq.db')
c = conn.cursor()
c.execute("SELECT is_deleted FROM crimes WHERE id=?", (crime_id,))
row = c.fetchone()
print("Direct DB check for is_deleted:", row[0] if row else "Not Found")
conn.close()

print("\n--- 4. POST /api/datasets/upload ---")
with open("backend/dummy.csv", "rb") as f:
    r = requests.post(f"{base_url}/api/datasets/upload", files={"file": f})
print(r.status_code, r.json())

print("\n--- 5. GET /api/reports/export ---")
for ext in ['csv', 'xlsx']:
    r = requests.get(f"{base_url}/api/reports/export.{ext}")
    print(f"Export {ext} - Status: {r.status_code}, Length: {len(r.content)} bytes")

print("\n--- 6. POST /api/copilot ---")
r = requests.post(f"{base_url}/api/copilot", json={"query": "hotspot"})
print(r.status_code, r.json())

print("\n--- 7. Rate Limiting ---")
for i in range(15):
    r = requests.post(f"{base_url}/api/copilot", json={"query": "spam"})
    if r.status_code == 429:
        print(f"Hit 429 Rate Limit on request {i+1}!")
        break
