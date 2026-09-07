"""
MarineAgent: core logic.

The Marine Agent retrieves marine/ecosystem information from
Copernicus Marine and returns structured results for the Coordinator Agent.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from .schemas import (
    MarineAgentInput,
    MarineAgentOutput,
    ParameterReading,
    SUPPORTED_PARAMETERS,
)

from .data_sources import (
    INCOISERDDAPClient,
    get_osf_forecast_reference,
)

logger = logging.getLogger("marine_agent.agent")


# Alert thresholds for the demo.
ALERT_THRESHOLDS = {
    "sea_surface_temperature": {
        "high": 30.5,
        "message": (
            "Elevated sea surface temperature — possible coral bleaching risk."
        ),
    },
    "wave_height": {
        "high": 2.5,
        "message": "High wave activity — rough sea conditions.",
    },
    "wind_speed": {
        "high": 40.0,
        "message": "High wind speed — small craft advisory territory.",
    },
}


# Common demo locations.
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
    """
    Main Marine Agent.

    Uses the Copernicus Marine Toolbox through the data_sources module.
    """

    def __init__(
        self,
        erddap_client: Optional[INCOISERDDAPClient] = None,
    ):
        self.erddap = erddap_client or INCOISERDDAPClient()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self, agent_input: MarineAgentInput) -> MarineAgentOutput:
        """
        Main Marine Agent entry point.

        Returns a structured MarineAgentOutput.
        """

        # Validate input.
        error = agent_input.validate()

        if error:
            return MarineAgentOutput(
                status="error",
                location={
                    "lat": agent_input.lat,
                    "lon": agent_input.lon,
                    "name": agent_input.location_name,
                },
                generated_at=MarineAgentOutput.now_iso(),
                readings=[],
                ecosystem_summary="Could not analyze: invalid input.",
                errors=[error],
            )

        # Resolve coordinates.
        lat, lon, resolved_name, errors = self._resolve_location(agent_input)

        # Only use parameters supported by our schema.
        parameters = [
            p
            for p in agent_input.parameters
            if p in SUPPORTED_PARAMETERS
        ]

        # If no specific parameters were requested,
        # use all supported parameters.
        if not parameters:
            parameters = SUPPORTED_PARAMETERS

        readings: List[ParameterReading] = []
        sources = set()

        # Fetch every requested marine parameter.
        for parameter in parameters:

            reading_dict = self._fetch_parameter(
                parameter,
                lat,
                lon,
            )

            readings.append(
                ParameterReading(
                    name=parameter,
                    **reading_dict,
                )
            )

            if reading_dict.get("source"):
                sources.add(reading_dict["source"])

        # Add INCOIS OSF reference.
        osf_reference = get_osf_forecast_reference()

        sources.add(osf_reference["name"])

        # Generate alerts.
        alerts = self._compute_alerts(readings)

        # Generate human-readable summary.
        summary = self._summarize(
            resolved_name,
            readings,
            alerts,
        )

        # Determine final status.
        has_errors = any(
            r.status == "error"
            for r in readings
        )

        status = "partial" if (has_errors or errors) else "ok"

        return MarineAgentOutput(
            status=status,
            location={
                "lat": lat,
                "lon": lon,
                "name": resolved_name,
            },
            generated_at=MarineAgentOutput.now_iso(),
            readings=readings,
            ecosystem_summary=summary,
            alerts=alerts,
            sources=sorted(sources),
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Location handling
    # ------------------------------------------------------------------

    def _resolve_location(
        self,
        agent_input: MarineAgentInput,
    ):
        errors: List[str] = []

        # Direct coordinates were provided.
        if (
            agent_input.lat is not None
            and agent_input.lon is not None
        ):
            return (
                agent_input.lat,
                agent_input.lon,
                agent_input.location_name or "custom coordinates",
                errors,
            )

        # Try known demo locations.
        name_key = (
            agent_input.location_name or ""
        ).strip().lower()

        if name_key in KNOWN_LOCATIONS:
            lat, lon = KNOWN_LOCATIONS[name_key]

            return (
                lat,
                lon,
                agent_input.location_name,
                errors,
            )

        # Unknown location.
        errors.append(
            f"Location '{agent_input.location_name}' "
            "was not found in the known-location lookup. "
            "Using the default Chennai coastal point."
        )

        return (
            13.08,
            80.27,
            agent_input.location_name
            or "default coastal location",
            errors,
        )

    # ------------------------------------------------------------------
    # Data retrieval
    # ------------------------------------------------------------------

    def _fetch_parameter(
        self,
        parameter: str,
        lat: float,
        lon: float,
    ) -> dict:

        # All marine parameters now go through
        # the Copernicus-backed data_sources client.
        return self.erddap.get_parameter(
            parameter,
            lat,
            lon,
        )

    # ------------------------------------------------------------------
    # Alert calculation
    # ------------------------------------------------------------------

    def _compute_alerts(
        self,
        readings: List[ParameterReading],
    ) -> List[str]:

        alerts = []

        for reading in readings:

            rule = ALERT_THRESHOLDS.get(reading.name)

            if (
                rule
                and reading.value is not None
                and reading.value >= rule["high"]
            ):
                alerts.append(rule["message"])

        return alerts

    # ------------------------------------------------------------------
    # Summary generation
    # ------------------------------------------------------------------

    def _summarize(
        self,
        location_name: Optional[str],
        readings: List[ParameterReading],
        alerts: List[str],
    ) -> str:

        location = (
            location_name
            or "the requested location"
        )

        parts = []

        for reading in readings:

            if reading.value is None:
                continue

            parts.append(
                f"{reading.name.replace('_', ' ')} "
                f"is {reading.value} {reading.unit}".strip()
            )

        if parts:
            body = "; ".join(parts)
        else:
            body = "no readings could be retrieved"

        summary = (
            f"Marine snapshot for {location}: "
            f"{body}."
        )

        if alerts:
            summary += (
                " Alerts: "
                + " ".join(alerts)
            )

        return summary

    # ------------------------------------------------------------------
    # Coordinator integration
    # ------------------------------------------------------------------

    def to_coordinator_payload(
        self,
        output: MarineAgentOutput,
    ) -> dict:
        """
        Convert MarineAgentOutput into the Coordinator format.
        """

        return {
            "agent": "marine_agent",
            "result": output.to_dict(),
        }