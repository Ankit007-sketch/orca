"""
Asynchronous Multi-Agent Dispatcher for ORCA (SIH26176)

Dispatches concurrent requests to:
- Weather Agent
- Ocean Agent
- Marine Agent

The dispatcher is designed to keep the complete ORCA pipeline working
even when real external data sources are unavailable.

Real agent integrations are attempted where available, with deterministic
fallback/demo values so the frontend always receives a valid response.
"""

import asyncio
import time
import math
from typing import Dict, Any, Optional

from backend.models.agent_schemas import (
    WeatherAgentResponse,
    OceanAgentResponse,
    MarineAgentResponse,
    AgentLocation,
    AgentAssessment,
    AgentSource,
    WeatherData,
    OceanData,
    MarineData,
)

from data.loader import data_loader


# ---------------------------------------------------------------------------
# Real specialist agents
# ---------------------------------------------------------------------------

# Ocean-state agent
try:
    from agents.marine_agent import MarineAgent, MarineAgentInput
except Exception:
    MarineAgent = None
    MarineAgentInput = None


# Chlorophyll / marine ecosystem agent
try:
    from agents.ocean_agent import OceanAgent, OceanAgentInput
except Exception:
    OceanAgent = None
    OceanAgentInput = None


# Real weather agent
try:
    from agents.weather_agent.weather_agent import WeatherAgent
except Exception:
    WeatherAgent = None


# ---------------------------------------------------------------------------
# Agent Dispatcher
# ---------------------------------------------------------------------------

