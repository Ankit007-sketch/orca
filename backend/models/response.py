"""
Pydantic Response Schemas for ORCA (SIH26176)
Defines unified API output contracts for recommendations, risk scoring,
auditable evidence trails, and WebGIS GeoJSON layers.
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class RiskFactor(BaseModel):
    """Specific factor contributing to overall risk calculation."""
    factor_name: str = Field(..., json_schema_extra={"example": "Wave Height"})
    value: Any = Field(..., json_schema_extra={"example": 1.8})
    unit: Optional[str] = Field(default=None, json_schema_extra={"example": "m"})
    threshold_limit: Optional[str] = Field(default=None, json_schema_extra={"example": "> 2.5m is UNSAFE"})
    severity: str = Field(default="low", description="'low', 'moderate', 'high', 'critical'")
    description: str = Field(..., json_schema_extra={"example": "Wave conditions are within manageable limits for motorized boats."})


class RiskAssessment(BaseModel):
    """Consolidated multi-factor risk assessment score."""
    level: str = Field(
        ...,
        description="Overall classification: 'SAFE', 'CAUTION', 'UNSAFE'",
        json_schema_extra={"example": "SAFE"}
    )
    risk_score: float = Field(
        ...,
        description="Continuous normalized risk index on [0.0, 1.0] scale",
        ge=0.0,
        le=1.0,
        json_schema_extra={"example": 0.25}
    )
    primary_hazard: Optional[str] = Field(
        default=None,
        description="Primary hazard driving the risk score if caution/unsafe",
        json_schema_extra={"example": "High swell waves"}
    )
    confidence: float = Field(
        default=0.92,
        ge=0.0,
        le=1.0,
        description="Statistical confidence score of the synthesized assessment",
        json_schema_extra={"example": 0.92}
    )
    contributing_factors: List[RiskFactor] = Field(
        default_factory=list,
        description="Detailed breakdown of meteorological, oceanographic, and marine factors"
    )


class EvidenceItem(BaseModel):
    """Auditable evidence trail item attributed to ISRO/INCOIS/IMD data sources."""
    source: str = Field(
        ...,
        description="Name of contributing satellite or meteorological agency",
        json_schema_extra={"example": "IRS P4 OCM Chlorophyll"}
    )
    observation: str = Field(
        ...,
        description="Direct observational finding or metric extraction",
        json_schema_extra={"example": "Chlorophyll-a concentration is 2.1 mg/m³ indicating active PFZ front."}
    )
    timestamp: str = Field(
        ...,
        description="Timestamp of observation/satellite pass",
        json_schema_extra={"example": "2026-09-01T09:30:00Z"}
    )
    category: str = Field(
        default="general",
        description="Domain category: 'weather', 'ocean', 'satellite', 'geofence', 'fisheries'",
        json_schema_extra={"example": "satellite"}
    )
    severity: str = Field(
        default="info",
        description="'info', 'favorable', 'warning', 'critical'",
        json_schema_extra={"example": "favorable"}
    )


class GeoJSONFeature(BaseModel):
    """Standard GeoJSON Feature object."""
    type: str = "Feature"
    geometry: Dict[str, Any]
    properties: Dict[str, Any] = Field(default_factory=dict)


class GeoJSONFeatureCollection(BaseModel):
    """Standard GeoJSON FeatureCollection."""
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature] = Field(default_factory=list)


class UnifiedResponse(BaseModel):
    """
    Unified JSON Output Payload returned to Frontend (Member 6) and API clients.
    Complies with SIH ORCA Blueprint Section 9 Data Contract.
    """
    session_id: str = Field(..., description="Unique session identifier", json_schema_extra={"example": "orca-sess-001"})
    query_id: str = Field(..., description="Unique query execution identifier", json_schema_extra={"example": "qry-98a76b"})
    user_query: str = Field(..., description="Original user prompt or translated prompt", json_schema_extra={"example": "Is it safe off Mangalore?"})
    recommendation: str = Field(
        ...,
        description="Synthesized natural language recommendation in requested language",
        json_schema_extra={"example": "Safe for fishing. Favorable Potential Fishing Zone (PFZ) detected 18 km west with low wave activity (1.2m)."}
    )
    language_code: str = Field(default="en", description="Target language code of recommendation", json_schema_extra={"example": "kn"})
    risk: RiskAssessment = Field(..., description="Consolidated risk assessment object")
    evidence: List[EvidenceItem] = Field(
        default_factory=list,
        description="Auditable provenance list with timestamps & official data sources"
    )
    geojson_layers: Dict[str, Any] = Field(
        default_factory=dict,
        description="Mapbox/Leaflet vector layers containing PFZ polygons, IMBL boundaries, MPA zones, and hazard contours"
    )
    agent_assessments: Dict[str, Any] = Field(
        default_factory=dict,
        description="Raw or semi-structured outputs from Weather, Ocean, and Marine agents for debugging / drilldown"
    )
    timestamps: Dict[str, str] = Field(
        default_factory=dict,
        description="Map of source systems to their respective data timestamps"
    )
    execution_time_ms: float = Field(
        default=0.0,
        description="Backend pipeline roundtrip processing latency in milliseconds",
        json_schema_extra={"example": 145.2}
    )


class HealthResponse(BaseModel):
    """System health check payload."""
    status: str = "healthy"
    version: str = "1.0.0"
    service: str = "ORCA Backend API & Multi-Agent Dispatcher"
    agents_available: Dict[str, bool] = Field(default_factory=dict)
    timestamp: str


class SessionHistoryItem(BaseModel):
    """Single query-response turn in session history."""
    query_id: str
    user_query: str
    recommendation: str
    risk_level: str
    risk_score: float
    timestamp: str
    latitude: float
    longitude: float


class HistoryResponse(BaseModel):
    """Full multi-turn history for a session."""
    session_id: str
    total_turns: int
    history: List[SessionHistoryItem]
