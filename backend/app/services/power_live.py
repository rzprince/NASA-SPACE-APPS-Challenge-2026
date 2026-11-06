"""Recent and historical NASA POWER context with fail-closed contracts, FAO-56 ET0, and root-zone soil moisture."""
from __future__ import annotations

import json
import os
import math
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
POWER_CLIMATOLOGY_URL = "https://power.larc.nasa.gov/api/temporal/climatology/point"
POWER_PARAMETERS = "T2M,T2M_MAX,T2M_MIN,T2MDEW,PRECTOTCORR,RH2M,WS2M,ALLSKY_SFC_SW_DWN,GWETTOP,GWETROOT"
MONTH_KEYS = {1: "JAN", 2: "FEB", 3: "MAR", 4: "APR", 5: "MAY", 6: "JUN", 7: "JUL", 8: "AUG", 9: "SEP", 10: "OCT", 11: "NOV", 12: "DEC"}
MISSING_SENTINEL = -999.0

_POWER_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL_SEC = 1800.0


def _is_offline() -> bool:
    return (
        os.getenv("OFFLINE", "").strip().lower() in ("1", "true", "yes")
        or os.getenv("BOPONX_OFFLINE", "").strip().lower() in ("1", "true", "yes")
    )


def _cache_get(key: str) -> dict[str, Any] | None:
    entry = _POWER_CACHE.get(key)
    if not entry:
        return None
    ts, value = entry
    if time.monotonic() - ts > _CACHE_TTL_SEC:
        _POWER_CACHE.pop(key, None)
        return None
    return value


def _cache_set(key: str, value: dict[str, Any]) -> dict[str, Any]:
    if len(_POWER_CACHE) > 256:
        _POWER_CACHE.clear()
    _POWER_CACHE[key] = (time.monotonic(), value)
    return value


def _extraterrestrial_radiation_mm_day(lat_deg: float, day_of_year: int = 180) -> float:
    """FAO-56 extraterrestrial radiation (Ra) expressed in equivalent evaporation (mm/day)."""
    phi = math.radians(max(-65.0, min(65.0, lat_deg)))
    dr = 1.0 + 0.033 * math.cos(2.0 * math.pi * day_of_year / 365.0)
    delta = 0.409 * math.sin(2.0 * math.pi * day_of_year / 365.0 - 1.39)
    ws_arg = max(-1.0, min(1.0, -math.tan(phi) * math.tan(delta)))
    ws = math.acos(ws_arg)
    ra_mj = (24.0 * 60.0 / math.pi) * 0.0820 * dr * (
        ws * math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.sin(ws)
    )
    return max(1.0, 0.408 * ra_mj)


def _hargreaves_et0_mm_day(
    t_mean: float | None,
    t_max: float | None,
    t_min: float | None,
    *,
    lat_deg: float = 24.0,
    day_of_year: int = 180,
) -> float | None:
    """FAO-56 Hargreaves-Samani reference evapotranspiration (ET0, mm/day)."""
    if t_mean is None or t_max is None or t_min is None:
        return None
    td = max(0.0, float(t_max) - float(t_min))
    if td <= 0.0:
        return None
    ra_mm = _extraterrestrial_radiation_mm_day(lat_deg, day_of_year)
    et0 = 0.0023 * (float(t_mean) + 17.8) * math.sqrt(td) * ra_mm
    return round(max(0.5, et0), 2)


def _vapor_pressure_deficit_kpa(t_mean: float | None, rh_mean: float | None) -> float | None:
    """Compute Vapor Pressure Deficit (VPD, kPa) from air temperature (°C) and relative humidity (%)."""
    if t_mean is None or rh_mean is None:
        return None
    es = 0.6108 * math.exp((17.27 * float(t_mean)) / (float(t_mean) + 237.3))
    rh_clamped = max(0.0, min(100.0, float(rh_mean)))
    vpd = es * (1.0 - rh_clamped / 100.0)
    return round(max(0.0, vpd), 2)


def _is_valid_num(val: Any, *, non_negative: bool = False) -> bool:
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        return False
    fv = float(val)
    if not math.isfinite(fv) or fv <= MISSING_SENTINEL:
        return False
    if non_negative and fv < 0.0:
        return False
    return True


