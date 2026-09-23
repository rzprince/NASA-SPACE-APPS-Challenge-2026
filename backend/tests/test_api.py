import json

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


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


def test_prepared_snapshot_read(monkeypatch, tmp_path):
    monkeypatch.setenv("BOPONX_DATA_ROOT", str(tmp_path))
    out = tmp_path / "processed" / "power_rajshahi-pilot_20240101_20241231.json"
    out.parent.mkdir()
    out.write_text(json.dumps({"schema_version": "power-pilot/v1", "evidence": {
        "ingestion_origin": "synthetic_test"}, "summary": {"temperature_mean_valid_days": 25}}))
    assert client.get("/api/v1/health").json()["climate_snapshot_ready"] is True
    data = client.get("/api/v1/climate/rajshahi-pilot").json()
    assert data["evidence"]["ingestion_origin"] == "synthetic_test"
