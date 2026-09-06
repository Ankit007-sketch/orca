# ORCA — Integration Fixes (submission day)

This documents what was changed to make the previously-disconnected pieces
of the project actually work together end-to-end.

## What was broken

1. `backend/services/agent_dispatcher.py` looked for a module-level
   `analyze(lat, lon, query, timestamp)` function on `agents.weather_agent`,
   `agents.ocean_agent`, `agents.marine_agent`. None of those modules
   exposed that — Marine and Ocean agents expose classes
   (`MarineAgent().analyze(MarineAgentInput(...))`), and Weather Agent is a
   stub with no data fetching at all. So every request was silently served
   by the backend's own built-in simulator, never the real agents.
2. Separately, the *content* of `agents/marine_agent` (SST, wave height,
   salinity, current) matches what the backend calls "ocean data", and the
   content of `agents/ocean_agent` (chlorophyll only) matches what the
   backend calls "marine data" (chlorophyll + PFZ/MPA). The two halves of
   the team built against different definitions of "marine" vs "ocean".
3. The frontend (`frontend/src/services/mockAnalysisService.js`) never
   called the backend at all — it only returned canned data after a fake
   delay.
4. `agents/coordinator_agent/` (router/aggregator/reasoning) is a full,
   separate orchestration layer that nothing imports. It's dead code
   duplicating what `backend/services/` already does. **Left untouched** —
   not safe to swap orchestration approaches same-day. Worth resolving
   after submission (see "Not done" below).

## What was fixed

- **`backend/services/agent_dispatcher.py`**: now calls the real
  `agents.marine_agent.MarineAgent` for ocean-state data (wave/SST/salinity/
  current) and the real `agents.ocean_agent.OceanAgent` for chlorophyll,
  matching content to the correct backend field, not folder name. PFZ/MPA/
  IMBL geofencing still runs locally against `data/raw/*.json` (it never
  needed network access). **Every real call is wrapped in try/except with a
  field-by-field fallback to the original simulator values** — if an agent
  isn't installed, has no dataset configured, or the network is down, the
  pipeline transparently keeps working with simulated values. Nothing about
  the previous fully-simulated demo behavior was removed, it's the same
  data as a safety net.
- **`backend/requirements.txt`**: added `requests`, `xarray`, `numpy`,
  `scipy` so a single `pip install -r backend/requirements.txt` activates
  the real agent code paths. Fully optional — the backend runs fine without
  them, just always uses the simulator.
- **`frontend/src/services/orcaApiService.js`** (new): calls
  `POST /api/v1/query` on the real backend and maps its response into the
  exact shape the existing UI components expect. Includes a small
  location-name → lat/lon lookup for the free-text location field (backend
  requires WGS84 coordinates).
- **`frontend/src/App.jsx`**: tries the real backend first, falls back to
  the mock service on any failure (backend not running, CORS issue,
  network error) — so a live demo never visibly breaks even if the backend
  process isn't up at that moment.

## How to run it today

```bash
# Backend
pip install -r backend/requirements.txt --break-system-packages   # or in a venv
uvicorn backend.main:app --reload --port 8000
# check: http://localhost:8000/api/v1/health

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
# open the printed localhost URL, backend must be running for live data
```

Run the existing backend test suite to confirm nothing broke:
```bash
pytest backend/tests -v
```
(If you installed the optional agent dependencies, tests may take a little
longer than before — the real agents will attempt live network calls with
an 8s timeout before falling back to mock values. This is expected and
still passes.)

## Known limitations / what's still simulated

- **Weather** is still 100% simulated — `agents/weather_agent` has no real
  data fetching built. If you have time, mention this honestly in the demo
  rather than claiming live weather data.
- **Ocean/chlorophyll** will use its "mocked" fallback unless
  `OCEAN_AGENT_DATASET_PATH` is set to an actual IRS-P4 OCM NetCDF subset
  (see `agents/ocean_agent/README.md`). Without that file, it's simulated —
  same as before, just via the same code path that would use real data if
  the file were present.
- **Marine ocean-state data** (SST/wave/salinity/current) will attempt live
  INCOIS ERDDAP / IMD calls if `requests` is installed and the network is
  reachable; only `sea_surface_temperature` has a confirmed real dataset ID
  wired up (see `agents/marine_agent/README.md` TODO) — the rest will fall
  back to simulated values even with the dependency installed.

## Not done (flag if asked, don't claim it's finished)

- `agents/coordinator_agent/` is still unused/dead code. It's not wired
  into the backend, and the backend's own `agent_dispatcher.py` +
  `aggregator.py` do that job instead. Fine to leave as-is for submission,
  but worth explaining if a judge asks why it exists.
