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


def test_outside_bangladesh_is_rejected():
    response = client.post("/api/v1/farms/validate", json=farmer(latitude=35.0, longitude=90.0))
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "OUTSIDE_BANGLADESH_PILOT"


def test_no_crop_or_rotation_claim_without_rules():
    assert client.get("/api/v1/crops").json()["crops"] == []
    response = client.post("/api/v1/rotations/compare", json=farmer())
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "AGRONOMIC_RULES_NOT_APPROVED"
