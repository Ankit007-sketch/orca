"""
Pydantic Request Schemas for ORCA (SIH26176)
Handles input validation for conversational queries, spatial coordinates,
and multi-turn session requests.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """
    Main conversational query payload sent from Frontend / API clients.
    """
    session_id: str = Field(
        ...,
        description="Unique multi-turn conversation ID",
        json_schema_extra={"example": "orca-sess-001"}
    )
    user_query: str = Field(
        ...,
        description="Natural language query from maritime user/fisherman",
        json_schema_extra={"example": "Is it safe to go fishing off Mangalore tomorrow morning?"}
    )
    latitude: float = Field(
        ...,
        description="Latitude of the query location (WGS84)",
        ge=-90.0,
        le=90.0,
        json_schema_extra={"example": 12.9141}
    )
    longitude: float = Field(
        ...,
        description="Longitude of the query location (WGS84)",
        ge=-180.0,
        le=180.0,
        json_schema_extra={"example": 74.8560}
    )
    language_code: str = Field(
        default="en",
        description="Regional Indian language code (e.g., 'en', 'kn', 'ta', 'te', 'ml', 'hi', 'bn', 'gu', 'mr')",
        json_schema_extra={"example": "kn"}
    )
    timestamp: Optional[str] = Field(
        default=None,
        description="ISO 8601 observation or forecast timestamp requested",
        json_schema_extra={"example": "2026-09-01T10:00:00Z"}
    )
    radius_km: Optional[float] = Field(
        default=25.0,
        description="Spatial reasoning radius around coordinates in kilometers",
        ge=1.0,
        le=200.0,
        json_schema_extra={"example": 25.0}
    )
    vessel_type: Optional[str] = Field(
        default="motorized_boat",
        description="Type of fishing/marine vessel (e.g., 'traditional_craft', 'motorized_boat', 'mechanized_trawler')",
        json_schema_extra={"example": "motorized_boat"}
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Arbitrary client metadata (device info, port of departure, etc.)"
    )


class FeedbackRequest(BaseModel):
    """
    Feedback submitted by user on accuracy of marine advisory.
    """
    session_id: str = Field(..., description="Session identifier")
    feedback_score: int = Field(..., ge=1, le=5, description="1 (Poor) to 5 (Excellent)")
    comments: Optional[str] = Field(default=None, description="User comments or ground observation")
    observed_weather: Optional[str] = Field(default=None, description="Actual observed sea condition")


class SessionCreateRequest(BaseModel):
    """
    Session initialization request.
    """
    user_id: Optional[str] = Field(default=None, description="Optional persistent user identifier")
    preferred_language: str = Field(default="en", description="Default regional language code")
    initial_location: Optional[Dict[str, float]] = Field(
        default=None,
        description="Initial GPS coordinates {'latitude': float, 'longitude': float}"
    )
