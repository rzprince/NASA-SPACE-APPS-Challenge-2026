"""API tests use synthetic fixtures only; no test value is represented as NASA data."""
import json

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def snapshot(*, origin="nasa_power_https"):
    return {
        "schema_version": "power-pilot/v1",
        "location_id": "rajshahi-pilot",
        "summary": {"temperature_mean_valid_days": 25, "coverage": {}},
        "daily": [{"date": "2024-01-01", "T2M": 25, "PRECTOTCORR": 1}],
        "evidence": {
            "provider": "NASA POWER",
            "ingestion_origin": origin,
            "source_request_url": "https://power.larc.nasa.gov/api/temporal/daily/point?TEST_FIXTURE_ONLY=1",
            "snapshot_id": "synthetic-unit-test-only",
        },
    }


def write_snapshot(tmp_path, data):
    out = tmp_path / "processed" / "power_rajshahi-pilot_20240101_20241231.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(data))


def farmer(**overrides):
    data = {
        "latitude": 24.37,
        "longitude": 88.60,
        "previous_crop": None,
        "previous_crops": [],
        "intended_crop": None,
        "water_source": "unknown",
        "water_after_heavy_rain": "unknown",
        "soil_test": "unknown",
        "soil_ph": None,
        "priority": "water",
    }
    data.update(overrides)
    return data


def test_health_and_area_reference_list(monkeypatch, tmp_path):
    monkeypatch.setenv("BOPONX_DATA_ROOT", str(tmp_path))
    health = client.get("/api/v1/health").json()
    assert health["pinned_power_snapshot_ready"] is False
    assert health["location_context_ready"] is True
    response = client.get("/api/v1/areas")
    assert response.status_code == 200
    ids = {area["id"] for area in response.json()["areas"]}
    assert {"rajshahi", "khulna", "rangpur", "barishal"} <= ids


def test_missing_pinned_data_is_not_fabricated(monkeypatch, tmp_path):
    monkeypatch.setenv("BOPONX_DATA_ROOT", str(tmp_path))
    response = client.get("/api/v1/climate/rajshahi-pilot")
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "DATASET_UNAVAILABLE"


def test_unverified_pinned_origin_is_rejected(monkeypatch, tmp_path):
    monkeypatch.setenv("BOPONX_DATA_ROOT", str(tmp_path))
    write_snapshot(tmp_path, snapshot(origin="local_input_unverified"))
    assert client.get("/api/v1/health").json()["pinned_power_snapshot_ready"] is False


def test_verified_pinned_origin_contract(monkeypatch, tmp_path):
    monkeypatch.setenv("BOPONX_DATA_ROOT", str(tmp_path))
    write_snapshot(tmp_path, snapshot())
    assert client.get("/api/v1/health").json()["pinned_power_snapshot_ready"] is True
    assert client.get("/api/v1/climate/rajshahi-pilot").json()["evidence"]["snapshot_id"] == "synthetic-unit-test-only"


def test_location_context_changes_by_selected_place():
    rajshahi = client.get("/api/v1/context?lat=24.37&lon=88.60").json()
    khulna = client.get("/api/v1/context?lat=22.84&lon=89.54").json()
    assert rajshahi["nearest_supported_region"]["id"] == "rajshahi"
    assert khulna["nearest_supported_region"]["id"] == "khulna"
    assert rajshahi["privacy"]["coordinates_persisted"] is False


def test_farmer_can_continue_without_soil_ph():
    response = client.post("/api/v1/farms/validate", json=farmer())
    assert response.status_code == 200
    content = response.json()
    assert content["profile"]["soil_ph"] is None
    assert "soil_test" in content["unknowns"]
    assert content["status"] == "FARM_CONTEXT_RECORDED"


def test_ph_is_only_accepted_with_explicit_soil_test():
    response = client.post("/api/v1/farms/validate", json=farmer(soil_test="no", soil_ph=6.5))
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "SOIL_TEST_REQUIRED"

    response = client.post("/api/v1/farms/validate", json=farmer(soil_test="yes", soil_ph=6.5))
    assert response.status_code == 200


