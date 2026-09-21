import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_passenger_registration_and_login():
    # 1. Register new passenger
    unique_phone = "9998887771"
    unique_email = "testpassenger@transitnow.com"

    reg_payload = {
        "full_name": "Test Passenger",
        "phone": unique_phone,
        "email": unique_email,
        "password": "Password123!",
        "confirm_password": "Password123!"
    }

    res = client.post("/api/auth/passenger/register", json=reg_payload)
    # 200 or 400 if already exists
    assert res.status_code in [200, 400]

    # 2. Login with email
    login_payload = {
        "username": unique_email,
        "password": "Password123!"
    }
    res_login = client.post("/api/auth/passenger/login", json=login_payload)
    assert res_login.status_code == 200
    data = res_login.json()
    assert "access_token" in data
    assert data["role"] == "passenger"

    # 3. Login with phone
    login_phone_payload = {
        "username": unique_phone,
        "password": "Password123!"
    }
    res_phone_login = client.post("/api/auth/passenger/login", json=login_phone_payload)
    assert res_phone_login.status_code == 200

def test_driver_login():
    # Pre-seeded driver DRV001
    driver_payload = {
        "driver_id": "DRV001",
        "password": "password123"
    }
    res = client.post("/api/auth/driver/login", json=driver_payload)
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "driver"

def test_invalid_login():
    res = client.post("/api/auth/passenger/login", json={
        "username": "nonexistent@user.com",
        "password": "wrongpassword"
    })
    assert res.status_code == 401
