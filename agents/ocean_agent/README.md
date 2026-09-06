# ORCA Ocean / Chlorophyll Agent

Specialist Ocean Agent for **SIH 2026 PS 26176 — ORCA Marine Ecosystem Reasoning with Collaborative Agents**.

This module is responsible for retrieving and processing **IRS-P4 OCM (Ocean Colour Monitor) chlorophyll observations** and returning structured information that the ORCA Coordinator Agent can combine with weather, marine, SST, GIS and other evidence.

## Responsibility

The problem statement asks ORCA to support questions such as:

- Which regions show high chlorophyll concentration and favourable sea-surface temperature?
- Why has fish productivity declined in a particular coastal region?
- What ocean conditions are observed near a fishing location?

This agent handles only its specialist evidence:

```text
Coordinator Agent
       |
       v
Ocean / Chlorophyll Agent
       |
       v
IRS-P4 OCM dataset
       |
       +-- time
       +-- latitude
       +-- longitude
       +-- chlorophyll
       |
       v
Structured chlorophyll observation
       |
       v
Coordinator Agent
```

It does **not** independently declare a location safe, a PFZ, or scientifically healthy. Chlorophyll should be correlated with SST, weather, marine conditions and other sources by the wider ORCA system.

## Folder structure

```text
agents/ocean_agent/
├── __init__.py
├── agent.py
├── data_sources.py
├── schemas.py
├── requirements.txt
├── README.md
└── tests/
    ├── __init__.py
    ├── test_agent.py
    └── test_data_sources.py
```

## Input contract

```python
from agents.ocean_agent import OceanAgentInput

OceanAgentInput(
    lat=13.08,
    lon=80.27,
    location_name="Chennai coast",
    date="2000-01-01",
    parameters=["chlorophyll"],
)
```

The agent accepts:

- `lat`, `lon` — geographic location; coordinates take priority.
- `location_name` — convenience lookup for a few demo locations.
- `date` — optional ISO date/time. Latest available observation is used if omitted.
- `parameters` — currently `chlorophyll`.
- `radius_km` — reserved for future regional aggregation.
- `raw_query` — optional original natural-language query.

## Output contract

Example shape:

```json
{
  "status": "ok",
  "location": {"lat": 13.08, "lon": 80.27, "name": "Chennai coast"},
  "generated_at": "2026-09-02T00:00:00Z",
  "readings": [
    {
      "name": "chlorophyll",
      "value": 0.42,
      "unit": "mg/m^3",
      "source": "IRS-P4-OCM:small_ocm_subset.nc",
      "observed_at": "2000-01-01T00:00:00",
      "status": "ok",
      "note": null,
      "grid_lat": 13.0,
      "grid_lon": 80.0
    }
  ],
  "ocean_summary": "Ocean snapshot for Chennai coast: chlorophyll is 0.42 mg/m^3.",
  "insights": [
    "Chlorophyll observation retrieved; correlate with sea-surface temperature, weather, and other marine evidence before making a fishing or ecosystem recommendation."
  ],
  "sources": ["IRS-P4-OCM:small_ocm_subset.nc"],
  "errors": []
}
```

For a Coordinator envelope:

```python
payload = agent.to_coordinator_payload(result)
```

which produces:

```json
{
  "agent": "ocean_agent",
  "result": {"...": "OceanAgentOutput"}
}
```

## Dataset and preprocessing

### Important development rule

The team task explicitly says not to download huge unnecessary portions of the dataset. Therefore this implementation expects a **small geographical/time subset** during development.

Recommended workflow:

1. Obtain the team's approved IRS-P4 OCM chlorophyll source.
2. Inspect its metadata and variable names.
3. Create/download only a small region and time subset for development.
4. Save it as a NetCDF/HDF-compatible file.
5. Set its path before running the agent:

```bash
export OCEAN_AGENT_DATASET_PATH=/absolute/path/to/irs_p4_ocm_subset.nc
```

Windows PowerShell:

```powershell
$env:OCEAN_AGENT_DATASET_PATH="C:\path\to\irs_p4_ocm_subset.nc"
```

### Preprocessing implemented

The client:

1. Opens the dataset lazily with `xarray`.
2. Detects common names for chlorophyll, latitude, longitude and time.
3. Selects the nearest latitude/longitude grid cell.
4. Selects the requested date/time, or latest available time if none is supplied.
5. Rejects NaN/negative values.
6. Preserves the dataset unit when available; otherwise uses `mg/m^3` as the conventional fallback.
7. Returns the selected grid coordinates and observation time.

No arbitrary scientific normalization or chlorophyll threshold is applied. This avoids making unsupported claims from a single variable.

### Variable aliases currently supported

Chlorophyll:

```text
chlorophyll, chlor_a, chl_a, chl, chla, chlorophyll_a
```

Latitude:

```text
lat, latitude, Latitude
```

Longitude:

```text
lon, longitude, Longitude
```

Time:

```text
time, Time, date, datetime
```

If the actual IRS-P4 OCM dataset uses different names, update the alias lists in `data_sources.py` after inspecting the file.

## Demo-safe fallback

If the dataset path is unavailable or the selected point cannot be read, the agent can return a clearly flagged mocked reading so the overall ORCA pipeline does not crash:

```json
{
  "status": "mocked",
  "source": "mock-fallback",
  "note": "IRS-P4 OCM request failed: ..."
}
```

Mock values are for development/demo continuity only and must **never be presented as scientific observations**.

Disable fallback when working with real data:

```bash
export OCEAN_AGENT_ALLOW_MOCK=false
```

## Usage

```python
from agents.ocean_agent import OceanAgent, OceanAgentInput

agent = OceanAgent()

result = agent.analyze(OceanAgentInput(
    lat=13.08,
    lon=80.27,
    location_name="Chennai coast",
    date="2000-01-01",
))

payload = result.to_dict()
print(payload)
```

## Dataset inspection

Before writing dataset-specific code, inspect the actual file:

```python
from agents.ocean_agent.data_sources import IRSP4OCMClient

client = IRSP4OCMClient("/path/to/irs_p4_ocm_subset.nc")
print(client.inspect_dataset())
```

Use the output to verify the real variable names, dimensions and coordinates.

## Running tests

```bash
pip install -r requirements.txt
python -m pytest agents/ocean_agent/tests -v
```

The tests create tiny temporary NetCDF files and use fake clients. No network access or large satellite download is required.

## Git workflow

```bash
# 1. Create your branch off main
git checkout main
git pull origin main
git checkout -b feature/ocean-agent

# 2. Add only your agent files
git add agents/ocean_agent
git commit -m "Add Ocean Agent: IRS-P4 OCM chlorophyll retrieval"

# 3. Push
git push -u origin feature/ocean-agent

# 4. Open Pull Request
# base: main
# compare: feature/ocean-agent
```

Do not modify other agents or backend/coordinator architecture without team discussion.

## Current limitation / next integration step

The code is intentionally dataset-schema-aware but not tied to a fabricated public download URL. Once the team provides the exact approved IRS-P4 OCM dataset file/source, inspect that file and adjust aliases/format handling if required. The public agent interface does not need to change.
