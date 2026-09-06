"""
Agent Data Schemas for ORCA (SIH26176)
Defines shared Pydantic contracts for Weather, Ocean, and Marine Agents.
Matches exact schema specs defined for SIH multi-agent architecture.
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class AgentLocation(BaseModel):
    """Spatial location context returned by agents."""
    name: Optional[str] = Field(default="Unknown", json_schema_extra={"example": "Mangalore"})
    latitude: float = Field(..., json_schema_extra={"example": 12.91})
    longitude: float = Field(..., json_schema_extra={"example": 74.86})


class AgentAssessment(BaseModel):
    """Domain-specific risk assessment from an individual agent."""
    risk_level: str = Field(
        default="low",
        description="Domain risk rating: 'low', 'moderate', 'high', 'critical'",
        json_schema_extra={"example": "low"}
    )
    summary: str = Field(
        default="",
        description="Textual summary of domain findings",
        json_schema_extra={"example": "Calm weather conditions suitable for maritime operations."}
    )


class AgentSource(BaseModel):
    """Provenance data source attribution."""
    name: str = Field(..., json_schema_extra={"example": "IMD"})
    timestamp: str = Field(..., json_schema_extra={"example": "2026-09-01T09:00:00Z"})
    details: Optional[Dict[str, Any]] = Field(default_factory=dict)


# --- Weather Agent Data Schema ---
class WeatherData(BaseModel):
    temperature_c: Optional[float] = Field(default=None, json_schema_extra={"example": 29.5})
    wind_speed_kmh: Optional[float] = Field(default=None, json_schema_extra={"example": 18.2})
    wind_direction_deg: Optional[float] = Field(default=None, json_schema_extra={"example": 240.0})
    wind_gusts_kmh: Optional[float] = Field(default=None, json_schema_extra={"example": 25.0})
    precipitation_mm: Optional[float] = Field(default=0.0, json_schema_extra={"example": 0.0})
    cyclone_warning: bool = Field(default=False, json_schema_extra={"example": False})
    cyclone_category: Optional[str] = Field(default=None, json_schema_extra={"example": None})
    lightning_risk: str = Field(default="low", json_schema_extra={"example": "low"})
    visibility_km: Optional[float] = Field(default=10.0, json_schema_extra={"example": 10.0})
    pressure_hpa: Optional[float] = Field(default=1012.0, json_schema_extra={"example": 1012.0})
    humidity_pct: Optional[float] = Field(default=75.0, json_schema_extra={"example": 75.0})


# --- Ocean Agent Data Schema ---
class OceanData(BaseModel):
    wave_height_m: Optional[float] = Field(default=None, json_schema_extra={"example": 1.2})
    wave_period_s: Optional[float] = Field(default=None, json_schema_extra={"example": 8.5})
    wave_direction_deg: Optional[float] = Field(default=None, json_schema_extra={"example": 210.0})
    swell_height_m: Optional[float] = Field(default=None, json_schema_extra={"example": 0.8})
    current_speed_ms: Optional[float] = Field(default=None, json_schema_extra={"example": 0.5})
    current_direction_deg: Optional[float] = Field(default=None, json_schema_extra={"example": 180.0})
    sea_surface_temperature_c: Optional[float] = Field(default=None, json_schema_extra={"example": 28.4})
    salinity_psu: Optional[float] = Field(default=None, json_schema_extra={"example": 35.0})
    tide_level_m: Optional[float] = Field(default=None, json_schema_extra={"example": 0.9})
    high_wave_alert: bool = Field(default=False, json_schema_extra={"example": False})


# --- Marine Agent Data Schema ---
class MarineData(BaseModel):
    chlorophyll_mg_m3: Optional[float] = Field(default=None, json_schema_extra={"example": 2.1})
    pfz_detected: bool = Field(default=False, json_schema_extra={"example": True})
    pfz_depth_m: Optional[float] = Field(default=None, json_schema_extra={"example": 35.0})
    pfz_confidence: Optional[float] = Field(default=None, json_schema_extra={"example": 0.88})
    mpa_violation: bool = Field(default=False, json_schema_extra={"example": False})
    mpa_name: Optional[str] = Field(default=None, json_schema_extra={"example": None})
    imbl_proximity_km: Optional[float] = Field(default=None, json_schema_extra={"example": 45.0})
    fish_species_indicators: List[str] = Field(default_factory=list, json_schema_extra={"example": ["Mackerel", "Sardine", "Tuna"]})
    hab_risk: bool = Field(default=False, description="Harmful Algal Bloom risk flag")


# --- Base Generic Agent Response ---
class BaseAgentResponse(BaseModel):
    agent: str = Field(..., json_schema_extra={"example": "weather_agent"})
    status: str = Field(default="success", json_schema_extra={"example": "success"})
    location: AgentLocation
    timestamp: str = Field(..., json_schema_extra={"example": "2026-09-01T10:00:00Z"})
    data: Dict[str, Any] = Field(default_factory=dict)
    assessment: AgentAssessment
    sources: List[AgentSource] = Field(default_factory=list)
    confidence: Optional[float] = Field(default=None, json_schema_extra={"example": 0.95})
    errors: List[str] = Field(default_factory=list)


# --- Strongly Typed Agent Responses ---
class WeatherAgentResponse(BaseAgentResponse):
    agent: str = "weather_agent"
    data: WeatherData = Field(default_factory=WeatherData)


class OceanAgentResponse(BaseAgentResponse):
    agent: str = "ocean_agent"
    data: OceanData = Field(default_factory=OceanData)


class MarineAgentResponse(BaseAgentResponse):
    agent: str = "marine_agent"
    data: MarineData = Field(default_factory=MarineData)


AgentResponse = Union[WeatherAgentResponse, OceanAgentResponse, MarineAgentResponse, BaseAgentResponse]
