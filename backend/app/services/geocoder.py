"""Global place search and reverse geocoding for BoponX.

Nominatim is used only for location selection and country identification. It is
not treated as agricultural evidence.
"""
from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

NOMINATIM = "https://nominatim.openstreetmap.org"
USER_AGENT = "BoponX-SpaceApps-2026 (https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026)"


def _request(path: str, params: dict[str, str]) -> object:
    url = f"{NOMINATIM}{path}?{urlencode(params)}"
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "en",
            "Accept": "application/json",
        },
    )
    with urlopen(request, timeout=8) as response:
        return json.loads(response.read().decode("utf-8"))


def _normalise(item: dict) -> dict:
    address = item.get("address") if isinstance(item.get("address"), dict) else {}
    country_code = str(address.get("country_code", "")).lower()
    return {
        "display_name": item.get("display_name"),
        "name": item.get("name") or item.get("display_name"),
        "latitude": float(item["lat"]),
        "longitude": float(item["lon"]),
        "type": item.get("type"),
        "category": item.get("category"),
        "address": {
            "village": address.get("village") or address.get("hamlet"),
            "town": address.get("town") or address.get("city") or address.get("municipality"),
            "upazila": address.get("subdistrict") or address.get("county"),
            "district": address.get("state_district") or address.get("county"),
            "division": address.get("state") or address.get("region"),
            "country": address.get("country"),
            "country_code": country_code,
        },
        "provider": "OpenStreetMap Nominatim",
    }


def search_global_places(query: str, limit: int = 8) -> list[dict]:
    clean = " ".join(query.split()).strip()
    if len(clean) < 2:
        return []
    payload = _request(
        "/search",
        {
            "q": clean,
            "format": "jsonv2",
            "addressdetails": "1",
            "limit": str(max(1, min(limit, 8))),
        },
    )
    if not isinstance(payload, list):
        return []
    results: list[dict] = []
    for item in payload:
        try:
            results.append(_normalise(item))
        except (KeyError, TypeError, ValueError):
            continue
    return results


def reverse_global_place(lat: float, lon: float) -> dict | None:
    payload = _request(
        "/reverse",
        {
            "lat": f"{lat:.6f}",
            "lon": f"{lon:.6f}",
            "format": "jsonv2",
            "addressdetails": "1",
            "zoom": "10",
        },
    )
    if not isinstance(payload, dict) or "lat" not in payload or "lon" not in payload:
        return None
    return _normalise(payload)


# Backward compatible aliases for older imports.
search_bangladesh_places = search_global_places
reverse_bangladesh_place = reverse_global_place
