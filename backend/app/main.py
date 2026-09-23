"""BoponX pilot API: environmental evidence and cautious farm intake.

No crop-rotation outcome is exposed until source-reviewed agronomic rules exist.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from backend.app.compute.monthly import aggregate_monthly
from backend.app.compute.plan import three_month_preview

app = FastAPI(title="BoponX API", version="0.4.0")
ROOT = Path(__file__).resolve().parents[2]
LOCATION = {
    "id": "rajshahi-pilot",
    "name": "Rajshahi regional pilot (provisional)",
    "latitude": 24.37,
    "longitude": 88.60,
    "location_note": "Illustrative regional reference point; not surveyed farm coordinates.",
}
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


class FarmProfile(BaseModel):
    """Farmer inputs, not independently verified agronomic facts."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    location_id: Literal["rajshahi-pilot"]
    previous_crop: str | None = Field(default=None, min_length=1, max_length=80)
    soil_ph: float | None = Field(default=None, ge=0, le=14, allow_inf_nan=False)
    soil_texture: Literal["sandy", "loamy", "clayey", "unknown"] = "unknown"
    irrigation_mode: Literal["none", "limited", "reliable", "unknown"] = "unknown"
    priorities: list[Literal["water", "soil", "production_stability"]] = Field(
        default_factory=list, max_length=3
    )


class PreviewRequest(BaseModel):
    """User-supplied context; no profile is stored and no crop is recommended."""
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    farm: FarmProfile
    start_year: int = Field(ge=2026, le=2035)
    start_month: int = Field(ge=1, le=12)
    candidate_crop: str | None = Field(default=None, min_length=1, max_length=80)


def snapshot_path() -> Path:
    configured = os.getenv("BOPONX_DATA_ROOT")
    data_root = Path(configured) if configured else ROOT / "data"
    return data_root / "processed" / SNAPSHOT_NAME


def trusted_snapshot() -> dict:
    """Only accept an explicitly NASA-acquired, schema-compatible snapshot."""
    try:
        payload = json.loads(snapshot_path().read_text(encoding="utf-8"))
        evidence = payload["evidence"]
        if not (
            payload.get("schema_version") == "power-pilot/v1"
            and payload.get("location_id") == LOCATION["id"]
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
            detail={
                "code": "DATASET_UNAVAILABLE",
                "message": "No validated NASA POWER snapshot is available. Run and review the acquisition first.",
            },
        ) from exc
    return payload


@app.get("/api/v1/health")
def health() -> dict:
    try:
        snapshot = trusted_snapshot()
        ready = True
        snapshot_id = snapshot["evidence"].get("snapshot_id")
    except HTTPException:
        ready = False
        snapshot_id = None
    return {
        "status": "ok",
        "version": app.version,
        "climate_snapshot_ready": ready,
        "climate_snapshot_id": snapshot_id,
    }


@app.get("/api/v1/locations")
def locations() -> dict:
    return {"locations": [LOCATION], "coverage": "regional pilot only"}


@app.get("/api/v1/climate/{location_id}")
def climate(location_id: str) -> dict:
    if location_id != LOCATION["id"]:
        raise HTTPException(status_code=404, detail={"code": "UNSUPPORTED_LOCATION"})
    return trusted_snapshot()

@app.get("/api/v1/climate/{location_id}/monthly")
def climate_monthly(location_id: str) -> dict:
    if location_id != LOCATION["id"]:
        raise HTTPException(status_code=404, detail={"code": "UNSUPPORTED_LOCATION"})
    try:
        return aggregate_monthly(trusted_snapshot())
    except (ValueError, KeyError, TypeError, OverflowError) as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "DATASET_UNAVAILABLE",
                    "message": "Historical climate snapshot failed monthly validation."},
        ) from exc


@app.post("/api/v1/farms/validate")
def validate_farm(profile: FarmProfile) -> dict:
    missing: list[str] = []
    if profile.previous_crop is None:
        missing.append("previous_crop")
    if profile.soil_ph is None:
        missing.append("soil_ph")
    if profile.soil_texture == "unknown":
        missing.append("soil_texture")
    if profile.irrigation_mode == "unknown":
        missing.append("irrigation_mode")
    if not profile.priorities:
        missing.append("priorities")
    return {
        "status": "PROFILE_RECORDED_NOT_AGRONOMICALLY_VALIDATED",
        "profile": profile.model_dump(),
        "missing_inputs": missing,
        "warnings": [
            "Farmer-entered values are not independently verified.",
            "Soil compatibility and crop-rotation rules have not yet been approved.",
        ],
    }


@app.post("/api/v1/plans/preview")
def planning_preview(request: PreviewRequest) -> dict:
    """A three-month printable PREPARATION brief, never a crop prescription.

    HTTP responses are generated for this request only; personal farm details
    are not persisted to disk or included in the NASA data cache.
    """
    try:
        history = aggregate_monthly(trusted_snapshot())
        return three_month_preview(
            request.farm.model_dump(),
            history,
            start_year=request.start_year,
            start_month=request.start_month,
            candidate_crop=request.candidate_crop,
        )
    except (ValueError, KeyError, TypeError, OverflowError) as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "REPORT_DATA_UNAVAILABLE",
                    "message": "A verified historical reference is required to prepare this brief."},
        ) from exc


@app.get("/api/v1/crops")
def crops() -> dict:
    return {
        "crops": [],
        "status": "PENDING_SOURCE_REVIEW",
        "message": "No crop profile is published until the references and rules are reviewed.",
    }


@app.post("/api/v1/rotations/compare")
def compare_rotations(profile: FarmProfile) -> dict:
    # The validated input model is shared with the farm intake API.
    # Intentionally no fabricated crop choices, scores, water savings or yield predictions.
    raise HTTPException(
        status_code=409,
        detail={
            "code": "AGRONOMIC_RULES_NOT_APPROVED",
            "message": "Rotation comparison is not available until reviewed local crop and soil rules are integrated.",
            "next_step": "Review and approve sourced pilot crop profiles and rotation constraints.",
        },
    )
