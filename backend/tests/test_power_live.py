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
