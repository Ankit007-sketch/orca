import logging
from typing import List, Optional
from .schemas import WeatherAgentInput, WeatherAgentOutput, WeatherReading, SUPPORTED_PARAMETERS
from .data_sources import OpenMeteoWeatherClient, _get_condition_from_code

logger = logging.getLogger("weather_agent.agent")

KNOWN_LOCATIONS = {
    "chennai coast": (13.08, 80.27),
    "mumbai coast": (18.96, 72.82),
    "kochi coast": (9.93, 76.26),
    "visakhapatnam coast": (17.68, 83.22),
    "lakshadweep": (10.57, 72.64),
    "andaman": (11.62, 92.73),
    "goa coast": (15.30, 73.82),
}

class WeatherAgent:
    def __init__(self, client: Optional[OpenMeteoWeatherClient] = None):
        self.client = client or OpenMeteoWeatherClient()

    def analyze(self, agent_input: WeatherAgentInput) -> WeatherAgentOutput:
        error = agent_input.validate()
        if error:
            return WeatherAgentOutput(
                status="error",
                location={"lat": agent_input.lat, "lon": agent_input.lon, "name": agent_input.location_name},
                generated_at=WeatherAgentOutput.now_iso(),
                readings=[],
                weather_summary="Could not analyze: invalid input.",
                errors=[error],
            )

        lat, lon, resolved_name, errors = self._resolve_location(agent_input)
        
        weather_data = self.client.get_weather(lat, lon)
        
        readings = []
        sources = ["Open-Meteo"]
        
        if "error" in weather_data:
            errors.append(weather_data["error"])
            status = "error"
            summary = "Failed to fetch weather data."
        else:
            current = weather_data.get("current", {})
            units = weather_data.get("current_units", {})
            observed_at = current.get("time")

            mapping = {
                "temperature": ("temperature_2m", "°C"),
                "humidity": ("relative_humidity_2m", "%"),
                "precipitation": ("precipitation", "mm"),
                "wind_speed": ("wind_speed_10m", "km/h"),
                "wind_direction": ("wind_direction_10m", "°"),
                "condition": ("weather_code", ""),
            }

            for param in agent_input.parameters:
                if param not in mapping:
                    continue
                
                api_key, default_unit = mapping[param]
                value = current.get(api_key)
                unit = units.get(api_key, default_unit)
                
                if param == "condition" and value is not None:
                    value = _get_condition_from_code(value)
                    unit = ""

                readings.append(WeatherReading(
                    name=param.replace("_", " ").title(),
                    value=value,
                    unit=unit,
                    source="Open-Meteo",
                    observed_at=observed_at,
                    status="ok" if value is not None else "unavailable"
                ))
            
            status = "ok"
            summary = self._summarize(resolved_name, readings)

        return WeatherAgentOutput(
            status=status,
            location={"lat": lat, "lon": lon, "name": resolved_name},
            generated_at=WeatherAgentOutput.now_iso(),
            readings=readings,
            weather_summary=summary,
            sources=sources,
            errors=errors,
        )

    def _resolve_location(self, agent_input: WeatherAgentInput):
        errors: List[str] = []
        if agent_input.lat is not None and agent_input.lon is not None:
            return agent_input.lat, agent_input.lon, agent_input.location_name or "custom coordinates", errors

        name_key = (agent_input.location_name or "").strip().lower()
        if name_key in KNOWN_LOCATIONS:
            lat, lon = KNOWN_LOCATIONS[name_key]
            return lat, lon, agent_input.location_name, errors

        errors.append(
            f"Location '{agent_input.location_name}' not found. Defaulting to Chennai coast."
        )
        return 13.08, 80.27, agent_input.location_name or "default location", errors

    def _summarize(self, location_name: Optional[str], readings: List[WeatherReading]) -> str:
        loc = location_name or "the requested location"
        parts = []
        for r in readings:
            if r.value is not None:
                if r.unit:
                    parts.append(f"{r.name}: {r.value} {r.unit}")
                else:
                    parts.append(f"{r.name}: {r.value}")
        
        body = ", ".join(parts) if parts else "no weather data could be retrieved"
        return f"Weather snapshot for {loc}: {body}."

    def to_coordinator_payload(self, output: WeatherAgentOutput) -> dict:
        return {
            "agent": "weather_agent",
            "result": output.to_dict(),
        }