def summarize_power_payload(payload: dict, *, lat: float = 24.0, max_valid_days: int | None = None) -> dict:
    properties = payload.get("properties", {})
    parameter = properties.get("parameter", {})
    t2m = parameter.get("T2M", {})
    t2m_max = parameter.get("T2M_MAX", {})
    t2m_min = parameter.get("T2M_MIN", {})
    t2m_dew = parameter.get("T2MDEW", {})
    rain = parameter.get("PRECTOTCORR", {})
    humidity = parameter.get("RH2M", {})
    wind = parameter.get("WS2M", {})
    solar = parameter.get("ALLSKY_SFC_SW_DWN", {})
    gwettop = parameter.get("GWETTOP", {})
    gwetroot = parameter.get("GWETROOT", {})

    all_dates = sorted(
        set(t2m)
        | set(t2m_max)
        | set(t2m_min)
        | set(t2m_dew)
        | set(rain)
        | set(humidity)
        | set(wind)
        | set(solar)
        | set(gwettop)
        | set(gwetroot)
    )

    # When max_valid_days is set (live recent queries), select the latest `max_valid_days` dates
    # where both T2M and PRECTOTCORR have arrived (not -999 fill value).
    if max_valid_days is not None and len(all_dates) > max_valid_days:
        complete_dates = [
            d for d in all_dates
            if _is_valid_num(t2m.get(d)) and _is_valid_num(rain.get(d), non_negative=True)
        ]
        if len(complete_dates) >= max_valid_days:
            dates = complete_dates[-max_valid_days:]
        elif complete_dates:
            dates = complete_dates
        else:
            valid_any = [
                d for d in all_dates
                if _is_valid_num(t2m.get(d)) or _is_valid_num(rain.get(d), non_negative=True)
            ]
            dates = valid_any[-max_valid_days:] if valid_any else all_dates[-max_valid_days:]
    else:
        dates = list(all_dates)

    def valid(values: dict, *, non_negative: bool = False, source_dates: list[str] | None = None) -> list[float]:
        out: list[float] = []
        for day in (source_dates if source_dates is not None else dates):
            value = values.get(day)
            if _is_valid_num(value, non_negative=non_negative):
                out.append(float(value))
        return out

    temperatures = valid(t2m)
    max_temperatures = valid(t2m_max)
    min_temperatures = valid(t2m_min)
    dew_points = valid(t2m_dew)
    precipitation = valid(rain, non_negative=True)
    humidities = valid(humidity)
    winds = valid(wind)
    solar_vals = valid(solar)

    # MERRA-2 Land soil wetness (GWETTOP / GWETROOT) often lags T2M by an extra 1-3 weeks in NASA POWER;
    # if the latest 14 T2M days have -999 for GWET, use the latest valid GWET days from the full query window.
    top_wetness = [v for v in valid(gwettop) if 0.0 <= v <= 1.0]
    if not top_wetness and max_valid_days is not None:
        top_wetness = [v for v in valid(gwettop, source_dates=all_dates) if 0.0 <= v <= 1.0][-max_valid_days:]

    root_wetness = [v for v in valid(gwetroot) if 0.0 <= v <= 1.0]
    if not root_wetness and max_valid_days is not None:
        root_wetness = [v for v in valid(gwetroot, source_dates=all_dates) if 0.0 <= v <= 1.0][-max_valid_days:]

    t_mean = round(sum(temperatures) / len(temperatures), 2) if temperatures else None
    t_max_mean = round(sum(max_temperatures) / len(max_temperatures), 2) if max_temperatures else None
    t_min_mean = round(sum(min_temperatures) / len(min_temperatures), 2) if min_temperatures else None
    dew_mean = round(sum(dew_points) / len(dew_points), 2) if dew_points else None
    rain_total = round(sum(precipitation), 2) if precipitation and len(precipitation) == len(dates) else None
    rain_daily_mean = round(sum(precipitation) / len(precipitation), 2) if precipitation else None
    rh_mean = round(sum(humidities) / len(humidities), 2) if humidities else None
    wind_mean = round(sum(winds) / len(winds), 2) if winds else None
    solar_mean = round(sum(solar_vals) / len(solar_vals), 2) if solar_vals else None
    gwettop_mean = round(sum(top_wetness) / len(top_wetness), 3) if top_wetness else None
    gwetroot_mean = round(sum(root_wetness) / len(root_wetness), 3) if root_wetness else None
    gwettop_pct = round(gwettop_mean * 100.0, 1) if gwettop_mean is not None else None
    gwetroot_pct = round(gwetroot_mean * 100.0, 1) if gwetroot_mean is not None else None

    et0_daily = _hargreaves_et0_mm_day(t_mean, t_max_mean, t_min_mean, lat_deg=lat)
    vpd_kpa = _vapor_pressure_deficit_kpa(t_mean, rh_mean)
    wb_daily = (
        round(rain_daily_mean - et0_daily, 2)
        if rain_daily_mean is not None and et0_daily is not None
        else None
    )
    wb_period = (
        round(rain_total - et0_daily * len(dates), 1)
        if rain_total is not None and et0_daily is not None and dates
        else None
    )

    heat_stress_days = sum(1 for v in max_temperatures if v >= 35.0)
    cold_stress_days = sum(1 for v in min_temperatures if v <= 12.0)
    frost_risk_days = sum(1 for v in min_temperatures if v <= 8.0)
    heavy_rain_days = sum(1 for v in precipitation if v >= 25.0)
    dry_days = sum(1 for v in precipitation if v < 1.0)

    fog_blight_risk_days = 0
    for day in dates:
        tv = t2m.get(day)
        dv = t2m_dew.get(day)
        rv = humidity.get(day)
        if (
            _is_valid_num(tv)
            and _is_valid_num(dv)
            and (float(tv) - float(dv)) <= 2.5
        ):
            if not _is_valid_num(rv) or float(rv) >= 80.0:
                fog_blight_risk_days += 1

    out: dict[str, Any] = {
        "days_requested": len(dates),
        "temperature_valid_days": len(temperatures),
        "precipitation_valid_days": len(precipitation),
        "temperature_mean_c": t_mean,
        "temperature_max_mean_c": t_max_mean,
        "temperature_min_mean_c": t_min_mean,
        "dew_point_mean_c": dew_mean,
        "precipitation_total_mm": rain_total,
        "precipitation_mean_daily_mm": rain_daily_mean,
        "relative_humidity_mean_pct": rh_mean,
        "wind_speed_mean_m_s": wind_mean,
        "solar_radiation_mean": solar_mean,
        "surface_soil_wetness_pct": gwettop_pct,
        "root_zone_soil_wetness_pct": gwetroot_pct,
        "et0_mean_daily_mm": et0_daily,
        "water_balance_daily_mm": wb_daily,
        "water_balance_period_mm": wb_period,
        "vpd_mean_kpa": vpd_kpa,
        "heat_stress_days": heat_stress_days,
        "cold_stress_days": cold_stress_days,
        "frost_risk_days": frost_risk_days,
        "fog_blight_risk_days": fog_blight_risk_days,
        "heavy_rain_days": heavy_rain_days,
        "dry_days": dry_days,
    }
    if max_valid_days is not None and dates:
        out["resolved_start_date"] = f"{dates[0][:4]}-{dates[0][4:6]}-{dates[0][6:8]}"
        out["resolved_end_date"] = f"{dates[-1][:4]}-{dates[-1][4:6]}-{dates[-1][6:8]}"
    return out


