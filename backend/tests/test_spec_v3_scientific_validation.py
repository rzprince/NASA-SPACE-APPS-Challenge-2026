"""Comprehensive Scientific Validation & NASA Data Reliability Test Suite (Spec V3 & V3.1).

Covers:
1. Priority 1: Historical NASA POWER acquisition, validation statuses (complete, partial, unavailable, failed_validation),
   missing-value preservation (-999 -> None, never 0), 40-cell / 64-district coverage classification.
2. Priority 2 & V3.1 Fix 1: NASA GPM IMERG numerical cross-validation (Mean Bias, MAE, RMSE, Pearson r, sample count,
   comparison period) and non-imputing half-hourly aggregation across 48/48, 44/48, 43/48, and 0/48 intervals
   verified against manually calculated fixtures.
3. Priority 3: Verified Bangladesh SRDI / BARC / BARI / BRRI soil evidence classifications
   (VERIFIED, REFERENCE, ESTIMATED, FARMER_REPORTED, UNKNOWN) and crop suitability gates.
4. Priority 4: Centralized NASA data provenance and product-specific freshness classification
   (Fresh, Recently updated, Delayed, Cached, Partial, Unavailable, Validation failed).
5. Priority 5 & V3.1 Fix 3: Standardized 8-criterion crop-rotation evaluation framework with strict separation of
   `scientific_performance`, `evidence_completeness`, `local_suitability` (kept None/UNKNOWN when soil test is absent),
   and `critical_constraints` (ensuring missing measurements never improve a strategy's ranking).
6. Statistical edge cases: insufficient samples, constant observations, missing dates, and boundary ties.
7. End-to-End Coastal Bangladesh Farmer Scenario (Patuakhali: Rice -> Mustard, limited irrigation,
   unknown salinity, no soil test).
"""
from __future__ import annotations

from datetime import date, timedelta
from fastapi.testclient import TestClient

from backend.app.compute.agro import build_planting_window_advisory, mann_whitney_u_test
from backend.app.compute.onset_stats import (
    bootstrap_shift_ci,
    find_onset,
    hodges_lehmann_shift,
    mann_kendall,
    sen_slope,
)
from backend.app.compute.rotation_science import DOCUMENTED_CRITERIA_WEIGHTS, evaluate_strategy_scientifically
from backend.app.compute.soil_evidence import (
    EVIDENCE_CLASSIFICATIONS,
    build_soil_evidence_model,
    evaluate_crop_soil_suitability,
)
from backend.app.main import app
from backend.app.services import power_history as ph
from backend.app.services.imerg_check import (
    aggregate_half_hourly_imerg_to_daily,
    compare_imerg_and_power_series,
    convert_half_hourly_rates_to_daily_mm,
    get_imerg_crosscheck_status,
    imerg_grid_indices,
)
from backend.app.services.provenance import (
    FRESHNESS_STATUSES,
    build_centralized_provenance_registry,
    classify_eonet_freshness,
    classify_power_daily_freshness,
)
from backend.tests.power_fixture import as_history, make_fixture_record
from scripts.build_onset_results import build_onset_results

client = TestClient(app)


# ------------------------------------------------------------------
# 1. Historical NASA POWER Validation & 64-District Coverage Tests
# ------------------------------------------------------------------
def test_snapshot_validation_distinguishes_complete_partial_and_failed():
    full_rec = make_fixture_record(shift_days=6, seed=10)
    val_full = ph.validate_snapshot_record(full_rec)
    assert val_full["validation_status"] == "complete"
    assert val_full["valid"] is True
    assert val_full["min_coverage_fraction"] >= 0.95

    partial_rec = make_fixture_record(shift_days=6, seed=10, missing_rate=0.30)
    val_partial = ph.validate_snapshot_record(partial_rec)
    assert val_partial["validation_status"] == "partial"
    assert val_partial["valid"] is True

    bad_rec = make_fixture_record(shift_days=6, seed=10)
    bad_rec["series"]["PRECTOTCORR"][0] = -5.0
    val_bad = ph.validate_snapshot_record(bad_rec)
    assert val_bad["validation_status"] == "failed_validation"
    assert val_bad["valid"] is False

    assert ph.validate_snapshot_record(None)["validation_status"] == "unavailable"


