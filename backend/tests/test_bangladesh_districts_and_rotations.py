"""Tests for 64-district Bangladesh local agronomy dataset, rotation scenario explorer, and bilingual plan parity."""
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_all_64_bangladesh_districts_and_8_divisions_are_indexed():
    response = client.get("/api/v1/bangladesh/districts")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 64
    assert len(payload["districts"]) == 64
    assert "SRDI" in payload["caution_en"]
    assert "SRDI" in payload["caution_bn"]
    assert payload["national_import_substitution_context"]["edible_oil_import_share_pct"] == 90

    division_counts = {
        "Rangpur": 8,
        "Rajshahi": 8,
        "Khulna": 10,
        "Barishal": 6,
        "Chattogram": 11,
        "Sylhet": 4,
        "Dhaka": 13,
        "Mymensingh": 4,
    }
    for division, expected in division_counts.items():
        div_resp = client.get(f"/api/v1/bangladesh/districts?division={division}")
        assert div_resp.status_code == 200
        assert div_resp.json()["count"] == expected


def test_bangladesh_resolve_works_offline_for_english_bangla_and_divisions():
    naogaon = client.get("/api/v1/bangladesh/resolve?q=নওগাঁ")
    assert naogaon.status_code == 200
    assert naogaon.json()["match"]["id"] == "naogaon"
    assert naogaon.json()["place"]["address"]["country_code"] == "bd"

    coxs = client.get("/api/v1/bangladesh/resolve?q=Cox's Bazar District")
    assert coxs.status_code == 200
    assert coxs.json()["match"]["id"] == "coxs-bazar"

    sylhet_div = client.get("/api/v1/bangladesh/resolve?q=Sylhet Division")
    assert sylhet_div.status_code == 200
    assert sylhet_div.json()["match"]["kind"] == "division"


def test_context_resolves_district_profile_online_evidence_and_scientific_glossary():
    # Naogaon coordinates
    naogaon_ctx = client.get("/api/v1/context?lat=24.7936&lon=88.9318").json()
    assert naogaon_ctx["within_bangladesh"] is True
    dp = naogaon_ctx["district_profile"]
    assert dp["id"] == "naogaon"
    assert "Dragon fruit" in dp["opportunity_crops_en"]
    evidence_ids = {item["id"] for item in dp["online_evidence"]}
    assert {"dragon-fruit-barind", "avocado-coffee-naogaon"} <= evidence_ids
    assert naogaon_ctx["multi_resolution_harmonization"]["layers"]
    assert len(naogaon_ctx["scientific_glossary"]) >= 5

    # Patuakhali coordinates
    patuakhali_ctx = client.get("/api/v1/context?lat=22.3596&lon=90.3298").json()
    p_dp = patuakhali_ctx["district_profile"]
    assert p_dp["id"] == "patuakhali"
    assert any(item["id"] == "red-mango-patuakhali" for item in p_dp["online_evidence"])


def test_rotation_explore_returns_three_explainable_strategies_including_existing_while_compare_stays_gated():
    farm = {
        "latitude": 24.3745,
        "longitude": 88.6042,
        "previous_crop": "rice",
        "previous_crops": ["rice", "mustard"],
        "intended_crop": "pulse",
        "water_source": "rainfed",
        "water_after_heavy_rain": "drains",
        "soil_test": "no",
        "soil_ph": None,
        "priority": "water",
    }
    explore_resp = client.post("/api/v1/rotations/explore", json=farm)
    assert explore_resp.status_code == 200
    bundle = explore_resp.json()
    assert bundle["ranking_approved"] is False
    scenarios = bundle["scenarios"]
    assert len(scenarios) == 3
    assert scenarios[0]["kind"] == "existing_baseline"
    assert scenarios[1]["kind"] == "soil_and_nitrogen"
    assert scenarios[2]["kind"] == "water_and_local_opportunity"
    for sc in scenarios:
        assert len(sc["crops_en"]) == 3
        assert len(sc["crops_bn"]) == 3
        assert sc["why_suggested_en"]
        assert sc["supporting_evidence"]
        assert sc["potential_benefits"]
        assert sc["information_gaps"]
        assert sc["local_review_risks"]

    # Confirm final prescriptive ranking endpoint remains fail-closed
    compare_resp = client.post("/api/v1/rotations/compare", json=farm)
    assert compare_resp.status_code == 409
    assert compare_resp.json()["detail"]["code"] == "AGRONOMIC_RULES_NOT_APPROVED"


