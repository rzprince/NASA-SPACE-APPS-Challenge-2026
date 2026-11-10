"""BoponX location-aware decision-support API."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import pydantic
from pydantic import BaseModel, Field

from backend.app.compute.agro import build_planting_window_advisory
from backend.app.compute.assistant import route as assistant_route
from backend.app.services.power_history import snapshot_health as onset_history_health
from backend.app.compute.agronomy import calendar_evidence_for_region, supported_calendar_regions
from backend.app.compute.bangladesh_districts import (
    DATASET_CAUTION_BN,
    DATASET_CAUTION_EN,
    NATIONAL_IMPORT_SUBSTITUTION_CONTEXT,
    ONLINE_EVIDENCE_NOTES,
    VERIFICATION_REQUIREMENTS,
    list_bangladesh_districts,
    lookup_bangladesh_area,
    nearest_bangladesh_district,
    serialize_district,
)
from backend.app.compute.context import build_context, in_bangladesh, list_areas
from backend.app.compute.local_sources import source_registry
from backend.app.compute.monthly import aggregate_monthly
from backend.app.compute.plan import build_rotation_scenarios, make_90_day_plan
from backend.app.services.eonet_live import fetch_eonet_hazards
from backend.app.services.geocoder import reverse_place, search_places
from backend.app.services.power_live import (
    fetch_power_climatology,
    fetch_power_climatology_window,
    fetch_recent_power,
)

app = FastAPI(title="BoponX API")
ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_NAME = "power_rajshahi-pilot_20240101_20241231.json"
POWER_API_PREFIX = "https://power.larc.nasa.gov/api/temporal/daily/point?"
PYDANTIC_V2 = int(str(getattr(pydantic, "__version__", "1")).split(".")[0]) >= 2

allowed_origins = [origin.strip() for origin in os.getenv("BOPONX_ALLOWED_ORIGINS", "").split(",") if origin.strip()]
if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )


if PYDANTIC_V2:
    from pydantic import ConfigDict

    class FarmerProfile(BaseModel):
        model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
        latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
        longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)
        previous_crop: str | None = Field(default=None, max_length=80)
        previous_crops: list[str] = Field(default_factory=list, max_length=4)
        intended_crop: str | None = Field(default=None, max_length=80)
        water_source: Literal["rainfed", "irrigated", "both", "unknown"] = "unknown"
        water_after_heavy_rain: Literal["drains", "stays", "sometimes", "unknown"] = "unknown"
        soil_test: Literal["yes", "no", "unknown"] = "unknown"
        soil_ph: float | None = Field(default=None, ge=0, le=14, allow_inf_nan=False)
        priority: Literal["water", "soil", "production_stability"] = "production_stability"
        equipment_access: Literal[
            "manual_traditional", "power_tiller_machinery", "conservation_zero_till", "unknown"
        ] = "unknown"
        market_preference: Literal[
            "household_subsistence", "local_cash_market", "high_value_commercial", "forage_livestock", "unknown"
        ] = "unknown"

    class PlanRequest(BaseModel):
        model_config = ConfigDict(extra="forbid")
        farm: FarmerProfile
        start_year: int = Field(ge=2026, le=2035)
        start_month: int = Field(ge=1, le=12)
        start_day: int = Field(default=1, ge=1, le=31)
        include_recent_power: bool = True
        include_climate_baseline: bool = False
        recent_environment: dict[str, Any] | None = None
        baseline_environment: dict[str, Any] | None = None
        baseline_window: dict[str, Any] | None = None
        eonet_hazards: dict[str, Any] | None = None
        advisory: dict[str, Any] | None = None
else:
    class _CompatModelV1(BaseModel):
        class Config:
            extra = "forbid"
            anystr_strip_whitespace = True

        def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
            return self.dict(*args, **kwargs)

    class FarmerProfile(_CompatModelV1):  # type: ignore[no-redef]
        latitude: float = Field(ge=-90, le=90)
        longitude: float = Field(ge=-180, le=180)
        previous_crop: str | None = Field(default=None, max_length=80)
        previous_crops: list[str] = Field(default_factory=list)
        intended_crop: str | None = Field(default=None, max_length=80)
        water_source: Literal["rainfed", "irrigated", "both", "unknown"] = "unknown"
        water_after_heavy_rain: Literal["drains", "stays", "sometimes", "unknown"] = "unknown"
        soil_test: Literal["yes", "no", "unknown"] = "unknown"
        soil_ph: float | None = Field(default=None, ge=0, le=14)
        priority: Literal["water", "soil", "production_stability"] = "production_stability"
        equipment_access: Literal[
            "manual_traditional", "power_tiller_machinery", "conservation_zero_till", "unknown"
        ] = "unknown"
        market_preference: Literal[
            "household_subsistence", "local_cash_market", "high_value_commercial", "forage_livestock", "unknown"
        ] = "unknown"

        def __init__(self, **data: Any) -> None:
            super().__init__(**data)
            if not math.isfinite(self.latitude) or not math.isfinite(self.longitude):
                raise ValueError("Coordinates must be finite numbers")
            if self.soil_ph is not None and not math.isfinite(self.soil_ph):
                raise ValueError("soil_ph must be a finite number")
            if len(self.previous_crops) > 4:
                raise ValueError("At most 4 previous crops can be recorded")

    class PlanRequest(_CompatModelV1):  # type: ignore[no-redef]
        farm: FarmerProfile
        start_year: int = Field(ge=2026, le=2035)
        start_month: int = Field(ge=1, le=12)
        start_day: int = Field(default=1, ge=1, le=31)
        include_recent_power: bool = True
        include_climate_baseline: bool = False
        recent_environment: dict[str, Any] | None = None
        baseline_environment: dict[str, Any] | None = None
        baseline_window: dict[str, Any] | None = None
        eonet_hazards: dict[str, Any] | None = None
        advisory: dict[str, Any] | None = None


def snapshot_path() -> Path:
    configured = os.getenv("BOPONX_DATA_ROOT")
    data_root = Path(configured) if configured else ROOT / "data"
    return data_root / "processed" / SNAPSHOT_NAME


def trusted_snapshot() -> dict:
    try:
        payload = json.loads(snapshot_path().read_text(encoding="utf-8"))
        evidence = payload["evidence"]
        if not (
            payload.get("schema_version") == "power-pilot/v1"
            and payload.get("location_id") == "rajshahi-pilot"
            and evidence.get("ingestion_origin") == "nasa_power_https"
            and evidence.get("provider") == "NASA POWER"
            and evidence.get("source_request_url", "").startswith(POWER_API_PREFIX)
            and isinstance(payload.get("daily"), list)
            and isinstance(payload.get("summary"), dict)
        ):
            raise ValueError("Unverified, unrecognized or malformed data snapshot")
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "DATASET_UNAVAILABLE", "message": "No validated pinned NASA POWER snapshot is available."},
        ) from exc
    return payload


class AssistantChatRequest(BaseModel):
    message: str
    lang: Literal["en", "bn"] = "en"
    history: list[dict[str, Any]] | None = None
    snapshot: dict[str, Any] | None = None


@app.post("/api/v1/assistant/chat")
def assistant_chat(request: AssistantChatRequest) -> dict:
    response = assistant_route(request.message, request.lang, request.history, request.snapshot)
    return response


@app.get("/api/v1/health")
def health() -> dict:
    try:
        snapshot = trusted_snapshot()
        pinned_ready = True
        snapshot_id = snapshot["evidence"].get("snapshot_id")
    except HTTPException:
        pinned_ready = False
        snapshot_id = None
    return {
        "status": "ok",
        "pinned_power_snapshot_ready": pinned_ready,
        "pinned_power_snapshot_id": snapshot_id,
        "location_context_ready": True,
        "place_search_ready": True,
        "regional_calendar_index_ready": True,
        "bangladesh_64_district_index_ready": True,
        "global_nasa_context_ready": True,
        "nasa_eonet_hazard_monitor_ready": True,
        "verified_local_source_registry_ready": True,
        "onset_history_snapshots": onset_history_health(),
    }


@app.get("/api/v1/areas")
def areas() -> dict:
    return {
        "areas": list_areas(),
        "note": "These are regional agricultural evidence hubs, not administrative boundary polygons.",
    }


@app.get("/api/v1/bangladesh/districts")
def bangladesh_districts(
    division: str | None = Query(default=None, max_length=60),
    lat: float | None = Query(default=None, ge=-90, le=90),
    lon: float | None = Query(default=None, ge=-180, le=180),
) -> dict:
    nearest = None
    if lat is not None and lon is not None and in_bangladesh(lat, lon):
        dist, km = nearest_bangladesh_district(lat, lon)
        nearest = serialize_district(dist, distance_km=km)
    districts = list_bangladesh_districts(division)
    return {
        "count": len(districts),
        "districts": districts,
        "nearest_district": nearest,
        "online_evidence_reports": list(ONLINE_EVIDENCE_NOTES.values()),
        "national_import_substitution_context": NATIONAL_IMPORT_SUBSTITUTION_CONTEXT,
        "verification_requirements": list(VERIFICATION_REQUIREMENTS),
        "caution_bn": DATASET_CAUTION_BN,
        "caution_en": DATASET_CAUTION_EN,
    }


@app.get("/api/v1/bangladesh/resolve")
def bangladesh_resolve(q: str = Query(min_length=2, max_length=120)) -> dict:
    match = lookup_bangladesh_area(q)
    if not match:
        raise HTTPException(
            status_code=404,
            detail={"code": "AREA_NOT_FOUND", "message": f"No Bangladesh division or district matched '{q}'."},
        )
    return {
        "status": "resolved",
        "match": match,
        "place": {
            "display_name": f"{match['name_en']}, {match['division_en']} Division, Bangladesh",
            "name": match["name_en"],
            "latitude": match["latitude"],
            "longitude": match["longitude"],
            "type": match["kind"],
            "category": "administrative",
            "address": {
                "village": None,
                "town": match["name_en"],
                "upazila": None,
                "district": match["district_profile"]["name_en"],
                "division": f"{match['division_en']} Division",
                "country": "Bangladesh",
                "country_code": "bd",
            },
            "provider": "BoponX 64-District Index",
        },
    }


@app.get("/api/v1/places/search")
def place_search(q: str = Query(min_length=2, max_length=120)) -> dict:
    local_match = lookup_bangladesh_area(q)
    local_place = None
    if local_match:
        local_place = {
            "display_name": f"{local_match['name_en']} ({local_match['name_bn']}), {local_match['division_en']} Division, Bangladesh",
            "name": local_match["name_en"],
            "latitude": local_match["latitude"],
            "longitude": local_match["longitude"],
            "type": local_match["kind"],
            "category": "administrative",
            "address": {
                "village": None,
                "town": local_match["name_en"],
                "upazila": None,
                "district": local_match["district_profile"]["name_en"],
                "division": f"{local_match['division_en']} Division",
                "country": "Bangladesh",
                "country_code": "bd",
            },
            "provider": "BoponX 64-District Index",
        }
    try:
        results = search_places(q)
    except Exception:
        results = []
    if local_place:
        already = any(
            abs(r.get("latitude", 0) - local_place["latitude"]) < 0.08
            and abs(r.get("longitude", 0) - local_place["longitude"]) < 0.08
            for r in results
        )
        if not already:
            results = [local_place, *results]
    return {
        "query": q,
        "results": results,
        "provider": "OpenStreetMap Nominatim + BoponX 64-District Index",
        "status": "available" if results else "no_results_or_service_unavailable",
        "note": "Global place search is for location selection only; it is not an agricultural evidence source.",
    }


@app.get("/api/v1/places/reverse")
def place_reverse(
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
) -> dict:
    try:
        place = reverse_place(lat, lon)
    except Exception:
        place = None
    if place is None and in_bangladesh(lat, lon):
        dist, _ = nearest_bangladesh_district(lat, lon)
        place = {
            "display_name": f"{dist.name_en} ({dist.name_bn}), {dist.division_en} Division, Bangladesh",
            "name": dist.name_en,
            "latitude": lat,
            "longitude": lon,
            "type": "district_fallback",
            "category": "administrative",
            "address": {
                "village": None,
                "town": None,
                "upazila": None,
                "district": dist.name_en,
                "division": f"{dist.division_en} Division",
                "country": "Bangladesh",
                "country_code": "bd",
            },
            "provider": "BoponX 64-District Index",
        }
    return {
        "place": place,
        "provider": "OpenStreetMap Nominatim",
        "status": "available" if place else "unavailable",
    }


@app.get("/api/v1/local-sources")
def local_sources(
    country_code: str = Query(min_length=2, max_length=2),
    country_name: str | None = Query(default=None, max_length=120),
) -> dict:
    return source_registry(country_code, country_name)


@app.get("/api/v1/agronomy/calendars")
def agronomy_calendars(region: str = Query(min_length=2, max_length=80)) -> dict:
    evidence = calendar_evidence_for_region(region)
    return {
        "region": region,
        "calendar_evidence": evidence,
        "supported_regions": supported_calendar_regions(),
        "status": "calendar_sources_found" if evidence else "no_indexed_calendar_sources",
        "warning": "Calendar presence means an official BAMIS regional crop-weather calendar exists. It is not a crop-suitability or rotation recommendation.",
    }


@app.get("/api/v1/context")
def location_context(
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
) -> dict:
    return build_context(lat, lon)


@app.get("/api/v1/environment/recent")
def recent_environment(
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
) -> dict:
    build_context(lat, lon)
    try:
        return fetch_recent_power(lat, lon)
    except Exception:
        return {
            "status": "unavailable",
            "data_origin": "unavailable",
            "retrieved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "lag_days": 7,
            "mode": "recent_query_failed",
            "provider": "NASA POWER",
            "coordinates": {"latitude": lat, "longitude": lon},
            "source_request_url": "https://power.larc.nasa.gov/docs/services/api/temporal/daily/",
            "limitations": [
                "The recent NASA POWER request could not be completed. No replacement value was invented.",
                "Use the map's dated IMERG layer for recent rainfall visualization and retry when connectivity is available.",
            ],
        }


@app.get("/api/v1/environment/baseline")
def environment_baseline(
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    month: int = Query(ge=1, le=12),
) -> dict:
    build_context(lat, lon)
    try:
        return fetch_power_climatology(lat, lon, month=month)
    except Exception:
        return {
            "status": "unavailable",
            "data_origin": "unavailable",
            "retrieved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "lag_days": 0,
            "provider": "NASA POWER",
            "kind": "historical_climatology",
            "coordinates": {"latitude": lat, "longitude": lon},
            "summary": None,
            "source_request_url": "https://power.larc.nasa.gov/docs/services/api/temporal/climatology/",
            "limitations": ["The POWER climatology request failed. No baseline value was invented."],
        }


@app.get("/api/v1/environment/baseline-window")
def environment_baseline_window(
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    start_month: int = Query(ge=1, le=12),
) -> dict:
    build_context(lat, lon)
    try:
        return fetch_power_climatology_window(lat, lon, start_month=start_month, months=3)
    except Exception:
        return {
            "status": "unavailable",
            "data_origin": "unavailable",
            "retrieved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "lag_days": 0,
            "provider": "NASA POWER",
            "kind": "historical_climatology_window",
            "coordinates": {"latitude": lat, "longitude": lon},
            "summaries": [],
            "source_request_url": "https://power.larc.nasa.gov/docs/services/api/temporal/climatology/",
            "limitations": ["The POWER climatology request failed. No monthly baseline was invented."],
        }


@app.get("/api/v1/environment/hazards")
def environment_hazards(
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    radius_km: float = Query(default=1200.0, ge=50.0, le=5000.0),
) -> dict:
    build_context(lat, lon)
    try:
        return fetch_eonet_hazards(lat, lon, radius_km=radius_km)
    except Exception:
        return {
            "status": "unavailable",
            "data_origin": "unavailable",
            "retrieved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "lag_days": 0,
            "provider": "NASA EONET v3",
            "coordinates": {"latitude": lat, "longitude": lon},
            "radius_km": radius_km,
            "active_count": 0,
            "agricultural_alert_count": 0,
            "events": [],
            "agricultural_events": [],
            "source_request_url": "https://eonet.gsfc.nasa.gov/api/v3/events?status=open&limit=40",
            "limitations": [
                "Live NASA EONET natural hazard feed could not be reached. No synthetic storm or flood alert was invented.",
                "Always check Bangladesh Meteorological Department (BMD), FFWC, or local weather alerts before field operations.",
            ],
        }


@app.get("/api/v1/climate/rajshahi-pilot")
def climate_rajshahi() -> dict:
    return trusted_snapshot()


@app.get("/api/v1/climate/rajshahi-pilot/monthly")
def climate_rajshahi_monthly() -> dict:
    try:
        return aggregate_monthly(trusted_snapshot())
    except (ValueError, KeyError, TypeError, OverflowError) as exc:
        raise HTTPException(status_code=503, detail={"code": "DATASET_UNAVAILABLE"}) from exc


@app.post("/api/v1/farms/validate")
def validate_farm(profile: FarmerProfile) -> dict:
    if profile.soil_ph is not None and profile.soil_test != "yes":
        raise HTTPException(
            status_code=422,
            detail={"code": "SOIL_TEST_REQUIRED", "message": "Enter soil pH only when it comes from a soil-test report."},
        )
    context = build_context(profile.latitude, profile.longitude)
    unknowns = []
    if not profile.previous_crop and not profile.previous_crops:
        unknowns.append("previous_crops")
    if not profile.intended_crop:
        unknowns.append("intended_crop")
    if profile.water_source == "unknown":
        unknowns.append("water_source")
    if profile.water_after_heavy_rain == "unknown":
        unknowns.append("water_after_heavy_rain")
    if profile.soil_test == "unknown":
        unknowns.append("soil_test")
    return {
        "status": "FARM_CONTEXT_RECORDED",
        "profile": profile.model_dump(),
        "unknowns": unknowns,
        "context": context,
        "note": "Unknown answers are accepted. No field soil property is inferred from NASA data.",
    }


@app.post("/api/v1/plans/preview")
def planning_preview(request: PlanRequest) -> dict:
    if request.farm.soil_ph is not None and request.farm.soil_test != "yes":
        raise HTTPException(
            status_code=422,
            detail={"code": "SOIL_TEST_REQUIRED", "message": "Enter soil pH only when it comes from a soil-test report."},
        )
    context = build_context(request.farm.latitude, request.farm.longitude)
    recent = request.recent_environment
    baseline = request.baseline_environment
    baseline_window = request.baseline_window
    eonet = request.eonet_hazards
    advisory = request.advisory
    if recent is None and request.include_recent_power:
        try:
            recent = fetch_recent_power(request.farm.latitude, request.farm.longitude)
        except Exception:
            recent = {
                "status": "unavailable",
                "data_origin": "unavailable",
                "provider": "NASA POWER",
                "message": "Recent selected-location context is unavailable. No fallback number was fabricated.",
            }
    if baseline is None and request.include_climate_baseline:
        try:
            baseline = fetch_power_climatology(
                request.farm.latitude,
                request.farm.longitude,
                month=request.start_month,
            )
        except Exception:
            baseline = {
                "status": "unavailable",
                "data_origin": "unavailable",
                "provider": "NASA POWER",
                "kind": "historical_climatology",
                "message": "Selected-month climate baseline is unavailable. No fallback number was fabricated.",
            }
    if baseline_window is None and request.include_climate_baseline:
        try:
            baseline_window = fetch_power_climatology_window(
                request.farm.latitude,
                request.farm.longitude,
                start_month=request.start_month,
                months=3,
            )
        except Exception:
            baseline_window = None
    if eonet is None and request.include_recent_power:
        try:
            eonet = fetch_eonet_hazards(request.farm.latitude, request.farm.longitude)
        except Exception:
            eonet = None
    if advisory is None:
        district_id = (context.get("district_profile") or {}).get("id") if isinstance(context.get("district_profile"), dict) else None
        advisory = build_planting_window_advisory(
            district_id,
            request.farm.intended_crop or "rice",
            lat=request.farm.latitude,
            lon=request.farm.longitude,
        )
    try:
        return make_90_day_plan(
            request.farm.model_dump(),
            context,
            start_year=request.start_year,
            start_month=request.start_month,
            start_day=request.start_day,
            recent_environment=recent,
            baseline_environment=baseline,
            baseline_window=baseline_window,
            eonet_hazards=eonet,
            advisory=advisory,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"code": "INVALID_PLAN_WINDOW", "message": str(exc)}) from exc


@app.get("/api/v1/crops")
def crops() -> dict:
    return {
        "crops": [],
        "status": "PENDING_SOURCE_REVIEW",
        "message": "Calendar sources are indexed by region, but crop profiles and rotation rules remain unpublished until agronomic review.",
    }


@app.post("/api/v1/rotations/explore")
def explore_rotations(profile: FarmerProfile) -> dict:
    """Return 3+ unranked, evidence-backed rotation exploration scenarios (including existing rotation)."""
    if profile.soil_ph is not None and profile.soil_test != "yes":
        raise HTTPException(
            status_code=422,
            detail={"code": "SOIL_TEST_REQUIRED", "message": "Enter soil pH only when it comes from a soil-test report."},
        )
    context = build_context(profile.latitude, profile.longitude)
    return build_rotation_scenarios(profile.model_dump(), context)


@app.post("/api/v1/rotations/compare")
def compare_rotations(profile: FarmerProfile) -> dict:
    raise HTTPException(
        status_code=409,
        detail={
            "code": "AGRONOMIC_RULES_NOT_APPROVED",
            "message": "Rotation alternatives remain locked until source-reviewed local crop requirements, soil constraints and crop-sequence rules are integrated.",
        },
    )


@app.get("/advisory")
@app.get("/api/v1/advisory")
def planting_window_advisory(
    district: str | None = Query(default=None, max_length=80),
    crop: str | None = Query(default="rice", max_length=60),
    lat: float | None = Query(default=None, ge=-90, le=90),
    lon: float | None = Query(default=None, ge=-180, le=180),
) -> dict:
    return build_planting_window_advisory(district, crop, lat=lat, lon=lon)


@app.get("/api/v1/validation/imerg")
def imerg_validation_endpoint(
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    live: bool = Query(default=False),
) -> dict:
    from backend.app.services.imerg_check import get_imerg_crosscheck_status

    return get_imerg_crosscheck_status(lat, lon, attempt_live_fetch=live)


@app.get("/api/v1/soil/evidence")
def soil_evidence_endpoint(
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    crop: str = Query(default="rice", max_length=60),
    soil_test: Literal["yes", "no", "unknown"] = Query(default="unknown"),
    soil_ph: float | None = Query(default=None, ge=0, le=14),
    drainage: Literal["drains", "stays", "sometimes", "unknown"] = Query(default="unknown"),
    water_source: Literal["rainfed", "irrigated", "both", "unknown"] = Query(default="unknown"),
) -> dict:
    from backend.app.compute.soil_evidence import build_soil_evidence_model, evaluate_crop_soil_suitability

    if soil_ph is not None and soil_test != "yes":
        raise HTTPException(
            status_code=422,
            detail={"code": "SOIL_TEST_REQUIRED", "message": "Enter soil pH only when it comes from a soil-test report."},
        )
    ctx = build_context(lat, lon)
    soil_model = build_soil_evidence_model(
        ctx.get("district_profile"),
        soil_test=soil_test,
        farmer_soil_ph=soil_ph,
        farmer_drainage=drainage,
    )
    suitability = evaluate_crop_soil_suitability(
        crop,
        soil_model,
        water_source=water_source,
        drainage=drainage,
        soil_test=soil_test,
        farmer_ph=soil_ph,
    )
    return {
        "coordinates": {"latitude": round(lat, 5), "longitude": round(lon, 5)},
        "soil_evidence": soil_model,
        "crop_suitability": suitability,
    }


@app.get("/api/v1/provenance")
def nasa_provenance_endpoint(
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
) -> dict:
    from backend.app.services.imerg_check import get_imerg_crosscheck_status
    from backend.app.services.provenance import build_centralized_provenance_registry

    adv = build_planting_window_advisory(None, "rice", lat=lat, lon=lon)
    imerg = get_imerg_crosscheck_status(lat, lon)
    return build_centralized_provenance_registry(lat, lon, advisory=adv, imerg_status=imerg)
