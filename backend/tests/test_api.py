"""All API fixtures are synthetic test data; no NASA observations are bundled."""
import json

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def snapshot(*, origin="nasa_power_https"):
    """Test the trust-gate contract with an intentionally fabricated fixture."""
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


def test_health_and_locations(monkeypatch, tmp_path):
    monkeypatch.setenv("BOPONX_DATA_ROOT", str(tmp_path))
    assert client.get("/api/v1/health").json()["climate_snapshot_ready"] is False
    response = client.get("/api/v1/locations")
    assert response.status_code == 200
    assert response.json()["locations"][0]["id"] == "rajshahi-pilot"


def test_missing_data_is_not_fabricated(monkeypatch, tmp_path):
    monkeypatch.setenv("BOPONX_DATA_ROOT", str(tmp_path))
    response = client.get("/api/v1/climate/rajshahi-pilot")
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "DATASET_UNAVAILABLE"
    assert client.get("/api/v1/climate/unknown").status_code == 404


def test_unverified_local_input_is_rejected(monkeypatch, tmp_path):
    monkeypatch.setenv("BOPONX_DATA_ROOT", str(tmp_path))
    write_snapshot(tmp_path, snapshot(origin="local_input_unverified"))
    assert client.get("/api/v1/health").json()["climate_snapshot_ready"] is False
    response = client.get("/api/v1/climate/rajshahi-pilot")
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "DATASET_UNAVAILABLE"


def test_verified_origin_marker_contract(monkeypatch, tmp_path):
    monkeypatch.setenv("BOPONX_DATA_ROOT", str(tmp_path))
    write_snapshot(tmp_path, snapshot())
    assert client.get("/api/v1/health").json()["climate_snapshot_ready"] is True
    data = client.get("/api/v1/climate/rajshahi-pilot").json()
    assert data["evidence"]["snapshot_id"] == "synthetic-unit-test-only"


def test_farm_validation_preserves_unknowns():
    response = client.post("/api/v1/farms/validate", json={
        "location_id": "rajshahi-pilot",
        "previous_crop": None,
        "soil_ph": None,
        "soil_texture": "unknown",
        "irrigation_mode": "unknown",
        "priorities": ["water"],
    })
    assert response.status_code == 200
    content = response.json()
    assert content["profile"]["soil_ph"] is None
    assert "soil_ph" in content["missing_inputs"]
    assert "priorities" not in content["missing_inputs"]
    assert content["status"] == "PROFILE_RECORDED_NOT_AGRONOMICALLY_VALIDATED"


def test_invalid_ph_and_unsupported_region():
    base = {"location_id": "rajshahi-pilot", "soil_ph": 20}
    assert client.post("/api/v1/farms/validate", json=base).status_code == 422
    base["soil_ph"] = 7
    base["location_id"] = "unsupported-region"
    assert client.post("/api/v1/farms/validate", json=base).status_code == 422


def test_no_crop_or_rotation_claim_without_rules():
    crops = client.get("/api/v1/crops").json()
    assert crops["crops"] == []
    response = client.post("/api/v1/rotations/compare", json={"location_id": "rajshahi-pilot"})
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "AGRONOMIC_RULES_NOT_APPROVED"


def test_monthly_api_respects_trusted_snapshot_and_coverage(monkeypatch, tmp_path):
    monkeypatch.setenv("BOPONX_DATA_ROOT", str(tmp_path))
    assert client.get("/api/v1/climate/rajshahi-pilot/monthly").status_code == 503
    data = snapshot()
    data["period"] = {"start": "2024-01-01", "end": "2024-01-02", "time_standard": "LST"}
    data["variables"] = {
        "T2M": {"provider_unit": "C"},
        "PRECTOTCORR": {"provider_unit": "mm/day"},
    }
    data["daily"] = [
        {"date": "2024-01-01", "T2M": 25, "PRECTOTCORR": 2},
        {"date": "2024-01-02", "T2M": 27, "PRECTOTCORR": 3},
    ]
    write_snapshot(tmp_path, data)
    response = client.get("/api/v1/climate/rajshahi-pilot/monthly")
    assert response.status_code == 200
    report = response.json()
    assert report["snapshot_id"] == "synthetic-unit-test-only"
    assert report["metrics"][0]["temperature_mean_c"] == 26
    assert report["metrics"][0]["precipitation_total_mm"] == 5
    assert client.get("/api/v1/climate/not-supported/monthly").status_code == 404
