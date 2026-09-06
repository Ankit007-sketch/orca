"""
Unit Tests for ORCA Backend Services
Tests AgentDispatcher, ResponseAggregator, MultilingualTranslator,
SessionManager, and DataLoader.
"""

import asyncio
import pytest
from backend.services.agent_dispatcher import agent_dispatcher
from backend.services.aggregator import aggregator_service
from backend.services.translator import translator_service
from backend.services.session_manager import session_manager
from backend.services.cache import cache_service
from data.loader import data_loader


def test_agent_dispatcher_concurrent():
    """Verify that agent dispatcher runs all 3 agents in parallel and returns valid structures."""
    lat, lon = 12.9141, 74.8560
    results = asyncio.run(agent_dispatcher.dispatch_all(
        latitude=lat,
        longitude=lon,
        user_query="Is it safe off Mangalore?",
        session_id="test-session-01"
    ))

    assert "weather" in results
    assert "ocean" in results
    assert "marine" in results

    w = results["weather"]
    o = results["ocean"]
    m = results["marine"]

    assert w["agent"] == "weather_agent"
    assert "wind_speed_kmh" in w["data"]

    assert o["agent"] == "ocean_agent"
    assert "wave_height_m" in o["data"]

    assert m["agent"] == "marine_agent"
    assert "chlorophyll_mg_m3" in m["data"]


def test_aggregator_safe_pfz_synthesis():
    """Test aggregator with calm conditions and active PFZ."""
    mock_agent_data = {
        "weather": {
            "agent": "weather_agent",
            "timestamp": "2026-09-01T10:00:00Z",
            "data": {"wind_speed_kmh": 15.0, "cyclone_warning": False}
        },
        "ocean": {
            "agent": "ocean_agent",
            "timestamp": "2026-09-01T10:00:00Z",
            "data": {"wave_height_m": 1.2, "current_speed_ms": 0.5, "sea_surface_temperature_c": 28.4}
        },
        "marine": {
            "agent": "marine_agent",
            "timestamp": "2026-09-01T10:00:00Z",
            "data": {"chlorophyll_mg_m3": 2.2, "pfz_detected": True, "mpa_violation": False, "imbl_proximity_km": 50.0}
        }
    }

    unified = aggregator_service.synthesize(
        session_id="test-sess-02",
        user_query="Can we go fishing?",
        latitude=12.9141,
        longitude=74.8560,
        language_code="en",
        agent_data=mock_agent_data
    )

    assert unified.risk.level == "SAFE"
    assert unified.risk.risk_score < 0.35
    assert len(unified.evidence) >= 3
    assert "pfz_layer" in unified.geojson_layers
    assert "query_point" in unified.geojson_layers


def test_aggregator_severe_weather_unsafe():
    """Test aggregator under cyclonic and high wave conditions."""
    mock_agent_data = {
        "weather": {
            "agent": "weather_agent",
            "timestamp": "2026-09-01T10:00:00Z",
            "data": {"wind_speed_kmh": 65.0, "cyclone_warning": True}
        },
        "ocean": {
            "agent": "ocean_agent",
            "timestamp": "2026-09-01T10:00:00Z",
            "data": {"wave_height_m": 3.8, "current_speed_ms": 1.4, "sea_surface_temperature_c": 29.0}
        },
        "marine": {
            "agent": "marine_agent",
            "timestamp": "2026-09-01T10:00:00Z",
            "data": {"chlorophyll_mg_m3": 1.5, "pfz_detected": False, "mpa_violation": False}
        }
    }

    unified = aggregator_service.synthesize(
        session_id="test-sess-03",
        user_query="Can we go fishing?",
        latitude=12.9141,
        longitude=74.8560,
        language_code="en",
        agent_data=mock_agent_data
    )

    assert unified.risk.level == "UNSAFE"
    assert unified.risk.risk_score >= 0.70
    assert unified.risk.primary_hazard is not None


def test_translator_regional_languages():
    """Test translation to regional Indian languages."""
    base_rec = "Safe for fishing and marine operations."
    
    # Kannada
    kn_rec = translator_service.translate_recommendation(base_rec, "SAFE", "kn")
    assert "ಮೀನುಗಾರಿಕೆ" in kn_rec

    # Tamil
    ta_rec = translator_service.translate_recommendation(base_rec, "SAFE", "ta")
    assert "மீன்பிடிக்க" in ta_rec

    # Hindi
    hi_rec = translator_service.translate_recommendation(base_rec, "SAFE", "hi")
    assert "मत्स्य" in hi_rec or "सुरक्षित" in hi_rec


def test_session_manager():
    """Test multi-turn session creation and history retention."""
    sess = session_manager.get_or_create_session("sess-abc", language_code="ta")
    assert sess.session_id == "sess-abc"
    assert sess.preferred_language == "ta"

    sess.add_turn(
        query_id="q1",
        user_query="Is it safe?",
        recommendation="Yes, safe.",
        risk_level="SAFE",
        risk_score=0.2,
        latitude=12.9,
        longitude=74.8
    )

    history_resp = sess.to_history_response()
    assert history_resp.total_turns == 1
    assert history_resp.history[0].query_id == "q1"


def test_data_loader():
    """Test data loader port lookups and distance calculations."""
    ports = data_loader.get_ports()
    assert len(ports) > 0

    nearest, dist = data_loader.find_nearest_port(12.91, 74.85)
    assert nearest is not None
    assert nearest["name"] == "Mangalore"
    assert dist < 5.0
