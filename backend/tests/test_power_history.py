"""Loader, snapshot integrity and fail-closed behaviour."""
import json
from datetime import date

import pytest

from backend.app.services import power_history as ph
from backend.tests.power_fixture import make_fixture_record


def test_grid_cell_is_the_power_native_cell_and_is_shared_between_nearby_points():
    a = ph.grid_cell(24.37, 88.60)
    b = ph.grid_cell(24.30, 88.55)
    assert a["id"] == b["id"]
    assert a["resolution_deg"] == {"latitude": 0.5, "longitude": 0.625}
    assert ph.grid_cell(24.80, 88.60)["id"] != a["id"]


def test_parse_power_response_marks_fill_values_as_missing():
    payload = {
        "header": {"fill_value": -999.0},
        "properties": {"parameter": {
            "PRECTOTCORR": {"20240101": 1.5, "20240102": -999.0, "20240103": 0.0},
            "T2M_MAX": {"20240101": 20.0, "20240102": 21.0, "20240103": 22.0},
            "T2M_MIN": {"20240101": 10.0, "20240102": 11.0, "20240103": 12.0},
        }},
    }
    out = ph.parse_power_response(payload, start=date(2024, 1, 1), end=date(2024, 1, 3))
    assert out["PRECTOTCORR"] == [1.5, None, 0.0]


def test_parse_power_response_rejects_missing_variable():
    payload = {"properties": {"parameter": {"PRECTOTCORR": {}}}}
    with pytest.raises(ValueError):
        ph.parse_power_response(payload, start=date(2024, 1, 1), end=date(2024, 1, 2))


def test_snapshot_roundtrip_and_tamper_detection(tmp_path):
    rec = make_fixture_record(seed=1, end=date(2002, 6, 1))
    digest = ph.write_snapshot(rec, tmp_path)
    assert ph.read_snapshot(rec["cell"]["id"], tmp_path)["retrieved_at"] == rec["retrieved_at"]
    path = tmp_path / f"{rec['cell']['id']}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["series"]["PRECTOTCORR"][5] = 999.0
    path.write_text(json.dumps(data), encoding="utf-8")
    assert ph.read_snapshot(rec["cell"]["id"], tmp_path) is None, "a modified snapshot must be refused"
    assert len(digest) == 64


def test_load_history_offline_without_snapshot_is_unavailable(monkeypatch, tmp_path):
    monkeypatch.setenv("OFFLINE", "1")
    monkeypatch.setattr(ph, "SNAPSHOT_DIR", tmp_path)
    ph._CACHE.clear()
    out = ph.load_history(24.37, 88.60)
    assert out["status"] == "unavailable" and out["reason"] == "offline_no_snapshot"


def test_load_history_network_failure_is_unavailable_not_fabricated(monkeypatch, tmp_path):
    monkeypatch.delenv("OFFLINE", raising=False)
    monkeypatch.setattr(ph, "SNAPSHOT_DIR", tmp_path)
    ph._CACHE.clear()

    def boom(*a, **k):
        raise OSError("no route to host")

    monkeypatch.setattr(ph, "fetch_live", boom)
    out = ph.load_history(24.37, 88.60)
    assert out["status"] == "unavailable" and out["reason"] == "live_request_failed"
    assert "record" not in out


def test_load_history_prefers_verified_snapshot(monkeypatch, tmp_path):
    rec = make_fixture_record(seed=2, end=date(2002, 6, 1))
    ph.write_snapshot(rec, tmp_path)
    monkeypatch.setattr(ph, "SNAPSHOT_DIR", tmp_path)
    ph._CACHE.clear()
    out = ph.load_history(24.37, 88.60)
    assert out["status"] == "available" and out["data_origin"] == "nasa_power_snapshot"
