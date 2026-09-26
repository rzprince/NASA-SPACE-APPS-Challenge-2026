"""Bangladesh place search/reverse geocoding for the map.

Nominatim is used only to translate human place names / map coordinates. It is
not an agricultural or NASA data source. Calls fail closed and the map remains
usable if the service is unavailable.
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
            "Accept-Language": "en,bn;q=0.8",
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
            "district": address.get("state_district"),
            "division": address.get("state"),
            "country": address.get("country"),
            "country_code": country_code,
        },
        "provider": "OpenStreetMap Nominatim",
    }


def search_bangladesh_places(query: str, limit: int = 8) -> list[dict]:
    clean = " ".join(query.split()).strip()
    if len(clean) < 2:
        return []
    payload = _request(
        "/search",
        {
            "q": clean,
            "format": "jsonv2",
            "addressdetails": "1",
            "countrycodes": "bd",
            "limit": str(max(1, min(limit, 8))),
        },
    )
    if not isinstance(payload, list):
        return []
    results = []
    for item in payload:
        try:
            normal = _normalise(item)
        except (KeyError, TypeError, ValueError):
            continue
        if normal["address"]["country_code"] == "bd":
            results.append(normal)
    return results


def reverse_bangladesh_place(lat: float, lon: float) -> dict | None:
    payload = _request(
        "/reverse",
        {
            "lat": f"{lat:.6f}",
            "lon": f"{lon:.6f}",
            "format": "jsonv2",
            "addressdetails": "1",
            "zoom": "12",
        },
    )
    if not isinstance(payload, dict) or "lat" not in payload or "lon" not in payload:
        return None
    normal = _normalise(payload)
    return normal if normal["address"]["country_code"] == "bd" else None
