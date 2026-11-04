from backend.app.services.power_live import summarize_power_payload


def test_power_summary_requires_complete_precipitation_for_total():
    payload = {
        "properties": {
            "parameter": {
                "T2M": {"20260901": 30.0, "20260902": 32.0},
                "PRECTOTCORR": {"20260901": 5.0, "20260902": -999.0},
            }
        }
    }
    result = summarize_power_payload(payload)
    assert result["temperature_mean_c"] == 31.0
    assert result["temperature_valid_days"] == 2
    assert result["precipitation_valid_days"] == 1
    assert result["precipitation_total_mm"] is None


def test_power_summary_reports_complete_total():
    payload = {
        "properties": {
            "parameter": {
                "T2M": {"20260901": 30.0, "20260902": 32.0},
                "PRECTOTCORR": {"20260901": 5.0, "20260902": 7.5},
            }
        }
    }
    result = summarize_power_payload(payload)
    assert result["precipitation_total_mm"] == 12.5


def test_power_summary_computes_fao56_et0_water_balance_vpd_and_stress_days():
    payload = {
        "properties": {
            "parameter": {
                "T2M": {"20260401": 30.0, "20260402": 31.0},
                "T2M_MAX": {"20260401": 36.2, "20260402": 34.0},
                "T2M_MIN": {"20260401": 22.0, "20260402": 23.0},
                "PRECTOTCORR": {"20260401": 0.0, "20260402": 2.0},
                "RH2M": {"20260401": 55.0, "20260402": 60.0},
                "WS2M": {"20260401": 2.5, "20260402": 3.0},
            }
        }
    }
    result = summarize_power_payload(payload, lat=24.37)
    assert result["et0_mean_daily_mm"] is not None and result["et0_mean_daily_mm"] > 3.0
    assert result["water_balance_daily_mm"] is not None and result["water_balance_daily_mm"] < 0
    assert result["vpd_mean_kpa"] is not None and result["vpd_mean_kpa"] > 1.0
    assert result["heat_stress_days"] == 1
    assert result["cold_stress_days"] == 0
    assert result["dry_days"] == 1
