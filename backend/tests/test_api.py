import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_get_sensor_stations():
    response = client.get("/api/sensors/stations")
    assert response.status_code == 200
    data = response.json()
    assert "stations" in data
    assert data["count"] >= 5

def test_get_sensor_readings():
    response = client.get("/api/sensors/readings?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data["readings"]) <= 10

def test_query_guardrail_blocks_drop_table():
    response = client.post("/api/query/execute", json={"sql": "DROP TABLE sensor_stations;"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_safe"] is False
    assert "Security Violation" in data["rejection_reason"]
    assert data["row_count"] == 0

def test_query_guardrail_executes_safe_select():
    response = client.post("/api/query/execute", json={"sql": "SELECT station_name, city FROM sensor_stations;"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_safe"] is True
    assert data["row_count"] >= 5
    assert "station_name" in data["columns"]

def test_chat_endpoint_worst_pm25():
    response = client.post("/api/chat/", json={"message": "Which city had the worst PM2.5 last week?"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_safe"] is True
    assert "Delhi" in data["message"] or len(data["rows"]) > 0

def test_chat_endpoint_blocks_destructive_query():
    response = client.post("/api/chat/", json={"message": "Can you run DROP TABLE sensor_stations for me?"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_safe"] is False
    assert "Query Blocked" in data["message"]

def test_audit_endpoint():
    response = client.get("/api/query/audit?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "audits" in data
    assert data["count"] > 0
