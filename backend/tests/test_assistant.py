from fastapi.testclient import TestClient

from backend.app.compute.assistant import route, suggestions
from backend.app.compute.bangladesh_districts import (
    DIVISION_COORDINATES,
    list_bangladesh_districts,
)
from backend.app.main import app

client = TestClient(app)


def test_compound_request_returns_actions_in_user_order():
    response = route(
        "Select Rajshahi, I grew rice last season, I want wheat, rainfed, generate my plan",
        "en",
    )

    assert [action["type"] for action in response["actions"]] == [
        "selectPlace",
        "addPreviousCrop",
        "setIntendedCrop",
        "setWaterSource",
        "runPlan",
    ]
    assert response["actions"][0]["payload"]["area"] == "Rajshahi"
    assert response["actions"][1]["payload"]["crop"] == "rice"
    assert response["actions"][2]["payload"]["crop"] == "wheat"


def test_banglish_is_understood_and_replied_to_in_bangla():
    response = route("amar jomite dhan chash korbo", "en")

    assert response["lang"] == "bn"
    assert response["actions"] == [
        {"type": "setIntendedCrop", "payload": {"crop": "rice"}}
    ]


def test_all_districts_and_divisions_can_be_selected():
    for district in list_bangladesh_districts():
        response = route(f"select {district['name_en']}", "en")
        assert response["actions"]
        assert response["actions"][0]["type"] == "selectPlace"
        assert response["actions"][0]["payload"]["area"] == district["name_en"]

    for division in DIVISION_COORDINATES.values():
        response = route(f"select {division['name_en']}", "en")
        assert response["actions"]
        assert response["actions"][0]["type"] == "selectPlace"


def test_bangla_location_names_resolve():
    district = next(item for item in list_bangladesh_districts() if item["name_en"] == "Rajshahi")
    response = route(f"{district['name_bn']} নির্বাচন করুন", "en")

    assert response["lang"] == "bn"
    assert response["actions"][0]["payload"]["area"] == "Rajshahi"


def test_soil_ph_requires_report_and_valid_range():
    missing_report = route("soil pH 6.5", "en", snapshot={"soilTest": "unknown"})
    assert not missing_report["actions"]
    assert missing_report["pending"] == "set_soil_ph"
    assert missing_report["choices"] == ["Yes", "No"]

    accepted_report = route("Yes", "en", history=[{"pending": "set_soil_ph"}])
    assert accepted_report["actions"][0]["payload"] == {"soil_test": "yes"}

    valid_ph = route("soil pH 6.5", "en", snapshot={"soilTest": "yes"})
    assert valid_ph["actions"][0]["payload"] == {"soil_ph": 6.5}

    invalid_ph = route("soil pH 15", "en", snapshot={"soilTest": "yes"})
    assert not invalid_ph["actions"]
    assert "0 and 14" in invalid_ph["reply"]
    assert invalid_ph["pending"] is None


def test_destructive_action_requires_follow_up_confirmation():
    request = route("reset the farm form", "en")
    assert request["actions"] == []
    assert request["pending"] == "reset_farm"
    assert request["choices"] == ["Yes", "No"]

    confirmed = route("Yes", "en", history=[{"pending": request["pending"]}])
    assert confirmed["actions"] == [
        {"type": "resetFarmForm", "payload": {"confirmed": True}}
    ]

    cancelled = route("No", "en", history=[{"pending": request["pending"]}])
    assert cancelled["actions"] == []
    assert "no changes" in cancelled["reply"].lower()


def test_follow_up_location_and_crop_choices_use_pending_context():
    location = route("Rajshahi", "en", history=[{"pending": "select_place"}])
    assert location["actions"][0]["type"] == "selectPlace"

    crop_prompt = route("I want to grow a crop", "en")
    assert crop_prompt["pending"] == "set_intended_crop"
    assert len(crop_prompt["choices"]) >= 3

    crop_choice = route(
        "ধান",
        "en",
        history=[{"pending": crop_prompt["pending"]}],
    )
    assert crop_choice["lang"] == "bn"
    assert crop_choice["actions"][0]["payload"]["crop"] == "rice"


