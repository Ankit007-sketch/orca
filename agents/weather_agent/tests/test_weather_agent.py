import unittest
from unittest.mock import patch, Mock
import sys
import os


# Add the weather_agent folder to Python path
sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            ".."
        )
    )
)

from weather_agent import WeatherAgent


class TestWeatherAgent(unittest.TestCase):

    # -----------------------------------
    # TEST 1: Successful API response
    # -----------------------------------

    @patch("weather_agent.requests.get")
    def test_successful_api_response(self, mock_get):

        mock_response = Mock()

        mock_response.json.return_value = {
            "current_condition": [
                {
                    "temp_C": "30",
                    "weatherDesc": [
                        {
                            "value": "Sunny"
                        }
                    ],
                    "humidity": "60",
                    "windspeedKmph": "10"
                }
            ]
        }

        mock_response.raise_for_status.return_value = None

        mock_get.return_value = mock_response

        agent = WeatherAgent()

        result = agent.get_weather("Chennai")

        self.assertEqual(result["status"], "success")

        self.assertEqual(
            result["location"]["name"],
            "Chennai"
        )

        self.assertEqual(
            result["data"]["temperature"],
            "30°C"
        )

        self.assertEqual(
            result["data"]["condition"],
            "Sunny"
        )

        self.assertEqual(
            result["assessment"]["risk_level"],
            "low"
        )

        self.assertEqual(
            result["errors"],
            []
        )


    # -----------------------------------
    # TEST 2: API failure
    # -----------------------------------

    @patch("weather_agent.requests.get")
    def test_api_failure(self, mock_get):

        mock_get.side_effect = Exception(
            "API connection failed"
        )

        agent = WeatherAgent()

        result = agent.get_weather("Chennai")

        self.assertEqual(
            result["status"],
            "error"
        )

        self.assertEqual(
            result["assessment"]["risk_level"],
            "unknown"
        )

        self.assertEqual(
            result["confidence"],
            0.0
        )

        self.assertGreater(
            len(result["errors"]),
            0
        )


    # -----------------------------------
    # TEST 3: ORCA response schema
    # -----------------------------------

    @patch("weather_agent.requests.get")
    def test_orca_response_schema(self, mock_get):

        mock_response = Mock()

        mock_response.json.return_value = {
            "current_condition": [
                {
                    "temp_C": "28",
                    "weatherDesc": [
                        {
                            "value": "Cloudy"
                        }
                    ],
                    "humidity": "70",
                    "windspeedKmph": "15"
                }
            ]
        }

        mock_response.raise_for_status.return_value = None

        mock_get.return_value = mock_response

        agent = WeatherAgent()

        result = agent.get_weather("Chennai")

        required_keys = [
            "agent",
            "status",
            "location",
            "timestamp",
            "data",
            "assessment",
            "sources",
            "confidence",
            "errors"
        ]

        for key in required_keys:

            self.assertIn(
                key,
                result
            )

        location_keys = [
            "name",
            "latitude",
            "longitude"
        ]

        for key in location_keys:

            self.assertIn(
                key,
                result["location"]
            )

        assessment_keys = [
            "risk_level",
            "summary"
        ]

        for key in assessment_keys:

            self.assertIn(
                key,
                result["assessment"]
            )


if __name__ == "__main__":

    unittest.main()