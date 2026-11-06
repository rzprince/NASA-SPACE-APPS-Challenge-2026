"""Real-time NASA EONET v3 (Earth Observatory Natural Event Tracker) hazard adapter.

Queries https://eonet.gsfc.nasa.gov/api/v3/events for active natural events
(floods, severe storms/cyclones, droughts, wildfires, landslides, temperature extremes),
computes distance to the selected farm coordinate, and classifies agricultural relevance
(Spec v2 Item E: floods/storms/droughts/landslides affect field operations; wildfires/volcanoes/ice do not).
Fails closed without inventing events.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
import time
from math import asin, cos, radians, sin, sqrt
from typing import Any
from urllib.request import Request, urlopen

EONET_URL = "https://eonet.gsfc.nasa.gov/api/v3/events?status=open&limit=40"
_EONET_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}
_CACHE_TTL_SEC = 900.0  # 15 minutes

AGRICULTURAL_CATEGORY_IDS = {
    "severestorms",
    "floods",
    "drought",
    "landslides",
    "tempextremes",
    "watercolor",
}
NON_AGRICULTURAL_CATEGORY_IDS = {
    "wildfires",
    "volcanoes",
    "sealakeice",
    "earthquakes",
    "snow",
    "manmade",
    "dusthaze",
}
AGRICULTURAL_KEYWORDS = ("flood", "storm", "cyclone", "typhoon", "drought", "landslide", "heavy rain", "monsoon", "heat")


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0088
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * radius * asin(sqrt(a))


def _extract_point(geometry_list: list[dict[str, Any]]) -> tuple[float | None, float | None, str | None]:
    if not geometry_list:
        return None, None, None
    latest = geometry_list[-1]
    date_str = latest.get("date")
    coords = latest.get("coordinates")
    gtype = latest.get("type")
    if gtype == "Point" and isinstance(coords, list) and len(coords) >= 2:
        try:
            lon, lat = float(coords[0]), float(coords[1])
            return lat, lon, date_str
        except (TypeError, ValueError):
            return None, None, None
    if gtype == "Polygon" and isinstance(coords, list) and coords and isinstance(coords[0], list) and coords[0]:
        ring = coords[0]
        try:
            lons = [float(pt[0]) for pt in ring if isinstance(pt, list) and len(pt) >= 2]
            lats = [float(pt[1]) for pt in ring if isinstance(pt, list) and len(pt) >= 2]
            if lats and lons:
                return sum(lats) / len(lats), sum(lons) / len(lons), date_str
        except (TypeError, ValueError):
            return None, None, None
    return None, None, None


def is_agriculturally_relevant_event(category_id: str, category_title: str, title: str = "") -> bool:
    """Return True for hydrometeorological hazards (floods, severe storms/cyclones, droughts, landslides)
    that directly affect seedbed drainage, transplanting, or irrigation; False for wildfires/volcanoes/ice."""
    cid = (category_id or "").strip().lower()
    ctitle = (category_title or "").strip().lower()
    ev_title = (title or "").strip().lower()
    if cid in NON_AGRICULTURAL_CATEGORY_IDS or "wildfire" in ctitle or "volcano" in ctitle:
        return False
    if cid in AGRICULTURAL_CATEGORY_IDS:
        return True
    return any(kw in ctitle or kw in ev_title for kw in AGRICULTURAL_KEYWORDS)


def summarize_eonet_payload(
    payload: dict[str, Any],
    lat: float,
    lon: float,
    *,
    radius_km: float = 1200.0,
    data_origin: str = "nasa_eonet_live",
    retrieved_at: str | None = None,
) -> dict[str, Any]:
    raw_events = payload.get("events", [])
    if not isinstance(raw_events, list):
        raw_events = []

    nearby: list[dict[str, Any]] = []
    agricultural_nearby: list[dict[str, Any]] = []
    global_highlights: list[dict[str, Any]] = []

    for ev in raw_events:
        if not isinstance(ev, dict):
            continue
        ev_lat, ev_lon, ev_date = _extract_point(ev.get("geometry") or [])
        if ev_lat is None or ev_lon is None:
            continue
        dist = round(_distance_km(lat, lon, ev_lat, ev_lon), 1)
        raw_cats = [cat for cat in (ev.get("categories") or []) if isinstance(cat, dict)]
        categories = [str(cat.get("title") or cat.get("id") or "Natural Event") for cat in raw_cats]
        first_cat_id = str(raw_cats[0].get("id") or "natural_event") if raw_cats else "natural_event"
        first_cat_title = categories[0] if categories else "Natural Event"
        ev_title = str(ev.get("title", "NASA EONET Event"))

        sources = [
            str(src.get("url") or src.get("id") or "")
            for src in (ev.get("sources") or [])
            if isinstance(src, dict)
        ]
        within_radius = dist <= radius_km
        ag_relevant = is_agriculturally_relevant_event(first_cat_id, first_cat_title, ev_title)
        item = {
            "id": str(ev.get("id", "")),
            "title": ev_title,
            "category_id": first_cat_id,
            "category_title": first_cat_title,
            "categories": categories,
            "date": ev_date,
            "latitude": round(ev_lat, 4),
            "longitude": round(ev_lon, 4),
            "distance_km": dist,
            "within_alert_radius": within_radius,
            "agricultural_relevance": "agricultural_impact" if ag_relevant else "low_agricultural_relevance",
            "affects_field_operations": bool(within_radius and ag_relevant),
            "source_url": sources[0] if sources and sources[0].startswith("http") else "https://eonet.gsfc.nasa.gov/",
        }
        global_highlights.append(item)
        if within_radius:
            nearby.append(item)
            if ag_relevant:
                agricultural_nearby.append(item)

    nearby.sort(key=lambda x: x["distance_km"])
    agricultural_nearby.sort(key=lambda x: x["distance_km"])
    global_highlights.sort(key=lambda x: x["distance_km"])
    display_events = nearby[:6] if nearby else global_highlights[:5]
    ts = retrieved_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "status": "available" if data_origin != "unavailable" else "unavailable",
        "data_origin": data_origin,
        "retrieved_at": ts,
        "lag_days": 0,
        "provider": "NASA EONET v3",
        "provider_full": "NASA EONET v3 (Earth Observatory Natural Event Tracker)",
        "source_request_url": EONET_URL,
        "coordinates": {"latitude": lat, "longitude": lon},
        "radius_km": radius_km,
        "search_radius_km": radius_km,
        "active_count": len(nearby),
        "regional_events_count": len(nearby),
        "agricultural_alert_count": len(agricultural_nearby),
        "events": display_events,
        "nearby_events": nearby[:6],
        "regional_events": nearby[:6],
        "agricultural_events": agricultural_nearby[:6],
        "nearest_global_events": global_highlights[:5],
        "note": (
            "Live open natural hazard events tracked by NASA EONET. Floods, cyclones/severe storms, droughts, "
            "and landslides within the alert radius trigger field-drainage and sowing checks; wildfires and "
            "non-hydrometeorological events are marked low agricultural relevance. Always verify with BMD and DAE (16123)."
        ),
    }


def fetch_eonet_hazards(lat: float, lon: float, radius_km: float = 1200.0) -> dict[str, Any]:
    if os.getenv("OFFLINE") == "1" or os.getenv("BOPONX_OFFLINE") == "1":
        return summarize_eonet_payload(
            {"events": []},
            lat,
            lon,
            radius_km=radius_km,
            data_origin="unavailable",
        )
    now = time.monotonic()
    cached = _EONET_CACHE.get("global_open")
    if cached and (now - cached[0]) < _CACHE_TTL_SEC:
        raw_payload = {"events": cached[1]}
    else:
        request = Request(EONET_URL, headers={"User-Agent": "BoponX/SpaceApps2026"})
        with urlopen(request, timeout=8) as response:
            raw_payload = json.loads(response.read().decode("utf-8"))
        if isinstance(raw_payload.get("events"), list):
            _EONET_CACHE["global_open"] = (now, raw_payload["events"])

    return summarize_eonet_payload(
        raw_payload,
        lat,
        lon,
        radius_km=radius_km,
        data_origin="nasa_eonet_live",
    )