def test_smap_question_is_explanation_not_layer_action_and_suggestions_are_bilingual():
    response = route("What is SMAP?", "en", snapshot={"activeLayer": "rain"})
    assert response["actions"] == []
    assert response["intent"] == "soil_limits"
    assert "not field-level pH" in response["reply"]
    assert len(response["suggestions"]) in {3, 4}
    assert "Show rain layer" not in response["suggestions"]

    bangla_suggestions = suggestions("conditions", {}, "bn")
    assert len(bangla_suggestions) in {3, 4}
    assert any("বৃষ্টি" in item for item in bangla_suggestions)


def test_greetings_and_unrecognized_messages_offer_useful_state_aware_suggestions():
    english_hi = route("Hi", "en", snapshot={"view": "earth", "selectedArea": "Rajshahi"})
    assert english_hi["intent"] == "welcome"
    assert "Hi!" in english_hi["reply"]
    assert {"Read my dashboard", "How is the rain here?", "Open Rotation Lab"} <= set(english_hi["suggestions"])

    bangla_hi = route("হাই", "en", snapshot={"view": "earth", "selectedArea": "রাজশাহী"})
    assert bangla_hi["lang"] == "bn"
    assert "হ্যালো!" in bangla_hi["reply"]
    assert any("ড্যাশবোর্ড" in item for item in bangla_hi["suggestions"])

    unknown = route("qzxv random words", "en", snapshot={"view": "plan"})
    assert unknown["intent"] == "fallback"
    assert "not sure I understood" in unknown["reply"]
    assert any("Print my plan" in item for item in unknown["suggestions"])
    assert len(unknown["suggestions"]) >= 3


def test_unavailable_conditions_are_not_replaced_with_fabricated_values():
    response = route("How is the rain here?", "en", snapshot={"fieldData": {}})
    assert "unavailable" in response["reply"]
    assert "not a forecast" in response["reply"]


def test_baseline_and_advice_answers_use_displayed_snapshot_values():
    comparison = route(
        "Compare with the baseline",
        "en",
        snapshot={
            "fieldData": {
                "rainfallDaily": "3.20 mm/day",
                "baselineRainfall": "2.50 mm/day",
                "rainAnomaly": "+28.0%",
            }
        },
    )
    assert "3.20 mm/day" in comparison["reply"]
    assert "2.50 mm/day" in comparison["reply"]
    assert "+28.0%" in comparison["reply"]
    assert "not a forecast" in comparison["reply"]
    assert "Compare with the baseline" not in comparison["suggestions"]

    advice = route(
        "Why this advice?",
        "en",
        snapshot={"planContext": {"reasons": ["Displayed evidence reason."]}},
    )
    assert advice["reply"] == "Displayed evidence reason."


def test_suggestions_do_not_repeat_completed_field_or_layer_actions():
    response = route(
        "What can you do?",
        "en",
        snapshot={"view": "earth", "selectedArea": "Rajshahi", "activeLayer": "rain"},
    )
    assert len(response["suggestions"]) in {3, 4}
    assert not any("select a field" in item.lower() for item in response["suggestions"])
    assert not any("rain layer" in item.lower() for item in response["suggestions"])


def test_map_scrubber_and_display_controls_are_routable():
    assert route("Set map date to 14 days ago")["actions"][0] == {
        "type": "setMapDate",
        "payload": {"days_ago": 14},
    }
    assert route("মানচিত্রের তারিখ ৩০ দিন আগে করুন")["actions"][0]["payload"] == {"days_ago": 30}
    assert route("Set the map date to 2024-06-15")["actions"][0]["payload"] == {"date": "2024-06-15"}
    assert route("Use the village/street map")["actions"][0]["payload"] == {"style": "streets"}
    assert route("Switch to 2D map")["actions"][0]["payload"] == {"is_globe": False}
    assert route("Set overlay opacity to 50%")["actions"][0]["payload"] == {"opacity": 0.5}

    invalid_opacity = route("Set overlay opacity to 100%")
    assert not invalid_opacity["actions"]
    assert "20% to 95%" in invalid_opacity["reply"]


