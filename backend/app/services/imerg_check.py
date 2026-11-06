"""NASA GPM IMERG numerical cross-validation and GES DISC OPeNDAP retrieval adapter (Spec V3.1).

Scientific Architecture:
1. Visual Satellite Layer (Always available, no credentials):
   - Product: `IMERG_Precipitation_Rate` via NASA GIBS WMTS/WMS (`0.1 deg`, ~4h latency).
   - Note: Visual GIBS imagery tiles are rendered RGB/palette images and do NOT provide numerical mm/day values.
2. Numerical IMERG Precipitation Products (NASA GES DISC):
   - `GPM_3IMERGDF` Version 07 (Final Daily, `0.1 deg x 0.1 deg`, `precipitation` in `mm/day`, ~3.5-month latency, research-grade gauge-calibrated).
   - `GPM_3IMERGDE` Version 07B (Early Daily, `0.1 deg x 0.1 deg`, `precipitation` in `mm/day`, ~4-14h latency, near-real-time forward morphing).
   - `GPM_3IMERGHHE` Version 07B (Early Half-Hourly, `0.1 deg x 0.1 deg`, `precipitation` in `mm/hr`; 48 half-hour intervals per UTC day, each representing 0.5 hr).
   - Official Catalog: https://www.earthdata.nasa.gov/data/catalog/ges-disc-gpm-3imergdf-07
   - Access Method: NASA GES DISC OPeNDAP ASCII/DAP4 point subsetting (`https://gpm1.gesdisc.eosdis.nasa.gov/opendap/GPM_L3/`)
     authenticated via NASA Earthdata Bearer Token (`NASA_EARTHDATA_TOKEN`).
3. Half-Hourly Missing-Data Policy (Spec V3.1):
   - Missing 30-minute intervals are NEVER silently assigned an average rainfall rate (zero scaling/imputation).
   - Observed accumulation (`observed_accumulation_mm = sum(r * 0.5 for r in valid)`) is calculated transparently without scaling.
   - A full daily total (`daily_total_mm`) is returned ONLY when all 48/48 half-hourly intervals are present and valid (`coverage_status == "complete"`).
   - Incomplete coverage is explicitly classified (`complete` for 48/48, `partial_incomplete` for 44/48–47/48, `insufficient_coverage` for 1/48–43/48, and `missing` for 0/48) with `missing_intervals` and `coverage_pct` included in metadata.
"""
from __future__ import annotations

import math
import os
import re
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any, Mapping, Sequence
from urllib.request import Request, urlopen

GES_DISC_OPENDAP_BASE = "https://gpm1.gesdisc.eosdis.nasa.gov/opendap/GPM_L3"
EXPECTED_HALF_HOURLY_INTERVALS = 48

IMERG_PRODUCTS: dict[str, dict[str, Any]] = {
    "GPM_3IMERGDF_V07": {
        "short_name": "GPM_3IMERGDF",
        "version": "07",
        "collection_path": "GPM_3IMERGDF.07",
        "temporal_resolution": "1 day (daily accumulation)",
        "spatial_resolution": "0.1° × 0.1° (~10 km)",
        "native_unit": "mm/day",
        "latency": "~3.5 months (Final research-grade, GPCC gauge-calibrated)",
        "catalog_url": "https://www.earthdata.nasa.gov/data/catalog/ges-disc-gpm-3imergdf-07",
        "auth_required": True,
    },
    "GPM_3IMERGDE_V07B": {
        "short_name": "GPM_3IMERGDE",
        "version": "07B",
        "collection_path": "GPM_3IMERGDE.07",
        "temporal_resolution": "1 day (early near-real-time daily accumulation)",
        "spatial_resolution": "0.1° × 0.1° (~10 km)",
        "native_unit": "mm/day",
        "latency": "~4–14 hours (Early run, satellite forward morphing)",
        "catalog_url": "https://www.earthdata.nasa.gov/data/catalog/ges-disc-gpm-3imergde-07",
        "auth_required": True,
    },
    "GIBS_IMERG_VISUAL": {
        "short_name": "IMERG_Precipitation_Rate",
        "version": "V07B (GIBS Visual Tile)",
        "temporal_resolution": "30-minute / daily visual composite",
        "spatial_resolution": "0.1° (~10 km visual raster)",
        "native_unit": "RGB visual colormap (not numerical mm/day)",
        "latency": "~4 hours",
        "catalog_url": "https://gpm.nasa.gov/data/imerg",
        "auth_required": False,
    },
}

