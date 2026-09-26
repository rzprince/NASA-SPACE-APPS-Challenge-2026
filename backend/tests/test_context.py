from backend.app.compute.context import build_context, nearest_area


def test_nearest_area_changes_with_location():
    rajshahi, _ = nearest_area(24.37, 88.60)
    khulna, _ = nearest_area(22.84, 89.54)
    assert rajshahi.id == "rajshahi"
    assert khulna.id == "khulna"


def test_context_distinguishes_environment_from_rotation_support():
    context = build_context(25.74, 89.27)
    assert context["within_bangladesh"] is True
    assert context["coverage"]["environmental_context"] == "available"
    assert context["coverage"]["rotation_decision"] == "evidence_review_required"
    assert context["privacy"]["coordinates_persisted"] is False


def test_context_fails_closed_outside_bangladesh():
    context = build_context(35.0, 90.0)
    assert context["within_bangladesh"] is False
    assert context["coverage"]["environmental_context"] == "outside_bangladesh_pilot"
