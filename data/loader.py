"""
Data Loader & Geospatial Helper Utility for ORCA (Member 5)
Loads raw/processed reference assets (ports, IMBL, MPAs, PFZ layers) and
provides fast spatial distance and bounding-box queries without heavy GIS dependencies.
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

DATA_DIR = Path(__file__).resolve().parent
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on Earth in km."""
    r = 6371.0  # Earth's radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def point_to_polyline_distance_km(lat: float, lon: float, polyline_coords: List[List[float]]) -> float:
    """
    Calculate minimum distance in km from a point (lat, lon) to a polyline
    given as [[lon, lat], [lon, lat], ...].
    """
    min_dist = float("inf")
    for pt in polyline_coords:
        pt_lon, pt_lat = pt[0], pt[1]
        dist = haversine_distance_km(lat, lon, pt_lat, pt_lon)
        if dist < min_dist:
            min_dist = dist
    return min_dist


class OceanDataLoader:
    """Singleton-style cache and access utility for ORCA datasets."""

    def __init__(self):
        self._ports: Optional[List[Dict[str, Any]]] = None
        self._imbl: Optional[List[Dict[str, Any]]] = None
        self._mpas: Optional[List[Dict[str, Any]]] = None
        self._pfz_features: Optional[List[Dict[str, Any]]] = None
        self._hazard_features: Optional[List[Dict[str, Any]]] = None

    def get_ports(self) -> List[Dict[str, Any]]:
        """Return list of major coastal Indian ports."""
        if self._ports is None:
            file_path = RAW_DIR / "indian_ports.json"
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    self._ports = json.load(f).get("ports", [])
            else:
                self._ports = []
        return self._ports

    def find_nearest_port(self, lat: float, lon: float) -> Tuple[Optional[Dict[str, Any]], float]:
        """Find the closest major Indian port and its distance in km."""
        ports = self.get_ports()
        if not ports:
            return None, float("inf")

        best_port = None
        min_dist = float("inf")
        for p in ports:
            d = haversine_distance_km(lat, lon, p["latitude"], p["longitude"])
            if d < min_dist:
                min_dist = d
                best_port = p
        return best_port, min_dist

    def get_imbl_boundaries(self) -> List[Dict[str, Any]]:
        """Return IMBL boundary segments."""
        if self._imbl is None:
            file_path = RAW_DIR / "imbl_boundaries.json"
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    self._imbl = json.load(f).get("imbl_lines", [])
            else:
                self._imbl = []
        return self._imbl

    def check_imbl_proximity(self, lat: float, lon: float) -> Tuple[Optional[str], float, bool]:
        """
        Check distance to nearest international maritime boundary.
        Returns: (boundary_name, distance_km, is_within_warning_zone)
        """
        lines = self.get_imbl_boundaries()
        nearest_boundary = None
        min_dist = float("inf")
        in_warning_zone = False

        for line in lines:
            coords = line.get("coordinates", [])
            warning_dist = line.get("warning_distance_km", 20.0)
            d = point_to_polyline_distance_km(lat, lon, coords)
            if d < min_dist:
                min_dist = d
                nearest_boundary = line.get("name")
                if d <= warning_dist:
                    in_warning_zone = True

        return nearest_boundary, min_dist, in_warning_zone

    def get_mpas(self) -> List[Dict[str, Any]]:
        """Return Marine Protected Areas."""
        if self._mpas is None:
            file_path = RAW_DIR / "mpa_zones.json"
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    self._mpas = json.load(f).get("marine_protected_areas", [])
            else:
                self._mpas = []
        return self._mpas

    def check_mpa_intersection(self, lat: float, lon: float) -> Tuple[Optional[str], bool]:
        """
        Check if coordinates fall within or very near an Indian MPA bbox.
        Returns: (mpa_name, is_inside)
        """
        mpas = self.get_mpas()
        for mpa in mpas:
            bbox = mpa.get("bbox")  # [min_lon, min_lat, max_lon, max_lat]
            if bbox and len(bbox) == 4:
                min_lon, min_lat, max_lon, max_lat = bbox
                if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
                    return mpa.get("name"), True
        return None, False

    def get_sample_pfz_layers(self) -> Dict[str, Any]:
        """Return sample PFZ GeoJSON FeatureCollection."""
        file_path = PROCESSED_DIR / "pfz_sample_layers.geojson"
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"type": "FeatureCollection", "features": []}

    def get_sample_hazard_layers(self) -> Dict[str, Any]:
        """Return sample Coastal Hazard GeoJSON FeatureCollection."""
        file_path = PROCESSED_DIR / "coastal_hazard_zones.geojson"
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"type": "FeatureCollection", "features": []}


# Global loader instance
data_loader = OceanDataLoader()
