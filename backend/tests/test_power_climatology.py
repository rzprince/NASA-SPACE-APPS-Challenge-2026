from backend.app.services.power_live import summarize_climatology_payload


def test_climatology_summary_uses_selected_calendar_month():
    payload = {
        "properties": {
            "parameter": {
                "T2M": {"JAN": 18.25, "SEP": 28.4},
                "PRECTOTCORR": {"JAN": 0.9, "SEP": 7.25},
            }
        }
    }
    result = summarize_climatology_payload(payload, 9)
    assert result["calendar_month"] == 9
    assert result["temperature_mean_c"] == 28.4
    assert result["precipitation_mean_daily_mm"] == 7.25


def test_climatology_missing_values_stay_missing():
    payload = {
        "properties": {
            "parameter": {
                "T2M": {"JAN": -999.0},
                "PRECTOTCORR": {},
            }
        }
    }
    result = summarize_climatology_payload(payload, 1)
    assert result["temperature_mean_c"] is None
    assert result["precipitation_mean_daily_mm"] is None