def test_global_farmer_context_is_accepted_and_local_gap_is_explicit():
    response = client.post(
        "/api/v1/farms/validate",
        json=farmer(
            latitude=35.0,
            longitude=90.0,
            country_code="cn",
            country_name="China",
            place_name="Global test field",
        ),
    )
    assert response.status_code == 200
    content = response.json()
    assert content["context"]["coverage"]["environmental_context"] == "global_nasa_stack_available"
    assert content["context"]["coverage"]["local_agricultural_evidence"] == "official_adapter_not_onboarded"


def test_no_crop_or_rotation_claim_without_rules():
    assert client.get("/api/v1/crops").json()["crops"] == []
    response = client.post("/api/v1/rotations/compare", json=farmer())
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "AGRONOMIC_RULES_NOT_APPROVED"



def test_90_day_plan_is_fast_deterministic_and_has_three_distinct_stages():
    payload = {
        "farm": farmer(
            previous_crop="rice",
            water_source="rainfed",
            water_after_heavy_rain="sometimes",
            soil_test="no",
            priority="water",
        ),
        "start_year": 2026,
        "start_month": 9,
        "include_recent_power": False,
        "include_climate_baseline": False,
    }
    response = client.post("/api/v1/plans/preview", json=payload)
    assert response.status_code == 200

    brief = response.json()
    assert brief["status"] == "DECISION_PREPARATION_READY"
    assert len(brief["months"]) == 3
    assert [month["phase"]["en"] for month in brief["months"]] == [
        "Know the field",
        "Watch the change",
        "Decide the next move",
    ]

    task_sets = [
        {task["code"] for task in month["tasks"]}
        for month in brief["months"]
    ]
    assert task_sets[0].isdisjoint(task_sets[1])
    assert task_sets[1].isdisjoint(task_sets[2])
    assert brief["recent_environment"] is None
    assert brief["historical_baseline"] is None


def test_90_day_plan_changes_month_two_with_farmer_priority():
    def plan_for(priority):
        response = client.post(
            "/api/v1/plans/preview",
            json={
                "farm": farmer(priority=priority),
                "start_year": 2026,
                "start_month": 9,
                "include_recent_power": False,
                "include_climate_baseline": False,
            },
        )
        assert response.status_code == 200
        return {task["code"] for task in response.json()["months"][1]["tasks"]}

    water = plan_for("water")
    soil = plan_for("soil")
    stability = plan_for("production_stability")

    assert "water_priority_check" in water
    assert "soil_priority_check" in soil
    assert "stability_priority_check" in stability
    assert water != soil != stability



def test_farmer_profile_accepts_crop_history_and_intention():
    response = client.post(
        "/api/v1/farms/validate",
        json=farmer(
            previous_crop="rice",
            previous_crops=["rice", "mustard"],
            intended_crop="wheat",
        ),
    )
    assert response.status_code == 200
    profile = response.json()["profile"]
    assert profile["previous_crops"] == ["rice", "mustard"]
    assert profile["intended_crop"] == "wheat"


def test_plan_advice_uses_region_and_intended_crop_calendar_evidence():
    response = client.post(
        "/api/v1/plans/preview",
        json={
            "farm": farmer(
                previous_crop="rice",
                previous_crops=["rice", "mustard"],
                intended_crop="wheat",
                water_source="irrigated",
                water_after_heavy_rain="drains",
                soil_test="no",
                priority="production_stability",
            ),
            "start_year": 2026,
            "start_month": 11,
            "include_recent_power": False,
            "include_climate_baseline": False,
        },
    )
    assert response.status_code == 200
    advice = response.json()["decision_advice"]
    assert advice["status"] == "REASONABLE_TO_EXPLORE"
    assert advice["regional_calendar_match"] is True
    assert "Wheat" in advice["verdict"]


