from backend.app.compute.context import build_context, nearest_area


def test_nearest_area_changes_with_location():
    rajshahi, _ = nearest_area(24.37, 88.60)
    khulna, _ = nearest_area(22.84, 89.54)
    assert rajshahi.id == "rajshahi"
    assert khulna.id == "khulna"


def test_bangladesh_context_keeps_deep_local_evidence():
    context = build_context(25.74, 89.27)
    assert context["within_bangladesh"] is True
    assert context["coverage"]["environmental_context"] == "global_nasa_stack_available"
    assert context["coverage"]["local_agricultural_evidence"] == "official_sources_indexed"
    assert context["coverage"]["rotation_decision"] == "evidence_review_required"
    assert context["privacy"]["coordinates_persisted"] is False
    assert context["calendar_evidence"]


def test_global_context_keeps_nasa_and_marks_local_adapter_gap():
    context = build_context(35.0, 90.0, country_code="cn", country_name="China")
    assert context["within_bangladesh"] is False
    assert context["coverage"]["environmental_context"] == "global_nasa_stack_available"
    assert context["coverage"]["local_agricultural_evidence"] == "official_adapter_not_onboarded"
    assert context["country"]["code"] == "cn"
    assert context["country"]["name"] == "China"
    assert context["calendar_evidence"] == []
    assert len(context["nasa_sources"]) >= 7


def test_global_context_uses_verified_country_adapter_when_available():
    context = build_context(38.0, -97.0, country_code="us", country_name="United States")
    assert context["coverage"]["local_agricultural_evidence"] == "official_sources_indexed"
    names = {item["name"] for item in context["agricultural_sources"]}
    assert "Web Soil Survey" in names
