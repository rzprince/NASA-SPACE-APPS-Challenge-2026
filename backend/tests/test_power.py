"""Synthetic test payloads: never farmer-facing or represented as NASA measurements."""
import hashlib
import json
from argparse import Namespace

import pytest

from data.acquisition.power import acquire, make_url, process_power


def payload():
    return {
        "header": {"title": "TEST ONLY — synthetic NASA-format payload", "fill_value": -999,
                   "sources": ["TEST"], "api": {"version": "synthetic"}},
        "parameters": {"T2M": {"units": "C"}, "PRECTOTCORR": {"units": "mm/day"}},
        "properties": {"parameter": {
            "T2M": {"20240101": 25.0, "20240102": -999.0, "20240103": 27.0},
            "PRECTOTCORR": {"20240101": 4.0, "20240102": 0.0, "20240103": 5.0},
        }},
        "geometry": {"type": "Point", "coordinates": [88.6, 24.37]},
    }


def transform(obj):
    return process_power(obj, url="https://power.larc.nasa.gov/TEST-ONLY", location="rajshahi-pilot",
                         start="20240101", end="20240103", raw_sha256="a" * 64,
                         ingestion_origin="synthetic_test")


def test_missing_values_are_not_imputed():
    result = transform(payload())
    assert result["daily"][1]["T2M"] is None
    assert result["summary"]["temperature_mean_valid_days"] == 26
    assert result["summary"]["coverage"]["T2M"]["valid_days"] == 2
    assert result["summary"]["precipitation_total_full_period"] == 9
    assert result["evidence"]["ingestion_origin"] == "synthetic_test"


def test_incomplete_precipitation_has_no_full_period_total():
    obj = payload()
    obj["properties"]["parameter"]["PRECTOTCORR"]["20240103"] = -999
    result = transform(obj)
    assert result["summary"]["precipitation_total_full_period"] is None
    assert result["summary"]["precipitation_sum_valid_days"] == 4


def test_missing_units_are_blocked():
    obj = payload()
    del obj["parameters"]["T2M"]["units"]
    with pytest.raises(ValueError, match="unit"):
        transform(obj)


def test_negative_precipitation_is_blocked():
    obj = payload()
    obj["properties"]["parameter"]["PRECTOTCORR"]["20240103"] = -1.0
    with pytest.raises(ValueError, match="Negative"):
        transform(obj)


def test_bad_coordinates_and_dates():
    with pytest.raises(ValueError, match="Latitude"):
        make_url(95, 88.6, "20240101", "20240103")
    with pytest.raises(ValueError, match="Start"):
        make_url(24.37, 88.6, "20240103", "20240101")
    assert "time-standard=LST" in make_url(24.37, 88.6, "20240101", "20240103")


def test_local_input_is_explicitly_unverified(tmp_path):
    obj = payload()
    source = tmp_path / "synthetic.json"
    raw = json.dumps(obj).encode()
    source.write_bytes(raw)
    args = Namespace(location="rajshahi-pilot", latitude=24.37, longitude=88.6,
                     start="20240101", end="20240103", data_root=str(tmp_path),
                     input=str(source), refresh=False)
    result = json.loads(acquire(args).read_text())
    assert result["evidence"]["raw_sha256"] == hashlib.sha256(raw).hexdigest()
    assert result["evidence"]["ingestion_origin"] == "local_input_unverified"
    assert (tmp_path / "raw" / f"power_{hashlib.sha256(raw).hexdigest()}.json").exists()