def _request_power_window(lat: float, lon: float, start: date, end: date) -> tuple[dict, str]:
    params = {
        "parameters": POWER_PARAMETERS,
        "community": "AG",
        "latitude": f"{lat:.5f}",
        "longitude": f"{lon:.5f}",
        "start": start.strftime("%Y%m%d"),
        "end": end.strftime("%Y%m%d"),
        "format": "JSON",
        "time-standard": "LST",
    }
    url = f"{POWER_URL}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": "BoponX/SpaceApps2026"})
    with urlopen(request, timeout=25) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload, url


def fetch_recent_power(lat: float, lon: float, days: int = 14, lag_days: int = 7) -> dict:
    if _is_offline():
        raise RuntimeError("OFFLINE=1 mode active; using local cache/snapshot")

    today = date.today()
    end = today - timedelta(days=max(2, lag_days))
    # Request a 75-day lookback window so NASA POWER NRT processing lag (typically 3-25 days for MERRA-2/GWET)
    # never leaves the latest 14 valid days empty.
    query_start = end - timedelta(days=max(days + 14, 75))
    cache_key = f"recent_v3:{lat:.3f}:{lon:.3f}:{end.isoformat()}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    payload = None
    url = ""
    summary = None
    # Try current clock year first; if system clock is set ahead of NASA's archive (e.g. simulated 2026 clock
    # when NASA POWER's server only has up to 2025), step back by 1 year so real NASA POWER data for the coordinate loads.
    for year_offset in (0, 1):
        try_end = end - timedelta(days=365 * year_offset)
        try_start = query_start - timedelta(days=365 * year_offset)
        try:
            cand_payload, cand_url = _request_power_window(lat, lon, try_start, try_end)
            cand_summary = summarize_power_payload(cand_payload, lat=lat, max_valid_days=days)
            if cand_summary.get("temperature_valid_days", 0) > 0 or cand_summary.get("precipitation_valid_days", 0) > 0:
                payload = cand_payload
                url = cand_url
                summary = cand_summary
                break
        except Exception:
            if year_offset == 1:
                raise

    if payload is None or summary is None:
        raise RuntimeError("NASA POWER returned no valid observation days for this coordinate")

    resolved_start = summary.pop("resolved_start_date", (end - timedelta(days=days - 1)).isoformat())
    resolved_end = summary.pop("resolved_end_date", end.isoformat())
    actual_lag = max(0, (today - date.fromisoformat(resolved_end)).days)
    retrieved_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    result = {
        "status": "available",
        "data_origin": "nasa_power_live",
        "retrieved_at": retrieved_at,
        "lag_days": actual_lag,
        "data_through": resolved_end,
        "mode": "recent_nasa_power_request",
        "provider": "NASA POWER",
        "source_products": payload.get("header", {}).get("sources", []),
        "period": {"start": resolved_start, "end": resolved_end, "time_standard": "LST"},
        "coordinates": {"latitude": lat, "longitude": lon},
        "summary": summary,
        "source_request_url": url,
        "limitations": [
            "This is regional gridded climate context (0.5° × 0.625°), not a measurement taken inside the farmer's field.",
            "GWETTOP (0–5 cm) and GWETROOT (0–100 cm) represent gridded physical soil wetness saturation (%), never soil pH or NPK chemistry.",
            "Reference evapotranspiration (ET0) is estimated via the FAO-56 Hargreaves-Samani equation; this endpoint is not a weather forecast.",
        ],
    }
    return _cache_set(cache_key, result)


