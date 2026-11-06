"""Centralized NASA Data Freshness & Provenance System (Spec V3 Priority 4).

Provides standardized provenance records and product-specific freshness classifications across:
- NASA POWER Daily Agroclimatology (`0.5 deg x 0.625 deg`, MERRA-2 / GEOS-5.12.4)
- NASA POWER Multi-Year Climatology (`2001-2020`, historical reference)
- NASA EONET v3 Natural Hazard Tracker (open events feed, 15-minute application cache)
- NASA GIBS / Worldview Visual Satellite Layers (MODIS, SRTM, IMERG, SMAP)
- NASA GPM IMERG (separating visual GIBS imagery from GES DISC OPeNDAP numerical cross-validation)

Freshness Statuses (product-specific, never arbitrary):
- `Fresh` — Within the product's nominal publication latency window and retrieved live in the current session.
- `Recently updated` — Valid observation within normal operational lag (e.g., 4–10 days for NASA POWER MERRA-2 daily).
- `Delayed` — Observation end date lags behind nominal publication latency (e.g., >10 days for NASA POWER daily).
- `Cached` — Served from a verified local snapshot or in-memory application cache.
- `Partial` — Dataset retrieved but has partial temporal or parameter coverage (<95%).
- `Unavailable` — Could not be retrieved or offline without local snapshot.
- `Validation failed` — Retrieved payload failed schema, range, or SHA-256 integrity checks.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

FRESHNESS_STATUSES = (
    "Fresh",
    "Recently updated",
    "Delayed",
    "Cached",
    "Partial",
    "Unavailable",
    "Validation failed",
)


def classify_power_daily_freshness(
    *,
    status: str,
    data_origin: str,
    observation_end: str | None,
    validation_status: str = "complete",
    today: date | None = None,
) -> dict[str, Any]:
    """Classify NASA POWER daily dataset freshness using MERRA-2/GEOS operational latency rules (~2–7 days)."""
    ref_today = today or date.today()
    if validation_status == "failed_validation":
        return {
            "freshness_status": "Validation failed",
            "is_live_realtime": False,
            "latency_days": None,
            "explanation": "Dataset failed meteorological range, continuity, or SHA-256 integrity validation.",
        }
    if status != "available" or data_origin == "unavailable" or not observation_end:
        return {
            "freshness_status": "Unavailable",
            "is_live_realtime": False,
            "latency_days": None,
            "explanation": "NASA POWER daily observations are unavailable (offline mode or network unreachable).",
        }
    if validation_status == "partial":
        return {
            "freshness_status": "Partial",
            "is_live_realtime": False,
            "latency_days": None,
            "explanation": "NASA POWER series has partial temporal coverage (<95% valid daily observations).",
        }

    try:
        end_d = date.fromisoformat(str(observation_end)[:10])
        lag = max(0, (ref_today - end_d).days)
    except ValueError:
        lag = None

    if "snapshot" in str(data_origin) or "cache" in str(data_origin):
        return {
            "freshness_status": "Cached",
            "is_live_realtime": False,
            "latency_days": lag,
            "explanation": (
                f"Served from verified local NASA POWER snapshot (observations through {observation_end}). "
                "NASA POWER is an archive/reanalysis product, not a live real-time sensor."
            ),
        }

    if lag is not None and lag <= 3:
        f_status = "Fresh"
    elif lag is not None and lag <= 10:
        f_status = "Recently updated"
    else:
        f_status = "Delayed"

    return {
        "freshness_status": f_status,
        "is_live_realtime": False,
        "latency_days": lag,
        "explanation": (
            f"Daily meteorological reanalysis retrieved from NASA POWER (latest observation: {observation_end}, "
            f"publication lag: {lag if lag is not None else 'unknown'} days). NASA POWER daily data has a nominal "
            "2–7 day processing latency and is never instantaneous real-time."
        ),
    }


def classify_eonet_freshness(
    *,
    status: str,
    data_origin: str,
    retrieved_at: str | None,
    cache_age_sec: float | None = None,
) -> dict[str, Any]:
    """Classify NASA EONET v3 hazard feed freshness (15-minute application cache)."""
    if status != "available" or data_origin == "unavailable":
        return {
            "freshness_status": "Unavailable",
            "is_live_realtime": False,
            "cache_ttl_seconds": 900,
            "explanation": "NASA EONET v3 natural hazard feed could not be reached; no synthetic alerts are generated.",
        }
    if "cache" in str(data_origin) or (cache_age_sec is not None and cache_age_sec > 60):
        return {
            "freshness_status": "Cached",
            "is_live_realtime": True,
            "cache_ttl_seconds": 900,
            "explanation": f"Served from 15-minute application cache (retrieved at {retrieved_at}).",
        }
    return {
        "freshness_status": "Fresh",
        "is_live_realtime": True,
        "cache_ttl_seconds": 900,
        "explanation": f"Live near-real-time event feed retrieved from NASA EONET v3 at {retrieved_at}.",
    }


def build_centralized_provenance_registry(
    lat: float,
    lon: float,
    *,
    recent_power: dict[str, Any] | None = None,
    baseline_power: dict[str, Any] | None = None,
    eonet_hazards: dict[str, Any] | None = None,
    advisory: dict[str, Any] | None = None,
    imerg_status: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Construct a centralized, auditable provenance registry for all NASA datasets used at (lat, lon)."""
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # 1. NASA POWER Recent Daily (14d)
    rec_status = (recent_power or {}).get("status", "unavailable")
    rec_origin = (recent_power or {}).get("data_origin", "unavailable")
    rec_end = (recent_power or {}).get("data_through")
    rec_start = (recent_power or {}).get("period", {}).get("start") if isinstance((recent_power or {}).get("period"), dict) else None
    rec_ret = (recent_power or {}).get("retrieved_at")
    rec_fresh = classify_power_daily_freshness(
        status=rec_status,
        data_origin=rec_origin,
        observation_end=rec_end,
        validation_status="complete" if rec_status == "available" else "unavailable",
    )

    # 2. NASA POWER Long-Record Historical Onset Series (2001-present)
    adv_ready = (advisory or {}).get("status") == "ADVISORY_READY"
    adv_origin = (advisory or {}).get("data_origin", "unavailable")
    adv_end = (advisory or {}).get("data_through")
    adv_ret = (advisory or {}).get("retrieved_at")
    adv_fresh = classify_power_daily_freshness(
        status="available" if adv_ready else "unavailable",
        data_origin=adv_origin,
        observation_end=adv_end,
        validation_status="complete" if adv_ready else "unavailable",
    )

    # 3. NASA POWER Climatology (2001-2020)
    clim_status = (baseline_power or {}).get("status", "unavailable")
    clim_origin = (baseline_power or {}).get("data_origin", "unavailable")
    clim_ret = (baseline_power or {}).get("retrieved_at")

    # 4. NASA EONET v3
    eo_status = (eonet_hazards or {}).get("status", "unavailable")
    eo_origin = (eonet_hazards or {}).get("data_origin", "unavailable")
    eo_ret = (eonet_hazards or {}).get("retrieved_at")
    eo_fresh = classify_eonet_freshness(status=eo_status, data_origin=eo_origin, retrieved_at=eo_ret)

    # 5. NASA GPM IMERG (Visual GIBS vs. Numerical GES DISC)
    im_stat = (imerg_status or {}).get("status", "skipped_no_token")
    im_fresh_label = (
        "Recently updated"
        if im_stat == "compared"
        else ("Cached" if im_stat == "token_configured_ready" else "Unavailable")
    )

    datasets = [
        {
            "source_id": "nasa_power_daily_recent",
            "source_name": "NASA POWER Daily Agroclimatology (14-Day Window)",
            "product_identifier": "MERRA-2 / GEOS-5.12.4 AG Daily (PRECTOTCORR, T2M, T2M_MAX, T2M_MIN, T2MDEW, RH2M, WS2M, ALLSKY_SFC_SW_DWN, GWETTOP, GWETROOT)",
            "retrieval_timestamp": rec_ret,
            "observation_start_date": rec_start,
            "observation_end_date": rec_end,
            "publication_latency_days": rec_fresh["latency_days"],
            "cache_policy": "6-hour in-memory cache",
            "data_status": rec_status,
            "freshness_status": rec_fresh["freshness_status"],
            "is_live_realtime": False,
            "geographic_coverage": f"0.5° × 0.625° (~50 km) grid cell containing ({lat:.4f}, {lon:.4f})",
            "validation_status": "complete" if rec_status == "available" else "unavailable",
            "freshness_note": rec_fresh["explanation"],
        },
        {
            "source_id": "nasa_power_historical_onset",
            "source_name": "NASA POWER Historical Daily Series (2001–Present Onset Engine)",
            "product_identifier": "MERRA-2 AG Daily (PRECTOTCORR, T2M_MAX, T2M_MIN)",
            "retrieval_timestamp": adv_ret,
            "observation_start_date": "2001-01-01" if adv_ready else None,
            "observation_end_date": adv_end,
            "publication_latency_days": adv_fresh["latency_days"],
            "cache_policy": "SHA-256 verified disk snapshot (`data/processed/power_history/`) + 6-hour memory cache",
            "data_status": "available" if adv_ready else (advisory or {}).get("status", "unavailable"),
            "freshness_status": adv_fresh["freshness_status"],
            "is_live_realtime": False,
            "geographic_coverage": (
                f"Grid cell {(advisory or {}).get('grid_cell', {}).get('id', '0.5°×0.625°')}"
            ),
            "validation_status": "complete" if adv_ready else "unavailable",
            "freshness_note": adv_fresh["explanation"],
        },
        {
            "source_id": "nasa_power_climatology",
            "source_name": "NASA POWER Multi-Year Monthly Climatology",
            "product_identifier": "NASA POWER Climatology API (2001–2020 Reference Normals)",
            "retrieval_timestamp": clim_ret,
            "observation_start_date": "2001-01-01",
            "observation_end_date": "2020-12-31",
            "publication_latency_days": None,
            "cache_policy": "24-hour in-memory cache (multi-decade static baseline)",
            "data_status": clim_status,
            "freshness_status": "Cached" if clim_status == "available" else "Unavailable",
            "is_live_realtime": False,
            "geographic_coverage": f"0.5° × 0.625° grid cell containing ({lat:.4f}, {lon:.4f})",
            "validation_status": "complete" if clim_status == "available" else "unavailable",
            "freshness_note": "Multi-year climatological baseline (2001–2020); historical reference only, not a real-time feed.",
        },
        {
            "source_id": "nasa_eonet_v3",
            "source_name": "NASA EONET v3 Natural Event Tracker",
            "product_identifier": "EONET v3 Open Events API (Floods, Severe Storms, Drought, Wildfires, Landslides)",
            "retrieval_timestamp": eo_ret,
            "observation_start_date": None,
            "observation_end_date": eo_ret[:10] if isinstance(eo_ret, str) and len(eo_ret) >= 10 else None,
            "publication_latency_days": 0,
            "cache_policy": "15-minute application cache (`_EONET_CACHE_TTL_SECONDS = 900`)",
            "data_status": eo_status,
            "freshness_status": eo_fresh["freshness_status"],
            "is_live_realtime": eo_fresh["is_live_realtime"],
            "geographic_coverage": f"1,200 km alert radius around ({lat:.4f}, {lon:.4f})",
            "validation_status": "complete" if eo_status == "available" else "unavailable",
            "freshness_note": eo_fresh["explanation"],
        },
        {
            "source_id": "nasa_gibs_imagery",
            "source_name": "NASA GIBS / Worldview Satellite Imagery Layers",
            "product_identifier": "MODIS_Terra_NDVI_8Day (8-day), MODIS_Terra_Land_Surface_Temp_Day (daily), IMERG_Precipitation_Rate (~4h), SMAP_L3_Passive_Day_Soil_Moisture (daily), SRTM_Color_Index (static DEM)",
            "retrieval_timestamp": now_iso,
            "observation_start_date": None,
            "observation_end_date": None,
            "publication_latency_days": None,
            "cache_policy": "Browser WMTS/WMS tile cache by selected ISO date",
            "data_status": "visual_tiles_ready",
            "freshness_status": "Recently updated",
            "is_live_realtime": False,
            "geographic_coverage": "Global WMTS/WMS raster tiles (250 m to 10 km product-dependent)",
            "validation_status": "visual_only_not_numerical",
            "freshness_note": (
                "Visual imagery only: MODIS TrueColor/LST update daily, MODIS NDVI is an 8-day composite, "
                "IMERG visual tiles have ~4h latency, and SRTM is a static elevation model."
            ),
        },
        {
            "source_id": "nasa_gpm_imerg_numerical",
            "source_name": "NASA GPM IMERG Numerical Precipitation Cross-Validation (GES DISC)",
            "product_identifier": "GPM_3IMERGDF V07 (Final Daily 0.1°) / GPM_3IMERGDE V07B (Early Daily 0.1°)",
            "retrieval_timestamp": (imerg_status or {}).get("retrieved_at", now_iso),
            "observation_start_date": ((imerg_status or {}).get("comparison_period") or {}).get("start_date"),
            "observation_end_date": ((imerg_status or {}).get("comparison_period") or {}).get("end_date"),
            "publication_latency_days": None,
            "cache_policy": "1-hour numerical comparison cache when NASA_EARTHDATA_TOKEN is configured",
            "data_status": im_stat,
            "freshness_status": im_fresh_label,
            "is_live_realtime": False,
            "geographic_coverage": f"0.1° × 0.1° (~10 km) grid cell containing ({lat:.4f}, {lon:.4f})",
            "validation_status": "complete" if im_stat == "compared" else "unavailable",
            "freshness_note": (imerg_status or {}).get(
                "why_unavailable",
                (imerg_status or {}).get("note", "Numerical IMERG comparison requires NASA_EARTHDATA_TOKEN."),
            ),
        },
    ]

    return {
        "generated_at": now_iso,
        "coordinates": {"latitude": round(lat, 4), "longitude": round(lon, 4)},
        "transparency_rule": (
            "Not all NASA services provide real-time observations: NASA POWER daily data has a 2–7 day processing latency, "
            "NASA POWER climatology is a 2001–2020 historical reference, MODIS NDVI is an 8-day composite, SRTM is a static "
            "DEM, and GPM IMERG numerical cross-validation is distinct from visual GIBS tiles."
        ),
        "datasets": datasets,
    }
