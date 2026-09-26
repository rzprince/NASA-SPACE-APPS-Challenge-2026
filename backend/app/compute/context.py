"""Location-aware context for BoponX.

This module deliberately distinguishes environmental coverage from agronomic
support. A map pin can resolve to a nearby Bangladesh agricultural region even
when no reviewed crop-rotation rule pack exists for that location.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import asin, cos, radians, sin, sqrt
from typing import Any

BANGLADESH_BOUNDS = {
    "south": 20.5,
    "north": 26.75,
    "west": 88.0,
    "east": 92.8,
}


@dataclass(frozen=True)
class Area:
    id: str
    name_en: str
    name_bn: str
    latitude: float
    longitude: float
    evidence_region: str


AREAS = (
    Area("dhaka", "Dhaka region", "ঢাকা অঞ্চল", 23.8103, 90.4125, "Dhaka"),
    Area("mymensingh", "Mymensingh region", "ময়মনসিংহ অঞ্চল", 24.7471, 90.4203, "Mymensingh"),
    Area("cumilla", "Cumilla region", "কুমিল্লা অঞ্চল", 23.4607, 91.1809, "Cumilla"),
    Area("chattogram", "Chattogram region", "চট্টগ্রাম অঞ্চল", 22.3569, 91.7832, "Chattogram"),
    Area("sylhet", "Sylhet region", "সিলেট অঞ্চল", 24.8949, 91.8687, "Sylhet"),
    Area("rangpur", "Rangpur region", "রংপুর অঞ্চল", 25.7439, 89.2752, "Rangpur"),
    Area("dinajpur", "Dinajpur region", "দিনাজপুর অঞ্চল", 25.6279, 88.6332, "Dinajpur"),
    Area("bogura", "Bogura region", "বগুড়া অঞ্চল", 24.8465, 89.3773, "Bogura"),
    Area("rajshahi", "Rajshahi region", "রাজশাহী অঞ্চল", 24.3745, 88.6042, "Rajshahi"),
    Area("jashore", "Jashore region", "যশোর অঞ্চল", 23.1664, 89.2081, "Jashore"),
    Area("faridpur", "Faridpur region", "ফরিদপুর অঞ্চল", 23.6071, 89.8429, "Faridpur"),
    Area("khulna", "Khulna region", "খুলনা অঞ্চল", 22.8456, 89.5403, "Khulna"),
    Area("barishal", "Barishal region", "বরিশাল অঞ্চল", 22.7010, 90.3535, "Barishal"),
    Area("rangamati", "Rangamati region", "রাঙ্গামাটি অঞ্চল", 22.7324, 92.2985, "Rangamati"),
)


NASA_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "id": "gpm-imerg-early-v07b",
        "name": "GPM IMERG Early Run",
        "role": "recent_rainfall",
        "kind": "near_real_time_earth_observation",
        "status": "map_layer_ready",
        "latency_note": "Minimum latency about 4 hours; not a forecast.",
        "resolution_note": "0.1 degree / about 10 km; 30-minute products available.",
        "source_url": "https://gpm.nasa.gov/data/directory",
    },
    {
        "id": "smap-spl3smp-e-v6",
        "name": "SMAP SPL3SMP_E Version 6",
        "role": "regional_surface_soil_moisture",
        "kind": "earth_observation",
        "status": "source_reviewed_adapter_pending",
        "latency_note": "Daily product. It does not measure soil pH.",
        "resolution_note": "9 km EASE-Grid.",
        "source_url": "https://nsidc.org/data/spl3smp_e/versions/6",
        "advisory": "SMAP Standard/NRT products had a geolocation issue from 14 May to 28 July 2026; verify reprocessing status for affected dates.",
    },
    {
        "id": "nasa-power-daily",
        "name": "NASA POWER Daily",
        "role": "historical_and_recent_climate_context",
        "kind": "model_assimilated_reanalysis_context",
        "status": "live_point_query",
        "latency_note": "Availability depends on upstream products; values are not field measurements.",
        "resolution_note": "Source-grid context, not parcel-scale sensing.",
        "source_url": "https://power.larc.nasa.gov/docs/services/api/temporal/daily/",
    },
    {
        "id": "nasa-gibs-imerg",
        "name": "NASA GIBS / IMERG map layer",
        "role": "map_visualization",
        "kind": "earth_observation_visualization",
        "status": "map_layer_ready",
        "latency_note": "The interface labels the imagery date and data product.",
        "resolution_note": "Visualization follows the source product's gridded resolution.",
        "source_url": "https://worldview.earthdata.nasa.gov/",
    },
)


def in_bangladesh(lat: float, lon: float) -> bool:
    return (
        BANGLADESH_BOUNDS["south"] <= lat <= BANGLADESH_BOUNDS["north"]
        and BANGLADESH_BOUNDS["west"] <= lon <= BANGLADESH_BOUNDS["east"]
    )


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0088
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * radius * asin(sqrt(a))


def nearest_area(lat: float, lon: float) -> tuple[Area, float]:
    area = min(AREAS, key=lambda item: _distance_km(lat, lon, item.latitude, item.longitude))
    return area, _distance_km(lat, lon, area.latitude, area.longitude)


def list_areas() -> list[dict[str, Any]]:
    return [asdict(area) for area in AREAS]


def build_context(lat: float, lon: float) -> dict[str, Any]:
    area, distance = nearest_area(lat, lon)
    inside = in_bangladesh(lat, lon)
    return {
        "coordinates": {"latitude": round(lat, 5), "longitude": round(lon, 5)},
        "within_bangladesh": inside,
        "nearest_supported_region": {
            **asdict(area),
            "distance_km": round(distance, 1),
            "note": "Regional evidence reference, not an administrative-boundary lookup.",
        },
        "coverage": {
            "environmental_context": "available" if inside else "outside_bangladesh_pilot",
            "local_agricultural_evidence": "calendar_sources_indexed" if inside else "not_assessed",
            "rotation_decision": "evidence_review_required",
        },
        "calendar_evidence": calendar_evidence_for_region(area.evidence_region) if inside else [],\n        "agricultural_sources": [
            {
                "name": "BAMIS / Department of Agricultural Extension crop-weather calendars",
                "scope": f"{area.evidence_region} regional calendar index",
                "status": "source_identified_not_encoded_as_rules",
                "source_url": "https://www.bamis.gov.bd/en/calendar",
            },
            {
                "name": "Bangladesh Agricultural Research Council crop zoning",
                "scope": "Agro-edaphic and agro-climatic zoning reference",
                "status": "source_identified_permissions_and_rule_review_required",
                "source_url": "https://apps.barc.gov.bd/cropzoning/",
            },
        ],
        "nasa_sources": [dict(source) for source in NASA_SOURCES],
        "privacy": {
            "coordinates_persisted": False,
            "note": "Coordinates are used for the current request only unless a future user explicitly chooses to save a profile.",
        },
    }
