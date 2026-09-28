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



def test_verified_country_gets_direct_official_agriculture_route():
    registry = source_registry("jp", "Japan")
    discovery = registry["government_discovery"]
    assert discovery["status"] == "verified_country_route"
    assert discovery["source_url"].startswith("https://www.maff.go.jp/")
    assert registry["global_sources"]


def test_unreviewed_country_gets_transparent_discovery_route():
    registry = source_registry("zz", "Exampleland")
    discovery = registry["government_discovery"]
    assert discovery["status"] == "discovery_link_not_verified"
    assert "Exampleland" in discovery["name"]
    assert "google.com/search" in discovery["source_url"]


def test_bangladesh_registry_includes_farmer_information_and_extension_sources():
    registry = source_registry("bd", "Bangladesh")
    ids = {item["id"] for item in registry["official_sources"]}
    assert {"bd-moa", "bd-dae", "bd-ais", "bd-bamis", "bd-barc-zoning"} <= ids


def test_verified_country_portal_route_is_not_a_search_engine():
    registry = source_registry("us", "United States")
    assert registry["coverage"] == "verified_country_adapter"
    assert registry["official_sources"]
    assert "google.com/search" not in registry["government_discovery"]["source_url"]
