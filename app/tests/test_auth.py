import uuid

def test_register_login_flow(test_client):
    phone = f"+9989{uuid.uuid4().int % 100000000:08d}"
    
    # Register
    resp = test_client.post("/api/v1/auth/register", json={"customer_name": "Pytest User", "phone_number": phone})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["customer_name"] == "Pytest User"
    
    # Login
    resp = test_client.post("/api/v1/auth/login", json={"phone_number": phone})
    assert resp.status_code == 200
    
    # Set Telegram ID
    tid = uuid.uuid4().int % 1000000000
    resp = test_client.patch("/api/v1/auth/set-telegram-id", json={"phone_number": phone, "telegram_id": tid})
    assert resp.status_code == 200
    assert resp.json()["data"]["telegram_id"] == tid
    
    # Get Me (Auth Required)
    resp = test_client.get("/api/v1/auth/get-me", headers={"X-Telegram-Id": str(tid)})
    assert resp.status_code == 200
    assert resp.json()["data"]["telegram_id"] == tid
    assert resp.json()["data"]["phone_number"] == phone

def test_auth_required_fail(test_client):
    resp = test_client.get("/api/v1/auth/get-me")
    assert resp.status_code == 401
