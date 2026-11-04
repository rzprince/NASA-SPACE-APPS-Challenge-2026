"""Unit tests for Challenge 07 ('Field Shift') onset detection, GDD, Mann-Whitney U test,
±5 mm threshold sensitivity check, <160-character SMS advisory, and GET /advisory endpoint.
"""
from fastapi.testclient import TestClient

from backend.app.compute.agro import (
    ONSET_DEFINITION_EN,
    build_planting_window_advisory,
    growing_degree_days,
    mann_whitney_u_test,
    onset_sensitivity_check,
    rain_onset,
)
from backend.app.main import app

client = TestClient(app)


def test_rain_onset_detects_first_valid_7day_window_without_dry_spell():
    # First burst at window index 2 has >=20mm (on day 8), but is followed by 7 dry days (0.0mm) -> rejected
    # Second burst reaches >=20mm in window starting at index 18 (day 24 = 22.0mm) AND has >1.0mm in next 7 days -> accepted
    daily_mm = [0.0] * 40
    daily_mm[8] = 22.0   # window [2..8] has 22.0mm, but days [9..15] are all 0.0mm -> rejected
    daily_mm[24] = 22.0  # window [18..24] has 22.0mm
    daily_mm[26] = 3.2   # > 1.0 mm within days [25..31] -> accepted at window start index 18

    onset_idx = rain_onset(daily_mm, window=7, threshold_mm=20.0, dry_spell_max=7)
    assert onset_idx == 18


def test_growing_degree_days_with_crop_specific_base():
    t_max = [32.0, 34.0, 36.0]
    t_min = [22.0, 24.0, 26.0]
    res_rice = growing_degree_days(t_max, t_min, base_temp_c=10.0, cap_temp_c=35.0)
    assert res_rice["days"] == 3
    assert res_rice["base_temp_c"] == 10.0
    assert res_rice["total_gdd_c_days"] > 50.0


def test_mann_whitney_u_test_detects_significant_shift():
    period_2001_2012 = [157, 160, 155, 162, 159, 164, 158, 161, 156, 163, 160, 159]
    period_2013_2025 = [x + 11 for x in period_2001_2012] + [171]
    mw = mann_whitney_u_test(period_2001_2012, period_2013_2025)
    assert mw["n_2001_2012"] == 12
    assert mw["n_2013_2025"] == 13
    assert mw["p_value"] < 0.001
    assert mw["significant_at_0_05"] is True


def test_rajshahi_aman_rice_killer_demo_and_sensitivity_check():
    advisory = build_planting_window_advisory("Rajshahi", "rice")
    assert advisory["status"] == "ADVISORY_READY"
    assert advisory["district"]["id"] == "rajshahi"
    assert advisory["crop"]["id"] == "rice"
    assert advisory["shift_days"] == 11
    assert "11 days later" in advisory["advisory_sentence"]["en"]
    assert "১১ দিন" in advisory["advisory_sentence"]["bn"]
    assert advisory["sms_advisory"]["char_count_en"] <= 160
    assert advisory["sms_advisory"]["char_count_bn"] <= 160
    assert advisory["assumptions"]["onset_definition_en"] == ONSET_DEFINITION_EN

    sens = advisory["sensitivity_check"]
    assert sens["is_stable"] is True
    thresh_vals = [t["threshold_mm"] for t in sens["thresholds"]]
    assert thresh_vals == [15.0, 20.0, 25.0]


def test_get_advisory_endpoint_supports_both_root_and_v1_paths():
    for path in ("/advisory?district=Rajshahi&crop=rice", "/api/v1/advisory?district=নওগাঁ&crop=mustard"):
        resp = client.get(path)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ADVISORY_READY"
        assert isinstance(data["shift_days"], int)
        assert len(data["distributions"]["period_2001_2012"]["onset_doy_values"]) == 12
        assert len(data["distributions"]["period_2013_2025"]["onset_doy_values"]) == 13
        assert data["sms_advisory"]["char_count_en"] <= 160
        assert data["sms_advisory"]["char_count_bn"] <= 160
        assert len(data["provenance"]["datasets"]) >= 4
