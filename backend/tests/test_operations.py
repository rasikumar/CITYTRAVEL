import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_operations_driver_lifecycle():
    # 1. Create Driver
    unique_id = "DRV_TEST_99"
    create_res = client.post("/api/operations/drivers", json={
        "driver_id": unique_id,
        "driver_name": "Test Operator",
        "phone": "9811122233",
        "password": "driverpassword123",
        "shift_start": "06:00",
        "shift_end": "14:00"
    })
    assert create_res.status_code == 200
    driver = create_res.json()
    pk = driver["id"]

    # 2. Update Driver
    update_res = client.put(f"/api/operations/drivers/{pk}", json={
        "driver_name": "Test Operator Senior",
        "shift_end": "15:00"
    })
    assert update_res.status_code == 200
    assert update_res.json()["driver_name"] == "Test Operator Senior"

    # 3. Delete Driver
    del_res = client.delete(f"/api/operations/drivers/{pk}")
    assert del_res.status_code == 200

def test_operations_bus_lifecycle():
    # 1. Create Bus
    unique_bus_id = "BUS_TEST_99"
    create_res = client.post("/api/operations/buses", json={
        "bus_id": unique_bus_id,
        "registration_number": "TN-58-TEST-9999",
        "bus_name": "Madurai Testing Coach",
        "capacity": 45
    })
    assert create_res.status_code == 200
    bus_pk = create_res.json()["bus"]["id"]

    # 2. Update Bus
    up_res = client.put(f"/api/operations/buses/{bus_pk}", json={
        "bus_name": "Madurai Testing Superfast",
        "capacity": 55
    })
    assert up_res.status_code == 200

    # 3. Delete Bus
    del_res = client.delete(f"/api/operations/buses/{bus_pk}")
    assert del_res.status_code == 200

def test_operations_route_and_stops_lifecycle():
    # 1. Create Route with Stops
    create_route_res = client.post("/api/operations/routes", json={
        "route_id": "TEST_RT",
        "route_name": "Test Terminal Corridor",
        "direction": "Outbound",
        "stops": [
            {
                "stop_name": "Test Depot Point A",
                "latitude": 9.9200,
                "longitude": 78.1100,
                "sequence": 1,
                "scheduled_arrival_time": "07:00",
                "dwell_time_minutes": 5
            }
        ]
    })
    assert create_route_res.status_code == 200
    r_id = create_route_res.json()["route_id"]

    # 2. Add Stop to existing route
    add_stop_res = client.post(f"/api/operations/routes/{r_id}/stops", json={
        "stop_name": "Test Transit Hub Point B",
        "latitude": 9.9300,
        "longitude": 78.1200,
        "sequence": 2,
        "scheduled_arrival_time": "07:20",
        "dwell_time_minutes": 3
    })
    assert add_stop_res.status_code == 200

    # 3. Delete Route
    del_res = client.delete(f"/api/operations/routes/{r_id}")
    assert del_res.status_code == 200
