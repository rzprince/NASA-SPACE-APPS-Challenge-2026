"""Initial BoponX API: truthful about which NASA data is available."""
from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException

app = FastAPI(title="BoponX API", version="0.1.0")
ROOT = Path(__file__).resolve().parents[2]
LOCATION = {
    "id": "rajshahi-pilot",
    "name": "Rajshahi regional pilot (provisional)",
    "latitude": 24.37,
    "longitude": 88.60,
    "location_note": "Illustrative regional reference point; not a surveyed farm.",
}
SNAPSHOT_NAME = "power_rajshahi-pilot_20240101_20241231.json"


def snapshot_path() -> Path:
    configured = os.getenv("BOPONX_DATA_ROOT")
    data_root = Path(configured) if configured else ROOT / "data"
    return data_root / "processed" / SNAPSHOT_NAME


@app.get("/api/v1/health")
def health() -> dict:
    path = snapshot_path()
    return {"status": "ok", "version": app.version, "climate_snapshot_ready": path.is_file()}


@app.get("/api/v1/locations")
def locations() -> dict:
    return {"locations": [LOCATION], "coverage": "regional pilot only"}


@app.get("/api/v1/climate/{location_id}")
def climate(location_id: str) -> dict:
    if location_id != LOCATION["id"]:
        raise HTTPException(status_code=404, detail={"code": "UNSUPPORTED_LOCATION"})
    path = snapshot_path()
    if not path.is_file():
        raise HTTPException(
            status_code=503,
            detail={"code": "DATASET_UNAVAILABLE", "message": "Run the NASA POWER acquisition command first; no fabricated climate values are served."},
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schema_version") != "power-pilot/v1":
            raise ValueError("Unsupported snapshot schema")
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=503, detail={"code": "DATASET_UNAVAILABLE", "message": "Prepared snapshot failed validation."}) from exc
    return data
