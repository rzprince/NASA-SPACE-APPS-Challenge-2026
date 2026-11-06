"""Tests for the real-data planting-window engine.

All numeric expectations come from TEST-ONLY fixtures with a known truth (power_fixture.py); no
expected value is hard-coded into the production code path.
"""
from fastapi.testclient import TestClient

from backend.app.compute.agro import (
    ONSET_DEFINITION_EN,
    build_planting_window_advisory,
    growing_degree_days,
    mann_whitney_u_test,
    rain_onset,
    sms_segments,
)
from backend.app.main import app
from backend.tests.power_fixture import as_history, make_fixture_record

client = TestClient(app)


def test_rain_onset_detects_first_valid_7day_window_without_dry_spell():
    daily_mm = [0.0] * 40
    daily_mm[8] = 22.0   # window has 22 mm but 7 dry days follow -> rejected
    daily_mm[24] = 22.0  # accepted: >1 mm within the next 7 days
    daily_mm[26] = 3.2
    assert rain_onset(daily_mm, window=7, threshold_mm=20.0, dry_spell_max=7) == 18


def test_rain_onset_skips_windows_with_missing_days_instead_of_guessing():
    daily_mm: list = [0.0] * 40
    daily_mm[24] = 22.0
    daily_mm[26] = 3.2
    daily_mm[20] = None  # inside every candidate window that reaches day 24 from index 18..20
    first = rain_onset(daily_mm)
    assert first is None or first > 20  # the damaged candidates are skipped, never imputed


def test_growing_degree_days_with_crop_specific_base():
    res = growing_degree_days([32.0, 34.0, 36.0], [22.0, 24.0, 26.0], base_temp_c=10.0, cap_temp_c=35.0)
    assert res["days"] == 3 and res["base_temp_c"] == 10.0 and res["total_gdd_c_days"] > 50.0


def test_mann_whitney_matches_scipy():
    a = [157, 160, 155, 162, 159, 164, 158, 161, 156, 163, 160, 159]
    b = [168, 171, 166, 173, 170, 175, 169, 172, 167, 174, 171, 170, 172, 165]
    mine = mann_whitney_u_test(a, b)
    try:
        from scipy.stats import mannwhitneyu

        ref = mannwhitneyu(a, b, alternative="two-sided", use_continuity=False, method="asymptotic")
        ref_pvalue = float(ref.pvalue)
        ref_u = float(min(ref.statistic, len(a) * len(b) - ref.statistic))
    except ImportError:
        # Exact reference output of scipy.stats.mannwhitneyu(a, b, alternative="two-sided", use_continuity=False, method="asymptotic")
        ref_pvalue = 1.5309243074967312e-05
        ref_u = 0.0
    assert abs(mine["p_value"] - ref_pvalue) < 1e-4
    assert mine["u_statistic"] == ref_u


def test_advisory_recovers_a_known_shift_from_real_shaped_data():
    rec = make_fixture_record(shift_days=11, seed=11)
    adv = build_planting_window_advisory("Rajshahi", "rice", history=as_history(rec))
    assert adv["status"] == "ADVISORY_READY"
    assert adv["advisory_kind"] == "shift_applied"
    assert 7 <= adv["shift_days"] <= 15  # truth is 11 with +-4 days of yearly jitter
    assert adv["shift"]["reliable"] is True
    lo, hi = adv["shift"]["ci_95_days"]["low"], adv["shift"]["ci_95_days"]["high"]
    assert lo <= 11 <= hi + 3
    assert adv["recommended_window"]["en"] != adv["baseline_window"]["en"]
    assert adv["assumptions"]["onset_definition_en"] == ONSET_DEFINITION_EN
    assert adv["data_origin"] == "test_fixture"


def test_advisory_does_not_claim_a_shift_when_there_is_none():
    rec = make_fixture_record(shift_days=0, seed=3)
    adv = build_planting_window_advisory("Rajshahi", "rice", history=as_history(rec))
    assert adv["status"] == "ADVISORY_READY"
    assert adv["advisory_kind"] == "no_reliable_shift"
    assert adv["shift"]["applied_shift_days"] == 0
    assert adv["recommended_window"] == adv["baseline_window"]
    assert "no reliable shift" in adv["advisory_sentence"]["en"].lower()
    assert "no reliable rain-onset shift" in adv["sms_advisory"]["en"]


