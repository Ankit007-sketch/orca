"""Basic tests for OceanAgent. No real dataset/network is required."""

import json
import unittest

from agents.ocean_agent.agent import OceanAgent
from agents.ocean_agent.schemas import OceanAgentInput, SUPPORTED_PARAMETERS


class FakeOCMClient:
    def get_chlorophyll(self, lat, lon, date=None):
        return {
            "value": 0.42,
            "unit": "mg/m^3",
            "source": "fake-irs-p4-ocm",
            "observed_at": date or "2000-01-01T00:00:00",
            "status": "ok",
            "grid_lat": lat,
            "grid_lon": lon,
        }


class MockedOCMClient(FakeOCMClient):
    def get_chlorophyll(self, lat, lon, date=None):
        result = super().get_chlorophyll(lat, lon, date)
        result["status"] = "mocked"
        result["source"] = "mock-fallback"
        result["note"] = "test fallback"
        return result


def make_agent(client=None):
    return OceanAgent(ocm_client=client or FakeOCMClient())


class TestOceanAgentInputValidation(unittest.TestCase):
    def test_rejects_missing_location(self):
        result = make_agent().analyze(OceanAgentInput())
        self.assertEqual(result.status, "error")
        self.assertTrue(result.errors)

    def test_rejects_bad_lat(self):
        result = make_agent().analyze(OceanAgentInput(lat=999, lon=80.0))
        self.assertEqual(result.status, "error")

    def test_rejects_invalid_date(self):
        result = make_agent().analyze(OceanAgentInput(lat=13.0, lon=80.0, date="not-a-date"))
        self.assertEqual(result.status, "error")


class TestOceanAgentAnalyze(unittest.TestCase):
    def test_basic_lat_lon_query_returns_ok(self):
        result = make_agent().analyze(OceanAgentInput(lat=13.08, lon=80.27, location_name="Chennai coast"))
        self.assertEqual(result.status, "ok")
        self.assertEqual(len(result.readings), len(SUPPORTED_PARAMETERS))
        self.assertIn("Chennai coast", result.ocean_summary)

    def test_named_known_location_resolves_coordinates(self):
        result = make_agent().analyze(OceanAgentInput(location_name="Lakshadweep"))
        self.assertEqual(result.status, "ok")
        self.assertAlmostEqual(result.location["lat"], 10.57)
        self.assertAlmostEqual(result.location["lon"], 72.64)

    def test_unknown_named_location_is_partial_but_runs(self):
        result = make_agent().analyze(OceanAgentInput(location_name="Atlantis"))
        self.assertEqual(result.status, "partial")
        self.assertTrue(result.errors)
        self.assertTrue(result.readings)

    def test_mocked_data_makes_result_partial(self):
        result = make_agent(MockedOCMClient()).analyze(OceanAgentInput(lat=13.08, lon=80.27))
        self.assertEqual(result.status, "partial")
        self.assertTrue(any("mock fallback" in i.lower() for i in result.insights))

    def test_output_is_json_serializable(self):
        result = make_agent().analyze(OceanAgentInput(lat=13.08, lon=80.27))
        json.dumps(result.to_dict())

    def test_to_coordinator_payload_wraps_result(self):
        agent = make_agent()
        result = agent.analyze(OceanAgentInput(lat=13.08, lon=80.27))
        payload = agent.to_coordinator_payload(result)
        self.assertEqual(payload["agent"], "ocean_agent")
        self.assertIn("result", payload)


if __name__ == "__main__":
    unittest.main()
