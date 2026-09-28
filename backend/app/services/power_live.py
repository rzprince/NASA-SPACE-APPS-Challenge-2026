"""Recent and historical NASA POWER context with fail closed contracts."""
from __future__ import annotations

import json
from datetime import date, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen

POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
POWER_CLIMATOLOGY_URL = "https://power.larc.nasa.gov/api/temporal/climatology/point"
MONTH_KEYS = {1: "JAN", 2: "FEB", 3: "MAR", 4: "APR", 5: "MAY", 6: "JUN", 7: "JUL", 8: "AUG", 9: "SEP", 10: "OCT", 11: "NOV", 12: "DEC"}
MISSING_SENTINEL = -999.0

RECENT_PARAMETERS = (
    "T2M",
    "T2M_MAX",
    "T2M_MIN",
    "PRECTOTCORR",
    "RH2M",
    "WS2M",
    "ALLSKY_SFC_SW_DWN",
)


def _valid_series(values: dict, dates: list[str]) -> list[float]:
    out: list[float] = []
    for day in dates:
        value = values.get(day)
        if isinstance(value, (int, float)) and float(value) != MISSING_SENTINEL:
            out.append(float(value))
    return out


def _mean(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 2) if values else None


def summarize_power_payload(payload: dict) -> dict:
    parameter = payload.get("properties", {}).get("parameter", {})
    dates = sorted({
        day
        for values in parameter.values()
        if isinstance(values, dict)
        for day in values.keys()
    })

    t2m = _valid_series(parameter.get("T2M", {}), dates)
    tmax = _valid_series(parameter.get("T2M_MAX", {}), dates)
    tmin = _valid_series(parameter.get("T2M_MIN", {}), dates)
    rain = _valid_series(parameter.get("PRECTOTCORR", {}), dates)
    humidity = _valid_series(parameter.get("RH2M", {}), dates)
    wind = _valid_series(parameter.get("WS2M", {}), dates)
    solar = _valid_series(parameter.get("ALLSKY_SFC_SW_DWN", {}), dates)

    return {
        "days_requested": len(dates),
        "temperature_valid_days": len(t2m),
        "precipitation_valid_days": len(rain),
        "temperature_mean_c": _mean(t2m),
        "temperature_max_mean_c": _mean(tmax),
        "temperature_min_mean_c": _mean(tmin),
        "precipitation_total_mm": round(sum(rain), 2) if rain and len(rain) == len(dates) else None,
        "relative_humidity_mean_pct": _mean(humidity),
        "wind_speed_2m_mean_ms": _mean(wind),
        "solar_radiation_mean_kwh_m2_day": _mean(solar),
    }


def fetch_recent_power(lat: float, lon: float, days: int = 14, lag_days: int = 7) -> dict:
    end = date.today() - timedelta(days=lag_days)
    start = end - timedelta(days=days - 1)
    params = {
        "parameters": ",".join(RECENT_PARAMETERS),
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
    with urlopen(request, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))
    summary = summarize_power_payload(payload)
    return {
        "status": "available",
        "mode": "recent_nasa_power_request",
        "provider": "NASA POWER",
        "product": "POWER Data v10 service",
        "parameters": list(RECENT_PARAMETERS),
        "source_products": payload.get("header", {}).get("sources", []),
        "period": {"start": start.isoformat(), "end": end.isoformat(), "time_standard": "LST"},
        "coordinates": {"latitude": lat, "longitude": lon},
        "summary": summary,
        "source_request_url": url,
        "limitations": [
            "These are global gridded agroclimate values, not measurements taken in the farmer's field.",
            "The period ends several days before today to reduce failures from upstream data latency.",
            "This endpoint does not provide a weather forecast.",
        ],
    }


def summarize_climatology_payload(payload: dict, month: int) -> dict:
    if month not in MONTH_KEYS:
        raise ValueError("month must be 1..12")
    key = MONTH_KEYS[month]
    parameter = payload.get("properties", {}).get("parameter", {})

    def value(name: str):
        values = parameter.get(name, {})
        raw = values.get(key) if isinstance(values, dict) else None
        if not isinstance(raw, (int, float)) or float(raw) == MISSING_SENTINEL:
            return None
        return round(float(raw), 2)

    return {
        "calendar_month": month,
        "calendar_month_key": key,
        "temperature_mean_c": value("T2M"),
        "precipitation_mean_daily_mm": value("PRECTOTCORR"),
        "relative_humidity_mean_pct": value("RH2M"),
        "wind_speed_2m_mean_ms": value("WS2M"),
        "solar_radiation_mean_kwh_m2_day": value("ALLSKY_SFC_SW_DWN"),
    }


def _climatology_params() -> str:
    return "T2M,PRECTOTCORR,RH2M,WS2M,ALLSKY_SFC_SW_DWN"


def fetch_power_climatology(
    lat: float,
    lon: float,
    *,
    month: int,
    start_year: int = 2001,
    end_year: int = 2020,
) -> dict:
    params = {
        "parameters": _climatology_params(),
        "community": "AG",
        "latitude": f"{lat:.5f}",
        "longitude": f"{lon:.5f}",
        "format": "JSON",
        "start": str(start_year),
        "end": str(end_year),
    }
    url = f"{POWER_CLIMATOLOGY_URL}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": "BoponX/SpaceApps2026"})
    with urlopen(request, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return {
        "status": "available",
        "provider": "NASA POWER",
        "product": "POWER Data v10 service",
        "kind": "historical_climatology",
        "baseline_period": {"start_year": start_year, "end_year": end_year},
        "coordinates": {"latitude": lat, "longitude": lon},
        "summary": summarize_climatology_payload(payload, month),
        "source_products": payload.get("header", {}).get("sources", []),
        "source_request_url": url,
        "limitations": [
            "This is a multi year regional climatology, not a forecast or a field measurement.",
            "Climate references are used to contextualize current conditions.",
        ],
    }


def summarize_climatology_window(payload: dict, start_month: int, months: int = 3) -> list[dict]:
    if start_month not in MONTH_KEYS:
        raise ValueError("start_month must be 1..12")
    if months < 1 or months > 12:
        raise ValueError("months must be 1..12")
    return [
        summarize_climatology_payload(payload, (start_month - 1 + offset) % 12 + 1)
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
    params = {
        "parameters": _climatology_params(),
        "community": "AG",
        "latitude": f"{lat:.5f}",
        "longitude": f"{lon:.5f}",
        "format": "JSON",
        "start": str(start_year),
        "end": str(end_year),
    }
    url = f"{POWER_CLIMATOLOGY_URL}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": "BoponX/SpaceApps2026"})
    with urlopen(request, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return {
        "status": "available",
        "provider": "NASA POWER",
        "product": "POWER Data v10 service",
        "kind": "historical_climatology_window",
        "baseline_period": {"start_year": start_year, "end_year": end_year},
        "coordinates": {"latitude": lat, "longitude": lon},
        "summaries": summarize_climatology_window(payload, start_month, months),
        "source_products": payload.get("header", {}).get("sources", []),
        "source_request_url": url,
        "limitations": [
            "These are multi year monthly climatology references, not weather forecasts or field measurements.",
            "Each month is used as historical context for planning and monitoring.",
        ],
    }
