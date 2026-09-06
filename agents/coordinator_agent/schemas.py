"""
Common input/output schemas for ORCA agents.

All specialized agents (Weather, Ocean, Marine, etc.)
should follow the common response structure defined here.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ============================================================
# INPUT
# ============================================================

@dataclass
class AgentRequest:
    """
    Standard request sent from the Coordinator to a specialized agent.
    """

    query: str

    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    start_date: Optional[str] = None
    end_date: Optional[str] = None

    parameters: List[str] = field(default_factory=list)

    def validate(self) -> Optional[str]:
        """Return an error message if the request is invalid."""

        if not self.query.strip():
            return "Query cannot be empty."

        if self.latitude is not None:
            if not -90 <= self.latitude <= 90:
                return "Latitude must be between -90 and 90."

        if self.longitude is not None:
            if not -180 <= self.longitude <= 180:
                return "Longitude must be between -180 and 180."

        return None


# ============================================================
# LOCATION
# ============================================================

@dataclass
class Location:
    """Standard geographic location used throughout ORCA."""

    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


# ============================================================
# ASSESSMENT
# ============================================================

@dataclass
class Assessment:
    """
    Agent's interpretation of the data.

    risk_level:
        low | moderate | high | unknown
    """

    risk_level: str = "unknown"
    summary: str = ""

    def validate(self) -> Optional[str]:
        valid_levels = {
            "low",
            "moderate",
            "high",
            "unknown",
        }

        if self.risk_level not in valid_levels:
            return (
                f"Invalid risk_level '{self.risk_level}'. "
                f"Expected one of: {sorted(valid_levels)}"
            )

        return None


# ============================================================
# COMMON AGENT RESPONSE
# ============================================================

@dataclass
class AgentResponse:
    """
    Standard response returned by every ORCA specialized agent.

    The Coordinator depends on this common structure.
    """

    agent: str

    status: str

    location: Location

    timestamp: str

    data: Dict[str, Any] = field(default_factory=dict)

    assessment: Assessment = field(
        default_factory=Assessment
    )

    sources: List[str] = field(default_factory=list)

    confidence: Optional[float] = None

    errors: List[str] = field(default_factory=list)

    def validate(self) -> Optional[str]:
        """Validate the common agent response."""

        valid_statuses = {
            "success",
            "partial",
            "error",
        }

        if not self.agent:
            return "Agent name cannot be empty."

        if self.status not in valid_statuses:
            return (
                f"Invalid status '{self.status}'. "
                f"Expected one of: {sorted(valid_statuses)}"
            )

        assessment_error = self.assessment.validate()

        if assessment_error:
            return assessment_error

        if self.confidence is not None:
            if not 0.0 <= self.confidence <= 1.0:
                return "Confidence must be between 0.0 and 1.0."

        return None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the response into a JSON-serializable dictionary.
        """

        return asdict(self)

    @staticmethod
    def now_iso() -> str:
        """Return the current UTC timestamp in ISO-8601 format."""

        return datetime.now(timezone.utc).isoformat()