def test_missing_observations_are_never_converted_to_zero():
    payload = {
        "header": {"fill_value": -999.0},
        "properties": {
            "parameter": {
                "PRECTOTCORR": {"20240601": -999.0, "20240602": 12.4},
                "T2M_MAX": {"20240601": -999.0, "20240602": 33.1},
                "T2M_MIN": {"20240601": -999.0, "20240602": 25.2},
            }
        },
    }
    parsed = ph.parse_power_response(payload, start=date(2024, 6, 1), end=date(2024, 6, 2))
    assert parsed["PRECTOTCORR"][0] is None, "Missing rainfall must remain None, never 0.0"
    assert parsed["T2M_MAX"][0] is None
    assert parsed["T2M_MIN"][0] is None
    assert parsed["PRECTOTCORR"][1] == 12.4


def test_all_64_districts_have_explicit_coverage_classification_across_40_cells(monkeypatch):
    monkeypatch.setenv("OFFLINE", "1")
    summary = build_onset_results()
    assert summary["districts_total"] == 64
    assert summary["cells_total"] == 40
    assert len(summary["districts"]) == 64
    allowed_cats = {"verified_complete", "partial_evidence", "insufficient_spatial_coverage", "unavailable"}
    for did, entry in summary["districts"].items():
        cov = entry.get("coverage")
        assert isinstance(cov, dict), f"Missing coverage block for {did}"
        assert cov["coverage_category"] in allowed_cats
        assert isinstance(cov["centroid_to_cell_center_km"], float)


# ------------------------------------------------------------------
# 2. NASA GPM IMERG Numerical Cross-Validation & V3.1 Half-Hourly Tests
# ------------------------------------------------------------------
def test_imerg_numerical_cross_validation_metrics_and_date_matching():
    imerg_map = {
        "2026-07-01": 14.0,
        "2026-07-02": 28.0,
        "2026-07-03": 0.0,
        "2026-07-04": 42.0,
        "2026-07-05": None,
    }
    power_map = {
        "2026-07-01": 10.0,
        "2026-07-02": 24.0,
        "2026-07-03": 2.0,
        "2026-07-04": 36.0,
        "2026-07-05": 15.0,
    }
    res = compare_imerg_and_power_series(imerg_map, power_map)
    assert res["status"] == "compared"
    assert res["sample_count"] == 4
    assert res["paired_days"] == 4
    assert res["comparison_period"] == {"start_date": "2026-07-01", "end_date": "2026-07-04"}
    assert res["bias_mm_per_day"] == 3.0
    assert res["mae_mm_per_day"] == 4.0
    assert res["rmse_mm_per_day"] is not None and res["rmse_mm_per_day"] > 0
    assert res["pearson_r"] is not None and res["pearson_r"] > 0.95
    assert "0.1°" in res["spatial_aggregation_method"]


def test_imerg_half_hourly_48_of_48_complete_coverage():
    rates_48 = [2.0] * 48
    agg_48 = aggregate_half_hourly_imerg_to_daily(rates_48)
    assert agg_48["valid_intervals"] == 48
    assert agg_48["missing_intervals"] == 0
    assert agg_48["coverage_pct"] == 100.0
    assert agg_48["coverage_status"] == "complete"
    assert agg_48["full_day_valid"] is True
    assert agg_48["imputation_applied"] is False
    assert agg_48["observed_accumulation_mm"] == 48.0
    assert agg_48["daily_total_mm"] == 48.0
    assert convert_half_hourly_rates_to_daily_mm(rates_48) == 48.0


def test_imerg_half_hourly_44_of_48_partial_incomplete_never_imputes():
    rates_44 = [2.0] * 44 + [None] * 4
    agg_44 = aggregate_half_hourly_imerg_to_daily(rates_44)
    assert agg_44["valid_intervals"] == 44
    assert agg_44["missing_intervals"] == 4
    assert agg_44["missing_interval_indices"] == [44, 45, 46, 47]
    assert agg_44["coverage_pct"] == 91.67
    assert agg_44["coverage_status"] == "partial_incomplete"
    assert agg_44["full_day_valid"] is False
    assert agg_44["imputation_applied"] is False
    assert agg_44["observed_accumulation_mm"] == 44.0  # 44 * 2.0 * 0.5 = 44.0 mm, never scaled to 48.0!
    assert agg_44["daily_total_mm"] is None
    assert convert_half_hourly_rates_to_daily_mm(rates_44) is None


