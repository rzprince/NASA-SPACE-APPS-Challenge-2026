"""Verified local and international agriculture source registry.

The registry is intentionally conservative. It only lists sources that were
manually reviewed as official public-sector or intergovernmental sources.
Countries not listed still receive global NASA coverage plus the FAO Crop
Calendar reference, but BoponX does not pretend that a national adapter exists.
"""
from __future__ import annotations

from typing import Any

GLOBAL_FALLBACK: tuple[dict[str, Any], ...] = (
    {
        "id": "fao-crop-calendar",
        "name": "FAO Crop Calendar",
        "organization": "Food and Agriculture Organization of the United Nations",
        "scope": "Country and agroecological-zone crop calendar reference",
        "kind": "intergovernmental_crop_calendar",
        "status": "global_reference",
        "source_url": "https://cropcalendar.apps.fao.org/",
        "note": "FAO describes this as a living platform using country and agroecological-zone crop calendar information.",
    },
)

COUNTRY_SOURCES: dict[str, tuple[dict[str, Any], ...]] = {
    "bd": (
        {
            "id": "bd-bamis",
            "name": "Bangladesh Agro-Meteorological Information Service",
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
            "scope": "Agro-edaphic and agro-climatic crop zoning reference",
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
            "scope": "District, block and state agrometeorological advisories and dynamic crop weather calendars",
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
            "scope": "Region-specific climate adaptation information for agriculture",
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
            "name": "DEFRA Agriculture and Climate Change",
            "organization": "UK Department for Environment, Food and Rural Affairs",
            "scope": "Agricultural climate statistics and official adaptation information",
            "kind": "national_climate_reference",
            "status": "official_source_reference",
            "source_url": "https://www.gov.uk/government/collections/agricultural-statistics-and-climate-change",
        },
    ),
}


def source_registry(country_code: str | None) -> dict[str, Any]:
    code = (country_code or "").strip().lower()
    local = [dict(item) for item in COUNTRY_SOURCES.get(code, ())]
    return {
        "country_code": code or None,
        "official_sources": local,
        "global_sources": [dict(item) for item in GLOBAL_FALLBACK],
        "coverage": "verified_country_adapter" if local else "global_reference_only",
        "warning": (
            "Only verified public-sector sources are listed. BoponX does not invent a local-government data adapter for countries that have not been reviewed."
        ),
    }
