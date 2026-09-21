import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_routes():
    res = client.get("/api/routes")
    assert res.status_code == 200
    routes = res.json()
    assert len(routes) >= 2
    # Verify Route 21G has ordered stops
    route_21g = next((r for r in routes if r["route_id"] == "21G"), None)
    assert route_21g is not None
    assert len(route_21g["stops"]) >= 4
    assert route_21g["stops"][0]["stop_name"] == "Madurai Central"

def test_get_buses():
    res = client.get("/api/buses")
    assert res.status_code == 200
    buses = res.json()
    assert len(buses) >= 2
    bus1 = next((b for b in buses if b["bus_id"] == "BUS001"), None)
    assert bus1 is not None
    assert bus1["driver_name"] == "K. Murugan"

def test_search_buses():
    # 1. Search by Bus ID
    res1 = client.get("/api/buses/search?q=BUS001")
    assert res1.status_code == 200
    assert len(res1.json()) >= 1
    assert res1.json()[0]["bus_id"] == "BUS001"

    # 2. Search by Route ID
    res2 = client.get("/api/buses/search?q=21G")
    assert res2.status_code == 200
    assert len(res2.json()) >= 1

    # 3. Search by Stop Name
    res3 = client.get("/api/buses/search?q=Mattuthavani")
    assert res3.status_code == 200
    assert len(res3.json()) >= 1

    # 4. Search no-result query
    res4 = client.get("/api/buses/search?q=NONEXISTENT_QUERY_999")
    assert res4.status_code == 200
    assert len(res4.json()) == 0