def test_imerg_half_hourly_43_of_48_insufficient_coverage_never_imputes():
    rates_43 = [2.0] * 43 + [None] * 5
    agg_43 = aggregate_half_hourly_imerg_to_daily(rates_43)
    assert agg_43["valid_intervals"] == 43
    assert agg_43["missing_intervals"] == 5
    assert agg_43["coverage_pct"] == 89.58
    assert agg_43["coverage_status"] == "insufficient_coverage"
    assert agg_43["full_day_valid"] is False
    assert agg_43["imputation_applied"] is False
    assert agg_43["observed_accumulation_mm"] == 43.0  # 43 * 2.0 * 0.5 = 43.0 mm
    assert agg_43["daily_total_mm"] is None
    assert convert_half_hourly_rates_to_daily_mm(rates_43) is None


def test_imerg_half_hourly_0_of_48_completely_missing():
    rates_0 = [None] * 48
    agg_0 = aggregate_half_hourly_imerg_to_daily(rates_0)
    assert agg_0["valid_intervals"] == 0
    assert agg_0["missing_intervals"] == 48
    assert agg_0["coverage_pct"] == 0.0
    assert agg_0["coverage_status"] == "missing"
    assert agg_0["full_day_valid"] is False
    assert agg_0["imputation_applied"] is False
    assert agg_0["observed_accumulation_mm"] is None
    assert agg_0["daily_total_mm"] is None
    assert convert_half_hourly_rates_to_daily_mm(rates_0) is None
    idx = imerg_grid_indices(22.3596, 90.3298)
    assert 0 <= idx["lat_index"] < 1800 and 0 <= idx["lon_index"] < 3600


def test_imerg_endpoint_and_fallback_without_token(monkeypatch):
    monkeypatch.delenv("NASA_EARTHDATA_TOKEN", raising=False)
    resp = client.get("/api/v1/validation/imerg?lat=22.3596&lon=90.3298")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "skipped_no_token"
    assert body["mode"] == "visual_gibs_layer_only"
    assert "NASA_EARTHDATA_TOKEN" in body["why_unavailable"]
    assert "bias_mm_per_day" not in body


# ------------------------------------------------------------------
# 3. Verified Bangladesh Soil Evidence & Suitability Gate Tests
# ------------------------------------------------------------------
def test_soil_evidence_classifications_and_false_precision_guard():
    coastal_ctx = client.get("/api/v1/context?lat=22.3596&lon=90.3298").json()  # Patuakhali
    soil = coastal_ctx["soil_evidence"]
    assert soil["status"] == "bangladesh_srdi_barc_reference_integrated"
    assert "AEZ-13" in soil["aez_id"]
    assert soil["parcel_lab_verified"] is False

    by_id = {r["property_id"]: r for r in soil["records"]}
    assert by_id["soil_ph"]["evidence_classification"] == "REFERENCE"
    assert by_id["soil_ph"]["reported_value"] is None
    assert by_id["salinity_ec_ds_m"]["evidence_classification"] == "REFERENCE"
    assert by_id["salinity_ec_ds_m"]["reference_range"]["max"] >= 8.0
    assert by_id["parcel_npk_nutrients"]["evidence_classification"] == "UNKNOWN"
    for r in soil["records"]:
        assert r["evidence_classification"] in EVIDENCE_CLASSIFICATIONS


def test_soil_suitability_flags_waterlogging_and_farmer_ph():
    coastal_ctx = client.get("/api/v1/context?lat=22.3596&lon=90.3298").json()
    soil_model = build_soil_evidence_model(
        coastal_ctx["district_profile"], soil_test="yes", farmer_soil_ph=4.6, farmer_drainage="stays"
    )
    suit = evaluate_crop_soil_suitability(
        "mustard", soil_model, water_source="rainfed", drainage="stays", soil_test="yes", farmer_ph=4.6
    )
    assert suit["suitability_status"] == "FLAGGED_CONSTRAINT_VIOLATION"
    assert suit["unconditional_recommendation_allowed"] is False
    assert len(suit["constraints_violated"]) >= 2


# ------------------------------------------------------------------
# 4. Data Freshness & Centralized Provenance Tests
# ------------------------------------------------------------------
def test_freshness_classifications_use_product_specific_latency():
    f_recent = classify_power_daily_freshness(
        status="available", data_origin="nasa_power_live", observation_end="2026-10-30", today=date(2026, 11, 6)
    )
    assert f_recent["freshness_status"] == "Recently updated"
    assert f_recent["is_live_realtime"] is False
    assert f_recent["latency_days"] == 7

    f_snap = classify_power_daily_freshness(
        status="available", data_origin="nasa_power_snapshot", observation_end="2026-10-30", today=date(2026, 11, 6)
    )
    assert f_snap["freshness_status"] == "Cached"

    f_unavail = classify_power_daily_freshness(status="unavailable", data_origin="unavailable", observation_end=None)
    assert f_unavail["freshness_status"] == "Unavailable"

    f_eonet = classify_eonet_freshness(
        status="available", data_origin="nasa_eonet_live", retrieved_at="2026-11-06T12:00:00Z", cache_age_sec=5.0
    )
    assert f_eonet["freshness_status"] == "Fresh"

    reg = build_centralized_provenance_registry(24.3745, 88.6042)
    assert len(reg["datasets"]) == 6
    for ds in reg["datasets"]:
        assert ds["freshness_status"] in FRESHNESS_STATUSES


