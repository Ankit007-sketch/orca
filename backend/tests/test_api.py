"""
Integration Tests for ORCA FastAPI Endpoints
Tests /health, /api/v1/health, /api/v1/mock-query, /api/v1/query, /api/v1/layers, /api/v1/sessions.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_root_and_health():
    """Verify health endpoints."""
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["project"] == "Project ORCA (SIH26176)"

    resp_health = client.get("/health")
    assert resp_health.status_code == 200
    assert resp_health.json()["status"] == "healthy"

    resp_v1_health = client.get("/api/v1/health")
    assert resp_v1_health.status_code == 200
    assert resp_v1_health.json()["status"] == "healthy"
    assert resp_v1_health.json()["agents_available"]["weather_agent"] is True


def test_mock_query_endpoint():
    """Verify immediate mock query endpoint for Member 6 Frontend."""
    resp = client.get("/api/v1/mock-query?latitude=12.9141&longitude=74.8560&scenario=safe")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["risk"]["level"] == "SAFE"
    assert len(payload["evidence"]) >= 3
    assert "pfz_layer" in payload["geojson_layers"]


def test_real_query_endpoint():
    """Verify full end-to-end multi-agent query pipeline."""
    query_payload = {
        "session_id": "test-live-session-101",
        "user_query": "Is it safe to go fishing off Mangalore tomorrow morning?",
        "latitude": 12.9141,
        "longitude": 74.8560,
        "language_code": "kn",
        "radius_km": 25.0
    }
    resp = client.post("/api/v1/query", json=query_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "test-live-session-101"
    assert data["risk"]["level"] in ["SAFE", "CAUTION", "UNSAFE"]
    assert "evidence" in data
    assert "geojson_layers" in data
    assert data["language_code"] == "kn"


def test_layers_endpoint():
    """Verify WebGIS layers retrieval."""
    resp = client.get("/api/v1/layers?layer_type=all")
    assert resp.status_code == 200
    layers = resp.json()
    assert "ports" in layers
    assert "imbl_lines" in layers
    assert "marine_protected_areas" in layers


def test_history_and_session_lifecycle():
    """Verify session creation, turn insertion, and history retrieval."""
    sess_id = "lifecycle-sess-001"
    
    # Run query
    client.post("/api/v1/query", json={
        "session_id": sess_id,
        "user_query": "First query off Kochi",
        "latitude": 9.9312,
        "longitude": 76.2673,
        "language_code": "en"
    })

    # Retrieve history
    hist_resp = client.get(f"/api/v1/history/{sess_id}")
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    assert hist_data["total_turns"] == 1
    assert hist_data["history"][0]["latitude"] == 9.9312
