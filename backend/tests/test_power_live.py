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



def test_power_summary_includes_agriculture_context_metrics():
    payload = {
        "properties": {
            "parameter": {
                "T2M": {"20260901": 30.0, "20260902": 32.0},
                "T2M_MAX": {"20260901": 35.0, "20260902": 37.0},
                "T2M_MIN": {"20260901": 25.0, "20260902": 27.0},
                "PRECTOTCORR": {"20260901": 5.0, "20260902": 7.5},
                "RH2M": {"20260901": 70.0, "20260902": 74.0},
                "WS2M": {"20260901": 2.0, "20260902": 4.0},
                "ALLSKY_SFC_SW_DWN": {"20260901": 5.0, "20260902": 6.0},
            }
        }
    }
    result = summarize_power_payload(payload)
    assert result["temperature_mean_c"] == 31.0
    assert result["temperature_max_mean_c"] == 36.0
    assert result["temperature_min_mean_c"] == 26.0
    assert result["relative_humidity_mean_pct"] == 72.0
    assert result["wind_speed_2m_mean_ms"] == 3.0
    assert result["solar_radiation_mean_kwh_m2_day"] == 5.5