def summarize_climatology_payload(payload: dict, month: int, *, lat: float = 24.0) -> dict:
    if month not in MONTH_KEYS:
        raise ValueError("month must be 1..12")
    key = MONTH_KEYS[month]
    parameter = payload.get("properties", {}).get("parameter", {})
    t2m = parameter.get("T2M", {})
    t2m_max = parameter.get("T2M_MAX", {})
    t2m_min = parameter.get("T2M_MIN", {})
    t2m_dew = parameter.get("T2MDEW", {})
    rain = parameter.get("PRECTOTCORR", {})
    humidity = parameter.get("RH2M", {})
    wind = parameter.get("WS2M", {})
    solar = parameter.get("ALLSKY_SFC_SW_DWN", {})
    gwettop = parameter.get("GWETTOP", {})
    gwetroot = parameter.get("GWETROOT", {})

    def value(values: dict):
        raw = values.get(key)
        if not isinstance(raw, (int, float)) or float(raw) <= MISSING_SENTINEL:
            return None
        return round(float(raw), 2)

    t_mean = value(t2m)
    t_max = value(t2m_max)
    t_min = value(t2m_min)
    t_dew = value(t2m_dew)
    p_daily = value(rain)
    rh = value(humidity)
    ws = value(wind)
    sol = value(solar)
    top_w = value(gwettop)
    root_w = value(gwetroot)

    doy = max(15, min(350, month * 30 - 15))
    et0 = _hargreaves_et0_mm_day(t_mean, t_max, t_min, lat_deg=lat, day_of_year=doy)
    wb = round(p_daily - et0, 2) if p_daily is not None and et0 is not None else None

    return {
        "calendar_month": month,
        "calendar_month_key": key,
        "temperature_mean_c": t_mean,
        "temperature_max_mean_c": t_max,
        "temperature_min_mean_c": t_min,
        "dew_point_mean_c": t_dew,
        "precipitation_mean_daily_mm": p_daily,
        "relative_humidity_mean_pct": rh,
        "wind_speed_mean_m_s": ws,
        "solar_radiation_mean": sol,
        "surface_soil_wetness_pct": round(top_w * 100.0, 1) if top_w is not None and 0.0 <= top_w <= 1.0 else None,
        "root_zone_soil_wetness_pct": round(root_w * 100.0, 1) if root_w is not None and 0.0 <= root_w <= 1.0 else None,
        "et0_mean_daily_mm": et0,
        "water_balance_daily_mm": wb,
    }


