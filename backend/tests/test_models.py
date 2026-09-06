"""
Unit Tests for ORCA Backend Pydantic Models
"""

import pytest
from pydantic import ValidationError
from backend.models.request import QueryRequest, FeedbackRequest
from backend.models.response import (
    UnifiedResponse,
    RiskAssessment,
    RiskFactor,
    EvidenceItem
)
from backend.models.agent_schemas import (
    WeatherAgentResponse,
    OceanAgentResponse,
    MarineAgentResponse,
    AgentLocation,
    AgentAssessment,
    WeatherData,
    OceanData,
    MarineData
)


def test_query_request_validation():
    """Test valid and invalid QueryRequest schemas."""
    req = QueryRequest(
        session_id="sess-100",
        user_query="Is it safe to go fishing off Mangalore?",
        latitude=12.9141,
        longitude=74.8560,
        language_code="kn"
    )
    assert req.session_id == "sess-100"
    assert req.latitude == 12.9141
    assert req.language_code == "kn"

    # Out of range coordinates should fail validation
    with pytest.raises(ValidationError):
        QueryRequest(
            session_id="sess-bad",
            user_query="bad coords",
            latitude=120.0,  # Invalid latitude > 90
            longitude=74.8560
        )


def test_agent_schemas_matching_ocr_spec():
    """Test Weather, Ocean, and Marine agent response schemas against SIH OCR specs."""
    # 1. Weather Agent Schema
    w_resp = WeatherAgentResponse(
        agent="weather_agent",
        status="success",
        location=AgentLocation(name="Mangalore", latitude=12.91, longitude=74.86),
        timestamp="2026-09-01T10:00:00Z",
        data=WeatherData(
            temperature_c=29.5,
            wind_speed_kmh=18.2,
            wind_direction_deg=240.0,
            precipitation_mm=0.0,
            cyclone_warning=False,
            lightning_risk="low",
            visibility_km=10.0
        ),
        assessment=AgentAssessment(
            risk_level="low",
            summary="Calm weather conditions"
        ),
        sources=[{"name": "IMD", "timestamp": "2026-09-01T09:00:00Z"}],
        confidence=0.95,
        errors=[]
    )
    assert w_resp.agent == "weather_agent"
    assert w_resp.data.wind_speed_kmh == 18.2

    # 2. Ocean Agent Schema
    o_resp = OceanAgentResponse(
        agent="ocean_agent",
        status="success",
        location=AgentLocation(name="Mangalore", latitude=12.91, longitude=74.86),
        timestamp="2026-09-01T10:00:00Z",
        data=OceanData(
            wave_height_m=1.2,
            current_speed_ms=0.5,
            sea_surface_temperature_c=28.4
        ),
        assessment=AgentAssessment(
            risk_level="moderate",
            summary="Moderate wave conditions."
        ),
        sources=[{"name": "INCOIS", "timestamp": "2026-09-01T10:00:00Z"}],
        confidence=None,
        errors=[]
    )
    assert o_resp.agent == "ocean_agent"
    assert o_resp.data.wave_height_m == 1.2

    # 3. Marine Agent Schema
    m_resp = MarineAgentResponse(
        agent="marine_agent",
        status="success",
        location=AgentLocation(name="Mangalore", latitude=12.91, longitude=74.86),
        timestamp="2026-09-01T10:00:00Z",
        data=MarineData(
            chlorophyll_mg_m3=2.1,
            pfz_detected=True
        ),
        assessment=AgentAssessment(
            risk_level="low",
            summary="Marine indicators suggest a potentially productive area."
        ),
        sources=[{"name": "INCOIS", "timestamp": "2026-09-01T10:00:00Z"}],
        confidence=None,
        errors=[]
    )
    assert m_resp.agent == "marine_agent"
    assert m_resp.data.chlorophyll_mg_m3 == 2.1
    assert m_resp.data.pfz_detected is True


def test_unified_response_schema():
    """Test UnifiedResponse structure compliance."""
    risk = RiskAssessment(
        level="SAFE",
        risk_score=0.2,
        primary_hazard=None,
        confidence=0.95,
        contributing_factors=[
            RiskFactor(
                factor_name="Wave Height",
                value=1.2,
                unit="m",
                severity="low",
                description="Calm sea"
            )
        ]
    )
    evidence = [
        EvidenceItem(
            source="IRS P4 OCM Chlorophyll",
            observation="Chlorophyll-a 2.1 mg/m3",
            timestamp="2026-09-01T10:00:00Z",
            category="satellite",
            severity="favorable"
        )
    ]
    resp = UnifiedResponse(
        session_id="sess-01",
        query_id="qry-01",
        user_query="Is it safe?",
        recommendation="Safe for fishing. Favorable PFZ detected.",
        language_code="en",
        risk=risk,
        evidence=evidence,
        geojson_layers={"pfz_layer": {"type": "FeatureCollection", "features": []}},
        agent_assessments={},
        timestamps={"IMD": "2026-09-01T10:00:00Z"},
        execution_time_ms=120.0
    )
    assert resp.risk.level == "SAFE"
    assert resp.risk.risk_score == 0.2
    assert len(resp.evidence) == 1
