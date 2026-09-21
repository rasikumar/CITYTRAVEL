import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_ticketing_purchase_and_listing():
    # 1. Login passenger
    login_res = client.post("/api/auth/passenger/login", json={
        "username": "passenger@transitnow.com",
        "password": "password123"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Buy Ticket
    ticket_payload = {
        "bus_id": "BUS001",
        "ticket_type": "Day Pass",
        "payment_method": "Google Pay"
    }
    buy_res = client.post("/api/tickets", json=ticket_payload, headers=headers)
    assert buy_res.status_code == 200
    ticket_data = buy_res.json()
    assert ticket_data["success"] is True
    assert "ticket" in ticket_data
    assert ticket_data["ticket"]["ticket_type"] == "Day Pass"
    assert ticket_data["ticket"]["fare"] == 50.0

    # 3. List Passenger Tickets
    list_res = client.get("/api/tickets", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

def test_transit_ai_assistant_queries():
    # 1. Query bus location
    q1 = client.post("/api/chat", json={"message": "Where is BUS001?"})
    assert q1.status_code == 200
    assert "BUS001" in q1.json()["reply"]
    assert q1.json()["intent"] == "find_bus"

    # 2. Query delay status
    q2 = client.post("/api/chat", json={"message": "Why is my bus late?"})
    assert q2.status_code == 200
    assert q2.json()["intent"] == "get_delay"

    # 3. Query ETA to stop
    q3 = client.post("/api/chat", json={"message": "When will BUS001 arrive at Mattuthavani?"})
    assert q3.status_code == 200
    assert q3.json()["intent"] == "get_eta"

    # 4. Query next stop
    q4 = client.post("/api/chat", json={"message": "What is the next stop for BUS001?"})
    assert q4.status_code == 200
    assert q4.json()["intent"] == "get_next_stop"

    # 5. Query destination routing
    q5 = client.post("/api/chat", json={"message": "Find bus to Mattuthavani"})
    assert q5.status_code == 200
    assert "Mattuthavani" in q5.json()["reply"]
