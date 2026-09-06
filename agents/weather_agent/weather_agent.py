import requests
from datetime import datetime, timezone


class WeatherAgent:
    def __init__(self):
        self.agent_name = "weather_agent"

    def assess_risk(self, temperature, condition, wind_speed, humidity):
        """
        Determine weather risk based on current conditions.
        """

        condition_lower = condition.lower()

        temperature_value = int(temperature)
        wind_value = int(wind_speed)
        humidity_value = int(humidity)

        # High risk conditions
        if (
            "thunder" in condition_lower
            or "storm" in condition_lower
            or "tornado" in condition_lower
            or wind_value >= 60
        ):
            return {
                "risk_level": "high",
                "summary": "Potentially hazardous weather conditions detected."
            }

        # Medium risk conditions
        if (
            "rain" in condition_lower
            or "fog" in condition_lower
            or wind_value >= 30
            or temperature_value >= 40
            or temperature_value <= 5
            or humidity_value >= 90
        ):
            return {
                "risk_level": "medium",
                "summary": "Weather conditions may require caution."
            }

        # Low risk conditions
        return {
            "risk_level": "low",
            "summary": "Current weather conditions are generally favorable."
        }

    def get_weather(self, location):

        url = f"https://wttr.in/{location}?format=j1"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            weather_data = response.json()

            current = weather_data["current_condition"][0]

            temperature = current.get("temp_C", "0")
            condition = current.get("weatherDesc", [{}])[0].get("value", "Unknown")
            humidity = current.get("humidity", "0")
            wind_speed = current.get("windspeedKmph", "0")

            assessment = self.assess_risk(
                temperature,
                condition,
                wind_speed,
                humidity
            )

            return {
                "agent": "weather_agent",
                "status": "success",

                "location": {
                    "name": location,
                    "latitude": None,
                    "longitude": None
                },

                "timestamp": datetime.now(timezone.utc).isoformat(),

                "data": {
                    "temperature": f"{temperature}°C",
                    "condition": condition,
                    "humidity": f"{humidity}%",
                    "wind_speed": f"{wind_speed} km/h"
                },

                "assessment": assessment,

                "sources": [
                    "wttr.in"
                ],

                "confidence": 0.8,

                "errors": []
            }

        except Exception as error:

            return {
                "agent": "weather_agent",
                "status": "error",

                "location": {
                    "name": location,
                    "latitude": None,
                    "longitude": None
                },

                "timestamp": datetime.now(timezone.utc).isoformat(),

                "data": {},

                "assessment": {
                    "risk_level": "unknown",
                    "summary": "Unable to retrieve weather data."
                },

                "sources": [
                    "wttr.in"
                ],

                "confidence": 0.0,

                "errors": [
                    str(error)
                ]
            }


if __name__ == "__main__":

    agent = WeatherAgent()

    location = input("Enter city name: ")

    result = agent.get_weather(location)

    print("\nWeather Agent Result:")
    print(result)