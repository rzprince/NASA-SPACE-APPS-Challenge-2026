"""Reproducible aggregation of a single historical NASA POWER daily snapshot.

A monthly metric is withheld unless every expected day has a valid observation.
Monthly totals are sums of mm/day daily values, expressed in mm for the period.
No interpolations, climate forecasts or farm-level suitability claims.
"""
from __future__ import annotations

from calendar import monthrange
from datetime import date
from math import isfinite


def _valid_number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if isfinite(result) else None


def aggregate_monthly(snapshot: dict) -> dict:
    """Compute historical monthly indicators with explicit missing-data policy."""
    period = snapshot["period"]
    start = date.fromisoformat(period["start"])
    end = date.fromisoformat(period["end"])
    if end < start:
        raise ValueError("Reversed historical period")
    if snapshot["variables"]["T2M"]["provider_unit"] != "C":
        raise ValueError("Unsupported T2M unit; expected NASA POWER C")
    if snapshot["variables"]["PRECTOTCORR"]["provider_unit"] != "mm/day":
        raise ValueError("Unsupported precipitation unit; expected NASA POWER mm/day")

    expected: dict[str, int] = {}
    cursor = date(start.year, start.month, 1)
    while cursor <= end:
        key = cursor.strftime("%Y-%m")
        first = max(start, cursor)
        last = min(end, date(cursor.year, cursor.month, monthrange(cursor.year, cursor.month)[1]))
        expected[key] = (last - first).days + 1
        if cursor.month == 12:
            cursor = date(cursor.year + 1, 1, 1)
        else:
            cursor = date(cursor.year, cursor.month + 1, 1)

    buckets: dict[str, dict[str, list[float]]] = {
        key: {"T2M": [], "PRECTOTCORR": []} for key in expected
    }
    seen: set[date] = set()
    for row in snapshot["daily"]:
        day = date.fromisoformat(row["date"])
        if day < start or day > end or day in seen:
            raise ValueError("Daily dates outside requested range or duplicated")
        seen.add(day)
        key = day.strftime("%Y-%m")
        for parameter in ("T2M", "PRECTOTCORR"):
            value = _valid_number(row.get(parameter))
            if value is not None:
                if parameter == "PRECTOTCORR" and value < 0:
                    raise ValueError("Negative precipitation in a validated snapshot")
                buckets[key][parameter].append(value)

    months = []
    for key, count in expected.items():
        temps = buckets[key]["T2M"]
        rain = buckets[key]["PRECTOTCORR"]
        months.append({
            "month": key,
            "days_expected": count,
            "temperature_valid_days": len(temps),
            "precipitation_valid_days": len(rain),
            "temperature_mean_c": round(sum(temps) / count, 3) if len(temps) == count else None,
            "precipitation_total_mm": round(sum(rain), 3) if len(rain) == count else None,
        })
    return {
        "schema_version": "boponx-monthly/v1",
        "location_id": snapshot["location_id"],
        "period": period,
        "snapshot_id": snapshot["evidence"]["snapshot_id"],
        "provider": snapshot["evidence"]["provider"],
        "source_products": snapshot["evidence"].get("source_products", []),
        "source_request_url": snapshot["evidence"]["source_request_url"],
        "resolution_note": "NASA POWER gridded regional context; not measurements at an individual farm.",
        "scenario_note": "Historical records only. Not a future forecast or a crop-suitability model.",
        "metrics": months,
    }