def test_90_day_plan_has_distinct_english_and_bangla_translations_and_district_profile():
    response = client.post(
        "/api/v1/plans/preview",
        json={
            "farm": {
                "latitude": 24.3745,
                "longitude": 88.6042,
                "previous_crop": "rice",
                "previous_crops": ["rice", "wheat"],
                "intended_crop": "mustard",
                "water_source": "both",
                "water_after_heavy_rain": "drains",
                "soil_test": "yes",
                "soil_ph": 6.4,
                "priority": "soil",
            },
            "start_year": 2026,
            "start_month": 11,
            "include_recent_power": False,
            "include_climate_baseline": False,
        },
    )
    assert response.status_code == 200
    brief = response.json()
    assert brief["location"]["district_profile"]["id"] == "rajshahi"
    assert len(brief["rotation_explorer"]["scenarios"]) == 3
    for month in brief["months"]:
        assert month["month_name"]["en"] != month["month_name"]["bn"]
        assert month["phase"]["en"] != month["phase"]["bn"]
        assert month["objective"]["en"] != month["objective"]["bn"]
        for task in month["tasks"]:
            assert task["en"] != task["bn"]


def test_context_includes_functional_crop_roles_si_modeling_methods_and_eonet_source():
    ctx = client.get("/api/v1/context?lat=24.3745&lon=88.6042").json()
    roles = ctx.get("functional_crop_roles")
    assert isinstance(roles, list) and len(roles) == 4
    role_ids = {r["role_id"] for r in roles}
    assert {
        "nitrogen_fixing",
        "cover_crops",
        "deep_rooting",
        "drought_saline_tolerant",
    } == role_ids

    si_methods = ctx.get("si_modeling_methods")
    assert isinstance(si_methods, list) and len(si_methods) >= 3
    nasa_ids = {s["id"] for s in ctx["nasa_sources"]}
    assert "nasa-eonet-v3" in nasa_ids


def test_eonet_hazards_endpoint_and_equipment_market_forage_profile():
    from backend.app.services.eonet_live import summarize_eonet_payload

    sample_live_eonet = {
        "events": [
            {
                "id": "EONET_1234",
                "title": "Tropical Cyclone Bay of Bengal",
                "categories": [{"id": "severeStorms", "title": "Severe Storms"}],
                "sources": [{"id": "GDACS", "url": "https://www.gdacs.org/"}],
                "geometry": [{"date": "2026-11-01T00:00:00Z", "type": "Point", "coordinates": [89.5, 21.8]}],
            }
        ]
    }
    summarized = summarize_eonet_payload(sample_live_eonet, 24.3745, 88.6042, radius_km=1200.0)
    assert summarized["status"] == "available"
    assert summarized["provider"] == "NASA EONET v3"
    assert summarized["active_count"] == 1
    assert isinstance(summarized["events"], list) and len(summarized["events"]) == 1
    assert summarized["events"][0]["category_title"] == "Severe Storms"
    assert summarized["events"][0]["within_alert_radius"] is True

    hazards_resp = client.get("/api/v1/environment/hazards?lat=24.3745&lon=88.6042&radius_km=1200")
    assert hazards_resp.status_code == 200
    haz = hazards_resp.json()
    assert haz["provider"].startswith("NASA EONET v3")
    assert isinstance(haz["events"], list)
    assert "active_count" in haz
    assert "radius_km" in haz

    farm = {
        "latitude": 24.3745,
        "longitude": 88.6042,
        "previous_crop": "rice",
        "previous_crops": ["rice"],
        "intended_crop": "maize",
        "water_source": "both",
        "water_after_heavy_rain": "drains",
        "soil_test": "yes",
        "soil_ph": 6.6,
        "priority": "production_stability",
        "equipment_access": "conservation_zero_till",
        "market_preference": "forage_livestock",
    }
    explore_resp = client.post("/api/v1/rotations/explore", json=farm)
    assert explore_resp.status_code == 200
    scenarios = explore_resp.json()["scenarios"]
    assert any("Forage" in c for c in scenarios[2]["crops_en"])
