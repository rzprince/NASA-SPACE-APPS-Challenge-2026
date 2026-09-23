"""The printable plan is a preparation checklist, never an unsourced crop plan."""
from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient

from backend.app.compute.monthly import aggregate_monthly
from backend.app.compute.plan import three_month_preview
from backend.app.main import app

client = TestClient(app)


def synthetic_history() -> dict:
    start = date(2024, 1, 1)
    end = date(2024, 12, 31)
    days = (end - start).days + 1
    return aggregate_monthly({
        "location_id": "rajshahi-pilot",
        "period": {"start": start.isoformat(), "end": end.isoformat(), "time_standard": "LST"},
        "variables": {
            "T2M": {"provider_unit": "C"},
            "PRECTOTCORR": {"provider_unit": "mm/day"},
        },
        "daily": [
            {"date": (start + timedelta(days=i)).isoformat(), "T2M": 25.0, "PRECTOTCORR": 1.0}
            for i in range(days)
        ],
        "evidence": {
            "provider": "TEST_ONLY; not NASA",
            "source_products": ["SYNTHETIC"],
            "snapshot_id": "TEST_SYNTHETIC_ONLY",
            "source_request_url": "https://example.invalid/synthetic",
        },
    })


FARM = {
    "location_id": "rajshahi-pilot",
    "previous_crop": None,
    "soil_ph": None,
    "soil_texture": "unknown",
    "irrigation_mode": "none",
    "priorities": ["water"],
}


def test_three_month_plan_is_not_fake_crop_or_forecast():
    out = three_month_preview(
        FARM, synthetic_history(), start_year=2026, start_month=11, candidate_crop="Aman rice"
    )
    assert out["status"] == "DRAFT_NOT_AN_AGRONOMIC_CROP_PLAN"
    assert [m["planning_month"] for m in out["months"]] == ["2026-11", "2026-12", "2027-01"]
    assert [m["historical_reference_month"] for m in out["months"]] == [
        "2024-11", "2024-12", "2024-01",
    ]
    assert out["farm"]["candidate_crop_farmer_entered"] == "Aman rice"
    assert out["months"][0]["historical_precipitation_mm"] == 30
    assert out["months"][1]["historical_precipitation_mm"] == 31
    assert all(t["code"] not in {"sow_crop", "choose_crop", "recommend_crop"} for m in out["months"] for t in m["tasks"])
    assert all("no_planting_dates" in [t["code"] for t in m["tasks"]] for m in out["months"])
    assert out["evidence"]["snapshot_id"] == "TEST_SYNTHETIC_ONLY"
    assert {"soil_ph", "previous_crop"} <= {x["field"] for x in out["farm"]["missing_inputs"]}


def test_unknown_historical_month_is_null_not_fabricated():
    history = synthetic_history()
    history["metrics"] = [r for r in history["metrics"] if r["month"] != "2024-11"]
    out = three_month_preview(
        FARM, history, start_year=2026, start_month=11, candidate_crop=None
    )
    assert out["months"][0]["historical_precipitation_mm"] is None
    assert out["months"][0]["historical_reference_month"] is None
    assert out["months"][1]["historical_precipitation_mm"] is not None
    assert out["farm"]["candidate_crop_farmer_entered"] is None


def test_invalid_location_and_version_fail():
    history = synthetic_history()
    modified = {**FARM, "location_id": "dhaka"}
    import pytest
    with pytest.raises(ValueError, match="Rajshahi"):
        three_month_preview(modified, history, start_year=2026, start_month=11, candidate_crop=None)
    modified_history = {**history, "schema_version": "fake-v1"}
    with pytest.raises(ValueError, match="version"):
        three_month_preview(FARM, modified_history, start_year=2026, start_month=11, candidate_crop=None)


def test_api_does_not_create_report_without_real_snapshot(monkeypatch, tmp_path):
    monkeypatch.setenv("BOPONX_DATA_ROOT", str(tmp_path))
    response = client.post("/api/v1/plans/preview", json={
        "farm": FARM, "start_year": 2026, "start_month": 11, "candidate_crop": None
    })
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "DATASET_UNAVAILABLE"


def test_known_farm_changes_tasks_and_does_not_autoselect_crop():
    known = {
        **FARM,
        "previous_crop": "Farmer-entered harvest",
        "soil_ph": 6.4,
        "soil_texture": "loamy",
        "irrigation_mode": "reliable",
        "priorities": ["soil"],
    }
    out = three_month_preview(
        known, synthetic_history(), start_year=2027, start_month=5, candidate_crop=None
    )
    codes = [task["code"] for task in out["months"][0]["tasks"]]
    assert "get_soil_test" not in codes
    assert "verify_previous_crop" not in codes
    assert "record_irrigation" in codes
    assert "soil_priority" in codes
    assert out["farm"]["candidate_crop_farmer_entered"] is None
    assert out["farm"]["missing_inputs"] == []
    assert all(month["historical_reference_month"].startswith("2024-") for month in out["months"])


def test_preview_endpoint_succeeds_only_with_integrity_checked_snapshot(monkeypatch):
    # Test data are synthetic; patch only the snapshot provider, not the compute path.
    import backend.app.main as main
    from datetime import date, timedelta
    start = date(2024, 1, 1)
    snap = {
        "schema_version": "power-pilot/v1",
        "location_id": "rajshahi-pilot",
        "period": {"start": "2024-01-01", "end": "2024-03-31", "time_standard": "LST"},
        "variables": {"T2M": {"provider_unit": "C"},
                      "PRECTOTCORR": {"provider_unit": "mm/day"}},
        "daily": [
            {"date": (start + timedelta(days=i)).isoformat(), "T2M": 25, "PRECTOTCORR": 1}
            for i in range(91)
        ],
        "evidence": {"provider": "TEST_ONLY", "source_products": ["SYNTHETIC"],
                     "snapshot_id": "TEST_SYNTHETIC_ONLY",
                     "source_request_url": "https://example.invalid/test"},
    }
    monkeypatch.setattr(main, "trusted_snapshot", lambda: snap)
    response = client.post("/api/v1/plans/preview", json={
        "farm": FARM, "start_year": 2026, "start_month": 1,
        "candidate_crop": None,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["months"][0]["historical_reference_month"] == "2024-01"
    assert data["months"][0]["historical_precipitation_mm"] == 31
    assert data["months"][1]["historical_precipitation_mm"] == 29
    assert data["months"][2]["historical_precipitation_mm"] == 31
    assert data["status"] == "DRAFT_NOT_AN_AGRONOMIC_CROP_PLAN"


def test_invalid_report_inputs_are_rejected():
    response = client.post("/api/v1/plans/preview", json={
        "farm": FARM, "start_year": 2025, "start_month": 13,
        "candidate_crop": "x" * 100,
    })
    assert response.status_code == 422
