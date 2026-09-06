"""
Data source clients for the Marine Agent.

Wraps the three sources given for this project:

1. INCOIS ERDDAP  (https://erddap.incois.gov.in/erddap/index.html)
   A proper REST API for scientific ocean data (SST, waves, currents, etc).
   This is the PRIMARY source -- it's the only one of the three that's a
   real, queryable data API rather than a dashboard page.

2. INCOIS Ocean State Forecast page (osfforecast.jsp)
   A rendered HTML dashboard, not an API. We treat it as a "reference link"
   for now (surfaced in `sources`) rather than scraping it, since scraping
   government dashboard HTML is brittle and likely to break right before a
   demo. Swap in a scraper later if a teammate wants richer forecast text.

3. IMD public API (api.imd.gov.in)
   Weather data (wind, rain) that complements ocean parameters. Endpoint
   shape isn't finalized/verified here -- wrapped so it fails soft.

Design choice: every fetch function degrades gracefully. If the network
call fails or INCOIS/IMD are unreachable (common for gov't APIs, and this
sandbox itself has no outbound internet), we return a clearly-flagged mock
reading instead of crashing, so the rest of the pipeline / demo still works.
Set MARINE_AGENT_ALLOW_MOCK=False to disable this and force real errors.
"""

from __future__ import annotations

import os
import random
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import requests

logger = logging.getLogger("marine_agent.data_sources")

ALLOW_MOCK_FALLBACK = os.environ.get("MARINE_AGENT_ALLOW_MOCK", "true").lower() != "false"
REQUEST_TIMEOUT_SECONDS = 8

INCOIS_ERDDAP_BASE = "https://erddap.incois.gov.in/erddap"
INCOIS_OSF_FORECAST_URL = "https://incois.gov.in/oceanservices/osfforecast.jsp"
IMD_API_BASE = "https://api.imd.gov.in/public/index.php"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# INCOIS ERDDAP client
# ---------------------------------------------------------------------------

class INCOISERDDAPClient:
    """
    Thin client around INCOIS's ERDDAP server.

    ERDDAP query pattern (tabledap, for point/station data):
        {base}/tabledap/{dataset_id}.json?{vars}&{constraints}

    ERDDAP query pattern (griddap, for gridded satellite data e.g. SST):
        {base}/griddap/{dataset_id}.json?{var}[(time)][(lat)][(lon)]

    Known example dataset (verified to exist on INCOIS's ERDDAP):
        incois_tmi_3day_datasets   -- TMI 3-day gridded SST-related data

    NOTE for teammates: the exact dataset IDs you need (waves, salinity,
    chlorophyll, currents) should be confirmed by browsing:
        https://erddap.incois.gov.in/erddap/info/index.html
    and dropped into DATASET_IDS below. This client works for any valid
    dataset id/variable combo once you do.
    """

    # Fill in / adjust after browsing the ERDDAP dataset catalog.
    DATASET_IDS = {
        "sea_surface_temperature": "incois_tmi_3day_datasets",
    }

    def __init__(self, base_url: str = INCOIS_ERDDAP_BASE, session: Optional[requests.Session] = None):
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()

    def fetch_griddap_json(self, dataset_id: str, query: str) -> Dict[str, Any]:
        """
        Fetch a griddap dataset as JSON.
        `query` is the ERDDAP query string, e.g.:
            "sst[(2024-01-01T00:00:00Z)][(10):(15)][(75):(80)]"
        """
        url = f"{self.base_url}/griddap/{dataset_id}.json?{query}"
        resp = self.session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()
        return resp.json()

    def fetch_tabledap_json(self, dataset_id: str, variables: str, constraints: str = "") -> Dict[str, Any]:
        """
        Fetch a tabledap (tabular/station) dataset as JSON.
        Example: variables="time,latitude,longitude,sea_surface_temperature"
        """
        url = f"{self.base_url}/tabledap/{dataset_id}.json?{variables}{constraints}"
        resp = self.session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()
        return resp.json()

    def get_parameter(self, parameter: str, lat: float, lon: float) -> Dict[str, Any]:
        """
        High-level helper: fetch the nearest/latest value for a supported
        parameter near (lat, lon). Falls back to a mocked reading on any
        failure (network, missing dataset id, unexpected response shape)
        so the agent stays demo-safe.
        """
        dataset_id = self.DATASET_IDS.get(parameter)
        if not dataset_id:
            return _mock_reading(parameter, reason=f"No ERDDAP dataset id configured for '{parameter}' yet.")

        try:
            # Griddap point query: value at nearest time/lat/lon.
            query = f"sst[(last)][({lat})][({lon})]"
            data = self.fetch_griddap_json(dataset_id, query)
            rows = data.get("table", {}).get("rows", [])
            if not rows:
                raise ValueError("Empty response from ERDDAP.")
            row = rows[0]
            col_names = data["table"]["columnNames"]
            value = row[col_names.index("sst")] if "sst" in col_names else row[-1]
            return {
                "value": float(value),
                "unit": "°C",
                "source": f"INCOIS-ERDDAP:{dataset_id}",
                "observed_at": row[col_names.index("time")] if "time" in col_names else _utc_now_iso(),
                "status": "ok",
            }
        except Exception as exc:  # noqa: BLE001 -- intentionally broad: many failure modes, all handled the same
            logger.warning("INCOIS ERDDAP fetch failed for %s: %s", parameter, exc)
            return _mock_reading(parameter, reason=f"ERDDAP request failed: {exc}")


