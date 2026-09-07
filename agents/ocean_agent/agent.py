"""
OceanAgent: core logic.

Responsibility recap (from the team task):
  - Work with IRS P4 OCM-Chlorophyll data              -> data_sources.py
  - Understand time/latitude/longitude/chlorophyll    -> schemas.py + data source schema detection
  - Retrieve/process ocean information                -> this file
  - Build reasoning around ocean conditions            -> _build_insights()
  - Return structured Coordinator-compatible results  -> OceanAgentOutput.to_dict()
  - Document preprocessing and add tests               -> README.md + tests/
"""

from __future__ import annotations

import logging
from typing import List, Optional

from .data_sources import IRSP4OCMClient, OpenMeteoMarineClient
from .schemas import (
    SUPPORTED_PARAMETERS,
    OceanReading,
    OceanAgentInput,
    OceanAgentOutput,
)

logger = logging.getLogger("ocean_agent.agent")

KNOWN_LOCATIONS = {
    "chennai coast": (13.08, 80.27),
    "mumbai coast": (18.96, 72.82),
    "kochi coast": (9.93, 76.26),
    "visakhapatnam coast": (17.68, 83.22),
    "lakshadweep": (10.57, 72.64),
    "andaman": (11.62, 92.73),
    "goa coast": (15.30, 73.82),
}


class OceanAgent:
    """The Ocean specialist agent. One instance is reusable."""

    def __init__(
        self,
        ocm_client: Optional[IRSP4OCMClient] = None,
        marine_client: Optional[OpenMeteoMarineClient] = None
    ):
        self.ocm = ocm_client or IRSP4OCMClient()
        self.marine_client = marine_client or OpenMeteoMarineClient()

    def analyze(self, agent_input: OceanAgentInput) -> OceanAgentOutput:
        """Main entrypoint. Always returns an OceanAgentOutput (never raises)."""
        error = agent_input.validate()
        if error:
            return OceanAgentOutput(
                status="error",
                location={"lat": agent_input.lat, "lon": agent_input.lon, "name": agent_input.location_name},
                generated_at=OceanAgentOutput.now_iso(),
                readings=[],
                ocean_summary="Could not analyze: invalid input.",
                errors=[error],
            )

        lat, lon, resolved_name, errors = self._resolve_location(agent_input)
        parameters = [p for p in agent_input.parameters if p in SUPPORTED_PARAMETERS] or SUPPORTED_PARAMETERS

        readings: List[OceanReading] = []
        sources = set()
        
        # Fetch marine data in bulk if any marine params requested
        marine_params = ["wave_height", "wave_direction", "ocean_current_velocity", "ocean_current_direction"]
        needs_marine = any(p in parameters for p in marine_params)
        marine_data = {}
        if needs_marine:
            marine_data = self.marine_client.get_marine_data(lat, lon)
            if "error" in marine_data:
                errors.append(marine_data["error"])

        for parameter in parameters:
            if parameter == "chlorophyll":
                reading_dict = self.ocm.get_chlorophyll(lat, lon, agent_input.date)
                reading = OceanReading(name=parameter, **reading_dict)
                readings.append(reading)
                sources.add(reading.source)
            elif parameter in marine_params:
                if "error" not in marine_data and "current" in marine_data:
                    current = marine_data["current"]
                    units = marine_data.get("current_units", {})
                    value = current.get(parameter)
                    unit = units.get(parameter, "")
                    observed_at = current.get("time")
                    
                    if value is not None:
                        readings.append(OceanReading(
                            name=parameter,
                            value=value,
                            unit=unit,
                            source="Open-Meteo Marine",
                            observed_at=observed_at,
                            status="ok"
                        ))
                        sources.add("Open-Meteo Marine")
                    else:
                        readings.append(OceanReading(
                            name=parameter,
                            value=None,
                            unit="",
                            source="Open-Meteo Marine",
                            observed_at=None,
                            status="unavailable"
                        ))
                else:
                    readings.append(OceanReading(
                        name=parameter,
                        value=None,
                        unit="",
                        source="Open-Meteo Marine",
                        observed_at=None,
                        status="error"
                    ))
            elif parameter in ["ocean_temperature", "salinity"]:
                readings.append(OceanReading(
                    name=parameter,
                    value=None,
                    unit="",
                    source="unknown",
                    observed_at=None,
                    status="unavailable",
                    note=f"{parameter} currently unavailable from configured sources."
                ))

        insights = self._build_insights(readings)
        summary = self._summarize(resolved_name, readings, insights)

        any_mocked = any(r.status == "mocked" for r in readings)
        any_unavailable = any(r.status in ["unavailable", "error"] for r in readings)
        status = "partial" if (any_mocked or any_unavailable or errors) else "ok"

        return OceanAgentOutput(
            status=status,
            location={"lat": lat, "lon": lon, "name": resolved_name},
            generated_at=OceanAgentOutput.now_iso(),
            readings=readings,
            ocean_summary=summary,
            insights=insights,
            sources=sorted(sources),
            errors=errors,
        )

    def _resolve_location(self, agent_input: OceanAgentInput):
        errors: List[str] = []
        if agent_input.lat is not None and agent_input.lon is not None:
            return agent_input.lat, agent_input.lon, agent_input.location_name or "custom coordinates", errors

        name_key = (agent_input.location_name or "").strip().lower()
        if name_key in KNOWN_LOCATIONS:
            lat, lon = KNOWN_LOCATIONS[name_key]
            return lat, lon, agent_input.location_name, errors

        errors.append(
            f"Location '{agent_input.location_name}' not in the known-location lookup; "
            "used a default point. Wire up a shared geocoder for production."
        )
        return 13.08, 80.27, agent_input.location_name or "unresolved location (defaulted)", errors

    def _build_insights(self, readings: List[OceanReading]) -> List[str]:
        """
        Build reasoning around ocean conditions.
        """
        insights = []
        for reading in readings:
            if reading.name == "chlorophyll":
                if reading.value is None:
                    insights.append("No usable chlorophyll observation was available for the requested point/time.")
                elif reading.status == "mocked":
                    insights.append("Chlorophyll value is a mock fallback and must not be treated as a scientific observation.")
                else:
                    insights.append(
                        "Chlorophyll observation retrieved; correlate with sea-surface temperature, weather, "
                        "and other marine evidence before making a fishing or ecosystem recommendation."
                    )
        return insights

    def _summarize(self, location_name: Optional[str], readings: List[OceanReading], insights: List[str]) -> str:
        loc = location_name or "the requested location"
        parts = []
        for r in readings:
            if r.value is not None:
                parts.append(f"{r.name.replace('_', ' ')} is {r.value} {r.unit}".strip())
        body = "; ".join(parts) if parts else "no valid observations could be retrieved"
        summary = f"Ocean snapshot for {loc}: {body}."
        if insights:
            summary += " " + insights[0]
        return summary

    def to_coordinator_payload(self, output: OceanAgentOutput) -> dict:
        return {
            "agent": "ocean_agent",
            "result": output.to_dict(),
        }

