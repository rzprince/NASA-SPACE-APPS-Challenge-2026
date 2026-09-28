"""Verified local agriculture sources plus a transparent global discovery path.

Direct government links are only labelled verified after manual review. For any
other country, BoponX still provides a country specific government portal
discovery link and FAO country references without pretending the destination has
already been verified.
"""
from __future__ import annotations

from typing import Any
from urllib.parse import quote_plus

GLOBAL_FALLBACK: tuple[dict[str, Any], ...] = (
    {
        "id": "fao-crop-calendar",
        "name": "FAO Crop Calendar",
        "organization": "Food and Agriculture Organization of the United Nations",
        "scope": "Country and agroecological zone crop calendar reference",
        "kind": "intergovernmental_crop_calendar",
        "status": "global_reference",
        "source_url": "https://cropcalendar.apps.fao.org/",
        "note": "Global crop calendar reference. It is not a substitute for a national agronomy authority.",
    },
    {
        "id": "faolex-country-profiles",
        "name": "FAOLEX Country Profiles",
        "organization": "Food and Agriculture Organization of the United Nations",
        "scope": "Country specific food, agriculture and natural resource policy and legal reference",
        "kind": "intergovernmental_country_reference",
        "status": "global_reference",
        "source_url": "https://www.fao.org/faolex/country-profiles/en/",
        "note": "Country profiles cover FAO members and provide a global policy reference layer.",
    },
)

COUNTRY_SOURCES: dict[str, tuple[dict[str, Any], ...]] = {
    "bd": (
        {
            "id": "bd-bamis",
            "name": "Bangladesh Agro Meteorological Information Service",
            "organization": "Department of Agricultural Extension, Bangladesh",
            "scope": "Crop weather calendars, agromet information, advisories and district crop information",
            "kind": "national_agromet",
            "status": "official_source_connected",
            "source_url": "https://www.bamis.gov.bd/",
        },
        {
            "id": "bd-barc-zoning",
            "name": "BARC Crop Zoning",
            "organization": "Bangladesh Agricultural Research Council",
            "scope": "Agro edaphic and agro climatic crop zoning reference",
            "kind": "national_crop_zoning",
            "status": "official_source_reference",
            "source_url": "https://apps.barc.gov.bd/cropzoning/",
        },
    ),
    "in": (
        {
            "id": "in-imd-agromet",
            "name": "IMD Agromet Advisory Services",
            "organization": "India Meteorological Department",
            "scope": "District, block and state agrometeorological advisories and crop weather guidance",
            "kind": "national_agromet",
            "status": "official_source_reference",
            "source_url": "https://mausam.imd.gov.in/responsive/agromet_adv_ser_district_current_en.php",
        },
    ),
    "us": (
        {
            "id": "us-usda-wss",
            "name": "USDA Web Soil Survey",
            "organization": "USDA Natural Resources Conservation Service",
            "scope": "Authoritative soil survey information for United States planning",
            "kind": "national_soil",
            "status": "official_source_reference",
            "source_url": "https://websoilsurvey.sc.egov.usda.gov/App/",
        },
        {
            "id": "us-usda-climate-hubs",
            "name": "USDA Climate Hubs",
            "organization": "United States Department of Agriculture",
            "scope": "Region specific climate adaptation information for agriculture",
            "kind": "national_climate_adaptation",
            "status": "official_source_reference",
            "source_url": "https://www.climatehubs.usda.gov/commodity/crops",
        },
    ),
    "au": (
        {
            "id": "au-daff-soils",
            "name": "Australian National Soil Strategy",
            "organization": "Australian Department of Agriculture, Fisheries and Forestry",
            "scope": "National soil strategy, monitoring and management references",
            "kind": "national_soil",
            "status": "official_source_reference",
            "source_url": "https://www.agriculture.gov.au/agriculture-land/farm-food-drought/natural-resources/soils",
        },
        {
            "id": "au-daff-climate",
            "name": "Australian Agriculture Climate Adaptation",
            "organization": "Australian Department of Agriculture, Fisheries and Forestry",
            "scope": "Agricultural climate adaptation policy and resilience information",
            "kind": "national_climate_adaptation",
            "status": "official_source_reference",
            "source_url": "https://www.agriculture.gov.au/agriculture-land/farm-food-drought/climatechange",
        },
    ),
    "gb": (
        {
            "id": "gb-defra-agriclimate",
            "name": "DEFRA Agricultural Statistics and Climate Change",
            "organization": "UK Department for Environment, Food and Rural Affairs",
            "scope": "Agricultural climate statistics and official adaptation information",
            "kind": "national_climate_reference",
            "status": "official_source_reference",
            "source_url": "https://www.gov.uk/government/collections/agricultural-statistics-and-climate-change",
        },
    ),
}


def source_registry(country_code: str | None, country_name: str | None = None) -> dict[str, Any]:
    code = (country_code or "").strip().lower()
    name = (country_name or "").strip()
    local = [dict(item) for item in COUNTRY_SOURCES.get(code, ())]

    discovery_query = f"{name or code.upper()} official ministry agriculture government data"
    government_discovery = {
        "name": f"{name or code.upper()} official agriculture portal finder",
        "scope": "Country specific government agriculture website discovery",
        "kind": "government_portal_discovery",
        "status": "discovery_link_not_verified",
        "source_url": f"https://www.google.com/search?q={quote_plus(discovery_query)}",
        "note": "This search route is available for every country. Verify the government domain before using the information as evidence.",
    }

    return {
        "country_code": code or None,
        "country_name": name or None,
        "official_sources": local,
        "government_discovery": government_discovery,
        "global_sources": [dict(item) for item in GLOBAL_FALLBACK],
        "coverage": "verified_country_adapter" if local else "global_reference_only",
        "warning": (
            "Direct national links are labelled verified only after manual review. The government portal finder is a discovery route, not a verified data source."
        ),
    }