# ---------------------------------------------------------------------------
# INCOIS Ocean State Forecast (reference link, not scraped)
# ---------------------------------------------------------------------------

def get_osf_forecast_reference() -> Dict[str, str]:
    """
    The OSF forecast page is a rendered dashboard rather than an API, so we
    surface it as a citable reference rather than scraping fragile HTML.
    """
    return {
        "name": "INCOIS Ocean State Forecast",
        "url": INCOIS_OSF_FORECAST_URL,
        "note": "Dashboard page (wave height / current / SST forecasts). "
                "Not machine-readable; link included for human follow-up.",
    }


# ---------------------------------------------------------------------------
# IMD client (weather, complements ocean data)
# ---------------------------------------------------------------------------

class IMDClient:
    """
    Wrapper around IMD's public API. Endpoint shape should be confirmed
    against current IMD docs -- this fails soft (mocked reading) if the
    call doesn't succeed, so it never blocks the rest of the agent.
    """

    def __init__(self, base_url: str = IMD_API_BASE, session: Optional[requests.Session] = None):
        self.base_url = base_url
        self.session = session or requests.Session()

    def get_wind_speed(self, lat: float, lon: float) -> Dict[str, Any]:
        try:
            resp = self.session.get(
                self.base_url,
                params={"lat": lat, "lon": lon},
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            resp.raise_for_status()
            data = resp.json()
            # Response shape not yet confirmed against live IMD docs --
            # adjust the key names below once verified.
            value = data.get("wind_speed") or data.get("windSpeed")
            if value is None:
                raise ValueError("Unexpected IMD response shape.")
            return {
                "value": float(value),
                "unit": "km/h",
                "source": "IMD-API",
                "observed_at": data.get("time", _utc_now_iso()),
                "status": "ok",
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("IMD fetch failed: %s", exc)
            return _mock_reading("wind_speed", reason=f"IMD request failed: {exc}")


# ---------------------------------------------------------------------------
# Shared mock fallback
# ---------------------------------------------------------------------------

_MOCK_RANGES = {
    "sea_surface_temperature": (24.0, 30.0, "°C"),
    "wave_height": (0.5, 2.5, "m"),
    "salinity": (33.0, 36.0, "PSU"),
    "chlorophyll": (0.1, 2.0, "mg/m^3"),
    "wind_speed": (5.0, 25.0, "km/h"),
    "ocean_current": (0.1, 1.2, "m/s"),
}


def _mock_reading(parameter: str, reason: str) -> Dict[str, Any]:
    if not ALLOW_MOCK_FALLBACK:
        raise RuntimeError(reason)
    lo, hi, unit = _MOCK_RANGES.get(parameter, (0.0, 1.0, ""))
    return {
        "value": round(random.uniform(lo, hi), 2),
        "unit": unit,
        "source": "mock-fallback",
        "observed_at": _utc_now_iso(),
        "status": "mocked",
        "note": reason,
    }
