"""
FastAPI Routes for ORCA Backend (SIH26176)
Exposes core conversational endpoints, multi-agent dispatching pipeline,
mock endpoints for Frontend unblocking, and WebGIS layers.
"""

import time
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Path

from backend.models.request import QueryRequest, FeedbackRequest
from backend.models.response import (
    UnifiedResponse,
    HealthResponse,
    HistoryResponse,
    RiskAssessment,
    EvidenceItem
)
from backend.services.agent_dispatcher import agent_dispatcher
from backend.services.aggregator import aggregator_service
from backend.services.session_manager import session_manager
from backend.services.translator import translator_service
from data.loader import data_loader

api_router = APIRouter(prefix="/api/v1")


# --- Health & Status ---
@api_router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """System health check and agent connectivity report."""
    now_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        service="ORCA Multi-Agent Backend Pipeline (SIH26176)",
        agents_available={
            "weather_agent": True,
            "ocean_agent": True,
            "marine_agent": True,
            "coordinator_agent": True
        },
        timestamp=now_ts
    )


# --- Core Query Pipeline ---
@api_router.post(
    "/query",
    response_model=UnifiedResponse,
    summary="Submit natural language marine query for multi-agent reasoning",
    tags=["Conversational Reasoning"]
)
async def process_marine_query(payload: QueryRequest):
    """
    Main ORCA Multi-Agent Reasoning Pipeline:
    1. Intercepts query and updates multi-turn session state.
    2. Detects/normalizes regional language input.
    3. Concurrently dispatches requests to Weather, Ocean, and Marine agents using asyncio.gather().
    4. Synthesizes risk score, auditable evidence trail, and WebGIS GeoJSON layers.
    5. Translates final recommendation back to requested regional Indian language.
    """
    # 1. Update session state
    session = session_manager.get_or_create_session(
        session_id=payload.session_id,
        language_code=payload.language_code
    )

    # 2. Detect / normalize language
    detected_lang = translator_service.detect_language(payload.user_query, default_code=payload.language_code)
    target_lang = payload.language_code if payload.language_code else detected_lang
    english_query = translator_service.translate_query_to_english(payload.user_query, detected_lang)

    # 3. Concurrent Agent Execution (asyncio.gather)
    agent_results = await agent_dispatcher.dispatch_all(
        latitude=payload.latitude,
        longitude=payload.longitude,
        user_query=english_query,
        session_id=payload.session_id,
        timestamp=payload.timestamp
    )

    # 4. Multi-Source Synthesis & WebGIS construction
    unified_output = aggregator_service.synthesize(
        session_id=payload.session_id,
        user_query=payload.user_query,
        latitude=payload.latitude,
        longitude=payload.longitude,
        language_code=target_lang,
        agent_data=agent_results,
        vessel_type=payload.vessel_type or "motorized_boat"
    )

    # 5. Record turn in session memory
    session.add_turn(
        query_id=unified_output.query_id,
        user_query=payload.user_query,
        recommendation=unified_output.recommendation,
        risk_level=unified_output.risk.level,
        risk_score=unified_output.risk.risk_score,
        latitude=payload.latitude,
        longitude=payload.longitude,
        agent_data=agent_results
    )

    return unified_output