class AgentDispatcher:
    """
    Coordinates non-blocking parallel dispatch to domain-specialized agents.
    """

    def __init__(self):
        # Reusable real agent instances.
        self._marine_agent = MarineAgent() if MarineAgent else None
        self._ocean_agent = OceanAgent() if OceanAgent else None
        self._weather_agent = WeatherAgent() if WeatherAgent else None

    # -----------------------------------------------------------------------
    # DISPATCH ALL AGENTS
    # -----------------------------------------------------------------------

    async def dispatch_all(
        self,
        latitude: float,
        longitude: float,
        user_query: str,
        session_id: str,
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Dispatch Weather, Ocean and Marine agents concurrently.

        Each agent has its own fallback handling so one failed agent
        does not stop the complete ORCA pipeline.
        """

        ts = timestamp or time.strftime(
            "%Y-%m-%dT%H:%M:%SZ",
            time.gmtime()
        )

        results = await asyncio.gather(
            self.dispatch_weather_agent(
                latitude,
                longitude,
                user_query,
                ts
            ),
            self.dispatch_ocean_agent(
                latitude,
                longitude,
                user_query,
                ts
            ),
            self.dispatch_marine_agent(
                latitude,
                longitude,
                user_query,
                ts
            ),
            return_exceptions=True
        )

        weather_res, ocean_res, marine_res = results

        # Handle unexpected exceptions gracefully.
        if isinstance(weather_res, Exception):
            weather_res = self._fallback_error_response(
                "weather_agent",
                latitude,
                longitude,
                ts,
                str(weather_res)
            )

        if isinstance(ocean_res, Exception):
            ocean_res = self._fallback_error_response(
                "ocean_agent",
                latitude,
                longitude,
                ts,
                str(ocean_res)
            )

        if isinstance(marine_res, Exception):
            marine_res = self._fallback_error_response(
                "marine_agent",
                latitude,
                longitude,
                ts,
                str(marine_res)
            )

        return {
            "weather": weather_res,
            "ocean": ocean_res,
            "marine": marine_res
        }

    # -----------------------------------------------------------------------
    # WEATHER AGENT
    # -----------------------------------------------------------------------

    async def dispatch_weather_agent(
        self,
        lat: float,
        lon: float,
        query: str,
        timestamp: str
    ) -> Dict[str, Any]:
        """
        Weather Agent.

        The real WeatherAgent is attempted first.

        If the real weather service is unavailable, the dispatcher
        returns deterministic simulated weather data so that the
        end-to-end ORCA pipeline continues working.
        """

        try:
            # Resolve nearest known coastal location.
            nearest_port, _ = data_loader.find_nearest_port(
                lat,
                lon
            )

            location_name = (
                nearest_port["name"]
                if nearest_port
                else "Coastal Waters"
            )

            # ---------------------------------------------------------------
            # Try the real Weather Agent
            # ---------------------------------------------------------------

            if self._weather_agent is not None:

                try:
                    result = await asyncio.wait_for(
                        asyncio.to_thread(
                            self._weather_agent.get_weather,
                            location_name
                        ),
                        timeout=8.0
                    )

                    if isinstance(result, dict):

                        # Make sure location exists.
                        if "location" not in result:
                            result["location"] = {}

                        # Preserve actual requested coordinates.
                        result["location"]["name"] = location_name
                        result["location"]["latitude"] = lat
                        result["location"]["longitude"] = lon

                        # Preserve ORCA timestamp.
                        result["timestamp"] = timestamp

                        return result

                except Exception:
                    # Real weather source failed.
                    # Continue to deterministic fallback below.
                    pass

            # ---------------------------------------------------------------
            # Deterministic simulator fallback
            # ---------------------------------------------------------------

            temperature = round(
                27.0 + (math.sin(lat * 0.4) * 2.0),
                1
            )

            wind_speed = round(
                7.0 + abs(math.cos(lon * 0.3) * 4.0),
                1
            )

            humidity = round(
                72.0 + abs(math.sin(lat * 0.2) * 10.0),
                1
            )

            condition = "Partly Cloudy"

            # Risk assessment.
            if (
                wind_speed >= 60
            ):
                risk_level = "high"
                summary = (
                    "Strong wind conditions detected. "
                    "Marine activities may be hazardous."
                )

            elif (
                wind_speed >= 30
                or humidity >= 90
                or temperature >= 40
                or temperature <= 5
            ):
                risk_level = "moderate"
                summary = (
                    "Weather conditions may require caution."
                )

            else:
                risk_level = "low"
                summary = (
                    "Current weather conditions are generally favorable."
                )

            return {
                "agent": "weather_agent",
                "status": "success",
                "location": {
                    "name": location_name,
                    "latitude": lat,
                    "longitude": lon
                },
                "timestamp": timestamp,
                "data": {
                    "temperature": f"{temperature}°C",
                    "condition": condition,
                    "humidity": f"{humidity}%",
                    "wind_speed": f"{wind_speed} km/h"
                },
                "assessment": {
                    "risk_level": risk_level,
                    "summary": summary
                },
                "sources": [
                    {
                        "name": "ORCA Weather Simulator",
                        "timestamp": timestamp
                    }
                ],
                "confidence": 0.80,
                "errors": []
            }

        except Exception as error:

            return self._fallback_error_response(
                "weather_agent",
                lat,
                lon,
                timestamp,
                str(error)
            )

    # -----------------------------------------------------------------------
    # OCEAN AGENT
    # -----------------------------------------------------------------------

    async def dispatch_ocean_agent(
        self,
        lat: float,
        lon: float,
        query: str,
        timestamp: str
    ) -> Dict[str, Any]:
        """
        Ocean state agent.

        Provides:
        - Wave height
        - Wave period
        - Wave direction
        - Ocean current
        - Sea surface temperature
        - Salinity

        Attempts the real marine/ocean agent first and falls back to
        deterministic simulator values if required.
        """

        try:

            nearest_port, _ = data_loader.find_nearest_port(
                lat,
                lon
            )

            port_name = (
                nearest_port["name"]
                if nearest_port
                else "Coastal Waters"
            )

            real_readings: Dict[str, Any] = {}
            real_source: Optional[str] = None

            # ---------------------------------------------------------------
            # Try real Ocean-State Agent
            # ---------------------------------------------------------------

            if self._marine_agent and MarineAgentInput:

                try:
                    output = await asyncio.wait_for(
                        asyncio.to_thread(
                            self._marine_agent.analyze,
                            MarineAgentInput(
                                lat=lat,
                                lon=lon,
                                raw_query=query,
                                parameters=[
                                    "sea_surface_temperature",
                                    "wave_height",
                                    "salinity",
                                    "ocean_current",
                                ],
                            ),
                        ),
                        timeout=8.0
                    )

                    if hasattr(output, "readings"):

                        for reading in output.readings:

                            if (
                                reading.value is not None
                                and reading.status != "mocked"
                            ):
                                real_readings[reading.name] = reading

                        if real_readings:
                            real_source = "INCOIS-ERDDAP (live)"

                except Exception:
                    real_readings = {}

            # ---------------------------------------------------------------
            # Deterministic simulator fallback
            # ---------------------------------------------------------------

            wave_h_sim = round(
                1.1
                + (math.sin(lat * 0.8) * 0.4)
                + (0.3 if lon < 75.0 else 0.1),
                1
            )

            curr_spd_sim = round(
                0.4 + (math.cos(lon * 0.5) * 0.2),
                2
            )

            sst_sim = round(
                28.2 + (math.sin(lat * 0.3) * 0.6),
                1
            )

            wave_h = (
                real_readings["wave_height"].value
                if "wave_height" in real_readings
                else wave_h_sim
            )

            sst = (
                real_readings["sea_surface_temperature"].value
                if "sea_surface_temperature"
                in real_readings
                else sst_sim
            )

            salinity = (
                real_readings["salinity"].value
                if "salinity" in real_readings
                else 34.8
            )

            curr_spd = (
                real_readings["ocean_current"].value
                if "ocean_current" in real_readings
                else curr_spd_sim
            )

            # ---------------------------------------------------------------
            # Ocean risk
            # ---------------------------------------------------------------

            is_rough = wave_h > 2.2

            if wave_h > 3.0:
                risk_lvl = "high"

            elif is_rough or wave_h > 1.4:
                risk_lvl = "moderate"

            else:
                risk_lvl = "low"

            if is_rough:

                summary_text = (
                    f"Rough sea state with wave heights "
                    f"reaching {wave_h}m."
                )

            else:

                summary_text = (
                    f"Moderate wave conditions ({wave_h}m) "
                    f"and steady current ({curr_spd} m/s)."
                )

            response = OceanAgentResponse(
                agent="ocean_agent",
                status="success",
                location=AgentLocation(
                    name=port_name,
                    latitude=lat,
                    longitude=lon
                ),
                timestamp=timestamp,
                data=OceanData(
                    wave_height_m=wave_h,
                    wave_period_s=8.2,
                    wave_direction_deg=220.0,
                    current_speed_ms=curr_spd,
                    sea_surface_temperature_c=sst,
                    salinity_psu=salinity,
                    high_wave_alert=is_rough
                ),
                assessment=AgentAssessment(
                    risk_level=risk_lvl,
                    summary=summary_text
                ),
                sources=[
                    AgentSource(
                        name=(
                            real_source
                            or "INCOIS (simulated fallback)"
                        ),
                        timestamp=timestamp
                    )
                ],
                confidence=(
                    0.91
                    if real_source
                    else 0.75
                ),
                errors=[]
            )

            return response.model_dump()

        except Exception as error:

            return self._fallback_error_response(
                "ocean_agent",
                lat,
                lon,
                timestamp,
                str(error)
            )

    # -----------------------------------------------------------------------
    # MARINE AGENT
    # -----------------------------------------------------------------------

    async def dispatch_marine_agent(
        self,
        lat: float,
        lon: float,
        query: str,
        timestamp: str
    ) -> Dict[str, Any]:
        """
        Marine ecosystem agent.

        Provides:
        - Chlorophyll
        - PFZ status
        - MPA status
        - IMBL proximity
        - Fish species indicators

        Attempts the real Ocean/Chlorophyll Agent where available and
        falls back to deterministic simulator values.
        """

        try:

            nearest_port, _ = data_loader.find_nearest_port(
                lat,
                lon
            )

            port_name = (
                nearest_port["name"]
                if nearest_port
                else "Marine Zone"
            )

            # ---------------------------------------------------------------
            # MPA and IMBL checks
            # ---------------------------------------------------------------

            mpa_name, in_mpa = (
                data_loader.check_mpa_intersection(
                    lat,
                    lon
                )
            )

            boundary_name, imbl_dist, in_imbl_zone = (
                data_loader.check_imbl_proximity(
                    lat,
                    lon
                )
            )

            # ---------------------------------------------------------------
            # Chlorophyll
            # ---------------------------------------------------------------

            chloro: Optional[float] = None

            chloro_source = (
                "IRS P4 OCM (simulated fallback)"
            )

            # Try real chlorophyll/ocean agent.
            if self._ocean_agent and OceanAgentInput:

                try:

                    output = await asyncio.wait_for(
                        asyncio.to_thread(
                            self._ocean_agent.analyze,
                            OceanAgentInput(
                                lat=lat,
                                lon=lon,
                                raw_query=query
                            )
                        ),
                        timeout=8.0
                    )

                    if hasattr(output, "readings"):

                        reading = next(
                            (
                                r
                                for r in output.readings
                                if (
                                    r.name == "chlorophyll"
                                    and r.value is not None
                                    and r.status != "mocked"
                                )
                            ),
                            None
                        )

                        if reading:

                            chloro = reading.value
                            chloro_source = reading.source

                except Exception:
                    chloro = None

            # ---------------------------------------------------------------
            # Deterministic chlorophyll fallback
            # ---------------------------------------------------------------

            if chloro is None:

                chloro = round(
                    1.8 + (math.cos(lat * 1.2) * 0.6),
                    2
                )

            # ---------------------------------------------------------------
            # PFZ logic
            # ---------------------------------------------------------------

            pfz_detected = (
                chloro >= 1.5
                and not in_mpa
            )

            # ---------------------------------------------------------------
            # Marine risk
            # ---------------------------------------------------------------

            if in_mpa:

                risk_lvl = "high"

                summary_text = (
                    f"Restricted Marine Protected Area detected "
                    f"({mpa_name}). Extractive fishing is strictly prohibited."
                )

            elif in_imbl_zone:

                risk_lvl = "moderate"

                summary_text = (
                    f"Proximity warning: Vessel is within "
                    f"{round(imbl_dist, 1)} km of {boundary_name}."
                )

            elif pfz_detected:

                risk_lvl = "low"

                summary_text = (
                    "Marine indicators suggest a potentially productive "
                    "area (PFZ detected) with favorable chlorophyll concentration."
                )

            else:

                risk_lvl = "low"

                summary_text = (
                    "Normal marine ecosystem status. "
                    "Dispersed pelagic indicators."
                )

            response = MarineAgentResponse(
                agent="marine_agent",
                status="success",
                location=AgentLocation(
                    name=port_name,
                    latitude=lat,
                    longitude=lon
                ),
                timestamp=timestamp,
                data=MarineData(
                    chlorophyll_mg_m3=chloro,
                    pfz_detected=pfz_detected,
                    pfz_depth_m=(
                        35.0
                        if pfz_detected
                        else None
                    ),
                    pfz_confidence=(
                        0.88
                        if pfz_detected
                        else None
                    ),
                    mpa_violation=in_mpa,
                    mpa_name=mpa_name,
                    imbl_proximity_km=(
                        round(imbl_dist, 1)
                        if imbl_dist < 100.0
                        else None
                    ),
                    fish_species_indicators=(
                        [
                            "Mackerel",
                            "Sardine",
                            "Seer Fish"
                        ]
                        if pfz_detected
                        else ["Coastal Mixed"]
                    )
                ),
                assessment=AgentAssessment(
                    risk_level=risk_lvl,
                    summary=summary_text
                ),
                sources=[
                    AgentSource(
                        name="INCOIS",
                        timestamp=timestamp
                    ),
                    AgentSource(
                        name=chloro_source,
                        timestamp=timestamp
                    )
                ],
                confidence=(
                    0.90
                    if chloro_source !=
                    "IRS P4 OCM (simulated fallback)"
                    else 0.75
                ),
                errors=[]
            )

            return response.model_dump()

        except Exception as error:

            return self._fallback_error_response(
                "marine_agent",
                lat,
                lon,
                timestamp,
                str(error)
            )

    # -----------------------------------------------------------------------
    # FALLBACK ERROR RESPONSE
    # -----------------------------------------------------------------------

    def _fallback_error_response(
        self,
        agent_name: str,
        lat: float,
        lon: float,
        timestamp: str,
        error_msg: str
    ) -> Dict[str, Any]:
        """
        Final safety fallback.

        Even if an individual agent encounters an unexpected error,
        the dispatcher returns a structured result instead of allowing
        the entire ORCA request to fail.
        """

        return {
            "agent": agent_name,
            "status": "partial_error",
            "location": {
                "name": "Location",
                "latitude": lat,
                "longitude": lon
            },
            "timestamp": timestamp,
            "data": {},
            "assessment": {
                "risk_level": "moderate",
                "summary": (
                    f"Agent {agent_name} temporarily unavailable. "
                    "Fallback default applied."
                )
            },
            "sources": [
                {
                    "name": "ORCA Resilience Layer",
                    "timestamp": timestamp
                }
            ],
            "confidence": 0.5,
            "errors": [error_msg]
        }


# ---------------------------------------------------------------------------
# Global dispatcher instance
# ---------------------------------------------------------------------------

agent_dispatcher = AgentDispatcher()