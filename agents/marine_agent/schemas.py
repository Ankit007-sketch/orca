"""
Structured input/output contracts for the Marine Agent.

Deliberately built on stdlib `dataclasses` (no pydantic/external dependency)
so the Coordinator Agent (or any other teammate's module) can import this
file without needing to install anything extra.

If the team later standardizes on pydantic across all agents, this file is
the only one that needs to change -- `agent.py` just imports from here.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any


# ---------------------------------------------------------------------------
# INPUT
# ---------------------------------------------------------------------------

# The set of marine parameters this agent knows how to fetch/derive.
# Coordinator (or a user-facing NLU layer) is expected to send a subset of
# these in `parameters`. Unknown values are ignored (not errored).
SUPPORTED_PARAMETERS = [
    "sea_surface_temperature",
    "wave_height",
    "salinity",
    "chlorophyll",
    "wind_speed",
    "ocean_current",
]


@dataclass
class MarineAgentInput:
    """What the Coordinator Agent (or a user query) sends to the Marine Agent."""

    # Location: either a lat/lon pair, or a free-text location name (e.g.
    # "Chennai coast", "Lakshadweep"), or both (lat/lon takes priority).
    lat: Optional[float] = None
    lon: Optional[float] = None
    location_name: Optional[str] = None

    # Which parameters to analyze. Defaults to a sensible "ecosystem health"
    # bundle if left empty.
    parameters: List[str] = field(default_factory=lambda: list(SUPPORTED_PARAMETERS))

    # Optional ISO date range (YYYY-MM-DD). If omitted, agent uses latest
    # available observation.
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    # Free-text query, for logging / future NLU use. Not required.
    raw_query: Optional[str] = None

    def validate(self) -> Optional[str]:
        """Returns an error message if invalid, else None."""
        if self.lat is None and self.lon is None and not self.location_name:
            return "MarineAgentInput requires either (lat, lon) or location_name."
        if self.lat is not None and not (-90 <= self.lat <= 90):
            return f"lat={self.lat} out of range [-90, 90]."
        if self.lon is not None and not (-180 <= self.lon <= 180):
            return f"lon={self.lon} out of range [-180, 180]."
        return None


# ---------------------------------------------------------------------------
# OUTPUT
# ---------------------------------------------------------------------------

@dataclass
class ParameterReading:
    """A single marine parameter reading/estimate."""

    name: str                       # e.g. "sea_surface_temperature"
    value: Optional[float]          # numeric value, None if unavailable
    unit: str                       # e.g. "°C", "m", "PSU", "mg/m^3"
    source: str                     # e.g. "INCOIS-ERDDAP:incois_tmi_3day_datasets"
    observed_at: Optional[str]      # ISO timestamp of the observation, if known
    status: str = "ok"              # "ok" | "unavailable" | "mocked"
    note: Optional[str] = None      # human-readable caveat, if any


@dataclass
class MarineAgentOutput:
    """What the Marine Agent returns to the Coordinator Agent."""

    status: str                              # "ok" | "partial" | "error"
    location: Dict[str, Any]                 # {"lat":.., "lon":.., "name":..}
    generated_at: str                        # ISO timestamp
    readings: List[ParameterReading]
    ecosystem_summary: str                   # short natural-language synthesis
    alerts: List[str] = field(default_factory=list)   # e.g. ["High wave warning"]
    sources: List[str] = field(default_factory=list)  # data providers used
    errors: List[str] = field(default_factory=list)   # non-fatal issues encountered

    def to_dict(self) -> Dict[str, Any]:
        """JSON-serializable dict -- this is the contract the Coordinator Agent consumes."""
        return asdict(self)

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()
