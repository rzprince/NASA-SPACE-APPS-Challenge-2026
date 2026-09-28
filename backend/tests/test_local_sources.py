from backend.app.compute.local_sources import source_registry


def test_bangladesh_registry_has_verified_official_sources():
    registry = source_registry("bd")
    assert registry["coverage"] == "verified_country_adapter"
    assert any(item["id"] == "bd-bamis" for item in registry["official_sources"])
    assert registry["global_sources"]


def test_unreviewed_country_falls_back_without_fake_government_adapter():
    registry = source_registry("zz")
    assert registry["coverage"] == "global_reference_only"
    assert registry["official_sources"] == []
    assert registry["global_sources"][0]["id"] == "fao-crop-calendar"
