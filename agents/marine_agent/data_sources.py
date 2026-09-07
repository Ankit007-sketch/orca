"""
Real Copernicus Marine data sources for the Marine Agent.

This module uses the official Copernicus Marine Toolbox Python API.

The Copernicus Marine credentials are NOT stored in this file.
The Toolbox automatically uses the credentials configured on the
machine running the application.

Real parameters:
- sea_surface_temperature -> Copernicus temperature forecast
- salinity               -> Copernicus salinity forecast
- ocean_current          -> Copernicus surface currents
- wave_height            -> Copernicus wave forecast
- chlorophyll             -> Copernicus biogeochemistry forecast

If a real request fails, the function returns an error reading rather
than inventing a fake value.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import copernicusmarine

logger = logging.getLogger("marine_agent.data_sources")


# ---------------------------------------------------------------------------
# Current Copernicus Marine datasets
# ---------------------------------------------------------------------------

DATASETS = {
    "sea_surface_temperature": {
        "dataset_id": "cmems_mod_glo_phy-thetao_anfc_0.083deg_PT6H-i",
        "variable": "thetao",
        "unit": "°C",
        "depth": 0.5,
        "source": "Copernicus Marine - Global Ocean Physics",
    },

    "salinity": {
        "dataset_id": "cmems_mod_glo_phy-so_anfc_0.083deg_PT6H-i",
        "variable": "so",
        "unit": "PSU",
        "depth": 0.5,
        "source": "Copernicus Marine - Global Ocean Physics",
    },

    "ocean_current": {
        "dataset_id": "cmems_mod_glo_phy-cur_anfc_0.083deg_PT6H-i",
        "variable": "uo",
        "unit": "m/s",
        "depth": 0.5,
        "source": "Copernicus Marine - Global Ocean Physics",
    },

    "wave_height": {
        "dataset_id": "cmems_mod_glo_wav_anfc_0.083deg_PT3H-i",
        "variable": "VHM0",
        "unit": "m",
        "depth": None,
        "source": "Copernicus Marine - Global Ocean Waves",
    },

    "chlorophyll": {
        "dataset_id": "cmems_mod_glo_bgc-bio_anfc_0.25deg_P1D-m",
        "variable": "chl",
        "unit": "mg/m^3",
        "depth": 0.5,
        "source": "Copernicus Marine - Global Ocean Biogeochemistry",
    },
}


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_valid_number(value: Any) -> bool:
    try:
        value = float(value)
        return math.isfinite(value)
    except (TypeError, ValueError):
        return False


# ---------------------------------------------------------------------------
# Copernicus Marine client
# ---------------------------------------------------------------------------

class CopernicusMarineClient:
    """
    Client used by MarineAgent to retrieve real ocean data.

    Authentication is handled by the Copernicus Marine Toolbox.
    It will automatically use the credentials configured through
    copernicusmarine login on the machine where the application runs.
    """

    def __init__(self):
        pass

    def get_parameter(
        self,
        parameter: str,
        lat: float,
        lon: float,
    ) -> Dict[str, Any]:
        """
        Retrieve the latest available Copernicus Marine value
        near the requested latitude/longitude.
        """

        config = DATASETS.get(parameter)

        if config is None:
            return {
                "value": None,
                "unit": "",
                "source": "Copernicus Marine",
                "observed_at": _utc_now_iso(),
                "status": "error",
                "note": f"No Copernicus dataset configured for '{parameter}'.",
            }

        dataset_id = config["dataset_id"]
        variable = config["variable"]
        depth = config["depth"]

        try:
            # Small time window around now.
            #
            # This allows Copernicus to select the latest available
            # observation/forecast rather than using old fixed-year data.
            now = datetime.now(timezone.utc)
            start = now - timedelta(days=2)
            end = now + timedelta(days=2)

            kwargs = {
                "dataset_id": dataset_id,
                "variables": [variable],
                "minimum_longitude": lon,
                "maximum_longitude": lon,
                "minimum_latitude": lat,
                "maximum_latitude": lat,
                "start_datetime": start,
                "end_datetime": end,
                "coordinates_selection_method": "nearest",
                
            }

            if depth is not None:
                kwargs["minimum_depth"] = depth
                kwargs["maximum_depth"] = depth

            dataset = copernicusmarine.open_dataset(**kwargs)

            if variable not in dataset:
                raise ValueError(
                    f"Variable '{variable}' was not returned by dataset "
                    f"'{dataset_id}'."
                )

            data_array = dataset[variable]

            # Select nearest spatial point and latest available time.
            if "latitude" in data_array.dims:
                data_array = data_array.sel(
                    latitude=lat,
                    method="nearest",
                )

            if "longitude" in data_array.dims:
                data_array = data_array.sel(
                    longitude=lon,
                    method="nearest",
                )

            if "depth" in data_array.dims:
                data_array = data_array.sel(
                    depth=depth,
                    method="nearest",
                )

            if "time" in data_array.dims:
                data_array = data_array.sel(
                    time=data_array.time.max()
                )

            value = data_array.values

            # Convert numpy scalar / 0-dimensional array to float.
            try:
                value = float(value)
            except (TypeError, ValueError):
                value = float(value.item())

            if not _is_valid_number(value):
                raise ValueError(
                    f"Copernicus returned an invalid value: {value}"
                )

            observed_at = _utc_now_iso()

            if "time" in data_array.coords:
                try:
                    observed_at = str(data_array.coords["time"].values)
                except Exception:
                    pass

            return {
                "value": round(value, 4),
                "unit": config["unit"],
                "source": (
                    f"{config['source']} "
                    f"({dataset_id})"
                ),
                "observed_at": observed_at,
                "status": "ok",
            }

        except Exception as exc:
            logger.exception(
                "Copernicus Marine request failed for %s: %s",
                parameter,
                exc,
            )

            return {
                "value": None,
                "unit": config["unit"],
                "source": f"Copernicus Marine ({dataset_id})",
                "observed_at": _utc_now_iso(),
                "status": "error",
                "note": str(exc),
            }


# ---------------------------------------------------------------------------
# Backwards-compatible class name
# ---------------------------------------------------------------------------

class INCOISERDDAPClient:
    """
    Compatibility wrapper.

    Existing MarineAgent code already expects INCOISERDDAPClient,
    so we keep that class name while internally using the official
    Copernicus Marine Toolbox.
    """

    def __init__(self):
        self.client = CopernicusMarineClient()

    def get_parameter(
        self,
        parameter: str,
        lat: float,
        lon: float,
    ) -> Dict[str, Any]:
        return self.client.get_parameter(parameter, lat, lon)


# ---------------------------------------------------------------------------
# INCOIS Ocean State Forecast reference
# ---------------------------------------------------------------------------

def get_osf_forecast_reference() -> Dict[str, str]:
    return {
        "name": "INCOIS Ocean State Forecast",
        "url": "https://incois.gov.in/oceanservices/osfforecast.jsp",
        "note": (
            "INCOIS Ocean State Forecast reference. "
            "Primary machine-readable marine data is obtained "
            "through Copernicus Marine."
        ),
    }


# ---------------------------------------------------------------------------
# IMD compatibility client
# ---------------------------------------------------------------------------

class IMDClient:
    """
    Kept for compatibility with the existing MarineAgent.

    Wind data will be handled separately by the Weather Agent.
    The Marine Agent therefore does not depend on IMD for its
    core marine parameters.
    """

    def get_wind_speed(
        self,
        lat: float,
        lon: float,
    ) -> Dict[str, Any]:
        return {
            "value": None,
            "unit": "km/h",
            "source": "Weather Agent",
            "observed_at": _utc_now_iso(),
            "status": "not_available",
            "note": (
                "Wind speed is handled by the Weather Agent."
            ),
        }