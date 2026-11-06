"""Tests for Spec v2 Phases 1, 2B, and 3 upgrades:
- Dry vs. wet NASA POWER inputs (GWETTOP, GWETROOT, P - ET0, rain_signal) produce different tasks
- Start-date changes (including leap-year 2028) shift all task and phase date ranges accurately
- Every task carries a non-empty `source`, valid `evidence_label`, `date_range`, and distinct EN/BN copy
- EN/BN structural parity across the 90-day plan
- EONET flood/storm vs. wildfire agricultural relevance (Item E)
- Window guidance only shows shifted window when shift is statistically reliable & monsoon-linked
- Seasonal water balance (2001-2012 vs 2013-latest, Item W)
- Optional IMERG cross-check adapter (Item G)
- Freshness & fail-closed data_origin across /context and /environment/* endpoints (Items L & Z)
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.compute.agro import ONSET_DEFINITION_BN, ONSET_DEFINITION_EN, build_planting_window_advisory
from backend.app.compute.context import build_context
from backend.app.compute.plan import make_90_day_plan
from backend.app.main import app
from backend.app.services.eonet_live import summarize_eonet_payload
from backend.app.services.imerg_check import compare_imerg_and_power_series, get_imerg_crosscheck_status
from backend.tests.power_fixture import as_history, make_fixture_record

client = TestClient(app)

ALLOWED_EVIDENCE_LABELS = {
    "observed_nasa",
    "derived_from_nasa",
    "official_local_reference",
    "rule_based",
    "preliminary_estimate",
}


def _base_farm(**over):
    f = {
        "latitude": 24.3745,
        "longitude": 88.6042,
        "previous_crop": "rice",
        "previous_crops": ["rice", "mustard"],
        "intended_crop": "rice",
        "water_source": "both",
        "water_after_heavy_rain": "drains",
        "soil_test": "no",
        "soil_ph": None,
        "priority": "water",
    }
    f.update(over)
    return f


def test_onset_definition_explicitly_names_may_1_and_missing_day_policy():
    assert "01 May" in ONSET_DEFINITION_EN
    assert "missing day" in ONSET_DEFINITION_EN and "never imputed" in ONSET_DEFINITION_EN
    assert "১ মে" in ONSET_DEFINITION_BN
    assert "অনুমান করা হয় না" in ONSET_DEFINITION_BN


def test_dry_vs_wet_nasa_thresholds_produce_different_tasks():
    ctx = build_context(24.3745, 88.6042)
    baseline_window = {
        "status": "available",
        "summaries": [
            {"calendar_month": 11, "temperature_mean_c": 23.0, "precipitation_mean_daily_mm": 2.0, "et0_mean_daily_mm": 3.5},
            {"calendar_month": 12, "temperature_mean_c": 19.5, "precipitation_mean_daily_mm": 0.5, "et0_mean_daily_mm": 2.8},
            {"calendar_month": 1, "temperature_mean_c": 18.0, "precipitation_mean_daily_mm": 0.4, "et0_mean_daily_mm": 2.6},
        ],
    }
    dry_recent = {
        "status": "available",
        "data_through": "2026-10-29",
        "summary": {
            "days_requested": 14,
            "temperature_valid_days": 14,
            "precipitation_valid_days": 14,
            "temperature_mean_c": 26.5,
            "precipitation_total_mm": 4.2,  # 0.3 mm/day -> drier_than_baseline
            "et0_mean_daily_mm": 4.2,
            "water_balance_daily_mm": -3.9,  # < -2.0 mm/day deficit
            "surface_soil_wetness_pct": 24.0,  # < 35% dry seedbed
            "root_zone_soil_wetness_pct": 31.0,  # < 40% root-zone deficit
        },
    }
    wet_recent = {
        "status": "available",
        "data_through": "2026-10-29",
        "summary": {
            "days_requested": 14,
            "temperature_valid_days": 14,
            "precipitation_valid_days": 14,
            "temperature_mean_c": 24.0,
            "precipitation_total_mm": 126.0,  # 9.0 mm/day -> wetter_than_baseline
            "et0_mean_daily_mm": 3.1,
            "water_balance_daily_mm": 5.9,  # > +3.0 mm/day surplus
            "surface_soil_wetness_pct": 88.0,  # > 80% saturated seedbed
            "root_zone_soil_wetness_pct": 84.0,
        },
    }

    dry_plan = make_90_day_plan(
        _base_farm(), ctx, start_year=2026, start_month=11,
        recent_environment=dry_recent, baseline_window=baseline_window,
    )
    wet_plan = make_90_day_plan(
        _base_farm(), ctx, start_year=2026, start_month=11,
        recent_environment=wet_recent, baseline_window=baseline_window,
    )

    dry_m1_codes = {t["code"] for t in dry_plan["months"][0]["tasks"]}
    wet_m1_codes = {t["code"] for t in wet_plan["months"][0]["tasks"]}
    dry_m2_codes = {t["code"] for t in dry_plan["months"][1]["tasks"]}
    wet_m2_codes = {t["code"] for t in wet_plan["months"][1]["tasks"]}

    assert "m1_gwettop_dry_seedbed" in dry_m1_codes
    assert "m1_recent_dry_signal" in dry_m1_codes
    assert "m1_gwettop_saturated_seedbed" in wet_m1_codes
    assert "m1_recent_wet_signal" in wet_m1_codes
    assert dry_m1_codes != wet_m1_codes

    assert "m2_gwetroot_deficit" in dry_m2_codes
    assert "m2_water_balance_deficit" in dry_m2_codes
    assert "m2_water_balance_surplus" in wet_m2_codes
    assert dry_m2_codes != wet_m2_codes


def test_start_date_changes_shift_all_dates_including_leap_year():
    ctx = build_context(24.3745, 88.6042)
    plan_a = make_90_day_plan(_base_farm(), ctx, start_year=2026, start_month=11, start_day=1)
    plan_b = make_90_day_plan(_base_farm(), ctx, start_year=2028, start_month=2, start_day=15)  # 2028 is a leap year

    assert plan_a["planner_header"]["plan_start_date"] == "2026-11-01"
    assert plan_b["planner_header"]["plan_start_date"] == "2028-02-15"
    # 2028-02-15 + 14 days = 2028-02-29 (leap day!)
    assert plan_b["months"][0]["date_range"]["start"] == "2028-02-15"
    assert plan_b["months"][0]["date_range"]["end"] == "2028-03-15"  # 30 days including Feb 29

    for m_a, m_b in zip(plan_a["months"], plan_b["months"]):
        assert m_a["date_range"]["start"] != m_b["date_range"]["start"]
        for t_a, t_b in zip(m_a["tasks"], m_b["tasks"]):
            assert t_a["date_range"]["start"] != t_b["date_range"]["start"]
            assert t_a["date_range"]["end"] != t_b["date_range"]["end"]


def test_every_task_has_source_valid_evidence_label_no_duplicates_and_en_bn_parity():
    ctx = build_context(24.3745, 88.6042)
    plan = make_90_day_plan(_base_farm(soil_test="yes", soil_ph=6.2), ctx, start_year=2026, start_month=11, start_day=5)

    assert len(plan["months"]) == 3
    all_codes: list[str] = []
    for m in plan["months"]:
        assert m["day_span"]["en"] and m["day_span"]["bn"] and m["day_span"]["en"] != m["day_span"]["bn"]
        assert m["date_range"]["en"] and m["date_range"]["bn"] and m["date_range"]["en"] != m["date_range"]["bn"]
        assert len(m["tasks"]) >= 3
        for t in m["tasks"]:
            all_codes.append(t["code"])
            assert t["en"].strip() and t["bn"].strip()
            assert t["en"] != t["bn"], f"Task {t['code']} must have distinct EN and BN text"
            assert t["reason"].strip() and t["reason_bn"].strip()
            assert t["reason"] != t["reason_bn"], f"Task {t['code']} must have distinct EN and BN reason"
            assert t["source"].strip(), f"Task {t['code']} missing source"
            assert t["evidence_label"] in ALLOWED_EVIDENCE_LABELS, f"Invalid label {t['evidence_label']}"
            assert t["date_range"]["start"] and t["date_range"]["end"]

    assert len(all_codes) == len(set(all_codes)), "Duplicate task codes found across the 90-day plan"
    assert plan["footer"]["verify_en"] == "Verify with DAE 16123"
    assert "১৬১২৩" in plan["footer"]["verify_bn"]


def test_eonet_flood_adds_rule_based_drainage_task_while_wildfire_does_not():
    ctx = build_context(24.3745, 88.6042)
    flood_payload = {
        "events": [
            {
                "id": "EONET_FLOOD_1",
                "title": "Brahmaputra River Basin Flood",
                "categories": [{"id": "floods", "title": "Floods"}],
                "sources": [{"id": "GDACS", "url": "https://www.gdacs.org/"}],
                "geometry": [{"date": "2026-08-10T00:00:00Z", "type": "Point", "coordinates": [89.2, 24.8]}],
            }
        ]
    }
    wildfire_payload = {
        "events": [
            {
                "id": "EONET_FIRE_1",
                "title": "Forest Wildfire Event",
                "categories": [{"id": "wildfires", "title": "Wildfires"}],
                "sources": [{"id": "FIRMS", "url": "https://firms.modaps.eosdis.nasa.gov/"}],
                "geometry": [{"date": "2026-08-10T00:00:00Z", "type": "Point", "coordinates": [89.2, 24.8]}],
            }
        ]
    }

    flood_haz = summarize_eonet_payload(flood_payload, 24.3745, 88.6042, radius_km=1200.0)
    fire_haz = summarize_eonet_payload(wildfire_payload, 24.3745, 88.6042, radius_km=1200.0)

    assert flood_haz["events"][0]["affects_field_operations"] is True
    assert flood_haz["agricultural_alert_count"] == 1
    assert fire_haz["events"][0]["affects_field_operations"] is False
    assert fire_haz["agricultural_alert_count"] == 0

    plan_with_flood = make_90_day_plan(_base_farm(), ctx, start_year=2026, start_month=8, eonet_hazards=flood_haz)
    plan_with_fire = make_90_day_plan(_base_farm(), ctx, start_year=2026, start_month=8, eonet_hazards=fire_haz)

    flood_m1_tasks = {t["code"]: t for t in plan_with_flood["months"][0]["tasks"]}
    fire_m1_codes = {t["code"] for t in plan_with_fire["months"][0]["tasks"]}

    assert "m1_eonet_hazard_check" in flood_m1_tasks
    assert flood_m1_tasks["m1_eonet_hazard_check"]["evidence_label"] == "rule_based"
    assert "DAE (16123)" in flood_m1_tasks["m1_eonet_hazard_check"]["en"]
    assert "m1_eonet_hazard_check" not in fire_m1_codes


def test_window_guidance_shows_shifted_window_only_when_reliable():
    ctx = build_context(24.3745, 88.6042)
    sig_adv = build_planting_window_advisory("Rajshahi", "rice", history=as_history(make_fixture_record(shift_days=11, seed=11)))
    nosig_adv = build_planting_window_advisory("Rajshahi", "rice", history=as_history(make_fixture_record(shift_days=0, seed=3)))

    plan_sig = make_90_day_plan(_base_farm(intended_crop="rice"), ctx, start_year=2026, start_month=7, advisory=sig_adv)
    plan_nosig = make_90_day_plan(_base_farm(intended_crop="rice"), ctx, start_year=2026, start_month=7, advisory=nosig_adv)

    assert plan_sig["window_guidance"]["shift_reliable"] is True
    assert plan_sig["window_guidance"]["shifted_window"] is not None
    assert plan_sig["window_guidance"]["shifted_window"]["en"] != plan_sig["window_guidance"]["bamis_baseline_window"]["en"]

    assert plan_nosig["window_guidance"]["shift_reliable"] is False
    assert plan_nosig["window_guidance"]["shifted_window"] is None


def test_seasonal_water_balance_is_computed_from_real_series():
    rec = make_fixture_record(shift_days=8, seed=9)
    adv = build_planting_window_advisory("Rajshahi", "rice", history=as_history(rec))
    swb = adv.get("seasonal_water_balance")
    assert isinstance(swb, dict)
    assert swb["kharif2_aman"]["status"] == "ok"
    assert swb["rabi"]["status"] == "ok"
    assert "water_balance_daily_mm" in swb["kharif2_aman"]["period_2013_latest"]
    assert "water_balance_daily_mm" in swb["rabi"]["period_2013_latest"]


def test_imerg_crosscheck_skips_cleanly_without_token_and_compares_series(monkeypatch):
    monkeypatch.delenv("NASA_EARTHDATA_TOKEN", raising=False)
    status = get_imerg_crosscheck_status(24.3745, 88.6042)
    assert status["status"] == "skipped_no_token"

    comp = compare_imerg_and_power_series([10.0, 20.0, 0.0, None], [8.0, 18.0, 2.0, 5.0])
    assert comp["status"] == "compared"
    assert comp["paired_days"] == 3
    assert comp["imerg_total_mm"] == 30.0
    assert comp["power_total_mm"] == 28.0


def test_environment_and_context_endpoints_include_data_origin_and_fail_closed_offline(monkeypatch):
    monkeypatch.setenv("OFFLINE", "1")
    ctx = client.get("/api/v1/context?lat=24.3745&lon=88.6042").json()
    assert ctx["data_origin"] == "static_verified_registry"
    assert "retrieved_at" in ctx and "lag_days" in ctx

    for path in (
        "/api/v1/environment/recent?lat=24.3745&lon=88.6042",
        "/api/v1/environment/baseline?lat=24.3745&lon=88.6042&month=11",
        "/api/v1/environment/baseline-window?lat=24.3745&lon=88.6042&start_month=11",
        "/api/v1/environment/hazards?lat=24.3745&lon=88.6042",
    ):
        resp = client.get(path)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "unavailable"
        assert body["data_origin"] == "unavailable"
        assert "retrieved_at" in body and "lag_days" in body
