from backend.app.compute.agronomy import calendar_evidence_for_region


def test_region_calendar_evidence_is_specific_and_non_recommending():
    rajshahi = calendar_evidence_for_region("Rajshahi")
    rangamati = calendar_evidence_for_region("Rangamati")
    assert any(item["id"] == "wheat" for item in rajshahi)
    assert not any(item["id"] == "wheat" for item in rangamati)
    assert all(item["status"] == "calendar_source_identified_not_rotation_rule" for item in rajshahi)
    assert all("does not by itself mean" in item["meaning"] for item in rajshahi)
