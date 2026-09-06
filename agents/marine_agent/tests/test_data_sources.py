"""
Tests for data_sources.py -- focused on the mock-fallback contract, since
we don't want tests to depend on live INCOIS/IMD network access.
"""

import unittest
from unittest.mock import patch

from agents.marine_agent import data_sources as ds


class TestMockFallback(unittest.TestCase):
    def test_mock_reading_has_expected_shape(self):
        reading = ds._mock_reading("wave_height", reason="test reason")
        self.assertIn("value", reading)
        self.assertIn("unit", reading)
        self.assertEqual(reading["status"], "mocked")
        self.assertEqual(reading["note"], "test reason")

    def test_erddap_client_falls_back_on_missing_dataset_id(self):
        client = ds.INCOISERDDAPClient()
        result = client.get_parameter("salinity", lat=13.0, lon=80.0)
        # "salinity" has no dataset id configured yet in DATASET_IDS,
        # so this should mock rather than raise.
        self.assertEqual(result["status"], "mocked")

    @patch("agents.marine_agent.data_sources.requests.Session.get")
    def test_erddap_client_falls_back_on_network_error(self, mock_get):
        mock_get.side_effect = ConnectionError("no network in test env")
        client = ds.INCOISERDDAPClient()
        result = client.get_parameter("sea_surface_temperature", lat=13.0, lon=80.0)
        self.assertEqual(result["status"], "mocked")

    @patch("agents.marine_agent.data_sources.requests.Session.get")
    def test_imd_client_falls_back_on_network_error(self, mock_get):
        mock_get.side_effect = ConnectionError("no network in test env")
        client = ds.IMDClient()
        result = client.get_wind_speed(lat=13.0, lon=80.0)
        self.assertEqual(result["status"], "mocked")

    def test_osf_forecast_reference_shape(self):
        ref = ds.get_osf_forecast_reference()
        self.assertIn("url", ref)
        self.assertTrue(ref["url"].startswith("https://"))


if __name__ == "__main__":
    unittest.main()
