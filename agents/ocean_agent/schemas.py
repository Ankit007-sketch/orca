"""
Structured input/output contracts for the Ocean/Chlorophyll Agent.

Uses stdlib dataclasses so other ORCA agents can import this module without
an extra schema dependency. If the team later standardizes on Pydantic, this
file can be replaced without changing the public agent entrypoint.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

SUPPORTED_PARAMETERS = ["chlorophyll"]


@dataclass
class OceanAgentInput:
    """What the Coordinator Agent (or a user query) sends to the Ocean Agent."""

    # Either coordinates or a known free-text location. Coordinates take priority.
    lat: Optional[float] = None
    lon: Optional[float] = None
    location_name: Optional[str] = None

    # Chlorophyll is the current scope of this specialist agent.
    parameters: List[str] = field(default_factory=lambda: list(SUPPORTED_PARAMETERS))

    # Optional ISO date/time. If omitted, the latest available observation is used.
    date: Optional[str] = None

    # Optional search window. The first implementation uses nearest-grid-cell
    # retrieval; this field is retained for future regional aggregation.
    radius_km: Optional[float] = None

    # Free-text query for logging / future NLU use.
    raw_query: Optional[str] = None

    def validate(self) -> Optional[str]:
        if self.lat is None and self.lon is None and not self.location_name:
            return "OceanAgentInput requires either (lat, lon) or location_name."
        if self.lat is not None and not (-90 <= self.lat <= 90):
            return f"lat={self.lat} out of range [-90, 90]."
        if self.lon is not None and not (-180 <= self.lon <= 180):
            return f"lon={self.lon} out of range [-180, 180]."
        if self.radius_km is not None and self.radius_km <= 0:
            return "radius_km must be greater than 0 when provided."
        if self.date:
            try:
                datetime.fromisoformat(self.date.replace("Z", "+00:00"))
            except ValueError:
                return f"date='{self.date}' is not a valid ISO date/time."
        return None


@dataclass
class ChlorophyllReading:
    """A chlorophyll observation/estimate returned by the OCM dataset."""

    name: str
    value: Optional[float]
    unit: str
    source: str
    observed_at: Optional[str]
    status: str = "ok"              # ok | unavailable | mocked
    note: Optional[str] = None
    grid_lat: Optional[float] = None
    grid_lon: Optional[float] = None


@dataclass
class OceanAgentOutput:
    """What the Ocean Agent returns to the Coordinator Agent."""

    status: str
    location: Dict[str, Any]
    generated_at: str
    readings: List[ChlorophyllReading]
    ocean_summary: str
    insights: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()