def _fetch_raw_climatology(lat: float, lon: float, start_year: int = 2001, end_year: int = 2020) -> tuple[dict, str, str]:
    if _is_offline():
        raise RuntimeError("OFFLINE=1 mode active; using local cache/snapshot")
    cache_key = f"clim_raw_v2:{lat:.3f}:{lon:.3f}:{start_year}:{end_year}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached["payload"], cached["url"], cached["retrieved_at"]

    params = {
        "parameters": POWER_PARAMETERS,
        "community": "AG",
        "latitude": f"{lat:.5f}",
        "longitude": f"{lon:.5f}",
        "format": "JSON",
        "start": str(start_year),
        "end": str(end_year),
    }
    url = f"{POWER_CLIMATOLOGY_URL}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": "BoponX/SpaceApps2026"})
    with urlopen(request, timeout=25) as response:
        payload = json.loads(response.read().decode("utf-8"))
    retrieved_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    _cache_set(cache_key, {"payload": payload, "url": url, "retrieved_at": retrieved_at})
    return payload, url, retrieved_at


def fetch_power_climatology(
    lat: float,
    lon: float,
    *,
    month: int,
    start_year: int = 2001,
    end_year: int = 2020,
) -> dict:
    payload, url, retrieved_at = _fetch_raw_climatology(lat, lon, start_year=start_year, end_year=end_year)
    return {
        "status": "available",
        "data_origin": "nasa_power_live",
        "retrieved_at": retrieved_at,
        "lag_days": 0,
        "provider": "NASA POWER",
        "kind": "historical_climatology",
        "baseline_period": {"start_year": start_year, "end_year": end_year},
        "coordinates": {"latitude": lat, "longitude": lon},
        "summary": summarize_climatology_payload(payload, month, lat=lat),
        "source_products": payload.get("header", {}).get("sources", []),
        "source_request_url": url,
        "limitations": [
            "This is a multi-year regional climatology (2001–2020), not a forecast or a field measurement.",
            "PRECTOTCORR is shown as the POWER climatological daily precipitation value for the selected calendar month.",
        ],
    }


def summarize_climatology_window(payload: dict, start_month: int, months: int = 3, *, lat: float = 24.0) -> list[dict]:
    if start_month not in MONTH_KEYS:
        raise ValueError("start_month must be 1..12")
    if months < 1 or months > 12:
        raise ValueError("months must be 1..12")
    return [
        summarize_climatology_payload(payload, (start_month - 1 + offset) % 12 + 1, lat=lat)
        for offset in range(months)
    ]


def fetch_power_climatology_window(
    lat: float,
    lon: float,
    *,
    start_month: int,
    months: int = 3,
    start_year: int = 2001,
    end_year: int = 2020,
) -> dict:
    payload, url, retrieved_at = _fetch_raw_climatology(lat, lon, start_year=start_year, end_year=end_year)
    return {
        "status": "available",
        "data_origin": "nasa_power_live",
        "retrieved_at": retrieved_at,
        "lag_days": 0,
        "provider": "NASA POWER",
        "kind": "historical_climatology_window",
        "baseline_period": {"start_year": start_year, "end_year": end_year},
        "coordinates": {"latitude": lat, "longitude": lon},
        "summaries": summarize_climatology_window(payload, start_month, months, lat=lat),
        "source_products": payload.get("header", {}).get("sources", []),
        "source_request_url": url,
        "limitations": [
            "These are multi-year monthly climatology references (2001–2020), not weather forecasts or field measurements.",
            "Each month is used as historical context for planning and monitoring.",
        ],
    }