def test_rabi_crops_keep_the_bamis_window_even_when_onset_shifts():
    rec = make_fixture_record(shift_days=11, seed=11)
    adv = build_planting_window_advisory("Rajshahi", "rice", history=as_history(rec))
    adv = build_planting_window_advisory("Rajshahi", "wheat", history=as_history(rec))
    assert adv["advisory_kind"] == "context_only"
    assert adv["recommended_window"] == adv["baseline_window"]


def test_unavailable_data_is_reported_not_invented():
    adv = build_planting_window_advisory(
        "Rajshahi", "rice", history={"status": "unavailable", "reason": "offline_no_snapshot", "message": "none"}
    )
    assert adv["status"] == "UNAVAILABLE"
    assert adv["data_origin"] == "unavailable"
    for key in ("shift_days", "distributions", "sms_advisory", "mann_whitney_test", "recommended_window"):
        assert key not in adv


def test_too_few_valid_years_is_insufficient_not_guessed():
    rec = make_fixture_record(shift_days=5, seed=5, missing_rate=0.35)
    adv = build_planting_window_advisory("Rajshahi", "rice", history=as_history(rec))
    assert adv["status"] == "INSUFFICIENT_DATA"
    assert "shift_days" not in adv


def test_distributions_keep_year_alignment_and_period_labels():
    rec = make_fixture_record(shift_days=8, seed=2)
    adv = build_planting_window_advisory("Rajshahi", "rice", history=as_history(rec))
    early = adv["distributions"]["period_2001_2012"]
    late = adv["distributions"]["period_2013_2025"]  # legacy key, label carries the real range
    assert len(early["years"]) == len(early["onset_doy_values"])
    assert len(late["years"]) == len(late["onset_doy_values"])
    assert early["years"][0] == 2001 and late["label"].startswith("2013–")
    assert adv["trend"]["years_used"] >= 20
    assert adv["sensitivity_check"]["grid"], "sensitivity grid must be computed on the real series"
    assert adv["yearly_evidence"], "each onset must be traceable to the daily data"


def test_sms_segments_follow_real_encoding_rules():
    assert sms_segments("a" * 160) == {"encoding": "GSM-7", "length": 160, "segments": 1, "single_segment_limit": 160}
    assert sms_segments("a" * 161)["segments"] == 2
    assert sms_segments("a – b")["encoding"] == "UCS-2"  # an en dash silently switches encoding
    bn = sms_segments("রাজশাহী: আমন ধান রোপণ")
    assert bn["encoding"] == "UCS-2" and bn["single_segment_limit"] == 70
    assert sms_segments("ক" * 71)["segments"] == 2


def test_generated_sms_fit_one_segment_and_are_never_cut_mid_word():
    adv = build_planting_window_advisory("Rajshahi", "rice", history=as_history(make_fixture_record(shift_days=11, seed=11)))
    sms = adv["sms_advisory"]
    assert sms["segments_en"] == 1 and sms["encoding_en"] == "GSM-7"
    assert sms["segments_bn"] == 1 and sms["char_count_bn"] <= 70
    assert sms["en"].endswith("DAE 16123") and sms["bn"].endswith("১৬১২৩")


def test_advisory_endpoint_fails_closed_offline_without_snapshot(monkeypatch, tmp_path):
    from backend.app.services import power_history as ph

    monkeypatch.setenv("OFFLINE", "1")
    monkeypatch.setattr(ph, "SNAPSHOT_DIR", tmp_path)
    ph._CACHE.clear()
    for path in ("/advisory?district=Rajshahi&crop=rice", "/api/v1/advisory?district=নওগাঁ&crop=mustard"):
        res = client.get(path)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "UNAVAILABLE" and data["data_origin"] == "unavailable"
        assert "shift_days" not in data
