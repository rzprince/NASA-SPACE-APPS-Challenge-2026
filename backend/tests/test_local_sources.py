from backend.app.compute.local_sources import source_registry


def test_bangladesh_registry_has_verified_official_sources():
    registry = source_registry("bd", "Bangladesh")
    assert registry["coverage"] == "verified_country_adapter"
    assert any(item["id"] == "bd-bamis" for item in registry["official_sources"])
    assert registry["global_sources"]


def test_unreviewed_country_falls_back_without_fake_government_adapter():
    registry = source_registry("zz", "Exampleland")
    assert registry["coverage"] == "global_reference_only"
    assert registry["official_sources"] == []
    assert registry["global_sources"][0]["id"] == "fao-crop-calendar"



def test_every_country_gets_a_transparent_government_portal_discovery_link():
    registry = source_registry("jp", "Japan")
    discovery = registry["government_discovery"]
    assert discovery["status"] == "discovery_link_not_verified"
    assert "Japan" in discovery["name"]
    assert "official" in discovery["source_url"].lower()
    assert registry["global_sources"]


def test_verified_country_still_includes_portal_discovery_path():
    registry = source_registry("us", "United States")
    assert registry["coverage"] == "verified_country_adapter"
    assert registry["official_sources"]
    assert registry["government_discovery"]["source_url"].startswith("https://www.google.com/search")
