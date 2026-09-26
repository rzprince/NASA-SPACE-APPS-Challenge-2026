from backend.app.compute.context import build_context
from backend.app.compute.plan import make_90_day_plan


def profile(**overrides):
    data = {
        "latitude": 24.37,
        "longitude": 88.60,
        "previous_crop": "rice",
        "water_source": "rainfed",
        "water_after_heavy_rain": "sometimes",
        "soil_test": "no",
        "soil_ph": None,
        "priority": "water",
    }
    data.update(overrides)
    return data


def test_three_months_have_distinct_objectives_and_tasks():
    result = make_90_day_plan(profile(), build_context(24.37, 88.60), start_year=2026, start_month=11)
    assert [m["planning_month"] for m in result["months"]] == ["2026-11", "2026-12", "2027-01"]
    assert len({m["phase"]["en"] for m in result["months"]}) == 3
    task_codes = [[t["code"] for t in month["tasks"]] for month in result["months"]]
    assert set(task_codes[0]).isdisjoint(task_codes[1])
    assert set(task_codes[1]).isdisjoint(task_codes[2])
    assert set(task_codes[0]).isdisjoint(task_codes[2])


def test_unknown_soil_does_not_block_plan_or_create_ph():
    result = make_90_day_plan(
        profile(soil_test="unknown", soil_ph=None),
        build_context(22.84, 89.54),
        start_year=2026,
        start_month=9,
    )
    assert result["status"] == "DECISION_PREPARATION_READY"
    assert result["farmer_context"]["soil_ph"] is None
    assert result["rotation_explorer"]["status"] == "EVIDENCE_REVIEW_REQUIRED"