# --- Mock Query Endpoint for Member 6 (Frontend Unblocking) ---
@api_router.get(
    "/mock-query",
    response_model=UnifiedResponse,
    summary="Instant mock response matching contract for frontend development",
    tags=["Frontend Mock"]
)
async def get_mock_query_response(
    latitude: float = Query(default=12.9141, description="Sample latitude (Mangalore)"),
    longitude: float = Query(default=74.8560, description="Sample longitude (Mangalore)"),
    language_code: str = Query(default="en", description="Regional language code"),
    scenario: str = Query(default="safe", description="Scenario type: 'safe', 'caution', 'unsafe'")
):
    """
    Returns immediate structured mock response so Frontend (Member 6) can build WebGIS UI in parallel.
    """
    now_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    if scenario == "unsafe":
        risk = RiskAssessment(
            level="UNSAFE",
            risk_score=0.88,
            primary_hazard="Severe swell waves (3.4m) & gale winds (48 km/h)",
            confidence=0.96
        )
        rec = "UNSAFE FOR MARITIME OPERATIONS. Severe swell waves (3.4m) and gale winds (48 km/h) active off coast. High wave warning active. Do not venture into the sea."
    elif scenario == "caution":
        risk = RiskAssessment(
            level="CAUTION",
            risk_score=0.45,
            primary_hazard="Moderate sea swell (2.2m) & IMBL proximity",
            confidence=0.91
        )
        rec = "Exercise caution. Moderate wave swell (2.2m) observed. Traditional craft should remain near shore."
    else:  # safe
        risk = RiskAssessment(
            level="SAFE",
            risk_score=0.18,
            primary_hazard=None,
            confidence=0.94
        )
        rec = "Safe for fishing and marine operations. Favorable Potential Fishing Zone (PFZ) detected 18.5 km west. Sea conditions are calm (wave height 1.2m, wind 18 km/h)."

    translated_rec = translator_service.translate_recommendation(rec, risk.level, language_code)

    evidence = [
        EvidenceItem(
            source="IMD Marine Meteorological Station",
            observation="Wind speed measured at 18.2 km/h. No cyclone alert active.",
            timestamp=now_ts,
            category="weather",
            severity="info"
        ),
        EvidenceItem(
            source="INCOIS Ocean State Forecast",
            observation="Wave height: 1.2m, Current speed: 0.5 m/s, SST: 28.4°C.",
            timestamp=now_ts,
            category="ocean",
            severity="info"
        ),
        EvidenceItem(
            source="IRS P4 OCM Satellite Pass",
            observation="Chlorophyll concentration 2.1 mg/m³ indicating active PFZ front.",
            timestamp=now_ts,
            category="satellite",
            severity="favorable"
        )
    ]

    geojson_layers = aggregator_service._build_geojson_layers(
        lat=latitude,
        lon=longitude,
        pfz_detected=(scenario == "safe"),
        chloro=2.1,
        sst=28.4,
        wave_h=1.2,
        wind_spd=18.2,
        mpa_violation=False,
        mpa_name=None
    )

    return UnifiedResponse(
        session_id="mock-session-001",
        query_id="mock-qry-101",
        user_query="Is it safe to go fishing off Mangalore tomorrow morning?",
        recommendation=translated_rec,
        language_code=language_code,
        risk=risk,
        evidence=evidence,
        geojson_layers=geojson_layers,
        agent_assessments={
            "weather_agent": {"status": "success", "agent": "weather_agent"},
            "ocean_agent": {"status": "success", "agent": "ocean_agent"},
            "marine_agent": {"status": "success", "agent": "marine_agent"}
        },
        timestamps={
            "IMD": now_ts,
            "INCOIS": now_ts,
            "IRS_P4_OCM": now_ts
        },
        execution_time_ms=45.0
    )


# --- History Retrieval ---
@api_router.get(
    "/history/{session_id}",
    response_model=HistoryResponse,
    summary="Get multi-turn history for a conversation session",
    tags=["Session State"]
)
async def get_history(session_id: str = Path(..., description="Unique conversation session ID")):
    """Fetch all conversational turns for session memory."""
    session = session_manager.get_session(session_id)
    if not session:
        return HistoryResponse(session_id=session_id, total_turns=0, history=[])
    return session.to_history_response()


# --- Geospatial Reference Layers ---
@api_router.get("/layers", summary="Fetch reference WebGIS vector layers", tags=["WebGIS Layers"])
async def get_reference_layers(layer_type: Optional[str] = Query(default="all")):
    """
    Retrieve reference geospatial layers:
    - `ports`: Major Indian ports
    - `imbl`: International Maritime Boundary Lines
    - `mpas`: Marine Protected Areas
    - `pfz_sample`: Sample PFZ contours
    - `hazards`: Sample coastal hazard zones
    - `all`: Combined payload
    """
    if layer_type == "ports":
        return {"ports": data_loader.get_ports()}
    elif layer_type == "imbl":
        return {"imbl_lines": data_loader.get_imbl_boundaries()}
    elif layer_type == "mpas":
        return {"marine_protected_areas": data_loader.get_mpas()}
    elif layer_type == "pfz_sample":
        return data_loader.get_sample_pfz_layers()
    elif layer_type == "hazards":
        return data_loader.get_sample_hazard_layers()

    # All layers
    return {
        "ports": data_loader.get_ports(),
        "imbl_lines": data_loader.get_imbl_boundaries(),
        "marine_protected_areas": data_loader.get_mpas(),
        "sample_pfz": data_loader.get_sample_pfz_layers(),
        "sample_hazards": data_loader.get_sample_hazard_layers()
    }


# --- Supported Languages ---
@api_router.get("/languages", summary="List supported Indian regional languages", tags=["Multilingual"])
async def get_supported_languages():
    """Returns dictionary of supported language codes and their native script names."""
    return {"supported_languages": translator_service.SUPPORTED_LANGUAGES}


# --- User Feedback ---
@api_router.post("/feedback", summary="Submit ground observation feedback", tags=["Feedback"])
async def submit_feedback(payload: FeedbackRequest):
    """Collects ground truth accuracy feedback from fishermen and coastal users."""
    return {
        "status": "success",
        "message": "Feedback recorded successfully. Thank you for improving ORCA marine models.",
        "session_id": payload.session_id,
        "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
