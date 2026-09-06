"""
MarineAgent: core logic.

Responsibility recap (from the team task):
  - Determine what marine/ecosystem info to analyze        -> SUPPORTED_PARAMETERS (schemas.py)
  - Design input/output structure                            -> schemas.py
  - Implement agent logic                                     -> this file
  - Connect to marine/ecosystem datasets or APIs               -> data_sources.py
  - Return structured info the Coordinator Agent can use       -> MarineAgentOutput.to_dict()
"""

from __future__ import annotations

import logging
from typing import List, Optional

from .schemas import MarineAgentInput, MarineAgentOutput, ParameterReading, SUPPORTED_PARAMETERS
from .data_sources import INCOISERDDAPClient, IMDClient, get_osf_forecast_reference

logger = logging.getLogger("marine_agent.agent")

# Simple, tunable thresholds for flagging alerts. Adjust as the team
# refines what "concerning" looks like for the demo/dataset.
ALERT_THRESHOLDS = {
    "sea_surface_temperature": {"high": 30.5, "message": "Elevated sea surface temperature — possible coral bleaching risk."},
    "wave_height": {"high": 2.5, "message": "High wave activity — rough sea conditions."},
    "wind_speed": {"high": 40.0, "message": "High wind speed — small craft advisory territory."},
}

# Very rough geocoding for common named locations used in demos, since we
# don't have a geocoding API wired up yet. Extend this or swap for a real
# geocoder (e.g. Nominatim) later.
KNOWN_LOCATIONS = {
    "chennai coast": (13.08, 80.27),
    "mumbai coast": (18.96, 72.82),
    "kochi coast": (9.93, 76.26),
    "visakhapatnam coast": (17.68, 83.22),
    "lakshadweep": (10.57, 72.64),
    "andaman": (11.62, 92.73),
    "goa coast": (15.30, 73.82),
}


class MarineAgent:
    """The Marine Agent. One instance can be reused across requests."""

    def __init__(
        self,
        erddap_client: Optional[INCOISERDDAPClient] = None,
        imd_client: Optional[IMDClient] = None,
    ):
        self.erddap = erddap_client or INCOISERDDAPClient()
        self.imd = imd_client or IMDClient()

    # -- public API ----------------------------------------------------

    def analyze(self, agent_input: MarineAgentInput) -> MarineAgentOutput:
        """Main entrypoint. Always returns a MarineAgentOutput (never raises)."""
        error = agent_input.validate()
        if error:
            return MarineAgentOutput(
                status="error",
                location={"lat": agent_input.lat, "lon": agent_input.lon, "name": agent_input.location_name},
                generated_at=MarineAgentOutput.now_iso(),
                readings=[],
                ecosystem_summary="Could not analyze: invalid input.",
                errors=[error],
            )

        lat, lon, resolved_name, errors = self._resolve_location(agent_input)

        parameters = [p for p in agent_input.parameters if p in SUPPORTED_PARAMETERS] or SUPPORTED_PARAMETERS

        readings: List[ParameterReading] = []
        sources = set()

        for param in parameters:
            reading_dict = self._fetch_parameter(param, lat, lon)
            readings.append(ParameterReading(name=param, **reading_dict))
            sources.add(reading_dict["source"])

        osf_ref = get_osf_forecast_reference()
        sources.add(osf_ref["name"])

        alerts = self._compute_alerts(readings)
        summary = self._summarize(resolved_name, readings, alerts)

        any_mocked = any(r.status == "mocked" for r in readings)
        status = "partial" if (any_mocked or errors) else "ok"

        return MarineAgentOutput(
            status=status,
            location={"lat": lat, "lon": lon, "name": resolved_name},
            generated_at=MarineAgentOutput.now_iso(),
            readings=readings,
            ecosystem_summary=summary,
            alerts=alerts,
            sources=sorted(sources),
            errors=errors,
        )

    # -- internal helpers ------------------------------------------------

    def _resolve_location(self, agent_input: MarineAgentInput):
        errors: List[str] = []
        if agent_input.lat is not None and agent_input.lon is not None:
            return agent_input.lat, agent_input.lon, agent_input.location_name or "custom coordinates", errors

        name_key = (agent_input.location_name or "").strip().lower()
        if name_key in KNOWN_LOCATIONS:
            lat, lon = KNOWN_LOCATIONS[name_key]
            return lat, lon, agent_input.location_name, errors

        # Fallback: unknown named location, no coordinates given.
        errors.append(
            f"Location '{agent_input.location_name}' not in the known-location lookup; "
            f"used a default point. Wire up a real geocoder for production."
        )
        # Default to somewhere along the Indian coastline so the demo still runs.
        return 13.08, 80.27, agent_input.location_name or "unresolved location (defaulted)", errors

    def _fetch_parameter(self, parameter: str, lat: float, lon: float) -> dict:
        if parameter == "wind_speed":
            return self.imd.get_wind_speed(lat, lon)
        # Everything else currently routes through ERDDAP (with mock
        # fallback baked into the client for parameters not yet wired to a
        # real dataset id -- see INCOISERDDAPClient.DATASET_IDS).
        return self.erddap.get_parameter(parameter, lat, lon)

    def _compute_alerts(self, readings: List[ParameterReading]) -> List[str]:
        alerts = []
        for r in readings:
            rule = ALERT_THRESHOLDS.get(r.name)
            if rule and r.value is not None and r.value >= rule["high"]:
                alerts.append(rule["message"])
        return alerts

    def _summarize(self, location_name: Optional[str], readings: List[ParameterReading], alerts: List[str]) -> str:
        loc = location_name or "the requested location"
        parts = []
        for r in readings:
            if r.value is None:
                continue
            parts.append(f"{r.name.replace('_', ' ')} is {r.value} {r.unit}".strip())
        body = "; ".join(parts) if parts else "no readings could be retrieved"
        summary = f"Marine snapshot for {loc}: {body}."
        if alerts:
            summary += " Alerts: " + " ".join(alerts)
        return summary

    def to_coordinator_payload(self, output: MarineAgentOutput) -> dict:
        """
        Convenience wrapper in case the Coordinator Agent expects a
        slightly different envelope (e.g. wrapped under an "agent" key).
        Adjust this once the Coordinator's actual contract is confirmed.
        """
        return {
            "agent": "marine_agent",
            "result": output.to_dict(),
        }
