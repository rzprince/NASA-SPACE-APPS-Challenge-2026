"""Historical monthly aggregation tests use synthetic payloads, never NASA measurements."""
from copy import deepcopy

import pytest

from backend.app.compute.monthly import aggregate_monthly


@pytest.fixture
def sample():
    return {
        "location_id": "rajshahi-pilot",
        "period": {"start": "2024-02-28", "end": "2024-03-01", "time_standard": "LST"},
        "variables": {
            "T2M": {"provider_unit": "C"},
            "PRECTOTCORR": {"provider_unit": "mm/day"},
        },
        "daily": [
            {"date": "2024-02-28", "T2M": 28, "PRECTOTCORR": 2.5},
            {"date": "2024-02-29", "T2M": 30, "PRECTOTCORR": 0.5},
            {"date": "2024-03-01", "T2M": 32, "PRECTOTCORR": 4.5},
        ],
        "evidence": {
            "snapshot_id": "SYNTHETIC_TEST",
            "provider": "TEST_ONLY",
            "source_products": ["TEST_ONLY"],
            "source_request_url": "https://example.invalid/SYNTHETIC_TEST",
        },
    }


def test_february_leap_day_and_partial_march(sample):
    out = aggregate_monthly(sample)
    assert out["schema_version"] == "boponx-monthly/v1"
    assert out["snapshot_id"] == "SYNTHETIC_TEST"
    assert [row["days_expected"] for row in out["metrics"]] == [2, 1]
    assert out["metrics"][0]["temperature_mean_c"] == 29
    assert out["metrics"][0]["precipitation_total_mm"] == 3
    assert out["metrics"][1]["temperature_mean_c"] == 32


def test_one_missing_day_suppresses_monthly_total_and_mean(sample):
    edited = deepcopy(sample)
    edited["daily"][1]["T2M"] = None
    edited["daily"][1]["PRECTOTCORR"] = None
    out = aggregate_monthly(edited)["metrics"][0]
    assert out["temperature_mean_c"] is None
    assert out["precipitation_total_mm"] is None
    assert out["temperature_valid_days"] == 1


def test_missing_date_in_series_suppresses_aggregate(sample):
    edited = deepcopy(sample)
    edited["daily"].pop(1)
    out = aggregate_monthly(edited)["metrics"][0]
    assert out["days_expected"] == 2
    assert out["temperature_mean_c"] is None
    assert out["precipitation_valid_days"] == 1


def test_duplicate_date_fails_closed(sample):
    edited = deepcopy(sample)
    edited["daily"].append(dict(edited["daily"][0]))
    with pytest.raises(ValueError, match="duplicated"):
        aggregate_monthly(edited)


def test_wrong_unit_fails_closed(sample):
    edited = deepcopy(sample)
    edited["variables"]["T2M"]["provider_unit"] = "K"
    with pytest.raises(ValueError, match="Unsupported"):
        aggregate_monthly(edited)


def test_negative_precipitation_fails_closed(sample):
    edited = deepcopy(sample)
    edited["daily"][0]["PRECTOTCORR"] = -1
    with pytest.raises(ValueError, match="Negative"):
        aggregate_monthly(edited)