# ------------------------------------------------------------------
# 5. Statistical Edge Cases (Ties, Constant Series, Insufficient Samples)
# ------------------------------------------------------------------
def test_statistical_edge_cases_constant_series_and_ties():
    const_a = [140] * 10
    const_b = [140] * 10
    mw = mann_whitney_u_test(const_a, const_b)
    assert mw["p_value"] == 1.0 and mw["significant_at_0_05"] is False
    assert hodges_lehmann_shift(const_a, const_b) == 0.0
    assert sen_slope(list(range(2001, 2021)), [140] * 20) == 0.0
    mk = mann_kendall([140] * 20)
    assert mk["s"] == 0 and mk["significant_at_0_05"] is False

    early_tied = [121, 121, 121, 121, 121, 121, 128, 130, 132, 134, 135, 136]
    late_tied = [121, 121, 121, 121, 121, 121, 121, 121, 121, 121, 122, 123]
    ci = bootstrap_shift_ci(early_tied, late_tied, n_boot=300)
    assert ci["low"] <= 0.0 <= ci["high"]

    assert find_onset([None, 10.0, 10.0, 5.0, 0.0, 0.0, 0.0, 2.0, 0.0, 0.0]) is None


# ------------------------------------------------------------------
# 6. Standardized 8-Criterion Rotation Engine & V3.1 Uncertainty Separation Tests
# ------------------------------------------------------------------
def test_rotation_scoring_separates_performance_completeness_suitability_and_constraints():
    assert abs(sum(DOCUMENTED_CRITERIA_WEIGHTS.values()) - 1.0) < 1e-9
    ctx = client.get("/api/v1/context?lat=24.3745&lon=88.6042").json()
    soil_no_test = build_soil_evidence_model(ctx["district_profile"], soil_test="no", farmer_soil_ph=None, farmer_drainage="drains")
    soil_with_test = build_soil_evidence_model(ctx["district_profile"], soil_test="yes", farmer_soil_ph=6.5, farmer_drainage="drains")

    eval_unknown_soil = evaluate_strategy_scientifically(
        "B",
        ["Rice Aman", "Mustard / Lentil (Pulse)", "Green Gram (Mungbean) / Aus"],
        profile={
            "latitude": 24.3745,
            "longitude": 88.6042,
            "water_source": "both",
            "water_after_heavy_rain": "drains",
            "soil_test": "no",
            "soil_ph": None,
            "priority": "soil",
        },
        context=ctx,
        condition={"et0_daily_mm": 3.8, "recent_daily_rain_mm": 1.2},
        soil_model=soil_no_test,
    )
    eval_verified_soil = evaluate_strategy_scientifically(
        "B",
        ["Rice Aman", "Mustard / Lentil (Pulse)", "Green Gram (Mungbean) / Aus"],
        profile={
            "latitude": 24.3745,
            "longitude": 88.6042,
            "water_source": "both",
            "water_after_heavy_rain": "drains",
            "soil_test": "yes",
            "soil_ph": 6.5,
            "priority": "soil",
        },
        context=ctx,
        condition={"et0_daily_mm": 3.8, "recent_daily_rain_mm": 1.2},
        soil_model=soil_with_test,
    )

    assert eval_unknown_soil["criteria"]["local_suitability"]["score_0_100"] is None
    assert eval_unknown_soil["criteria_scores_0_100"]["local_suitability"] is None
    assert eval_unknown_soil["local_suitability_summary"]["status"] == "UNVERIFIED_MISSING_SOIL_TEST"
    assert "parcel_laboratory_soil_ph_verified" in eval_unknown_soil["evidence_completeness"]["unknown_dimensions"]

    assert eval_verified_soil["criteria"]["local_suitability"]["score_0_100"] is not None
    assert eval_verified_soil["evidence_completeness"]["completeness_pct"] > eval_unknown_soil["evidence_completeness"]["completeness_pct"]

    eval_b_waterlogged = evaluate_strategy_scientifically(
        "B",
        ["Rice Aman", "Mustard / Lentil (Pulse)", "Green Gram (Mungbean) / Aus"],
        profile={
            "latitude": 24.3745,
            "longitude": 88.6042,
            "water_source": "both",
            "water_after_heavy_rain": "stays",
            "soil_test": "no",
            "soil_ph": None,
            "priority": "soil",
        },
        context=ctx,
        condition={"et0_daily_mm": 3.8, "recent_daily_rain_mm": 1.2},
        soil_model=soil_no_test,
    )
    assert eval_b_waterlogged["critical_constraint_violated"] is True
    assert eval_b_waterlogged["critical_constraints"]["critical_constraint_violated"] is True
    assert eval_b_waterlogged["recommendation_gate"] == "FLAGGED_CONSTRAINT_VIOLATION"
    assert any("standing water" in f for f in eval_b_waterlogged["constraint_flags"])