def test_camera_plan_date_strategy_and_climate_controls_are_routable():
    assert route("Zoom to space")["actions"][0] == {
        "type": "setCameraPreset",
        "payload": {"mode": "space"},
    }
    assert route("Zoom to Bangladesh")["actions"][0]["payload"] == {"mode": "bangladesh"}
    assert route("Zoom to my field")["actions"][0]["payload"] == {"mode": "field"}
    assert route("Switch to satellite map")["actions"][0]["payload"] == {"style": "satellite"}
    assert route("Set plan start date to 2028-02-29")["actions"][0] == {
        "type": "setPlanStartDate",
        "payload": {"year": 2028, "month": 2, "day": 29},
    }

    invalid_date = route("Set plan start date to 2027-02-29")
    assert not invalid_date["actions"]
    assert "not a valid date" in invalid_date["reply"]

    assert route("Select Strategy B")["actions"][0]["payload"] == {"strategy_id": "B"}
    scenario = route(
        "Set rainfall shift +20%, set temperature shift +1C",
        snapshot={"scenarioRainShiftPct": 0, "scenarioTempShiftC": 0},
    )
    assert scenario["actions"] == [
        {
            "type": "setClimateScenario",
            "payload": {"rain_shift_pct": 20, "temperature_shift_c": 0},
        },
        {
            "type": "setClimateScenario",
            "payload": {"rain_shift_pct": 20, "temperature_shift_c": 1.0},
        },
    ]

    invalid_scenario = route("Set rainfall shift +53%")
    assert not invalid_scenario["actions"]
    assert "5% steps" in invalid_scenario["reply"]


def test_project_questions_and_dashboard_summary_are_grounded_in_snapshot():
    project = route("What is BoponX?", "en")
    assert "decision-support website" in project["reply"]
    assert project["intent"] == "project_info"

    authorship = route("Who made this project?", "en")
    assert "Rezwan Hossain Prince" in authorship["reply"]
    assert "Team EARTH.exe" in authorship["reply"]
    assert authorship["intent"] == "project_info"

    bangla_authorship = route("বপনএক্স কে বানিয়েছে?", "en")
    assert bangla_authorship["lang"] == "bn"
    assert "Team EARTH.exe" in bangla_authorship["reply"]

    data_sources = route("What data does BoponX use?", "en")
    assert "NASA POWER" in data_sources["reply"]
    assert "SMAP" in data_sources["reply"]

    usage = route("How do I use BoponX?", "en")
    assert "selecting your field or district" in usage["reply"]
    assert "90-day plan" in usage["reply"]

    dashboard = route(
        "Read my dashboard",
        "en",
        snapshot={
            "selectedArea": "Khulna",
            "activeLayer": "soil",
            "fieldData": {
                "dataStatus": "available",
                "rainfall": "18.4 mm / 14 days",
                "rainAnomaly": "+12.0%",
                "temperature": "29.1 °C",
                "soilMoisture": "24% surface / 31% root zone",
                "hazards": "unavailable",
            },
            "planContext": {"verdict": "Evidence is limited."},
        },
    )
    assert dashboard["intent"] == "dashboard_summary"
    for displayed_value in ("Khulna", "18.4 mm / 14 days", "+12.0%", "29.1 °C", "24% surface / 31% root zone", "unavailable"):
        assert displayed_value in dashboard["reply"]

    unavailable = route(
        "Read dashboard",
        "en",
        snapshot={"fieldData": {"dataStatus": "unavailable"}},
    )
    assert "unavailable" in unavailable["reply"]
    assert "zero" in unavailable["reply"]


