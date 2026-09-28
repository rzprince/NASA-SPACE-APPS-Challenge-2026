"""Global Earth-observation context with Bangladesh deep local evidence.

NASA environmental coverage is global. Local agronomic evidence is deliberately
separate: Bangladesh has a reviewed source index in this repository, while
other countries use the verified source registry and FAO reference layer until
a country adapter is added.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import asin, cos, radians, sin, sqrt
from typing import Any

from backend.app.compute.agronomy import calendar_evidence_for_region

BANGLADESH_BOUNDS = {"south": 20.5, "north": 26.75, "west": 88.0, "east": 92.8}


@dataclass(frozen=True)
class Area:
    id: str
    name_en: str
    name_bn: str
    latitude: float
    longitude: float
    evidence_region: str


AREAS = (
    Area("dhaka", "Dhaka region", "Dhaka", 23.8103, 90.4125, "Dhaka"),
    Area("mymensingh", "Mymensingh region", "Mymensingh", 24.7471, 90.4203, "Mymensingh"),
    Area("cumilla", "Cumilla region", "Cumilla", 23.4607, 91.1809, "Cumilla"),
    Area("chattogram", "Chattogram region", "Chattogram", 22.3569, 91.7832, "Chattogram"),
    Area("sylhet", "Sylhet region", "Sylhet", 24.8949, 91.8687, "Sylhet"),
    Area("rangpur", "Rangpur region", "Rangpur", 25.7439, 89.2752, "Rangpur"),
    Area("dinajpur", "Dinajpur region", "Dinajpur", 25.6279, 88.6332, "Dinajpur"),
    Area("bogura", "Bogura region", "Bogura", 24.8465, 89.3773, "Bogura"),
    Area("rajshahi", "Rajshahi region", "Rajshahi", 24.3745, 88.6042, "Rajshahi"),
    Area("jashore", "Jashore region", "Jashore", 23.1664, 89.2081, "Jashore"),
    Area("faridpur", "Faridpur region", "Faridpur", 23.6071, 89.8429, "Faridpur"),
    Area("khulna", "Khulna region", "Khulna", 22.8456, 89.5403, "Khulna"),
    Area("barishal", "Barishal region", "Barishal", 22.7010, 90.3535, "Barishal"),
    Area("rangamati", "Rangamati region", "Rangamati", 22.7324, 92.2985, "Rangamati"),
)

NASA_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "id": "gpm-imerg-early-v07b",
        "name": "GPM IMERG Early V07B",
        "role": "recent_precipitation",
        "kind": "near_real_time_earth_observation",
        "status": "global_map_layer_ready",
        "latency_note": "NASA documents about 4 hour minimum latency. This is not a forecast.",
        "resolution_note": "0.1 degree, about 10 km.",
        "source_url": "https://gpm.nasa.gov/data/directory",
    },
    {
        "id": "smap-spl3smp-e-v6",
        "name": "SMAP SPL3SMP_E Version 6",
        "role": "surface_soil_moisture",
        "kind": "earth_observation",
        "status": "global_map_layer_ready_numeric_adapter_gated",
        "latency_note": "Daily surface soil moisture. It does not measure pH or nutrients.",
        "resolution_note": "9 km EASE-Grid.",
        "source_url": "https://nsidc.org/data/spl3smp_e/versions/6",
        "advisory": "SMAP Standard and NRT products experienced a geolocation issue from 14 May to 28 July 2026. Affected dates require QA awareness.",
    },
    {
        "id": "nasa-power-daily",
        "name": "NASA POWER Daily Agroclimatology",
        "role": "recent_agroclimate",
        "kind": "analysis_ready_gridded_context",
        "status": "global_point_query_ready",
        "latency_note": "Daily data are available to near real time, depending on upstream products.",
        "resolution_note": "Source grid context, not a parcel sensor.",
        "source_url": "https://power.larc.nasa.gov/docs/services/api/temporal/daily/",
    },
    {
        "id": "nasa-power-climatology",
        "name": "NASA POWER Climatology",
        "role": "historical_baseline",
        "kind": "historical_climate_context",
        "status": "global_point_query_ready",
        "latency_note": "Historical baseline only.",
        "resolution_note": "Source grid context, not a field measurement.",
        "source_url": "https://power.larc.nasa.gov/docs/services/api/temporal/climatology/",
    },
    {
        "id": "nasa-gibs",
        "name": "NASA GIBS / Worldview",
        "role": "spatial_visualization",
        "kind": "earth_observation_visualization",
        "status": "global_layers_ready",
        "latency_note": "Layer dates are displayed in the interface.",
        "resolution_note": "Resolution follows each source product.",
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
    inside = in_bangladesh(lat, lon)
    if inside:
        area, distance = nearest_area(lat, lon)
        region = {
            **asdict(area),
            "distance_km": round(distance, 1),
            "note": "Nearest Bangladesh agricultural evidence hub, not an administrative boundary lookup.",
        }
        calendars = calendar_evidence_for_region(area.evidence_region)
        agricultural_sources = [
            {
                "name": "BAMIS / Department of Agricultural Extension",
                "scope": f"{area.evidence_region} crop weather calendars and agromet information",
                "status": "official_calendar_index_connected",
                "source_url": "https://www.bamis.gov.bd/",
            },
            {
                "name": "Bangladesh Agricultural Research Council crop zoning",
                "scope": "Agro-edaphic and agro-climatic crop zoning reference",
                "status": "official_reference",
                "source_url": "https://apps.barc.gov.bd/cropzoning/",
            },
            {
                "name": "FAO Crop Calendar",
                "scope": "Country and agroecological-zone crop calendar reference",
                "status": "global_reference",
                "source_url": "https://cropcalendar.apps.fao.org/",
            },
        ]
        local_status = "bangladesh_deep_adapter"
    else:
        region = {
            "id": "global-field",
            "name_en": "Global field",
            "name_bn": "Global field",
            "latitude": lat,
            "longitude": lon,
            "evidence_region": "Country adapter",
            "distance_km": 0.0,
            "note": "NASA context is global. Country-specific agricultural evidence is resolved separately from the verified source registry.",
        }
        calendars = []
        agricultural_sources = [
            {
                "name": "FAO Crop Calendar",
                "scope": "Country and agroecological-zone crop calendar reference",
                "status": "global_reference",
                "source_url": "https://cropcalendar.apps.fao.org/",
            }
        ]
        local_status = "country_adapter_required"

    return {
        "coordinates": {"latitude": round(lat, 5), "longitude": round(lon, 5)},
        "within_bangladesh": inside,
        "global_environmental_coverage": True,
        "nearest_supported_region": region,
        "coverage": {
            "environmental_context": "global_nasa_coverage",
            "local_agricultural_evidence": local_status,
            "rotation_decision": "evidence_bounded_exploration",
        },
        "calendar_evidence": calendars,
        "agricultural_sources": agricultural_sources,
        "nasa_sources": [dict(source) for source in NASA_SOURCES],
        "privacy": {
            "coordinates_persisted": False,
            "note": "Coordinates are used for the current session unless the user explicitly saves them.",
        },
    }