_IMERG_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_IMERG_CACHE_TTL_SEC = 3600.0


def imerg_grid_indices(lat: float, lon: float) -> dict[str, Any]:
    """Map latitude (-90..90) and longitude (-180..180) to 0.1° IMERG L3 grid index and center."""
    if not (math.isfinite(lat) and -90.0 <= lat <= 90.0 and math.isfinite(lon) and -180.0 <= lon <= 180.0):
        raise ValueError("Invalid coordinates for IMERG grid indexing")
    lat_idx = min(1799, max(0, int(math.floor((lat + 90.0) / 0.1))))
    lon_idx = min(3599, max(0, int(math.floor((lon + 180.0) / 0.1))))
    c_lat = round(-89.95 + lat_idx * 0.1, 2)
    c_lon = round(-179.95 + lon_idx * 0.1, 2)
    return {
        "lat_index": lat_idx,
        "lon_index": lon_idx,
        "center_latitude": c_lat,
        "center_longitude": c_lon,
        "cell_id": f"{c_lat:.2f}_{c_lon:.2f}",
        "resolution_deg": 0.1,
    }


def aggregate_half_hourly_imerg_to_daily(
    rates_mm_per_hr: Sequence[float | None],
    *,
    expected_intervals: int = EXPECTED_HALF_HOURLY_INTERVALS,
) -> dict[str, Any]:
    """Aggregate 30-minute IMERG precipitation rates (mm/hr) into daily precipitation metadata without imputation.

    Rules (Spec V3.1):
    - Each valid 30-minute interval contributes exactly `rate * 0.5` mm to `observed_accumulation_mm`.
    - Missing intervals are NEVER assigned the mean rate of observed intervals (`imputation_applied = False`).
    - `daily_total_mm` is returned ONLY when all `48/48` intervals are valid (`coverage_status == "complete"`).
    - When `44 <= valid_intervals < 48` (`>=90%` but `<100%`), `coverage_status` is `"partial_incomplete"` and
      `daily_total_mm` is `None` (while `observed_accumulation_mm` reports the exact unscaled lower-bound sum).
    - When `1 <= valid_intervals < 44`, `coverage_status` is `"insufficient_coverage"` and `daily_total_mm` is `None`.
    - When `valid_intervals == 0`, `coverage_status` is `"missing"`, `daily_total_mm` is `None`, and
      `observed_accumulation_mm` is `None`.
    """
    if expected_intervals <= 0:
        raise ValueError("expected_intervals must be positive")

    slots = list(rates_mm_per_hr)
    total_slots = max(expected_intervals, len(slots))
    valid_rates: list[float] = []
    missing_indices: list[int] = []

    for i in range(total_slots):
        r = slots[i] if i < len(slots) else None
        if r is None or isinstance(r, bool) or not isinstance(r, (int, float)):
            missing_indices.append(i)
            continue
        val = float(r)
        if not math.isfinite(val) or val < 0.0 or val > 500.0:
            missing_indices.append(i)
            continue
        valid_rates.append(val)

    valid_count = len(valid_rates)
    missing_count = total_slots - valid_count
    coverage_pct = round((valid_count / total_slots) * 100.0, 2)
    observed_mm = round(sum(r * 0.5 for r in valid_rates), 2) if valid_count > 0 else None

    if valid_count == total_slots and total_slots == expected_intervals:
        coverage_status = "complete"
        daily_total_mm: float | None = observed_mm
        validity_note = "All 48/48 half-hourly intervals are valid (100% coverage); full-day total is scientifically justified."
    elif valid_count == 0:
        coverage_status = "missing"
        daily_total_mm = None
        validity_note = "0/48 valid half-hourly intervals; no precipitation observation available."
    elif valid_count >= 44 and total_slots == expected_intervals:
        coverage_status = "partial_incomplete"
        daily_total_mm = None
        validity_note = (
            f"Incomplete sub-daily coverage ({valid_count}/{total_slots} intervals, {coverage_pct}%). "
            "Missing intervals are never imputed with average rainfall; observed_accumulation_mm is an unscaled partial lower bound."
        )
    else:
        coverage_status = "insufficient_coverage"
        daily_total_mm = None
        validity_note = (
            f"Insufficient sub-daily coverage ({valid_count}/{total_slots} intervals, {coverage_pct}% < 90%). "
            "Full daily total is withheld; observed_accumulation_mm records only the unscaled valid intervals."
        )

    return {
        "daily_total_mm": daily_total_mm,
        "observed_accumulation_mm": observed_mm,
        "valid_intervals": valid_count,
        "expected_intervals": total_slots,
        "missing_intervals": missing_count,
        "missing_interval_indices": missing_indices,
        "coverage_pct": coverage_pct,
        "coverage_status": coverage_status,
        "full_day_valid": coverage_status == "complete",
        "imputation_applied": False,
        "validity_note": validity_note,
    }


