"""Verified agriculture portals plus a transparent global discovery path.

A direct national link is labelled official only after the source has been
reviewed. Countries without a reviewed adapter still receive NASA analysis,
FAO references, and a country specific discovery route without inventing a
government dataset.
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
        "note": "Global crop calendar reference. It does not replace a national agronomy authority.",
    },
    {
        "id": "faolex-country-profiles",
        "name": "FAOLEX Country Profiles",
        "organization": "Food and Agriculture Organization of the United Nations",
        "scope": "Country specific food, agriculture and natural resource policy reference",
        "kind": "intergovernmental_country_reference",
        "status": "global_reference",
        "source_url": "https://www.fao.org/faolex/country-profiles/en/",
        "note": "Country profiles provide a global policy reference layer.",
    },
)

COUNTRY_SOURCES: dict[str, tuple[dict[str, Any], ...]] = {
    "bd": (
        {
            "id": "bd-moa",
            "name": "Bangladesh Ministry of Agriculture",
            "organization": "Government of Bangladesh",
            "scope": "National agriculture ministry, policy, services and official programme information",
            "kind": "national_agriculture_portal",
            "status": "official_source_reference",
            "source_url": "https://moa.gov.bd/",
        },
        {
            "id": "bd-dae",
            "name": "Department of Agricultural Extension",
            "organization": "Ministry of Agriculture, Bangladesh",
            "scope": "Government agricultural extension services and farmer support",
            "kind": "national_extension",
            "status": "official_source_reference",
            "source_url": "https://dae.gov.bd/",
        },
        {
            "id": "bd-ais",
            "name": "Agriculture Information Service",
            "organization": "Ministry of Agriculture, Bangladesh",
            "scope": "Crop production technology, seasonal agriculture guidance, market information and farmer information services",
            "kind": "national_farmer_information",
            "status": "official_source_connected",
            "source_url": "https://ais.gov.bd/",
        },
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
            "scope": "Upazila level agro edaphic and agro climatic crop suitability and zoning reference",
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
        {
            "id": "in-agri",
            "name": "Department of Agriculture and Farmers Welfare",
            "organization": "Government of India",
            "scope": "National agriculture policy, farmer schemes and crop information",
            "kind": "national_agriculture_portal",
            "status": "official_source_reference",
            "source_url": "https://agriwelfare.gov.in/",
        },
    ),
    "us": (
        {
            "id": "us-usda",
            "name": "United States Department of Agriculture",
            "organization": "USDA",
            "scope": "National agriculture programmes, data, crop and farmer services",
            "kind": "national_agriculture_portal",
            "status": "official_source_reference",
            "source_url": "https://www.usda.gov/",
        },
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
            "scope": "Regional climate adaptation information for agriculture",
            "kind": "national_climate_adaptation",
            "status": "official_source_reference",
            "source_url": "https://www.climatehubs.usda.gov/commodity/crops",
        },
    ),
    "ca": (
        {
            "id": "ca-aafc",
            "name": "Agriculture and Agri Food Canada",
            "organization": "Government of Canada",
            "scope": "Crops, drought conditions, agricultural services, programmes and sector information",
            "kind": "national_agriculture_portal",
            "status": "official_source_reference",
            "source_url": "https://agriculture.canada.ca/en",
        },
    ),
    "jp": (
        {
            "id": "jp-maff",
            "name": "Ministry of Agriculture, Forestry and Fisheries",
            "organization": "Government of Japan",
            "scope": "National agriculture, food, rural policy, reports and official farmer information",
            "kind": "national_agriculture_portal",
            "status": "official_source_reference",
            "source_url": "https://www.maff.go.jp/e/",
        },
    ),
    "br": (
        {
            "id": "br-mapa",
            "name": "Ministry of Agriculture and Livestock",
            "organization": "Government of Brazil",
            "scope": "Agricultural policy, risk management, production statistics, publications and services",
            "kind": "national_agriculture_portal",
            "status": "official_source_reference",
            "source_url": "https://www.gov.br/agricultura/pt-br/",
        },
    ),
    "ph": (
        {
            "id": "ph-da",
            "name": "Department of Agriculture",
            "organization": "Government of the Philippines",
            "scope": "National agriculture programmes, crop information, regional offices and farmer services",
            "kind": "national_agriculture_portal",
            "status": "official_source_reference",
            "source_url": "https://www.da.gov.ph/",
        },
    ),
    "lk": (
        {
            "id": "lk-doa",
            "name": "Department of Agriculture",
            "organization": "Government of Sri Lanka",
            "scope": "Crop recommendations, agricultural research, extension and farmer information",
            "kind": "national_agriculture_portal",
            "status": "official_source_reference",
            "source_url": "https://doa.gov.lk/",
        },
    ),
    "au": (
        {
            "id": "au-daff",
            "name": "Department of Agriculture, Fisheries and Forestry",
            "organization": "Australian Government",
            "scope": "National agriculture, land, drought, soil and climate policy and services",
            "kind": "national_agriculture_portal",
            "status": "official_source_reference",
            "source_url": "https://www.agriculture.gov.au/",
        },
        {
            "id": "au-daff-soils",
            "name": "Australian National Soil Strategy",
            "organization": "Australian Department of Agriculture, Fisheries and Forestry",
            "scope": "National soil strategy, monitoring and management references",
            "kind": "national_soil",
            "status": "official_source_reference",
            "source_url": "https://www.agriculture.gov.au/agriculture-land/farm-food-drought/natural-resources/soils",
        },
    ),
    "gb": (
        {
            "id": "gb-defra",
            "name": "Department for Environment, Food and Rural Affairs",
            "organization": "Government of the United Kingdom",
            "scope": "Agriculture, food, farming, environment and rural services",
            "kind": "national_agriculture_portal",
            "status": "official_source_reference",
            "source_url": "https://www.gov.uk/government/organisations/department-for-environment-food-rural-affairs",
        },
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

    if local:
        government_discovery = {
            "name": f"{name or code.upper()} official agriculture portal",
            "scope": "Reviewed government agriculture entry point",
            "kind": "government_portal_verified_route",
            "status": "verified_country_route",
            "source_url": local[0]["source_url"],
            "note": "Opens a reviewed official agriculture source for the selected country.",
        }
    else:
        discovery_query = f"{name or code.upper()} official ministry agriculture government data"
        government_discovery = {
            "name": f"Find the official agriculture authority for {name or code.upper()}",
            "scope": "Country specific government agriculture website discovery",
            "kind": "government_portal_discovery",
            "status": "discovery_link_not_verified",
            "source_url": f"https://www.google.com/search?q={quote_plus(discovery_query)}",
            "note": "No direct national adapter has been reviewed for this country yet. Verify the government domain before using it as evidence.",
        }

    return {
        "country_code": code or None,
        "country_name": name or None,
        "official_sources": local,
        "government_discovery": government_discovery,
        "global_sources": [dict(item) for item in GLOBAL_FALLBACK],
        "coverage": "verified_country_adapter" if local else "global_reference_only",
        "warning": (
            "NASA coverage is global. National agriculture links are labelled official only after source review."
        ),
    }
