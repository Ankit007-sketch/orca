# ORCA
ORCA - Marine Ecosystem Reasoning with Collaborative Agents - SIH26176
# Walkthrough - Project ORCA Backend & Data Pipeline (Member 5)

As **Member 5 (Backend API & Data Pipeline Scope)** for **Project ORCA (SIH26176)**, the backend infrastructure and geospatial data systems have been developed and verified. All development was strictly isolated to `backend/` and `data/` directories.

---

## Architecture & Deliverables Summary

### 1. Data Contracts & Pydantic Models (`backend/models/`)
- [`request.py`](file:///e:/CSE/PROJECT/ORCA/backend/models/request.py): `QueryRequest` (WGS84 lat/lon validation, `session_id`, `language_code`, `vessel_type`), `FeedbackRequest`, `SessionCreateRequest`.
- [`agent_schemas.py`](file:///e:/CSE/PROJECT/ORCA/backend/models/agent_schemas.py): Pydantic data schemas directly matching the SIH OCR specification sheets for `weather_agent`, `ocean_agent`, and `marine_agent`.
- [`response.py`](file:///e:/CSE/PROJECT/ORCA/backend/models/response.py): `RiskAssessment` (`SAFE`/`CAUTION`/`UNSAFE` with 0.0–1.0 risk score), `EvidenceItem` (auditable timestamped provenance), WebGIS `GeoJSONLayers`, and `UnifiedResponse`.

### 2. Multi-Agent Dispatcher & Services (`backend/services/`)
- [`agent_dispatcher.py`](file:///e:/CSE/PROJECT/ORCA/backend/services/agent_dispatcher.py): Concurrently queries Weather, Ocean, and Marine agents via `asyncio.gather()`. Includes dynamic module integration with teammates' `agents/` modules and realistic domain fallback simulation.
- [`aggregator.py`](file:///e:/CSE/PROJECT/ORCA/backend/services/aggregator.py): Multi-source spatial-temporal risk engine. Integrates wind, cyclone, wave height, SST, chlorophyll-a PFZ detection, MPA compliance, and IMBL geofencing into an explainable recommendation and interactive GeoJSON overlays.
- [`translator.py`](file:///e:/CSE/PROJECT/ORCA/backend/services/translator.py): Multilingual bridge supporting 9 Indian regional languages (Kannada `kn`, Tamil `ta`, Telugu `te`, Malayalam `ml`, Hindi `hi`, Bengali `bn`, Gujarati `gu`, Marathi `mr`, Odia `or`, English `en`).
- [`session_manager.py`](file:///e:/CSE/PROJECT/ORCA/backend/services/session_manager.py): Multi-turn conversational memory, coordinate history tracking, and LRU session eviction.
- [`cache.py`](file:///e:/CSE/PROJECT/ORCA/backend/services/cache.py): In-memory TTL cache for satellite raster metadata and forecast grids.

### 3. FastAPI Server & Routing (`backend/api/` & `backend/main.py`)
- [`main.py`](file:///e:/CSE/PROJECT/ORCA/backend/main.py): FastAPI server configured with CORS for Member 6's Frontend and execution timing middleware.
- [`routes.py`](file:///e:/CSE/PROJECT/ORCA/backend/api/routes.py):
  - `POST /api/v1/query`: Core conversational multi-agent reasoning pipeline.
  - `GET /api/v1/mock-query`: Instant mock response returning locked JSON contracts to immediately unblock Member 6 (Frontend WebGIS).
  - `GET /health` & `GET /api/v1/health`: System health and agent connectivity status.
  - `GET /api/v1/history/{session_id}`: Multi-turn conversational history.
  - `GET /api/v1/layers`: Standard reference GeoJSON layers (ports, IMBL, MPAs, sample PFZ).
  - `POST /api/v1/feedback`: User ground-truth feedback recording.

### 4. Geospatial Data Fixtures (`data/`)
- [`loader.py`](file:///e:/CSE/PROJECT/ORCA/data/loader.py): Geospatial distance math (Haversine & polyline distance) and MPA/IMBL geofence detection.
- [`data/raw/`](file:///e:/CSE/PROJECT/ORCA/data/raw/): `indian_ports.json`, `imbl_boundaries.json`, `mpa_zones.json`.
- [`data/processed/`](file:///e:/CSE/PROJECT/ORCA/data/processed/): `pfz_sample_layers.geojson`, `coastal_hazard_zones.geojson`.

---

## Verification & Test Results

The backend test suite (`backend/tests/`) was executed with `pytest` and passed all 14 tests in 0.53s:

```
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.1.1
collected 14 items

backend/tests/test_api.py::test_root_and_health PASSED                   [  7%]
backend/tests/test_api.py::test_mock_query_endpoint PASSED               [ 14%]
backend/tests/test_api.py::test_real_query_endpoint PASSED               [ 21%]
backend/tests/test_api.py::test_layers_endpoint PASSED                   [ 28%]
backend/tests/test_api.py::test_history_and_session_lifecycle PASSED     [ 35%]
backend/tests/test_models.py::test_query_request_validation PASSED       [ 42%]
backend/tests/test_models.py::test_agent_schemas_matching_ocr_spec PASSED [ 50%]
backend/tests/test_models.py::test_unified_response_schema PASSED        [ 57%]
backend/tests/test_services.py::test_agent_dispatcher_concurrent PASSED  [ 64%]
backend/tests/test_services.py::test_aggregator_safe_pfz_synthesis PASSED [ 71%]
backend/tests/test_services.py::test_aggregator_severe_weather_unsafe PASSED [ 78%]
backend/tests/test_services.py::test_translator_regional_languages PASSED [ 85%]
backend/tests/test_services.py::test_session_manager PASSED              [ 92%]
backend/tests/test_services.py::test_data_loader PASSED                  [100%]

======================== 14 passed in 0.53s ========================
```

---

## How to Run the Backend Server

To start the FastAPI development server:
```bash
uvicorn backend.main:app --reload --port 8000
```
- Interactive OpenAPI Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/v1/health`
- Instant Mock Query for Frontend: `http://localhost:8000/api/v1/mock-query`
