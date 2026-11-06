"""Compute and export onset shift results and 64-district coverage verification for Bangladesh.

Usage:
    python -m scripts.build_onset_results             # uses committed snapshots or live NASA POWER when online
    OFFLINE=1 python -m scripts.build_onset_results   # strictly offline; never makes network requests

Writes `data/processed/onset_results.json` with:
- Complete 40-cell spatial grid inventory and validation statuses (`complete`, `partial`, `unavailable`, `failed_validation`)
- Explicit 64-district coverage classification:
  1. `verified_complete` — District has complete verified historical NASA POWER evidence (>=95% daily coverage, >=8 early & >=8 late seasons)
  2. `partial_evidence` — District has partial historical evidence or shared-cell partial seasons
  3. `insufficient_spatial_coverage` — District centroid is >35 km from cell center or has <8 valid seasons per period
  4. `unavailable` — Historical observations have not been acquired yet (offline without snapshot or network unreachable)
- Documented spatial assignment methodology (0.5 deg x 0.625 deg native MERRA-2 grid cell containment + centroid distance in km).
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from typing import Any

from backend.app.compute.agro import build_planting_window_advisory
from backend.app.compute.bangladesh_districts import DISTRICTS
from backend.app.services.power_history import (
    ROOT,
    SNAPSHOT_DIR,
    all_bangladesh_grid_cells,
    grid_cell,
    read_snapshot,
    snapshot_health,
    validate_snapshot_record,
)

PILOT_IDS = ("rajshahi", "naogaon", "sunamganj", "patuakhali", "dhaka")
OUT_FILE = ROOT / "data" / "processed" / "onset_results.json"


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0088
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    )
    return 2.0 * r * math.asin(math.sqrt(a))


def classify_district_coverage(
    district_obj: Any,
    adv: dict[str, Any],
    cell_validation_status: str,
    centroid_distance_km: float,
) -> dict[str, Any]:
    """Classify a district into one of the 4 Spec V3 coverage categories without forcing unverified districts."""
    status = adv.get("status", "UNAVAILABLE")
    if status == "UNAVAILABLE":
        return {
            "coverage_category": "unavailable",
            "verified": False,
            "snapshot_validation_status": cell_validation_status,
            "centroid_to_cell_center_km": centroid_distance_km,
            "spatial_assignment_method": "0.5° × 0.625° native NASA POWER MERRA-2 grid cell containment",
            "limitation_note": (
                "No validated local NASA POWER historical snapshot is present on disk and live acquisition was blocked or offline."
            ),
        }
    if status == "INSUFFICIENT_DATA" or centroid_distance_km > 35.0:
        return {
            "coverage_category": "insufficient_spatial_coverage",
            "verified": False,
            "snapshot_validation_status": cell_validation_status,
            "centroid_to_cell_center_km": centroid_distance_km,
            "spatial_assignment_method": "0.5° × 0.625° native NASA POWER MERRA-2 grid cell containment",
            "limitation_note": (
                "Insufficient valid monsoon seasons (<8 per period) or district centroid lies >35 km from cell center."
            ),
        }

    years_excluded = len(adv.get("data_quality", {}).get("years_excluded", []))
    shared_with = adv.get("shared_with", [])
    if cell_validation_status == "complete" and years_excluded <= 2:
        return {
            "coverage_category": "verified_complete",
            "verified": True,
            "snapshot_validation_status": "complete",
            "centroid_to_cell_center_km": centroid_distance_km,
            "spatial_assignment_method": "0.5° × 0.625° native NASA POWER MERRA-2 grid cell containment",
            "limitation_note": (
                f"Shares 0.5°×0.625° cell with {', '.join(shared_with)}."
                if shared_with
                else "Dedicated 0.5°×0.625° NASA POWER grid cell."
            ),
        }
    return {
        "coverage_category": "partial_evidence",
        "verified": False,
        "snapshot_validation_status": cell_validation_status,
        "centroid_to_cell_center_km": centroid_distance_km,
        "spatial_assignment_method": "0.5° × 0.625° native NASA POWER MERRA-2 grid cell containment",
        "limitation_note": (
            f"Partial temporal coverage ({years_excluded} season(s) excluded or partial snapshot span)."
        ),
    }


def build_onset_results() -> dict[str, Any]:
    health = snapshot_health()
    cells_inventory = all_bangladesh_grid_cells()
    cell_status_table: list[dict[str, Any]] = []
    for item in cells_inventory:
        cid = item["cell_id"]
        rec = read_snapshot(cid)
        val = validate_snapshot_record(rec) if rec is not None else {"validation_status": "unavailable", "valid": False}
        cell_status_table.append(
            {
                "cell_id": cid,
                "center_latitude": item["cell"]["center_latitude"],
                "center_longitude": item["cell"]["center_longitude"],
                "districts": item["districts"],
                "district_count": len(item["districts"]),
                "max_centroid_distance_km": item["max_centroid_distance_km"],
                "validation_status": val["validation_status"],
                "start_date": val.get("start_date"),
                "end_date": val.get("end_date"),
                "min_coverage_fraction": val.get("min_coverage_fraction"),
            }
        )

    results_by_district: dict[str, dict[str, Any]] = {}
    pilot_rows: list[dict[str, Any]] = []
    coverage_counts = {
        "verified_complete": 0,
        "partial_evidence": 0,
        "insufficient_spatial_coverage": 0,
        "unavailable": 0,
    }

    for d in DISTRICTS:
        cell = grid_cell(d.latitude, d.longitude)
        snap = read_snapshot(cell["id"])
        hist_arg = (
            {"status": "available", "record": snap, "data_origin": "nasa_power_snapshot"}
            if snap is not None
            else {"status": "unavailable", "reason": "offline_no_snapshot", "cell": cell, "message": "No local snapshot built yet."}
        )
        adv = build_planting_window_advisory(d.id, "rice", lat=d.latitude, lon=d.longitude, history=hist_arg)
        dist_km = round(_haversine_km(d.latitude, d.longitude, cell["center_latitude"], cell["center_longitude"]), 2)
        snap = read_snapshot(cell["id"])
        snap_val = validate_snapshot_record(snap)["validation_status"] if snap is not None else (
            "complete" if adv.get("status") == "ADVISORY_READY" else "unavailable"
        )
        cov = classify_district_coverage(d, adv, snap_val, dist_km)
        coverage_counts[cov["coverage_category"]] += 1

        if adv.get("status") != "ADVISORY_READY":
            entry: dict[str, Any] = {
                "district_id": d.id,
                "district_name_en": d.name_en,
                "division_en": d.division_en,
                "cell_id": cell["id"],
                "status": adv.get("status", "UNAVAILABLE"),
                "data_origin": adv.get("data_origin", "unavailable"),
                "reason": adv.get("reason", "no_snapshot"),
                "coverage": cov,
            }
        else:
            early = adv["distributions"]["period_2001_2012"]
            late = adv["distributions"]["period_2013_2025"]
            mw = adv["mann_whitney_test"]
            shift = adv["shift"]
            trend = adv.get("trend", {})
            entry = {
                "district_id": d.id,
                "district_name_en": d.name_en,
                "division_en": d.division_en,
                "cell_id": cell["id"],
                "shared_with": adv.get("shared_with", []),
                "status": "ADVISORY_READY",
                "data_origin": adv.get("data_origin"),
                "data_through": adv.get("data_through"),
                "retrieved_at": adv.get("retrieved_at"),
                "coverage": cov,
                "mean_onset_2001_2012_doy": early["mean_onset_doy"],
                "mean_onset_2001_2012_label": early["mean_onset_label_en"],
                "mean_onset_2013_latest_doy": late["mean_onset_doy"],
                "mean_onset_2013_latest_label": late["mean_onset_label_en"],
                "hl_shift_days": shift["estimate_days"],
                "mean_difference_days": shift.get("mean_difference_days"),
                "ci_95_days": shift["ci_95_days"],
                "mann_whitney_p": mw["p_value"],
                "significant_at_0_05": mw["significant_at_0_05"],
                "sen_slope_days_per_decade": trend.get("sen_slope_days_per_decade"),
                "advisory_kind": adv.get("advisory_kind"),
                "baseline_window_en": adv["baseline_window"]["en"],
                "recommended_window_en": adv["recommended_window"]["en"],
                "seasonal_water_balance": adv.get("seasonal_water_balance"),
            }
        results_by_district[d.id] = entry
        if d.id in PILOT_IDS:
            pilot_rows.append(entry)

    ready_count = sum(1 for r in results_by_district.values() if r["status"] == "ADVISORY_READY")
    payload = {
        "schema": "boponx.onset_results.v2",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "snapshot_dir": str(SNAPSHOT_DIR.relative_to(ROOT)),
        "spatial_methodology": {
            "grid_resolution": "0.5° latitude × 0.625° longitude (~50 km × ~62 km native MERRA-2 grid)",
            "total_bangladesh_cells": len(cells_inventory),
            "assignment_method": "Exact coordinate containment in native 0.5°×0.625° cell, with Haversine centroid distance audit",
            "limitations": [
                "Multiple nearby districts share a single 0.5°×0.625° NASA POWER grid cell (64 districts map to 40 unique cells).",
                "Sub-grid topographic rainfall gradients (e.g., Sylhet/Sunamganj haor rim vs. hill slope) are not resolved by a 50 km grid.",
            ],
        },
        "snapshot_health": health,
        "cells_total": len(cells_inventory),
        "cells_inventory": cell_status_table,
        "districts_total": len(DISTRICTS),
        "districts_ready": ready_count,
        "district_coverage_summary": coverage_counts,
        "status": "ready" if ready_count == len(DISTRICTS) else ("partial_ready" if ready_count > 0 else "snapshots_not_built"),
        "pilot_districts": pilot_rows,
        "districts": results_by_district,
    }
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def main() -> int:
    payload = build_onset_results()
    print(
        f"Wrote {OUT_FILE} (status={payload['status']}, ready={payload['districts_ready']}/{payload['districts_total']}, "
        f"cells={payload['cells_total']}, coverage={payload['district_coverage_summary']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
