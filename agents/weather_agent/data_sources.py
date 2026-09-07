import requests
from typing import Dict, Any, Optional

class OpenMeteoWeatherClient:
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        
    def get_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,wind_direction_10m,weather_code",
            "timezone": "auto"
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}

def _get_condition_from_code(code: int) -> str:
    # WMO Weather interpretation codes (WW)
    if code == 0: return "Clear sky"
    elif code in [1, 2, 3]: return "Mainly clear, partly cloudy, and overcast"
    elif code in [45, 48]: return "Fog and depositing rime fog"
    elif code in [51, 53, 55]: return "Drizzle: Light, moderate, and dense intensity"
    elif code in [56, 57]: return "Freezing Drizzle: Light and dense intensity"
    elif code in [61, 63, 65]: return "Rain: Slight, moderate and heavy intensity"
    elif code in [66, 67]: return "Freezing Rain: Light and heavy intensity"
    elif code in [71, 73, 75]: return "Snow fall: Slight, moderate, and heavy intensity"
    elif code == 77: return "Snow grains"
    elif code in [80, 81, 82]: return "Rain showers: Slight, moderate, and violent"
    elif code in [85, 86]: return "Snow showers slight and heavy"
    elif code == 95: return "Thunderstorm: Slight or moderate"
    elif code in [96, 99]: return "Thunderstorm with slight and heavy hail"
    return "Unknown"
