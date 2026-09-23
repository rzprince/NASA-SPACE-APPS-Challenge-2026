"""Validate BoponX's pinned NASA POWER pilot snapshot against its original bytes.

This is an integrity/reproducibility check, not a claim that gridded data measure a
specific farm or that NASA endorses the BoponX project.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from data.acquisition.power import process_power

PINNED_PILOT_SHA256 = "512420f8cd947e21a84aa1e43292674be7e047fadfbcdd4ae4b3684647726495"
PILOT_FILE = "power_rajshahi-pilot_20240101_20241231.json"


def verify_snapshot(data_root: Path, expected_sha: str = PINNED_PILOT_SHA256) -> dict:
    processed_path = data_root / "processed" / PILOT_FILE
    processed = json.loads(processed_path.read_text(encoding="utf-8"))
    evidence = processed["evidence"]
    digest = evidence["raw_sha256"]
    if not isinstance(digest, str) or len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise ValueError("Invalid raw SHA-256 format")
    if digest != expected_sha:
        raise ValueError("This is not the pinned, independently tested pilot snapshot")
    original_bytes = (data_root / "raw" / f"power_{digest}.json").read_bytes()
    if hashlib.sha256(original_bytes).hexdigest() != digest:
        raise ValueError("Original NASA POWER bytes do not match the recorded SHA-256")
    original = json.loads(original_bytes)
    original_header = original["header"]
    if original_header.get("title") != evidence.get("product"):
        raise ValueError("Raw and processed source-product titles disagree")
    if original_header.get("sources") != evidence.get("source_products"):
        raise ValueError("Raw and processed source-product identifiers disagree")
    if original_header.get("time_standard") != processed["period"]["time_standard"]:
        raise ValueError("Daily time conventions disagree")
    if evidence.get("ingestion_origin") != "nasa_power_https" or evidence.get("provider") != "NASA POWER":
        raise ValueError("Data acquisition provenance was not confirmed")
    request = urlsplit(evidence["source_request_url"])
    if request.scheme != "https" or request.netloc != "power.larc.nasa.gov" or request.path != "/api/temporal/daily/point":
        raise ValueError("Unrecognized NASA POWER API origin")
    arguments = parse_qs(request.query)
    if arguments.get("parameters") != ["T2M,PRECTOTCORR"] or arguments.get("community") != ["AG"]:
        raise ValueError("Unexpected POWER parameter request")
    start = processed["period"]["start"].replace("-", "")
    end = processed["period"]["end"].replace("-", "")
    if arguments.get("start") != [start] or arguments.get("end") != [end]:
        raise ValueError("Raw request and processed historical period disagree")
    recalculated = process_power(
        original,
        url=evidence["source_request_url"],
        location="rajshahi-pilot",
        start=start,
        end=end,
        raw_sha256=digest,
        ingestion_origin="nasa_power_https",
    )
    for field in ("schema_version", "location_id", "period", "variables", "summary", "daily"):
        if processed[field] != recalculated[field]:
            raise ValueError(f"Processed {field} does not match the original NASA response")
    for field in ("provider", "product", "api_version", "source_products", "source_request_url",
                  "raw_sha256", "snapshot_id", "source_geometry", "ingestion_origin", "data_kind"):
        if evidence.get(field) != recalculated["evidence"].get(field):
            raise ValueError(f"Processed evidence field {field} differs from raw-source derivation")
    return {
        "verification": "PASS",
        "snapshot_id": evidence["snapshot_id"],
        "source_products": evidence["source_products"],
        "period": processed["period"],
        "coverage": processed["summary"]["coverage"],
        "raw_sha256": digest,
        "note": "Historical gridded regional context; not a crop-rotation or yield model.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path(__file__).resolve().parents[1] / "data")
    args = parser.parse_args()
    try:
        report = verify_snapshot(args.data_root)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        parser.exit(1, f"Pilot verification failed: {exc}\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