def test_dashboard_metric_questions_use_only_snapshot_values():
    data = {
        "fogBlightRisk": "3 days",
        "frostRisk": "unavailable",
        "humidity": "78.2%",
        "dewPoint": "18.4 °C",
        "vaporPressureDeficit": "0.83 kPa",
        "evapotranspiration": "4.20 mm/day",
        "waterBalance": "-1.10 mm/day",
        "heatStress": "2 days",
        "coldStress": "unavailable",
        "heavyRain": "1 day",
        "dryDays": "5 days",
        "wind": "2.3 m/s",
        "climatology": "March: 29 °C, 3 mm/day rain",
        "dataFreshness": "NASA POWER through 2026-03-01; about 7 days lag",
        "evidenceOrigin": "nasa_power_live",
        "hazards": "2 agricultural alerts within 1200 km",
        "hazardEvents": ["Cyclone (2026-03-01), 90 km"],
        "dataStatus": "available",
    }
    questions = {
        "How many fog-risk days?": "3 days",
        "What is the frost risk?": "unavailable",
        "What is the relative humidity?": "78.2%",
        "What is the dew point?": "18.4 °C",
        "What is the VPD?": "0.83 kPa",
        "What is evapotranspiration?": "4.20 mm/day",
        "What is the water balance?": "-1.10 mm/day",
        "How many heat-stress days?": "2 days",
        "How many cold-stress days?": "unavailable",
        "How many heavy-rain days?": "1 day",
        "How many dry days?": "5 days",
        "What is the wind?": "2.3 m/s",
        "Show climatology": "March: 29 °C",
        "What is the data freshness?": "2026-03-01",
        "What are the hazard alerts?": "Cyclone",
    }
    for question, displayed_value in questions.items():
        response = route(question, snapshot={"fieldData": data})
        assert displayed_value in response["reply"], question


def test_recommendation_requires_and_uses_displayed_plan_evidence():
    no_plan = route("What should I do next?", "en")
    assert "no displayed plan" in no_plan["reply"]
    assert "invent" in no_plan["reply"]

    with_plan = route(
        "What should I do next?",
        "en",
        snapshot={
            "planContext": {
                "verdict": "Proceed cautiously.",
                "reasons": ["Reason from the visible plan."],
                "boundary": "Verify with extension staff.",
            }
        },
    )
    assert "Proceed cautiously." in with_plan["reply"]
    assert "Reason from the visible plan." in with_plan["reply"]
    assert "Verify with extension staff." in with_plan["reply"]


def test_project_data_explanations_keep_forecasts_and_soil_limits_clear():
    sources = route("What data sources do you use?", "en")
    assert "NASA POWER" in sources["reply"]
    assert "SMAP" in sources["reply"]
    assert "not a forecast" in sources["reply"]
    assert "pH/NPK" in sources["reply"]

    forecast = route("Will it rain tomorrow?", "en")
    assert "does not provide weather forecasts" in forecast["reply"]

    bangla = route("ড্যাশবোর্ডের সারাংশ দিন", "en", snapshot={"fieldData": {"dataStatus": "unavailable"}})
    assert bangla["lang"] == "bn"
    assert "ড্যাশবোর্ড সারাংশ" in bangla["reply"]


def test_site_help_and_crop_questions_do_not_create_false_crop_actions():
    website_help = route("How do I use this website?", "en")
    assert "Rotation Lab" in website_help["reply"]
    assert "drag" in website_help["reply"].lower()

    suitability = route("Should I plant rice?", "en")
    assert suitability["actions"] == []
    assert "evidence gate" in suitability["reply"]
    assert all(isinstance(item, str) for item in suitability["suggestions"])
    assert len(suitability["suggestions"]) in {3, 4}

    bangla = route("এই ফসল চাষ করা যাবে?", "en")
    assert bangla["lang"] == "bn"
    assert bangla["actions"] == []
    assert "প্রমাণ-গেটে" in bangla["reply"]


def test_chat_endpoint_returns_expected_response_shape():
    response = client.post(
        "/api/v1/assistant/chat",
        json={"message": "Open Rotation Lab", "lang": "en", "history": [], "snapshot": {}},
    )

    assert response.status_code == 200
    body = response.json()
    assert {"reply", "intent", "mode", "lang", "actions", "suggestions"} <= body.keys()
    assert body["actions"][0]["payload"]["view"] == "rotation"
