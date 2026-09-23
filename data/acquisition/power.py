"""Retrieve and validate NASA POWER daily data without manufacturing missing values."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
PARAMETERS = ("T2M", "PRECTOTCORR")
ROOT = Path(__file__).resolve().parents[2]


def date_key(raw: str) -> date:
    try:
        if len(raw) != 8 or not raw.isdigit():
            raise ValueError("Invalid format")
        return datetime.strptime(raw, "%Y%m%d").date()
    except ValueError as exc:
        raise ValueError("Dates must use valid YYYYMMDD values") from exc


def make_url(latitude: float, longitude: float, start: str, end: str) -> str:
    if not (math.isfinite(latitude) and -90 <= latitude <= 90):
        raise ValueError("Latitude must be finite and between -90 and 90")
    if not (math.isfinite(longitude) and -180 <= longitude <= 180):
        raise ValueError("Longitude must be finite and between -180 and 180")
    if date_key(start) > date_key(end):
        raise ValueError("Start must be on or before end")
    args = {
        "parameters": ",".join(PARAMETERS), "community": "AG",
        "latitude": latitude, "longitude": longitude,
        "start": start, "end": end, "format": "JSON", "time-standard": "LST",
    }
    return API_URL + "?" + urlencode(args)


def numeric_or_none(value: object, fill: float) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(result) or result == fill:
        return None
    return result


def process_power(payload: dict, *, url: str, location: str, start: str,
                  end: str, raw_sha256: str, ingestion_origin: str) -> dict:
    """Turn one real-format POWER response into a provenance-rich pilot snapshot.

    Synthetic inputs are allowed in tests but must be labeled by the caller.
    """
    if not isinstance(payload, dict):
        raise ValueError("NASA response is not a JSON object")
    header = payload.get("header")
    observations = payload.get("properties", {}).get("parameter")
    parameter_metadata = payload.get("parameters")
    if not isinstance(header, dict) or not isinstance(observations, dict):
        raise ValueError("Missing NASA POWER header or parameter time series")
    if not isinstance(parameter_metadata, dict):
        raise ValueError("NASA parameter units are missing; refusing to publish")
    for name in PARAMETERS:
        if not isinstance(observations.get(name), dict):
            raise ValueError(f"Missing parameter time series: {name}")
        if not isinstance(parameter_metadata.get(name), dict) or not parameter_metadata[name].get("units"):
            raise ValueError(f"Missing provider unit metadata: {name}")
    fill = float(header.get("fill_value", -999.0))
    start_day, end_day = date_key(start), date_key(end)
    records: list[dict] = []
    day = start_day
    while day <= end_day:
        key = day.strftime("%Y%m%d")
        item = {"date": day.isoformat()}
        for name in PARAMETERS:
            item[name] = numeric_or_none(observations[name].get(key), fill)
        if item["PRECTOTCORR"] is not None and item["PRECTOTCORR"] < 0:
            raise ValueError("Negative non-fill precipitation value")
        records.append(item)
        day += timedelta(days=1)
    expected = len(records)
    counts = {name: sum(row[name] is not None for row in records) for name in PARAMETERS}
    if any(count == 0 for count in counts.values()):
        raise ValueError("No valid values for at least one requested variable")
    temps = [row["T2M"] for row in records if row["T2M"] is not None]
    rain = [row["PRECTOTCORR"] for row in records if row["PRECTOTCORR"] is not None]
    summary = {
        "temperature_mean_valid_days": sum(temps) / len(temps),
        "precipitation_total_full_period": sum(rain) if len(rain) == expected else None,
        "precipitation_sum_valid_days": sum(rain),
        "coverage": {name: {"valid_days": count, "expected_days": expected,
                            "fraction": count / expected} for name, count in counts.items()},
    }
    return {
        "schema_version": "power-pilot/v1", "location_id": location,
        "period": {"start": start_day.isoformat(), "end": end_day.isoformat(), "time_standard": "LST"},
        "variables": {name: {"provider_unit": parameter_metadata[name]["units"],
                             "description": parameter_metadata[name].get("longname")} for name in PARAMETERS},
        "summary": summary, "daily": records,
        "evidence": {
            "provider": "NASA POWER", "product": header.get("title"),
            "api_version": header.get("api", {}).get("version") if isinstance(header.get("api"), dict) else header.get("api_version"),
            "source_products": header.get("sources", []),
            "source_request_url": url, "raw_sha256": raw_sha256,
            "snapshot_id": raw_sha256[:16],
            "source_geometry": payload.get("geometry"),
            "ingestion_origin": ingestion_origin,
            "data_kind": "historical regional context; not a farm measurement or forecast",
        },
    }


def acquire(args: argparse.Namespace) -> Path:
    url = make_url(args.latitude, args.longitude, args.start, args.end)
    root = Path(args.data_root)
    processed = root / "processed" / f"power_{args.location}_{args.start}_{args.end}.json"
    if processed.is_file() and not args.refresh and args.input is None:
        print(f"Reusing validated local snapshot: {processed}")
        return processed
    if args.input:
        raw = Path(args.input).read_bytes()
        origin = "local_input_unverified"
    else:
        request = Request(url, headers={"User-Agent": "BoponX/0.1 (NASA Space Apps project)"})
        with urlopen(request, timeout=45) as response:
            raw = response.read()
        origin = "nasa_power_https"
    sha = hashlib.sha256(raw).hexdigest()
    payload = json.loads(raw)
    result = process_power(payload, url=url, location=args.location, start=args.start,
                           end=args.end, raw_sha256=sha, ingestion_origin=origin)
    result["evidence"]["retrieved_at_utc"] = datetime.now(timezone.utc).isoformat()
    root.joinpath("raw").mkdir(parents=True, exist_ok=True)
    processed.parent.mkdir(parents=True, exist_ok=True)
    raw_dest = root / "raw" / f"power_{sha}.json"
    if not raw_dest.exists():
        raw_dest.write_bytes(raw)
    staging = processed.with_suffix(".json.tmp")
    staging.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    staging.replace(processed)
    print(f"Validated snapshot: {processed} ({len(result['daily'])} dates, source: {origin})")
    return processed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--location", default="rajshahi-pilot")
    parser.add_argument("--latitude", type=float, default=24.37)
    parser.add_argument("--longitude", type=float, default=88.60)
    parser.add_argument("--start", default="20240101")
    parser.add_argument("--end", default="20241231")
    parser.add_argument("--data-root", default=os.getenv("BOPONX_DATA_ROOT") or str(ROOT / "data"))
    parser.add_argument("--input", help="Process a local response; it remains labeled unverified until independently checked")
    parser.add_argument("--refresh", action="store_true", help="Deliberately fetch again instead of reusing processed cache")
    args = parser.parse_args()
    try:
        acquire(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(1, f"POWER pipeline failed: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
