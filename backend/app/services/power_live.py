"""Recent and historical NASA POWER context with fail-closed contracts."""
from __future__ import annotations

import json
from datetime import date, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen

POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
POWER_CLIMATOLOGY_URL = "https://power.larc.nasa.gov/api/temporal/climatology/point"
MONTH_KEYS = {1: "JAN", 2: "FEB", 3: "MAR", 4: "APR", 5: "MAY", 6: "JUN", 7: "JUL", 8: "AUG", 9: "SEP", 10: "OCT", 11: "NOV", 12: "DEC"}
MISSING_SENTINEL = -999.0


def summarize_power_payload(payload: dict) -> dict:
    properties = payload.get("properties", {})
    parameter = properties.get("parameter", {})
    t2m = parameter.get("T2M", {})
    t2m_max = parameter.get("T2M_MAX", {})
    t2m_min = parameter.get("T2M_MIN", {})
    rain = parameter.get("PRECTOTCORR", {})
    humidity = parameter.get("RH2M", {})
    wind = parameter.get("WS2M", {})
    dates = sorted(set(t2m) | set(t2m_max) | set(t2m_min) | set(rain) | set(humidity) | set(wind))

    def valid(values: dict) -> list[float]:
        out: list[float] = []
        for day in dates:
            value = values.get(day)
            if isinstance(value, (int, float)) and float(value) != MISSING_SENTINEL:
                out.append(float(value))
        return out

    temperatures = valid(t2m)
    max_temperatures = valid(t2m_max)
    min_temperatures = valid(t2m_min)
    precipitation = valid(rain)
    humidities = valid(humidity)
    winds = valid(wind)
    return {
        "days_requested": len(dates),
        "temperature_valid_days": len(temperatures),
        "precipitation_valid_days": len(precipitation),
        "temperature_mean_c": round(sum(temperatures) / len(temperatures), 2) if temperatures else None,
        "temperature_max_mean_c": round(sum(max_temperatures) / len(max_temperatures), 2) if max_temperatures else None,
        "temperature_min_mean_c": round(sum(min_temperatures) / len(min_temperatures), 2) if min_temperatures else None,
        "precipitation_total_mm": round(sum(precipitation), 2) if precipitation and len(precipitation) == len(dates) else None,
        "relative_humidity_mean_pct": round(sum(humidities) / len(humidities), 2) if humidities else None,
        "wind_speed_mean_m_s": round(sum(winds) / len(winds), 2) if winds else None,
    }


def fetch_recent_power(lat: float, lon: float, days: int = 14, lag_days: int = 7) -> dict:
    end = date.today() - timedelta(days=lag_days)
    start = end - timedelta(days=days - 1)
    params = {
        "parameters": "T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M,WS2M",
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
    with urlopen(request, timeout=12) as response:
        payload = json.loads(response.read().decode("utf-8"))
    summary = summarize_power_payload(payload)
    return {
        "status": "available",
        "mode": "recent_nasa_power_request",
        "provider": "NASA POWER",
        "source_products": payload.get("header", {}).get("sources", []),
        "period": {"start": start.isoformat(), "end": end.isoformat(), "time_standard": "LST"},
        "coordinates": {"latitude": lat, "longitude": lon},
        "summary": summary,
        "source_request_url": url,
        "limitations": [
            "This is regional gridded climate context, not a measurement taken in the farmer's field.",
            "The period ends several days before today to reduce failures from upstream data latency.",
            "This endpoint is not a weather forecast.",
        ],
    }



def summarize_climatology_payload(payload: dict, month: int) -> dict:
    if month not in MONTH_KEYS:
        raise ValueError("month must be 1..12")
    key = MONTH_KEYS[month]
    parameter = payload.get("properties", {}).get("parameter", {})
    t2m = parameter.get("T2M", {})
    t2m_max = parameter.get("T2M_MAX", {})
    t2m_min = parameter.get("T2M_MIN", {})
    rain = parameter.get("PRECTOTCORR", {})
    humidity = parameter.get("RH2M", {})
    wind = parameter.get("WS2M", {})

    def value(values: dict):
        raw = values.get(key)
        if not isinstance(raw, (int, float)) or float(raw) == MISSING_SENTINEL:
            return None
        return round(float(raw), 2)

    return {
        "calendar_month": month,
        "calendar_month_key": key,
        "temperature_mean_c": value(t2m),
        "temperature_max_mean_c": value(t2m_max),
        "temperature_min_mean_c": value(t2m_min),
        "precipitation_mean_daily_mm": value(rain),
        "relative_humidity_mean_pct": value(humidity),
        "wind_speed_mean_m_s": value(wind),
    }


def fetch_power_climatology(
    lat: float,
    lon: float,
    *,
    month: int,
    start_year: int = 2001,
    end_year: int = 2020,
) -> dict:
    params = {
        "parameters": "T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M,WS2M",
        "community": "AG",
        "latitude": f"{lat:.5f}",
        "longitude": f"{lon:.5f}",
        "format": "JSON",
        "start": str(start_year),
        "end": str(end_year),
    }
    url = f"{POWER_CLIMATOLOGY_URL}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": "BoponX/SpaceApps2026"})
    with urlopen(request, timeout=12) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return {
        "status": "available",
        "provider": "NASA POWER",
        "kind": "historical_climatology",
        "baseline_period": {"start_year": start_year, "end_year": end_year},
        "coordinates": {"latitude": lat, "longitude": lon},
        "summary": summarize_climatology_payload(payload, month),
        "source_products": payload.get("header", {}).get("sources", []),
        "source_request_url": url,
        "limitations": [
            "This is a multi-year regional climatology, not a forecast or a field measurement.",
            "PRECTOTCORR is shown as the POWER climatological daily precipitation value for the selected calendar month.",
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
        "parameters": "T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M,WS2M",
        "community": "AG",
        "latitude": f"{lat:.5f}",
        "longitude": f"{lon:.5f}",
        "format": "JSON",
        "start": str(start_year),
        "end": str(end_year),
    }
    url = f"{POWER_CLIMATOLOGY_URL}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": "BoponX/SpaceApps2026"})
    with urlopen(request, timeout=12) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return {
        "status": "available",
        "provider": "NASA POWER",
        "kind": "historical_climatology_window",
        "baseline_period": {"start_year": start_year, "end_year": end_year},
        "coordinates": {"latitude": lat, "longitude": lon},
        "summaries": summarize_climatology_window(payload, start_month, months),
        "source_products": payload.get("header", {}).get("sources", []),
        "source_request_url": url,
        "limitations": [
            "These are multi-year monthly climatology references, not weather forecasts or field measurements.",
            "Each month is used as historical context for planning and monitoring.",
        ],
    }
