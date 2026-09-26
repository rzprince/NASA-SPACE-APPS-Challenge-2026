"""BoponX location-aware decision-support API."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from backend.app.compute.context import build_context, list_areas
from backend.app.compute.monthly import aggregate_monthly
from backend.app.compute.plan import make_90_day_plan
from backend.app.services.power_live import fetch_recent_power

app = FastAPI(title="BoponX API")
ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_NAME = "power_rajshahi-pilot_20240101_20241231.json"
POWER_API_PREFIX = "https://power.larc.nasa.gov/api/temporal/daily/point?"

allowed_origins = [origin.strip() for origin in os.getenv("BOPONX_ALLOWED_ORIGINS", "").split(",") if origin.strip()]
if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )


class FarmerProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)
    previous_crop: str | None = Field(default=None, max_length=80)
    water_source: Literal["rainfed", "irrigated", "both", "unknown"] = "unknown"
    water_after_heavy_rain: Literal["drains", "stays", "sometimes", "unknown"] = "unknown"
    soil_test: Literal["yes", "no", "unknown"] = "unknown"
    soil_ph: float | None = Field(default=None, ge=0, le=14, allow_inf_nan=False)
    priority: Literal["water", "soil", "production_stability"] = "production_stability"


class PlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    farm: FarmerProfile
    start_year: int = Field(ge=2026, le=2035)
    start_month: int = Field(ge=1, le=12)
    include_recent_power: bool = True


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
    }


@app.get("/api/v1/areas")
def areas() -> dict:
    return {
        "areas": list_areas(),
        "note": "These are regional evidence reference points, not administrative boundary polygons.",
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
    context = build_context(lat, lon)
    if not context["within_bangladesh"]:
        raise HTTPException(status_code=400, detail={"code": "OUTSIDE_BANGLADESH_PILOT", "message": "Choose a location inside Bangladesh."})
    try:
        return fetch_recent_power(lat, lon)
    except Exception:
        return {
            "status": "unavailable",
            "mode": "live_query_failed",
            "provider": "NASA POWER",
            "coordinates": {"latitude": lat, "longitude": lon},
            "source_request_url": "https://power.larc.nasa.gov/docs/services/api/temporal/daily/",
            "limitations": [
                "The live NASA request could not be completed. No replacement value was invented.",
                "Use the map's dated IMERG layer for recent rainfall visualization and retry when connectivity is available.",
            ],
        }




@app.get("/api/v1/environment/baseline")
def environment_baseline(
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    month: int = Query(ge=1, le=12),
) -> dict:
    context = build_context(lat, lon)
    if not context["within_bangladesh"]:
        raise HTTPException(status_code=400, detail={"code": "OUTSIDE_BANGLADESH_PILOT", "message": "Choose a location inside Bangladesh."})
    try:
        return fetch_power_climatology(lat, lon, month=month)
    except Exception:
        return {
            "status": "unavailable",
            "provider": "NASA POWER",
            "kind": "historical_climatology",
            "coordinates": {"latitude": lat, "longitude": lon},
            "summary": None,
            "source_request_url": "https://power.larc.nasa.gov/docs/services/api/temporal/climatology/",
            "limitations": ["The POWER climatology request failed. No baseline value was invented."],
        }
\n\n@app.get("/api/v1/climate/rajshahi-pilot")
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
    if not context["within_bangladesh"]:
        raise HTTPException(
            status_code=400,
            detail={"code": "OUTSIDE_BANGLADESH_PILOT", "message": "The current farmer workflow supports locations inside Bangladesh."},
        )
    unknowns = []
    if not profile.previous_crop:
        unknowns.append("previous_crop")
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
    if not context["within_bangladesh"]:
        raise HTTPException(status_code=400, detail={"code": "OUTSIDE_BANGLADESH_PILOT"})
    recent = None
    if request.include_recent_power:
        try:
            recent = fetch_recent_power(request.farm.latitude, request.farm.longitude)
        except Exception:
            recent = {
                "status": "unavailable",
                "provider": "NASA POWER",
                "message": "Live selected-location context is unavailable. No fallback number was fabricated.",
            }
    try:
        return make_90_day_plan(
            request.farm.model_dump(),
            context,
            start_year=request.start_year,
            start_month=request.start_month,
            recent_environment=recent,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"code": "INVALID_PLAN_WINDOW", "message": str(exc)}) from exc


@app.get("/api/v1/crops")
def crops() -> dict:
    return {
        "crops": [],
        "status": "PENDING_SOURCE_REVIEW",
        "message": "Crop profiles remain unpublished until local calendars, requirements and reuse terms are reviewed.",
    }


@app.post("/api/v1/rotations/compare")
def compare_rotations(profile: FarmerProfile) -> dict:
    raise HTTPException(
        status_code=409,
        detail={
            "code": "AGRONOMIC_RULES_NOT_APPROVED",
            "message": "Rotation alternatives remain locked until source-reviewed local crop and sequence rules are integrated.",
        },
    )
