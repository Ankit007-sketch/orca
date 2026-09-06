# Marine Agent — ORCA

Marine/ecosystem data agent. Given a location, returns structured readings
(sea surface temperature, wave height, salinity, chlorophyll, wind speed,
ocean current) plus a short natural-language summary and any alerts, in a
format the Coordinator Agent can consume directly.

## Folder contents

```
agents/marine_agent/
├── __init__.py        # public exports: MarineAgent, MarineAgentInput, MarineAgentOutput
├── schemas.py          # input/output data contracts (dataclasses, no external deps)
├── data_sources.py     # INCOIS ERDDAP + IMD API clients, with mock fallback
├── agent.py            # MarineAgent core logic (fetch -> alerts -> summary)
├── tests/
│   ├── test_agent.py
│   └── test_data_sources.py
└── README.md
```

## Data sources used

| Source | Type | How it's used |
|---|---|---|
| [INCOIS ERDDAP](https://erddap.incois.gov.in/erddap/index.html) | Real REST API (JSON/CSV over HTTP) | Primary source — `INCOISERDDAPClient` in `data_sources.py` |
| [INCOIS Ocean State Forecast](https://incois.gov.in/oceanservices/osfforecast.jsp) | HTML dashboard | Surfaced as a reference link (`get_osf_forecast_reference()`), not scraped — too brittle to rely on for a demo |
| [IMD public API](https://api.imd.gov.in/public/index.php) | REST API | Wind speed, via `IMDClient` |

**Every external call fails soft.** If INCOIS/IMD are unreachable, rate-limited,
or return something unexpected, the agent returns a clearly-flagged mocked
reading (`status: "mocked"`) instead of crashing — so the pipeline/demo
still works end-to-end even with flaky government servers. Set
`MARINE_AGENT_ALLOW_MOCK=false` to disable this and surface real errors instead.

**TODO before final submission:** `INCOISERDDAPClient.DATASET_IDS` only has
`sea_surface_temperature` mapped to a real dataset id so far. Browse
https://erddap.incois.gov.in/erddap/info/index.html to find dataset ids for
wave height / salinity / chlorophyll / currents and add them there.

## Usage

```python
from agents.marine_agent import MarineAgent, MarineAgentInput

agent = MarineAgent()

result = agent.analyze(MarineAgentInput(
    location_name="Chennai coast",
    parameters=["sea_surface_temperature", "wave_height", "wind_speed"],
))

payload = result.to_dict()   # plain JSON-serializable dict for the Coordinator
```

Example output shape:

```json
{
  "status": "ok",
  "location": {"lat": 13.08, "lon": 80.27, "name": "Chennai coast"},
  "generated_at": "2026-09-01T08:27:59Z",
  "readings": [
    {"name": "sea_surface_temperature", "value": 28.4, "unit": "°C",
     "source": "INCOIS-ERDDAP:incois_tmi_3day_datasets", "observed_at": "...", "status": "ok"}
  ],
  "ecosystem_summary": "Marine snapshot for Chennai coast: sea surface temperature is 28.4 °C...",
  "alerts": [],
  "sources": ["INCOIS Ocean State Forecast", "INCOIS-ERDDAP:incois_tmi_3day_datasets"],
  "errors": []
}
```

If the Coordinator Agent expects a different envelope (e.g. wrapped under an
`"agent"` key), use `agent.to_coordinator_payload(result)` instead, or adjust
that method once the Coordinator's actual contract is confirmed.

## Running tests

```bash
pip install -r requirements.txt   # or: pip install requests pytest
python -m pytest agents/marine_agent/tests -v
```

Tests use fake/mocked clients — no network access required, so they run the
same in CI as on your laptop.

## Git workflow (per team instructions)

```bash
# 1. Create your own branch off main
git checkout main
git pull origin main
git checkout -b feature/marine-agent

# 2. Copy these files into agents/marine_agent/ in the repo, then:
git add agents/marine_agent
git commit -m "Add Marine Agent: ecosystem data fetch + structured output"

# 3. Push your branch
git push -u origin feature/marine-agent

# 4. Open a Pull Request on GitHub
#    - base: main   compare: feature/marine-agent
#    - Describe: what parameters are covered, which are still mocked,
#      and link this README for reviewers.
```

Do not touch other agents' folders or the main backend/coordinator wiring in
this branch — flag any integration changes needed as a comment on the PR
instead, per the team's guidelines.
