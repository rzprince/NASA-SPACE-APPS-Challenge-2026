"""Synthetic, offline integrity tests — no fixture is represented as NASA data."""
from __future__ import annotations

import hashlib
import json

import pytest

from data.acquisition.power import make_url, process_power
from scripts.verify_pilot import PILOT_FILE, verify_snapshot


def synthetic_pilot(tmp_path):
    raw = {
        "header": {
            "title": "SYNTHETIC TEST-ONLY POWER-SHAPED RESPONSE",
            "api": {"version": "TEST_ONLY"},
            "sources": ["TEST_ONLY"],
            "fill_value": -999.0,
            "time_standard": "LST",
        },
        "parameters": {
            "T2M": {"units": "C"},
            "PRECTOTCORR": {"units": "mm/day"},
        },
        "properties": {"parameter": {
            "T2M": {"20240101": 25.0, "20240102": 26.0},
            "PRECTOTCORR": {"20240101": 1.2, "20240102": 0.0},
        }},
        "geometry": {"type": "Point", "coordinates": [88.6, 24.37]},
    }
    raw_bytes = json.dumps(raw).encode("utf-8")
    digest = hashlib.sha256(raw_bytes).hexdigest()
    url = make_url(24.37, 88.6, "20240101", "20240102")
    processed = process_power(raw, url=url, location="rajshahi-pilot",
                              start="20240101", end="20240102",
                              raw_sha256=digest, ingestion_origin="nasa_power_https")
    (tmp_path / "raw").mkdir()
    (tmp_path / "processed").mkdir()
    raw_path = tmp_path / "raw" / f"power_{digest}.json"
    raw_path.write_bytes(raw_bytes)
    processed_path = tmp_path / "processed" / PILOT_FILE
    processed_path.write_text(json.dumps(processed), encoding="utf-8")
    return digest, raw_path, processed_path


def test_recalculates_values_from_original_bytes(tmp_path):
    digest, _, _ = synthetic_pilot(tmp_path)
    outcome = verify_snapshot(tmp_path, expected_sha=digest)
    assert outcome["verification"] == "PASS"
    assert outcome["coverage"]["T2M"]["valid_days"] == 2


def test_does_not_accept_wrong_pinned_snapshot(tmp_path):
    synthetic_pilot(tmp_path)
    with pytest.raises(ValueError, match="pinned"):
        verify_snapshot(tmp_path)


def test_does_not_accept_modified_raw_data(tmp_path):
    digest, raw_path, _ = synthetic_pilot(tmp_path)
    raw_path.write_bytes(raw_path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="SHA-256"):
        verify_snapshot(tmp_path, expected_sha=digest)


def test_does_not_accept_modified_processed_values(tmp_path):
    digest, _, processed_path = synthetic_pilot(tmp_path)
    result = json.loads(processed_path.read_text())
    result["daily"][0]["T2M"] = 999
    processed_path.write_text(json.dumps(result))
    with pytest.raises(ValueError, match="daily"):
        verify_snapshot(tmp_path, expected_sha=digest)
