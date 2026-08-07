import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_system():
    print("--- Testing API Backend Endpoints ---")
    
    # 1. Login Admin
    res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "admin@attendance.ai",
        "password": "admin123"
    })
    print(f"Login Admin: Status {res.status_code}")
    assert res.status_code == 200
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get Students
    res = requests.get(f"{BASE_URL}/students", headers=headers)
    print(f"Get Students: Status {res.status_code}, Count: {len(res.json())}")
    assert res.status_code == 200

    # 3. Get Attendance Logs
    res = requests.get(f"{BASE_URL}/attendance", headers=headers)
    print(f"Get Attendance Logs: Status {res.status_code}, Count: {len(res.json())}")
    assert res.status_code == 200

    # 4. Get Dashboard Analytics
    res = requests.get(f"{BASE_URL}/analytics/dashboard", headers=headers)
    print(f"Dashboard Analytics: Status {res.status_code}")
    assert res.status_code == 200

    print("--- ALL BACKEND CHECKS PASSED SUCCESSFULLY! ---")

if __name__ == "__main__":
    test_system()
