"""Public NASA Earthdata CMR coverage discovery for high resolution field observations.

This adapter only discovers whether relevant granules exist near a selected
coordinate. It does not download science arrays or invent values.
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen

CMR_GRANULES = "https://cmr.earthdata.nasa.gov/search/granules.json"

HLS_COLLECTIONS = (
    ("HLS Landsat Vegetation Indices V2.0", "C3246892554-LPCLOUD"),
    ("HLS Sentinel 2 Vegetation Indices V2.0", "C3246894861-LPCLOUD"),
)
ECOSTRESS_COLLECTIONS = (
    ("ECOSTRESS Evaporative Stress Index V2", "C2076104650-LPCLOUD"),
)


def _granule_search(
    collections: tuple[tuple[str, str], ...],
    lat: float,
    lon: float,
    *,
    days: int,
    page_size: int = 6,
) -> dict:
    end = date.today()
    start = end - timedelta(days=days)
    delta = 0.12
    params: list[tuple[str, str]] = [
        ("bounding_box", f"{lon-delta:.5f},{lat-delta:.5f},{lon+delta:.5f},{lat+delta:.5f}"),
        ("temporal", f"{start.isoformat()}T00:00:00Z,{end.isoformat()}T23:59:59Z"),
        ("page_size", str(page_size)),
        ("sort_key", "-start_date"),
    ]
    for _, concept_id in collections:
        params.append(("collection_concept_id", concept_id))

    url = f"{CMR_GRANULES}?{urlencode(params)}"
    request = Request(
        url,
        headers={
            "User-Agent": "BoponX-SpaceApps-2026",
            "Accept": "application/json",
        },
    )
    with urlopen(request, timeout=12) as response:
        payload = json.loads(response.read().decode("utf-8"))

    entries = payload.get("feed", {}).get("entry", [])
    if not isinstance(entries, list):
        entries = []

    granules = []
    for entry in entries[:page_size]:
        if not isinstance(entry, dict):
            continue
        granules.append(
            {
                "id": entry.get("id"),
                "title": entry.get("title"),
                "time_start": entry.get("time_start"),
                "time_end": entry.get("time_end"),
                "updated": entry.get("updated"),
            }
        )

    return {
        "status": "available" if granules else "no_recent_granules",
        "search_window_days": days,
        "collections": [{"name": name, "concept_id": concept_id} for name, concept_id in collections],
        "granule_count_returned": len(granules),
        "latest_time": granules[0].get("time_start") if granules else None,
        "granules": granules,
        "source_request_url": url,
    }


def discover_field_observations(lat: float, lon: float) -> dict:
    result = {
        "provider": "NASA Earthdata CMR",
        "coordinates": {"latitude": lat, "longitude": lon},
        "hls": None,
        "ecostress": None,
        "limitations": [
            "Coverage discovery reports granule availability, not vegetation index or water stress values.",
            "Science array extraction remains a separate authenticated processing step.",
        ],
    }

    try:
        result["hls"] = _granule_search(HLS_COLLECTIONS, lat, lon, days=45)
    except Exception:
        result["hls"] = {
            "status": "unavailable",
            "collections": [{"name": name, "concept_id": concept_id} for name, concept_id in HLS_COLLECTIONS],
            "granules": [],
        }

    try:
        result["ecostress"] = _granule_search(ECOSTRESS_COLLECTIONS, lat, lon, days=90)
    except Exception:
        result["ecostress"] = {
            "status": "unavailable",
            "collections": [{"name": name, "concept_id": concept_id} for name, concept_id in ECOSTRESS_COLLECTIONS],
            "granules": [],
        }

    return result
