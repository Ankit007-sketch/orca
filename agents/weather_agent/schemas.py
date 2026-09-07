"""
Structured input/output contracts for the Weather Agent.
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

SUPPORTED_PARAMETERS = [
    "temperature",
    "humidity",
    "precipitation",
    "wind_speed",
    "wind_direction",
    "condition"
]

@dataclass
class WeatherAgentInput:
    lat: Optional[float] = None
    lon: Optional[float] = None
    location_name: Optional[str] = None
    parameters: List[str] = field(default_factory=lambda: list(SUPPORTED_PARAMETERS))

    def validate(self) -> Optional[str]:
        if self.lat is None and self.lon is None and not self.location_name:
            return "WeatherAgentInput requires either (lat, lon) or location_name."
        return None

@dataclass
class WeatherReading:
    name: str
    value: Optional[Any]
    unit: str
    source: str
    observed_at: Optional[str]
    status: str = "ok"

@dataclass
class WeatherAgentOutput:
    status: str
    location: Dict[str, Any]
    generated_at: str
    readings: List[WeatherReading]
    weather_summary: str
    sources: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()
