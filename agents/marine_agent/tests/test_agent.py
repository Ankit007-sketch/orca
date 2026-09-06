"""
Basic tests for MarineAgent.

Run with:
    python -m pytest agents/marine_agent/tests -v
or, with no pytest installed:
    python -m unittest discover -s agents/marine_agent/tests -v

These tests avoid real network calls by injecting fake clients, so they
run fast and pass with no internet access (important for CI).
"""

import unittest

from agents.marine_agent.agent import MarineAgent
from agents.marine_agent.schemas import MarineAgentInput, SUPPORTED_PARAMETERS


class FakeERDDAPClient:
    """Stands in for INCOISERDDAPClient without hitting the network."""

    def get_parameter(self, parameter, lat, lon):
        return {
            "value": 27.5,
            "unit": "°C" if parameter == "sea_surface_temperature" else "unit",
            "source": "fake-erddap",
            "observed_at": "2026-01-01T00:00:00Z",
            "status": "ok",
        }


class FakeIMDClient:
    def get_wind_speed(self, lat, lon):
        return {
            "value": 12.0,
            "unit": "km/h",
            "source": "fake-imd",
            "observed_at": "2026-01-01T00:00:00Z",
            "status": "ok",
        }


class HighAlertERDDAPClient(FakeERDDAPClient):
    def get_parameter(self, parameter, lat, lon):
        if parameter == "sea_surface_temperature":
            return {
                "value": 31.2,  # above ALERT_THRESHOLDS high
                "unit": "°C",
                "source": "fake-erddap",
                "observed_at": "2026-01-01T00:00:00Z",
                "status": "ok",
            }
        return super().get_parameter(parameter, lat, lon)


def make_agent(erddap=None, imd=None):
    return MarineAgent(erddap_client=erddap or FakeERDDAPClient(), imd_client=imd or FakeIMDClient())


class TestMarineAgentInputValidation(unittest.TestCase):
    def test_rejects_missing_location(self):
        agent = make_agent()
        result = agent.analyze(MarineAgentInput())
        self.assertEqual(result.status, "error")
        self.assertTrue(result.errors)

    def test_rejects_bad_lat(self):
        agent = make_agent()
        result = agent.analyze(MarineAgentInput(lat=999, lon=80.0))
        self.assertEqual(result.status, "error")


class TestMarineAgentAnalyze(unittest.TestCase):
    def test_basic_lat_lon_query_returns_ok(self):
        agent = make_agent()
        result = agent.analyze(MarineAgentInput(lat=13.08, lon=80.27, location_name="Chennai coast"))
        self.assertEqual(result.status, "ok")
        self.assertEqual(len(result.readings), len(SUPPORTED_PARAMETERS))
        self.assertIn("Chennai coast", result.ecosystem_summary)

    def test_named_known_location_resolves_coordinates(self):
        agent = make_agent()
        result = agent.analyze(MarineAgentInput(location_name="Lakshadweep", parameters=["sea_surface_temperature"]))
        self.assertEqual(result.status, "ok")
        self.assertAlmostEqual(result.location["lat"], 10.57)
        self.assertAlmostEqual(result.location["lon"], 72.64)

    def test_unknown_named_location_produces_soft_error_but_still_runs(self):
        agent = make_agent()
        result = agent.analyze(MarineAgentInput(location_name="Atlantis"))
        self.assertEqual(result.status, "partial")
        self.assertTrue(result.errors)
        self.assertTrue(result.readings)

    def test_alert_triggered_on_high_sst(self):
        agent = make_agent(erddap=HighAlertERDDAPClient())
        result = agent.analyze(MarineAgentInput(lat=13.08, lon=80.27, parameters=["sea_surface_temperature"]))
        self.assertTrue(any("bleaching" in a.lower() for a in result.alerts))

    def test_unsupported_parameter_is_ignored_gracefully(self):
        agent = make_agent()
        result = agent.analyze(MarineAgentInput(lat=13.08, lon=80.27, parameters=["not_a_real_parameter"]))
        # falls back to full supported set rather than erroring
        self.assertEqual(len(result.readings), len(SUPPORTED_PARAMETERS))

    def test_output_is_json_serializable_dict(self):
        import json

        agent = make_agent()
        result = agent.analyze(MarineAgentInput(lat=13.08, lon=80.27))
        payload = result.to_dict()
        json.dumps(payload)  # should not raise

    def test_to_coordinator_payload_wraps_result(self):
        agent = make_agent()
        result = agent.analyze(MarineAgentInput(lat=13.08, lon=80.27))
        payload = agent.to_coordinator_payload(result)
        self.assertEqual(payload["agent"], "marine_agent")
        self.assertIn("result", payload)


if __name__ == "__main__":
    unittest.main()
