"""The 90-day plan is stage-aware and remains non-prescriptive."""
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)

FARM = {
    "latitude": 24.37,
    "longitude": 88.60,
    "previous_crop": "rice",
    "water_source": "rainfed",
    "water_after_heavy_rain": "sometimes",
    "soil_test": "no",
    "soil_ph": None,
    "priority": "water",
}


def test_preview_endpoint_has_three_distinct_months_without_network():
    response = client.post("/api/v1/plans/preview", json={
        "farm": FARM,
        "start_year": 2026,
        "start_month": 11,
        "include_recent_power": False,
    })
    assert response.status_code == 200
    data = response.json()
    assert [m["planning_month"] for m in data["months"]] == ["2026-11", "2026-12", "2027-01"]
    assert len({m["phase"]["en"] for m in data["months"]}) == 3

    code_sets = [{task["code"] for task in month["tasks"]} for month in data["months"]]
    assert code_sets[0].isdisjoint(code_sets[1])
    assert code_sets[1].isdisjoint(code_sets[2])
    assert code_sets[0].isdisjoint(code_sets[2])

    assert data["rotation_explorer"]["status"] == "EVIDENCE_REVIEW_REQUIRED"
    assert data["farmer_context"]["soil_ph"] is None


def test_preview_changes_priority_specific_month_two_task():
    soil_farm = {**FARM, "priority": "soil"}
    water = client.post("/api/v1/plans/preview", json={
        "farm": FARM, "start_year": 2026, "start_month": 9, "include_recent_power": False,
    }).json()
    soil = client.post("/api/v1/plans/preview", json={
        "farm": soil_farm, "start_year": 2026, "start_month": 9, "include_recent_power": False,
    }).json()
    water_codes = {task["code"] for task in water["months"][1]["tasks"]}
    soil_codes = {task["code"] for task in soil["months"][1]["tasks"]}
    assert "water_priority_check" in water_codes
    assert "soil_priority_check" in soil_codes
    assert water_codes != soil_codes


def test_preview_invalid_window_is_rejected():
    response = client.post("/api/v1/plans/preview", json={
        "farm": FARM, "start_year": 2025, "start_month": 13, "include_recent_power": False,
    })
    assert response.status_code == 422
