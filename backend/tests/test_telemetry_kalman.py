import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.kalman import BusGPSKalmanFilter

client = TestClient(app)

def test_kalman_filter_smoothing_and_jump_rejection():
    filter = BusGPSKalmanFilter(max_realistic_speed_kmh=120.0)

    # Initial valid point (Madurai Central)
    lat1, lon1 = 9.9195, 78.1118
    f_lat, f_lon, f_speed, valid = filter.validate_and_filter(lat1, lon1, speed=20.0, timestamp=1000.0)
    assert valid is True
    assert round(f_lat, 4) == lat1
    assert round(f_lon, 4) == lon1

    # Second valid point nearby (moving normally at 30 km/h)
    lat2, lon2 = 9.9197, 78.1120
    f_lat2, f_lon2, f_speed2, valid2 = filter.validate_and_filter(lat2, lon2, speed=25.0, timestamp=1002.0)
    assert valid2 is True

    # Impossible jump (teleporting 50 km away in 1 second)
    lat_jump, lon_jump = 10.5000, 78.8000
    f_lat3, f_lon3, f_speed3, valid3 = filter.validate_and_filter(lat_jump, lon_jump, speed=40.0, timestamp=1003.0)
    assert valid3 is False  # Must reject impossible jump!

def test_trip_start_telemetry_and_delay_reporting():
    # 1. Driver Login
    login_res = client.post("/api/auth/driver/login", json={
        "driver_id": "DRV001",
        "password": "password123"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Start Trip
    start_res = client.post("/api/driver/trips/start", json={
        "driver_id": "DRV001",
        "bus_id": "BUS001",
        "route_id": "21G"
    }, headers=headers)
    assert start_res.status_code == 200
    trip_data = start_res.json()
    trip_id = trip_data["trip_id"]

    # 3. Ingest Valid GPS Telemetry
    telem_res = client.post("/api/driver/telemetry", json={
        "driver_id": "DRV001",
        "bus_id": "BUS001",
        "trip_id": trip_id,
        "route_id": "21G",
        "latitude": 9.9195,
        "longitude": 78.1118,
        "speed": 28.5,
        "accuracy": 8.0,
        "source": "phone_gps"
    })
    assert telem_res.status_code == 200
    assert telem_res.json()["status"] == "success"
    assert "next_stop" in telem_res.json()

    # 4. Report Route Delay
    delay_res = client.post("/api/driver/delay", json={
        "trip_id": trip_id,
        "bus_id": "BUS001",
        "driver_id": "DRV001",
        "reason": "Traffic issue",
        "note": "Road congestion near Goripalayam junction"
    })
    assert delay_res.status_code == 200

    # 5. End Trip
    end_res = client.post("/api/driver/trips/end", json={
        "trip_id": trip_id
    }, headers=headers)
    assert end_res.status_code == 200
    assert end_res.json()["status"] == "ENDED"
