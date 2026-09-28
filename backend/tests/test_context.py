from backend.app.compute.context import build_context, nearest_area


def test_nearest_area_changes_with_location():
    rajshahi, _ = nearest_area(24.37, 88.60)
    khulna, _ = nearest_area(22.84, 89.54)
    assert rajshahi.id == "rajshahi"
    assert khulna.id == "khulna"


def test_bangladesh_context_keeps_deep_local_evidence():
    context = build_context(25.74, 89.27)
    assert context["within_bangladesh"] is True
    assert context["global_environmental_coverage"] is True
    assert context["coverage"]["environmental_context"] == "global_nasa_coverage"
    assert context["coverage"]["local_agricultural_evidence"] == "bangladesh_deep_adapter"
    assert context["calendar_evidence"]
    assert context["privacy"]["coordinates_persisted"] is False


def test_context_supports_global_nasa_coverage_outside_bangladesh():
    context = build_context(35.0, 90.0)
    assert context["within_bangladesh"] is False
    assert context["global_environmental_coverage"] is True
    assert context["coverage"]["environmental_context"] == "global_nasa_coverage"
    assert context["coverage"]["local_agricultural_evidence"] == "country_adapter_required"
    assert context["calendar_evidence"] == []
