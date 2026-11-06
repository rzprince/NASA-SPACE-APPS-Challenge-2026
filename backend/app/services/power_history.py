"""Long-record (2001 to present) NASA POWER daily history for the planting-window engine.

Data order of preference for one POWER grid cell:
  1. in-memory cache (live fetch result, 6 h)
  2. committed snapshot  data/processed/power_history/<cell>.json   (verified by SHA-256 index + meteorological validation)
  3. live NASA POWER request (skipped when OFFLINE=1), which also auto-caches to disk when online
If none works the loader returns status "unavailable". It never fabricates values.

Variables: PRECTOTCORR (mm/day), T2M_MAX and T2M_MIN (deg C), community AG.
POWER native grid for these MERRA-2 based fields: 0.5 deg latitude x 0.625 deg longitude.
All 64 Bangladesh districts map to 40 unique 0.5 x 0.625 deg grid cells.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
PARAMETERS = ("PRECTOTCORR", "T2M_MAX", "T2M_MIN")
COMMUNITY = "AG"
DATASET_VERSION = "NASA POWER v2.x (MERRA-2 / GEOS-5.12.4 AG Daily)"
START_YEAR = 2001
LAT_STEP = 0.5
LON_STEP = 0.625
SCHEMA = "boponx.power_history.v1"
MISSING = -999.0
LATENCY_DAYS = 7  # newest days are often not final; stop a week before today

# Plausible physical ranges for Bangladesh / South Asia daily meteorology
MIN_VALID_RAIN_MM = 0.0
MAX_VALID_RAIN_MM = 1500.0
MIN_VALID_TEMP_C = -40.0
MAX_VALID_TEMP_C = 60.0
COMPLETE_COVERAGE_THRESHOLD = 0.95
PARTIAL_COVERAGE_THRESHOLD = 0.50

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SNAPSHOT_DIR = ROOT / "data" / "processed" / "power_history"
SNAPSHOT_DIR = DEFAULT_SNAPSHOT_DIR
INDEX_FILE = SNAPSHOT_DIR / "index.json"

_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL_SEC = 6 * 3600.0


# ---------------------------------------------------------------- grid helpers
def grid_cell(lat: float, lon: float) -> dict[str, Any]:
    """Return the POWER grid cell (id and centre) that contains the point."""
    if not (math.isfinite(lat) and -90 <= lat <= 90 and math.isfinite(lon) and -180 <= lon <= 180):
        raise ValueError("Invalid coordinates")
    row = math.floor(lat / LAT_STEP)
    col = math.floor(lon / LON_STEP)
    c_lat = round(row * LAT_STEP + LAT_STEP / 2.0, 4)
    c_lon = round(col * LON_STEP + LON_STEP / 2.0, 4)
    return {
        "id": f"{c_lat:.2f}_{c_lon:.4f}",
        "center_latitude": c_lat,
        "center_longitude": c_lon,
        "resolution_deg": {"latitude": LAT_STEP, "longitude": LON_STEP},
    }


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0088
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    )
    return 2.0 * r * math.asin(math.sqrt(a))


def history_end(today: date | None = None) -> date:
    return (today or date.today()) - timedelta(days=LATENCY_DAYS)


def build_url(c_lat: float, c_lon: float, start: date, end: date) -> str:
    args = {
        "parameters": ",".join(PARAMETERS),
        "community": COMMUNITY,
        "latitude": c_lat,
        "longitude": c_lon,
        "start": start.strftime("%Y%m%d"),
        "end": end.strftime("%Y%m%d"),
        "format": "JSON",
        "time-standard": "LST",
    }
    return API_URL + "?" + urlencode(args)


# ---------------------------------------------------------------- parsing & validation
def parse_power_response(payload: dict, *, start: date, end: date) -> dict[str, list[float | None]]:
    """Convert a POWER daily JSON response into dense per-day lists (None where missing).
    Never silently converts missing values into 0.0."""
    if not isinstance(payload, dict):
        raise ValueError("NASA POWER response is not a JSON object")
    parameter = payload.get("properties", {}).get("parameter")
    if not isinstance(parameter, dict):
        raise ValueError("NASA POWER response has no parameter time series")
    fill = float(payload.get("header", {}).get("fill_value", MISSING))
    n_days = (end - start).days + 1
    out: dict[str, list[float | None]] = {}
    for name in PARAMETERS:
        series = parameter.get(name)
        if not isinstance(series, dict):
            raise ValueError(f"NASA POWER response is missing {name}")
        values: list[float | None] = []
        for i in range(n_days):
            key = (start + timedelta(days=i)).strftime("%Y%m%d")
            raw = series.get(key)
            if isinstance(raw, bool) or not isinstance(raw, (int, float)):
                values.append(None)
            else:
                v = float(raw)
                if not math.isfinite(v) or v == fill or v <= MISSING:
                    values.append(None)
                elif name == "PRECTOTCORR" and (v < MIN_VALID_RAIN_MM or v > MAX_VALID_RAIN_MM):
                    values.append(None)
                elif name in ("T2M_MAX", "T2M_MIN") and (v < MIN_VALID_TEMP_C or v > MAX_VALID_TEMP_C):
                    values.append(None)
                else:
                    values.append(round(v, 2))
        out[name] = values
    return out


def _trim_trailing_missing(
    start: date, end: date, series: dict[str, list[float | None]]
) -> tuple[date, dict[str, list[float | None]]]:
    """Trim trailing days at the end of a live series where all variables are None (not yet published by NASA POWER)."""
    rain = series.get("PRECTOTCORR", [])
    tmax = series.get("T2M_MAX", [])
    tmin = series.get("T2M_MIN", [])
    n = len(rain)
    last_valid = n - 1
    while last_valid >= 0 and rain[last_valid] is None and tmax[last_valid] is None and tmin[last_valid] is None:
        last_valid -= 1
    if last_valid < 0 or last_valid == n - 1:
        return end, series
    new_end = start + timedelta(days=last_valid)
    trimmed = {k: v[: last_valid + 1] for k, v in series.items()}
    return new_end, trimmed


def validate_snapshot_record(record: dict[str, Any] | None) -> dict[str, Any]:
    """Validate a historical NASA POWER snapshot record against Spec V3 scientific criteria.

    Returns explicit validation status in {"complete", "partial", "unavailable", "failed_validation"}
    along with detailed diagnostics. Never labels a partial dataset as complete.
    """
    if not isinstance(record, dict):
        return {
            "validation_status": "unavailable",
            "valid": False,
            "reasons": ["Record is absent or not a dictionary."],
        }

    reasons: list[str] = []
    if record.get("schema") != SCHEMA:
        reasons.append(f"Invalid schema: {record.get('schema')}")
    if record.get("origin") != "nasa_power_https":
        reasons.append(f"Unverified origin: {record.get('origin')}")

    cell = record.get("cell")
    if not isinstance(cell, dict):
        reasons.append("Missing grid cell metadata.")
    else:
        lat = cell.get("center_latitude")
        lon = cell.get("center_longitude")
        if not (isinstance(lat, (int, float)) and -90 <= lat <= 90 and isinstance(lon, (int, float)) and -180 <= lon <= 180):
            reasons.append("Invalid geographic coordinates in cell metadata.")

    units = record.get("units")
    expected_units = {"PRECTOTCORR": "mm/day", "T2M_MAX": "C", "T2M_MIN": "C"}
    if units != expected_units:
        reasons.append(f"Unit mismatch: expected {expected_units}, got {units}")

    try:
        start_d = date.fromisoformat(str(record.get("start", "")))
        end_d = date.fromisoformat(str(record.get("end", "")))
    except ValueError:
        return {
            "validation_status": "failed_validation",
            "valid": False,
            "reasons": [*reasons, "Malformed ISO start or end date."],
        }

    if end_d < start_d:
        reasons.append("End date precedes start date.")
    expected_days = (end_d - start_d).days + 1

    series = record.get("series")
    if not isinstance(series, dict):
        return {
            "validation_status": "failed_validation",
            "valid": False,
            "reasons": [*reasons, "Missing series object."],
        }

    coverage_by_param: dict[str, float] = {}
    missing_by_param: dict[str, int] = {}
    range_errors: int = 0
    tmax_lt_tmin_days: int = 0

    for param in PARAMETERS:
        arr = series.get(param)
        if not isinstance(arr, list):
            reasons.append(f"Missing parameter series: {param}")
            continue
        if len(arr) != expected_days:
            reasons.append(f"Temporal continuity/duplicate length mismatch for {param}: expected {expected_days}, got {len(arr)}")
            continue
        valid_count = 0
        for v in arr:
            if v is None:
                continue
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(float(v)):
                range_errors += 1
                continue
            fv = float(v)
            if param == "PRECTOTCORR" and not (MIN_VALID_RAIN_MM <= fv <= MAX_VALID_RAIN_MM):
                range_errors += 1
            elif param in ("T2M_MAX", "T2M_MIN") and not (MIN_VALID_TEMP_C <= fv <= MAX_VALID_TEMP_C):
                range_errors += 1
            else:
                valid_count += 1
        coverage_by_param[param] = round(valid_count / max(1, expected_days), 4)
        missing_by_param[param] = expected_days - valid_count

    if "T2M_MAX" in series and "T2M_MIN" in series and len(series["T2M_MAX"]) == len(series["T2M_MIN"]):
        for hi, lo in zip(series["T2M_MAX"], series["T2M_MIN"]):
            if isinstance(hi, (int, float)) and isinstance(lo, (int, float)) and float(hi) < float(lo) - 0.5:
                tmax_lt_tmin_days += 1

    if range_errors > 0:
        reasons.append(f"{range_errors} observation(s) outside plausible meteorological range.")
    if tmax_lt_tmin_days > 0:
        reasons.append(f"{tmax_lt_tmin_days} day(s) where T2M_MAX < T2M_MIN.")

    if reasons:
        return {
            "validation_status": "failed_validation",
            "valid": False,
            "expected_days": expected_days,
            "coverage_by_parameter": coverage_by_param,
            "missing_by_parameter": missing_by_param,
            "reasons": reasons,
        }

    min_cov = min(coverage_by_param.values()) if coverage_by_param else 0.0
    years_spanned = end_d.year - start_d.year + 1
    if min_cov >= COMPLETE_COVERAGE_THRESHOLD and start_d.year <= START_YEAR and years_spanned >= 16:
        status = "complete"
    elif min_cov >= PARTIAL_COVERAGE_THRESHOLD:
        status = "partial"
    else:
        status = "failed_validation"

    return {
        "validation_status": status,
        "valid": status in ("complete", "partial"),
        "start_date": start_d.isoformat(),
        "end_date": end_d.isoformat(),
        "expected_days": expected_days,
        "years_spanned": years_spanned,
        "coverage_by_parameter": coverage_by_param,
        "missing_by_parameter": missing_by_param,
        "min_coverage_fraction": round(min_cov, 4),
        "reasons": [] if status == "complete" else [f"Coverage or span is partial (min_coverage={min_cov:.3f}, years={years_spanned})."],
    }


def make_record(
    *,
    cell: dict[str, Any],
    start: date,
    end: date,
    series: dict[str, list[float | None]],
    url: str,
    origin: str,
    retrieved_at: str | None = None,
    dataset_version: str = DATASET_VERSION,
) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "origin": origin,
        "provider": "NASA POWER",
        "dataset_version": dataset_version,
        "community": COMMUNITY,
        "missing_value_indicator": MISSING,
        "source_request_url": url,
        "retrieved_at": retrieved_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "cell": cell,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "units": {"PRECTOTCORR": "mm/day", "T2M_MAX": "C", "T2M_MIN": "C"},
        "series": series,
    }


def fetch_live(
    c_lat: float,
    c_lon: float,
    start: date,
    end: date,
    *,
    timeout: float = 90.0,
    max_retries: int = 3,
    backoff_sec: float = 1.5,
) -> dict[str, Any]:
    """Execute a live NASA POWER daily point request with rate-limit (HTTP 429) and transient error retries.
    If `end` is beyond NASA POWER's latest archive date, automatically retries with the previous year's end date."""
    last_exc: Exception | None = None
    for try_end in (end, date(end.year - 1, 12, 31)):
        if try_end <= start:
            continue
        url = build_url(c_lat, c_lon, start, try_end)
        for attempt in range(1, max(1, max_retries) + 1):
            req = Request(url, headers={"User-Agent": "BoponX/1.0 (NASA Space Apps 2026; EARTH.exe)"})
            try:
                with urlopen(req, timeout=timeout) as resp:  # noqa: S310 - fixed https host
                    payload = json.loads(resp.read().decode("utf-8"))
                header_ver = payload.get("header", {}).get("api", {}).get("version")
                ds_version = f"NASA POWER {header_ver} ({COMMUNITY})" if header_ver else DATASET_VERSION
                series = parse_power_response(payload, start=start, end=try_end)
                actual_end, series = _trim_trailing_missing(start, try_end, series)
                return make_record(
                    cell=grid_cell(c_lat, c_lon),
                    start=start,
                    end=actual_end,
                    series=series,
                    url=url,
                    origin="nasa_power_https",
                    dataset_version=ds_version,
                )
            except HTTPError as exc:
                last_exc = exc
                if exc.code in (429, 502, 503, 504) and attempt < max_retries:
                    time.sleep(backoff_sec * attempt)
                    continue
                break
            except (URLError, TimeoutError, OSError, ValueError) as exc:
                last_exc = exc
                if attempt < max_retries:
                    time.sleep(backoff_sec * attempt)
                    continue
                break
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                break
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("NASA POWER live request failed")


# ---------------------------------------------------------------- snapshot files
def record_sha256(record: dict[str, Any]) -> str:
    blob = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def snapshot_path(cell_id: str) -> Path:
    return SNAPSHOT_DIR / f"{cell_id}.json"


def write_snapshot(record: dict[str, Any], directory: Path | None = None) -> str:
    directory = directory or SNAPSHOT_DIR
    val = validate_snapshot_record(record)
    if val["validation_status"] == "failed_validation":
        raise ValueError(f"Refusing to write snapshot that failed validation: {val['reasons']}")
    directory.mkdir(parents=True, exist_ok=True)
    cell_id = record["cell"]["id"]
    digest = record_sha256(record)
    (directory / f"{cell_id}.json").write_text(
        json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False), encoding="utf-8"
    )
    index_path = directory / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else {"schema": SCHEMA, "cells": {}}
    index["cells"][cell_id] = {
        "sha256": digest,
        "retrieved_at": record["retrieved_at"],
        "start": record["start"],
        "end": record["end"],
        "validation_status": val["validation_status"],
        "min_coverage_fraction": val.get("min_coverage_fraction", 1.0),
    }
    index_path.write_text(json.dumps(index, sort_keys=True, indent=1), encoding="utf-8")
    return digest


def read_snapshot(cell_id: str, directory: Path | None = None) -> dict[str, Any] | None:
    directory = directory or SNAPSHOT_DIR
    path = directory / f"{cell_id}.json"
    if not path.exists():
        return None
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if record.get("schema") != SCHEMA or record.get("origin") != "nasa_power_https":
        return None
    index_path = directory / "index.json"
    if index_path.exists():
        expected = json.loads(index_path.read_text(encoding="utf-8")).get("cells", {}).get(cell_id, {}).get("sha256")
        if expected and expected != record_sha256(record):
            return None  # tampered or corrupted: refuse rather than use
    val = validate_snapshot_record(record)
    if not val["valid"]:
        return None
    return record


def all_bangladesh_grid_cells() -> list[dict[str, Any]]:
    """Return the 40 unique 0.5 x 0.625 deg NASA POWER grid cells covering all 64 Bangladesh districts."""
    from backend.app.compute.bangladesh_districts import DISTRICTS

    cells_map: dict[str, dict[str, Any]] = {}
    for d in DISTRICTS:
        c = grid_cell(d.latitude, d.longitude)
        cid = c["id"]
        dist_km = round(_haversine_km(d.latitude, d.longitude, c["center_latitude"], c["center_longitude"]), 2)
        if cid not in cells_map:
            cells_map[cid] = {
                "cell_id": cid,
                "cell": c,
                "districts": [],
                "district_ids": [],
                "max_centroid_distance_km": 0.0,
            }
        cells_map[cid]["districts"].append(d.name_en)
        cells_map[cid]["district_ids"].append(d.id)
        if dist_km > cells_map[cid]["max_centroid_distance_km"]:
            cells_map[cid]["max_centroid_distance_km"] = dist_km
    return [cells_map[k] for k in sorted(cells_map)]


def snapshot_health(directory: Path | None = None) -> dict[str, Any]:
    """Integrity and 40-cell coverage summary used by /api/v1/health and onset_results.json."""
    directory = directory or SNAPSHOT_DIR
    expected_cells = all_bangladesh_grid_cells()
    idx_file = directory / "index.json"
    indexed_cells = json.loads(idx_file.read_text(encoding="utf-8")).get("cells", {}) if idx_file.exists() else {}

    failed: list[str] = []
    complete_cells: list[str] = []
    partial_cells: list[str] = []
    unavailable_cells: list[str] = []
    verified = 0

    for cell_id in indexed_cells:
        rec = read_snapshot(cell_id, directory)
        if rec is None:
            failed.append(cell_id)
        else:
            verified += 1
            val = validate_snapshot_record(rec)
            if val["validation_status"] == "complete":
                complete_cells.append(cell_id)
            elif val["validation_status"] == "partial":
                partial_cells.append(cell_id)

    for item in expected_cells:
        cid = item["cell_id"]
        if cid not in complete_cells and cid not in partial_cells and cid not in failed:
            unavailable_cells.append(cid)

    if not indexed_cells:
        status = "no_snapshots"
    elif failed:
        status = "integrity_failure"
    elif len(complete_cells) == len(expected_cells):
        status = "complete_40_cells"
    elif verified > 0:
        status = "partial_cells_available"
    else:
        status = "no_snapshots"

    return {
        "status": "ok" if (indexed_cells and not failed) else status,
        "coverage_state": status,
        "expected_bangladesh_cells": len(expected_cells),
        "cells": len(indexed_cells),
        "verified": verified,
        "complete_cells": len(complete_cells),
        "partial_cells": len(partial_cells),
        "unavailable_cells": len(unavailable_cells),
        "unavailable_cell_ids": unavailable_cells,
        "failed": failed,
    }


# ---------------------------------------------------------------- public loader
def _offline() -> bool:
    return (
        os.environ.get("OFFLINE", "").strip().lower() in ("1", "true", "yes")
        or os.environ.get("BOPONX_OFFLINE", "").strip().lower() in ("1", "true", "yes")
    )


def load_history(lat: float, lon: float) -> dict[str, Any]:
    """Return {"status": "available", "record": {...}, "data_origin": ..., "validation": ...} or an unavailable result."""
    cell = grid_cell(lat, lon)
    cell_id = cell["id"]

    cached = _CACHE.get(cell_id)
    if cached and time.monotonic() - cached[0] < _CACHE_TTL_SEC:
        val = validate_snapshot_record(cached[1])
        return {
            "status": "available",
            "record": cached[1],
            "data_origin": "nasa_power_live",
            "validation": val,
        }

    record = read_snapshot(cell_id)
    if record is not None:
        val = validate_snapshot_record(record)
        return {
            "status": "available",
            "record": record,
            "data_origin": "nasa_power_snapshot",
            "validation": val,
        }

    if _offline():
        return {
            "status": "unavailable",
            "validation_status": "unavailable",
            "reason": "offline_no_snapshot",
            "cell": cell,
            "message": "OFFLINE=1 is set in your terminal and no local NASA POWER snapshot exists yet for this grid cell. "
            "Clear OFFLINE (`Remove-Item Env:OFFLINE`) to fetch live NASA POWER data automatically, or run `python -m scripts.build_snapshot`.",
        }
    try:
        record = fetch_live(cell["center_latitude"], cell["center_longitude"], date(START_YEAR, 1, 1), history_end())
    except Exception as exc:  # noqa: BLE001 - any network/parse failure means unavailable
        return {
            "status": "unavailable",
            "validation_status": "unavailable",
            "reason": "live_request_failed",
            "cell": cell,
            "message": f"NASA POWER could not be reached or returned unusable data ({type(exc).__name__}). "
            "No substitute numbers are shown.",
        }
    val = validate_snapshot_record(record)
    if not val["valid"]:
        return {
            "status": "unavailable",
            "validation_status": "failed_validation",
            "reason": "failed_validation",
            "cell": cell,
            "message": f"NASA POWER response failed scientific validation ({'; '.join(val['reasons'])}).",
        }
    if len(_CACHE) > 64:
        _CACHE.clear()
    _CACHE[cell_id] = (time.monotonic(), record)
    if SNAPSHOT_DIR == DEFAULT_SNAPSHOT_DIR:
        try:
            write_snapshot(record, SNAPSHOT_DIR)
        except (OSError, ValueError):
            pass
    return {
        "status": "available",
        "record": record,
        "data_origin": "nasa_power_live",
        "validation": val,
    }