# ------------------------------------------------------------------
# 7. End-to-End Coastal Bangladesh Farmer Scenario (Section 7.D)
# ------------------------------------------------------------------
def test_e2e_coastal_bangladesh_farmer_scenario_patuakhali():
    lat, lon = 22.3596, 90.3298
    rec = make_fixture_record(shift_days=9, seed=22)
    adv = build_planting_window_advisory("Patuakhali", "mustard", lat=lat, lon=lon, history=as_history(rec))

    resp = client.post(
        "/api/v1/plans/preview",
        json={
            "farm": {
                "latitude": lat,
                "longitude": lon,
                "previous_crop": "rice",
                "previous_crops": ["rice"],
                "intended_crop": "mustard",
                "water_source": "rainfed",
                "water_after_heavy_rain": "sometimes",
                "soil_test": "no",
                "soil_ph": None,
                "priority": "water",
            },
            "start_year": 2026,
            "start_month": 11,
            "start_day": 1,
            "include_recent_power": False,
            "include_climate_baseline": False,
            "recent_environment": {
                "status": "available",
                "data_origin": "nasa_power_live",
                "retrieved_at": "2026-11-06T12:00:00Z",
                "data_through": (date.today() - timedelta(days=5)).isoformat(),
                "summary": {
                    "days_requested": 14,
                    "temperature_valid_days": 14,
                    "precipitation_valid_days": 14,
                    "temperature_mean_c": 26.2,
                    "precipitation_total_mm": 8.4,
                    "et0_mean_daily_mm": 3.9,
                    "water_balance_daily_mm": -3.3,
                    "surface_soil_wetness_pct": 62.0,
                    "root_zone_soil_wetness_pct": 74.0,
                },
            },
            "advisory": adv,
        },
    )
    assert resp.status_code == 200
    plan = resp.json()

    assert plan["data_status"] == "AVAILABLE"
    assert plan["nasa_provenance"]["datasets"][0]["freshness_status"] in ("Recently updated", "Fresh", "Cached")
    assert len(plan["watch_list"]) >= 3

    soil_ev = plan["soil_evidence"]
    assert "AEZ-13" in soil_ev["aez_id"]
    assert soil_ev["overall_classification"] == "REFERENCE_ONLY_PARCEL_UNKNOWN"

    assert adv["advisory_kind"] == "context_only"
    assert plan["window_guidance"]["bamis_baseline_window"]["en"] == "20 Oct – 15 Nov"

    scenarios = plan["rotation_explorer"]["scenarios"]
    assert len(scenarios) == 3
    for sc in scenarios:
        se = sc.get("scientific_evaluation")
        assert isinstance(se, dict)
        assert "scientific_performance" in se
        assert "evidence_completeness" in se
        assert "local_suitability_summary" in se
        assert "critical_constraints" in se
        assert se["criteria"]["local_suitability"]["score_0_100"] is None

    suit = plan["intended_crop_suitability"]
    assert suit["suitability_status"] == "CONDITIONAL_VERIFICATION_REQUIRED"
    assert suit["unconditional_recommendation_allowed"] is False
    assert any("salinity" in w.lower() for w in suit["soil_and_salinity_warnings"])
    assert any("soil test" in m.lower() for m in suit["missing_evidence"])

    assert len(plan["months"]) == 3
    for m in plan["months"]:
        assert len(m["tasks"]) >= 3
        for t in m["tasks"]:
            assert t["source"] and t["evidence_label"]
