"""
OceanAgent: core logic.

Responsibility recap (from the team task):
  - Work with IRS P4 OCM-Chlorophyll data              -> data_sources.py
  - Understand time/latitude/longitude/chlorophyll    -> schemas.py + data source schema detection
  - Retrieve/process chlorophyll information          -> this file
  - Build reasoning around ocean conditions            -> _build_insights()
  - Return structured Coordinator-compatible results  -> OceanAgentOutput.to_dict()
  - Document preprocessing and add tests               -> README.md + tests/
"""

from __future__ import annotations

import logging
from typing import List, Optional

from .data_sources import IRSP4OCMClient
from .schemas import (
    SUPPORTED_PARAMETERS,
    ChlorophyllReading,
    OceanAgentInput,
    OceanAgentOutput,
)

logger = logging.getLogger("ocean_agent.agent")

# Only used for demo-location convenience. A production ORCA system should use
# a shared geocoder/GIS service rather than duplicating location knowledge.
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
    """The Ocean/Chlorophyll specialist agent. One instance is reusable."""

    def __init__(self, ocm_client: Optional[IRSP4OCMClient] = None):
        self.ocm = ocm_client or IRSP4OCMClient()

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

        readings: List[ChlorophyllReading] = []
        sources = set()

        for parameter in parameters:
            if parameter == "chlorophyll":
                reading_dict = self.ocm.get_chlorophyll(lat, lon, agent_input.date)
                reading = ChlorophyllReading(name=parameter, **reading_dict)
                readings.append(reading)
                sources.add(reading.source)

        insights = self._build_insights(readings)
        summary = self._summarize(resolved_name, readings, insights)

        any_mocked = any(r.status == "mocked" for r in readings)
        any_unavailable = any(r.status == "unavailable" for r in readings)
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

    def _build_insights(self, readings: List[ChlorophyllReading]) -> List[str]:
        """
        Keep interpretation conservative. Chlorophyll alone is not enough to
        declare a fishing zone healthy/productive/safe. The Coordinator should
        correlate it with SST, weather, PFZ and other evidence.
        """
        insights = []
        for reading in readings:
            if reading.value is None:
                insights.append("No usable chlorophyll observation was available for the requested point/time.")
                continue
            if reading.status == "mocked":
                insights.append("Chlorophyll value is a mock fallback and must not be treated as a scientific observation.")
            else:
                insights.append(
                    "Chlorophyll observation retrieved; correlate with sea-surface temperature, weather, "
                    "and other marine evidence before making a fishing or ecosystem recommendation."
                )
        return insights

    def _summarize(self, location_name: Optional[str], readings: List[ChlorophyllReading], insights: List[str]) -> str:
        loc = location_name or "the requested location"
        parts = []
        for r in readings:
            if r.value is not None:
                parts.append(f"chlorophyll is {r.value} {r.unit}".strip())
        body = "; ".join(parts) if parts else "no chlorophyll observation could be retrieved"
        summary = f"Ocean snapshot for {loc}: {body}."
        if insights:
            summary += " " + insights[0]
        return summary

    def to_coordinator_payload(self, output: OceanAgentOutput) -> dict:
        return {
            "agent": "ocean_agent",
            "result": output.to_dict(),
        }
