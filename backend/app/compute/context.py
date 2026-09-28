"""Global location context for BoponX with Bangladesh agronomy depth.

NASA environmental evidence is global. Official agricultural evidence is
country-adapter based and remains explicit when coverage is unavailable.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import asin, cos, radians, sin, sqrt
from typing import Any

from backend.app.compute.agronomy import calendar_evidence_for_region
from backend.app.compute.global_sources import local_sources_for_country, nasa_data_stack

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
    Area("dhaka", "Dhaka region", "Dhaka region", 23.8103, 90.4125, "Dhaka"),
    Area("mymensingh", "Mymensingh region", "Mymensingh region", 24.7471, 90.4203, "Mymensingh"),
    Area("cumilla", "Cumilla region", "Cumilla region", 23.4607, 91.1809, "Cumilla"),
    Area("chattogram", "Chattogram region", "Chattogram region", 22.3569, 91.7832, "Chattogram"),
    Area("sylhet", "Sylhet region", "Sylhet region", 24.8949, 91.8687, "Sylhet"),
    Area("rangpur", "Rangpur region", "Rangpur region", 25.7439, 89.2752, "Rangpur"),
    Area("dinajpur", "Dinajpur region", "Dinajpur region", 25.6279, 88.6332, "Dinajpur"),
    Area("bogura", "Bogura region", "Bogura region", 24.8465, 89.3773, "Bogura"),
    Area("rajshahi", "Rajshahi region", "Rajshahi region", 24.3745, 88.6042, "Rajshahi"),
    Area("jashore", "Jashore region", "Jashore region", 23.1664, 89.2081, "Jashore"),
    Area("faridpur", "Faridpur region", "Faridpur region", 23.6071, 89.8429, "Faridpur"),
    Area("khulna", "Khulna region", "Khulna region", 22.8456, 89.5403, "Khulna"),
    Area("barishal", "Barishal region", "Barishal region", 22.7010, 90.3535, "Barishal"),
    Area("rangamati", "Rangamati region", "Rangamati region", 22.7324, 92.2985, "Rangamati"),
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


def _region_reference(
    lat: float,
    lon: float,
    country_code: str | None,
    country_name: str | None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if in_bangladesh(lat, lon) or (country_code or "").lower() == "bd":
        area, distance = nearest_area(lat, lon)
        return (
            {
                **asdict(area),
                "distance_km": round(distance, 1),
                "note": "Bangladesh regional evidence hub. This is not a surveyed field boundary.",
            },
            calendar_evidence_for_region(area.evidence_region),
        )

    name = country_name or "Global field"
    code = (country_code or "global").lower()
    return (
        {
            "id": code,
            "name_en": name,
            "name_bn": name,
            "latitude": round(lat, 5),
            "longitude": round(lon, 5),
            "evidence_region": name,
            "distance_km": 0.0,
            "note": "Global field context. A country specific agronomy adapter is required before local crop rules can be used.",
        },
        [],
    )


def build_context(
    lat: float,
    lon: float,
    country_code: str | None = None,
    country_name: str | None = None,
) -> dict[str, Any]:
    inside_bd = in_bangladesh(lat, lon)
    inferred_code = (country_code or ("bd" if inside_bd else "")).lower() or None
    inferred_name = country_name or ("Bangladesh" if inside_bd else None)
    region, calendars = _region_reference(lat, lon, inferred_code, inferred_name)
    local = local_sources_for_country(inferred_code, inferred_name)

    return {
        "coordinates": {"latitude": round(lat, 5), "longitude": round(lon, 5)},
        "within_bangladesh": inside_bd,
        "country": {
            "code": inferred_code,
            "name": local["country"],
        },
        "nearest_supported_region": region,
        "coverage": {
            "environmental_context": "global_nasa_stack_available",
            "local_agricultural_evidence": local["coverage"],
            "rotation_decision": "evidence_review_required",
        },
        "calendar_evidence": calendars,
        "agricultural_sources": local["sources"],
        "local_source_note": local["note"],
        "nasa_sources": nasa_data_stack(),
        "privacy": {
            "coordinates_persisted": False,
            "note": "Coordinates are used for the current request only unless a future user explicitly chooses to save a profile.",
        },
    }