def convert_half_hourly_rates_to_daily_mm(
    rates_mm_per_hr: Sequence[float | None],
    *,
    return_metadata: bool = False,
) -> float | None | dict[str, Any]:
    """Convert 48 half-hourly IMERG precipitation rates (mm/hr) into a full-day total (mm/day).

    Never imputes or scales across missing intervals. Returns a float ONLY when 48/48 intervals are valid
    (`coverage_status == "complete"`), or `None` if any interval is missing. Set `return_metadata=True` to
    retrieve the full transparency dictionary (`observed_accumulation_mm`, `missing_intervals`, `coverage_pct`,
    `coverage_status`).
    """
    agg = aggregate_half_hourly_imerg_to_daily(rates_mm_per_hr)
    if return_metadata:
        return agg
    return agg["daily_total_mm"]


def _pearson_r(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den_x = sum((x - mx) ** 2 for x in xs)
    den_y = sum((y - my) ** 2 for y in ys)
    if den_x <= 1e-12 or den_y <= 1e-12:
        return None
    return round(num / math.sqrt(den_x * den_y), 4)


def compare_imerg_and_power_series(
    imerg_daily_mm: Sequence[float | None] | Mapping[str, float | None],
    power_daily_mm: Sequence[float | None] | Mapping[str, float | None],
    *,
    dates: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Compare paired daily rainfall series (mm/day) from GPM IMERG and NASA POWER PRECTOTCORR.

    Supports both date-keyed dicts (`{"YYYY-MM-DD": mm}`) and aligned sequences.
    Calculates Mean Bias, MAE, RMSE, Pearson correlation r, sample count, and comparison period.
    """
    pairs: list[tuple[str | None, float, float]] = []
    if isinstance(imerg_daily_mm, Mapping) and isinstance(power_daily_mm, Mapping):
        common_dates = sorted(set(imerg_daily_mm.keys()) & set(power_daily_mm.keys()))
        for d_key in common_dates:
            im = imerg_daily_mm.get(d_key)
            pw = power_daily_mm.get(d_key)
            if im is None or pw is None:
                continue
            if math.isfinite(float(im)) and math.isfinite(float(pw)) and float(im) >= 0.0 and float(pw) >= 0.0:
                pairs.append((str(d_key), float(im), float(pw)))
    elif isinstance(imerg_daily_mm, Sequence) and isinstance(power_daily_mm, Sequence):
        for idx, (im, pw) in enumerate(zip(imerg_daily_mm, power_daily_mm)):
            if im is None or pw is None:
                continue
            if math.isfinite(float(im)) and math.isfinite(float(pw)) and float(im) >= 0.0 and float(pw) >= 0.0:
                d_label = str(dates[idx]) if dates and idx < len(dates) else None
                pairs.append((d_label, float(im), float(pw)))
    else:
        raise TypeError("imerg_daily_mm and power_daily_mm must both be Mappings or both be Sequences")

    if not pairs:
        return {
            "status": "insufficient_overlap",
            "paired_days": 0,
            "sample_count": 0,
            "comparison_period": None,
            "imerg_total_mm": None,
            "power_total_mm": None,
            "bias_mm_per_day": None,
            "mae_mm_per_day": None,
            "rmse_mm_per_day": None,
            "pearson_r": None,
            "spatial_aggregation_method": "0.1° IMERG L3 cell vs. 0.5°×0.625° NASA POWER MERRA-2 cell",
        }

    n = len(pairs)
    xs = [x for _, x, _ in pairs]
    ys = [y for _, _, y in pairs]
    im_sum = sum(xs)
    pw_sum = sum(ys)
    bias = sum(x - y for x, y in zip(xs, ys)) / n
    mae = sum(abs(x - y) for x, y in zip(xs, ys)) / n
    rmse = math.sqrt(sum((x - y) ** 2 for x, y in zip(xs, ys)) / n)
    corr = _pearson_r(xs, ys)
    dated = [d for d, _, _ in pairs if d]
    comp_period = {"start_date": dated[0], "end_date": dated[-1]} if dated else None

    return {
        "status": "compared",
        "paired_days": n,
        "sample_count": n,
        "comparison_period": comp_period,
        "imerg_total_mm": round(im_sum, 2),
        "power_total_mm": round(pw_sum, 2),
        "imerg_mean_daily_mm": round(im_sum / n, 2),
        "power_mean_daily_mm": round(pw_sum / n, 2),
        "bias_mm_per_day": round(bias, 2),
        "mae_mm_per_day": round(mae, 2),
        "rmse_mm_per_day": round(rmse, 2),
        "pearson_r": corr,
        "spatial_aggregation_method": (
            "Point-to-cell matching: 0.1° × 0.1° (~10 km) GPM IMERG grid cell compared against "
            "co-located 0.5° × 0.625° (~50 km) NASA POWER MERRA-2 grid cell over identical UTC/LST dates."
        ),
        "scientific_interpretation_note": (
            "Disagreement between GPM IMERG and NASA POWER does not prove either dataset is erroneous: "
            "IMERG retrieves 0.1° (~10 km) passive-microwave/IR satellite precipitation rates capable of capturing "
            "localized convective storms, whereas NASA POWER PRECTOTCORR provides 0.5°×0.625° (~50 km) area-averaged "
            "MERRA-2 reanalysis precipitation."
        ),
    }


def _parse_opendap_ascii_value(text: str) -> float | None:
    """Extract a single numeric precipitation value (mm/day) from a GES DISC OPeNDAP `.ascii` response."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for ln in reversed(lines):
        if ln.startswith("precipitation") or ln.startswith("["):
            nums = re.findall(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", ln)
            if nums:
                val = float(nums[-1])
                if math.isfinite(val) and 0.0 <= val <= 1500.0:
                    return round(val, 2)
    return None


def fetch_imerg_daily_opendap(
    lat: float,
    lon: float,
    start_date: date,
    end_date: date,
    token: str,
    *,
    product_key: str = "GPM_3IMERGDE_V07B",
    timeout: float = 12.0,
) -> dict[str, Any]:
    """Fetch daily numerical IMERG precipitation (`mm/day`) from NASA GES DISC OPeNDAP using an Earthdata Bearer token."""
    idx = imerg_grid_indices(lat, lon)
    prod = IMERG_PRODUCTS.get(product_key, IMERG_PRODUCTS["GPM_3IMERGDE_V07B"])
    col = prod["collection_path"]
    short = prod["short_name"]
    ver = prod["version"]

    n_days = (end_date - start_date).days + 1
    if n_days <= 0 or n_days > 31:
        raise ValueError("IMERG OPeNDAP point query span must be between 1 and 31 days")

    daily_by_date: dict[str, float | None] = {}
    urls_queried: list[str] = []
    errors: list[str] = []

    for i in range(n_days):
        d = start_date + timedelta(days=i)
        ymd = d.strftime("%Y%m%d")
        fname = f"3B-DAY-E.MS.MRG.3IMERG.{ymd}-S000000-E235959.V{ver}.nc4" if "DE" in short else (
            f"3B-DAY.MS.MRG.3IMERG.{ymd}-S000000-E235959.V{ver}.nc4"
        )
        url = (
            f"{GES_DISC_OPENDAP_BASE}/{col}/{d.year:04d}/{d.month:02d}/{fname}.ascii"
            f"?precipitation[0:1:0][{idx['lon_index']}:1:{idx['lon_index']}][{idx['lat_index']}:1:{idx['lat_index']}]"
        )
        urls_queried.append(url)
        req = Request(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": "BoponX/1.0 (NASA Space Apps 2026; EARTH.exe)",
            },
        )
        try:
            with urlopen(req, timeout=timeout) as resp:  # noqa: S310 - fixed NASA GES DISC host
                body = resp.read().decode("utf-8", errors="replace")
            val = _parse_opendap_ascii_value(body)
            daily_by_date[d.isoformat()] = val
        except Exception as exc:  # noqa: BLE001
            daily_by_date[d.isoformat()] = None
            errors.append(f"{d.isoformat()}: {type(exc).__name__}")

    valid_days = sum(1 for v in daily_by_date.values() if v is not None)
    return {
        "status": "available" if valid_days > 0 else "unavailable",
        "product": prod,
        "imerg_grid": idx,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "valid_days": valid_days,
        "requested_days": n_days,
        "daily_mm": daily_by_date,
        "retrieved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sample_request_url": urls_queried[0] if urls_queried else None,
        "errors": errors[:5],
    }


def get_imerg_crosscheck_status(
    lat: float,
    lon: float,
    *,
    imerg_series: Sequence[float | None] | Mapping[str, float | None] | None = None,
    power_series: Sequence[float | None] | Mapping[str, float | None] | None = None,
    dates: Sequence[str] | None = None,
    attempt_live_fetch: bool = False,
) -> dict[str, Any]:
    """Return IMERG cross-check metadata and numerical comparison when series or Earthdata credentials are provided.
    Never fabricates comparison statistics when credentials or network access are unavailable."""
    imerg_cell = imerg_grid_indices(lat, lon)
    retrieved_now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if imerg_series is not None and power_series is not None:
        comp = compare_imerg_and_power_series(imerg_series, power_series, dates=dates)
        return {
            "provider": "NASA GPM IMERG V07 vs. NASA POWER PRECTOTCORR",
            "product_metadata": IMERG_PRODUCTS["GPM_3IMERGDF_V07"],
            "visual_layer_metadata": IMERG_PRODUCTS["GIBS_IMERG_VISUAL"],
            "coordinates": {"latitude": round(lat, 4), "longitude": round(lon, 4)},
            "imerg_grid_cell": imerg_cell,
            "mode": "series_comparison",
            "retrieved_at": retrieved_now,
            **comp,
        }

    token = os.getenv("NASA_EARTHDATA_TOKEN", "").strip()
    is_offline = os.getenv("OFFLINE", "").strip().lower() in ("1", "true", "yes") or (
        os.getenv("BOPONX_OFFLINE", "").strip().lower() in ("1", "true", "yes")
    )

    if not token or is_offline:
        return {
            "status": "skipped_no_token",
            "numerical_validation_status": "unavailable_missing_earthdata_token" if not token else "unavailable_offline_mode",
            "mode": "visual_gibs_layer_only",
            "provider": "NASA GPM IMERG Early V07B",
            "product_metadata": IMERG_PRODUCTS["GPM_3IMERGDE_V07B"],
            "visual_layer_metadata": IMERG_PRODUCTS["GIBS_IMERG_VISUAL"],
            "coordinates": {"latitude": round(lat, 4), "longitude": round(lon, 4)},
            "imerg_grid_cell": imerg_cell,
            "retrieved_at": retrieved_now,
            "why_unavailable": (
                "NASA GES DISC numerical OPeNDAP access for GPM_3IMERGDF / GPM_3IMERGDE requires an Earthdata Login "
                "Bearer token (NASA_EARTHDATA_TOKEN), whereas NASA GIBS visual tiles (IMERG_Precipitation_Rate) are "
                "publicly accessible without authentication but contain rendered RGB imagery rather than numerical mm/day arrays."
            ),
            "note": (
                "GPM IMERG is active as a visual NASA GIBS layer (IMERG_Precipitation_Rate). "
                "Set NASA_EARTHDATA_TOKEN to enable numeric GES DISC point cross-checks against NASA POWER."
            ),
        }

    if attempt_live_fetch:
        cache_key = f"{imerg_cell['cell_id']}"
        cached = _IMERG_CACHE.get(cache_key)
        if cached and time.monotonic() - cached[0] < _IMERG_CACHE_TTL_SEC:
            return cached[1]
        try:
            from backend.app.services.power_live import fetch_recent_power

            pw_recent = fetch_recent_power(lat, lon, days=14)
            if pw_recent.get("status") == "available" and isinstance(pw_recent.get("daily"), list):
                pw_map = {
                    str(row["date"]): row.get("precipitation_mm")
                    for row in pw_recent["daily"]
                    if isinstance(row, dict) and row.get("date")
                }
                d_keys = sorted(pw_map.keys())
                if d_keys:
                    s_d = date.fromisoformat(d_keys[0])
                    e_d = date.fromisoformat(d_keys[-1])
                    im_res = fetch_imerg_daily_opendap(lat, lon, s_d, e_d, token)
                    if im_res["status"] == "available":
                        comp = compare_imerg_and_power_series(im_res["daily_mm"], pw_map)
                        out = {
                            "provider": "NASA GPM IMERG Early V07B (GES DISC OPeNDAP) vs. NASA POWER PRECTOTCORR",
                            "product_metadata": im_res["product"],
                            "visual_layer_metadata": IMERG_PRODUCTS["GIBS_IMERG_VISUAL"],
                            "coordinates": {"latitude": round(lat, 4), "longitude": round(lon, 4)},
                            "imerg_grid_cell": imerg_cell,
                            "mode": "live_ges_disc_comparison",
                            "retrieved_at": im_res["retrieved_at"],
                            "sample_request_url": im_res["sample_request_url"],
                            **comp,
                        }
                        _IMERG_CACHE[cache_key] = (time.monotonic(), out)
                        return out
        except Exception as exc:  # noqa: BLE001
            return {
                "status": "unavailable",
                "numerical_validation_status": "ges_disc_request_failed",
                "mode": "visual_gibs_layer_only",
                "provider": "NASA GPM IMERG Early V07B",
                "product_metadata": IMERG_PRODUCTS["GPM_3IMERGDE_V07B"],
                "visual_layer_metadata": IMERG_PRODUCTS["GIBS_IMERG_VISUAL"],
                "coordinates": {"latitude": round(lat, 4), "longitude": round(lon, 4)},
                "imerg_grid_cell": imerg_cell,
                "retrieved_at": retrieved_now,
                "why_unavailable": f"GES DISC OPeNDAP request failed ({type(exc).__name__}). Visual GIBS layer remains active.",
            }

    return {
        "status": "token_configured_ready",
        "numerical_validation_status": "ready_for_query",
        "mode": "earthdata_token_present",
        "provider": "NASA GPM IMERG Early V07B",
        "product_metadata": IMERG_PRODUCTS["GPM_3IMERGDE_V07B"],
        "visual_layer_metadata": IMERG_PRODUCTS["GIBS_IMERG_VISUAL"],
        "coordinates": {"latitude": round(lat, 4), "longitude": round(lon, 4)},
        "imerg_grid_cell": imerg_cell,
        "retrieved_at": retrieved_now,
        "note": "Earthdata token detected; numeric IMERG comparison adapter is enabled.",
    }