def test_plan_uses_weather_signal_for_water_risk():
    recent = {
        "status": "available",
        "summary": {
            "days_requested": 14,
            "temperature_valid_days": 14,
            "precipitation_valid_days": 14,
            "temperature_mean_c": 28.0,
            "precipitation_total_mm": 140.0,
        },
    }
    baseline_window = {
        "status": "available",
        "summaries": [
            {"calendar_month": 9, "temperature_mean_c": 27.0, "precipitation_mean_daily_mm": 5.0},
            {"calendar_month": 10, "temperature_mean_c": 26.0, "precipitation_mean_daily_mm": 4.0},
            {"calendar_month": 11, "temperature_mean_c": 23.0, "precipitation_mean_daily_mm": 1.0},
        ],
    }
    response = client.post(
        "/api/v1/plans/preview",
        json={
            "farm": farmer(
                intended_crop="rice",
                water_source="rainfed",
                water_after_heavy_rain="stays",
                soil_test="no",
                priority="water",
            ),
            "start_year": 2026,
            "start_month": 9,
            "include_recent_power": False,
            "include_climate_baseline": False,
            "recent_environment": recent,
            "baseline_window": baseline_window,
        },
    )
    assert response.status_code == 200
    brief = response.json()
    assert brief["conditions"]["rain_signal"] == "wetter_than_baseline"
    assert brief["decision_advice"]["status"] == "REVIEW_WATER_RISK_FIRST"
    assert brief["months"][0]["context"]["baseline"]["calendar_month"] == 9
    assert brief["months"][1]["context"]["baseline"]["calendar_month"] == 10
    assert brief["months"][2]["context"]["baseline"]["calendar_month"] == 11


def test_each_month_has_location_specific_climate_task():
    baseline_window = {
        "status": "available",
        "summaries": [
            {"calendar_month": 1, "temperature_mean_c": 18.0, "precipitation_mean_daily_mm": 0.5},
            {"calendar_month": 2, "temperature_mean_c": 21.0, "precipitation_mean_daily_mm": 1.0},
            {"calendar_month": 3, "temperature_mean_c": 25.0, "precipitation_mean_daily_mm": 2.0},
        ],
    }
    response = client.post(
        "/api/v1/plans/preview",
        json={
            "farm": farmer(intended_crop="mustard", priority="soil"),
            "start_year": 2027,
            "start_month": 1,
            "include_recent_power": False,
            "include_climate_baseline": False,
            "baseline_window": baseline_window,
        },
    )
    assert response.status_code == 200
    months = response.json()["months"]
    climate_tasks = [month["tasks"][0]["en"] for month in months]
    assert "January" in climate_tasks[0]
    assert "February" in climate_tasks[1]
    assert "March" in climate_tasks[2]
    assert len(set(climate_tasks)) == 3



def test_nasa_catalog_exposes_cohesive_observation_stack():
    response = client.get("/api/v1/nasa/catalog")
    assert response.status_code == 200
    sources = response.json()["sources"]
    ids = {source["id"] for source in sources}
    assert {
        "gpm-imerg-early-v07b",
        "smap-spl3smp-e-v6",
        "nasa-power-data-v10",
        "modis-terra-ndvi-8day",
        "modis-terra-lst-day",
        "hls-vegetation-indices-v2",
        "ecostress-esi-v2",
    } <= ids


def test_verified_local_source_registry_and_unknown_country_gap():
    us = client.get("/api/v1/local-sources?country_code=us&country_name=United%20States")
    assert us.status_code == 200
    assert us.json()["coverage"] == "official_sources_indexed"
    assert any(item["name"] == "Web Soil Survey" for item in us.json()["sources"])

    unknown = client.get("/api/v1/local-sources?country_code=zz&country_name=Testland")
    assert unknown.status_code == 200
    assert unknown.json()["coverage"] == "official_adapter_not_onboarded"
    assert unknown.json()["sources"] == []


def test_global_plan_remains_evidence_bounded_without_local_crop_rules():
    response = client.post(
        "/api/v1/plans/preview",
        json={
            "farm": farmer(
                latitude=40.0,
                longitude=-100.0,
                country_code="us",
                country_name="United States",
                place_name="Test field",
                intended_crop="wheat",
            ),
            "start_year": 2026,
            "start_month": 10,
            "include_recent_power": False,
            "include_climate_baseline": False,
        },
    )
    assert response.status_code == 200
    brief = response.json()
    assert brief["location"]["region_id"] == "us"
    assert brief["decision_advice"]["regional_calendar_match"] is False
    assert brief["rotation_explorer"]["status"] == "EVIDENCE_REVIEW_REQUIRED"
