"""Curated NASA and official agricultural source registry for BoponX.

This module separates three ideas:
1. NASA sources that can provide global Earth context.
2. Official national or regional agricultural sources that have been manually verified.
3. Coverage gaps that must remain explicit instead of being filled with invented data.
"""
from __future__ import annotations

from typing import Any


NASA_DATA_STACK: tuple[dict[str, Any], ...] = (
    {
        "id": "gpm-imerg-early-v07b",
        "name": "GPM IMERG Early Run",
        "mission": "GPM",
        "role": "recent_precipitation",
        "decision_use": "Recent rainfall context and rainfall anomaly review.",
        "product": "IMERG Early Run V07B",
        "temporal": "30 minute source product",
        "spatial": "0.1 degree / about 10 km",
        "latency": "about 4 hours minimum",
        "coverage": "global except small areas near the poles",
        "access": "GPM PPS / GES DISC / NASA GIBS",
        "integration": "map_visualization_ready",
        "source_url": "https://gpm.nasa.gov/data/imerg",
        "boundary": "Not a field rain gauge and not a future forecast.",
    },
    {
        "id": "smap-spl3smp-e-v6",
        "name": "SMAP Enhanced L3 Soil Moisture",
        "mission": "SMAP",
        "role": "regional_surface_soil_moisture",
        "decision_use": "Regional moisture context before irrigation or drainage decisions.",
        "product": "SPL3SMP_E Version 6",
        "temporal": "daily",
        "spatial": "9 km EASE Grid",
        "latency": "standard and near real time access vary by product",
        "coverage": "global land",
        "access": "NSIDC DAAC / NASA GIBS",
        "integration": "map_visualization_ready_numeric_adapter_gated",
        "source_url": "https://nsidc.org/data/spl3smp_e/versions/6",
        "boundary": "Surface soil moisture is not pH, nutrients, or a parcel soil test.",
        "advisory": "NSIDC reports a geolocation issue affecting Standard and NRT products from 14 May to 28 July 2026. Standard data for the interval are being reprocessed; NRT data will not be replaced.",
    },
    {
        "id": "nasa-power-data-v10",
        "name": "NASA POWER Agroclimatology",
        "mission": "POWER",
        "role": "agroclimate",
        "decision_use": "Recent temperature, rainfall, humidity, wind and solar context plus historical baselines.",
        "product": "POWER Data v10 services",
        "temporal": "daily to climatology",
        "spatial": "native source grids; meteorology roughly 0.5 by 0.625 degree",
        "latency": "daily data available to near real time",
        "coverage": "global",
        "access": "POWER REST API",
        "integration": "numeric_point_query_ready",
        "source_url": "https://power.larc.nasa.gov/docs/services/api/temporal/daily/",
        "boundary": "Analysis ready gridded context, not a sensor placed in the farmer's field.",
    },
    {
        "id": "modis-terra-ndvi-8day",
        "name": "MODIS Terra NDVI",
        "mission": "Terra MODIS",
        "role": "vegetation_vigor",
        "decision_use": "Visual check of vegetation vigor and change around the selected field.",
        "product": "MODIS Terra NDVI 8 Day",
        "temporal": "8 day composite",
        "spatial": "250 m visualization layer",
        "latency": "product dependent",
        "coverage": "global land",
        "access": "NASA GIBS",
        "integration": "map_visualization_ready",
        "source_url": "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_NDVI_8Day/",
        "boundary": "NDVI is a vegetation index, not crop identity, yield, or soil chemistry.",
    },
    {
        "id": "modis-terra-lst-day",
        "name": "MODIS Terra Land Surface Temperature",
        "mission": "Terra MODIS",
        "role": "surface_heat",
        "decision_use": "Visual surface heat context for crop stress and irrigation review.",
        "product": "MODIS Terra Daytime Land Surface Temperature",
        "temporal": "daily visualization",
        "spatial": "about 1 km visualization layer",
        "latency": "product dependent",
        "coverage": "global land",
        "access": "NASA GIBS",
        "integration": "map_visualization_ready",
        "source_url": "https://gibs.earthdata.nasa.gov/twms/epsg4326/all/MODIS_Terra_Land_Surface_Temp_Day/",
        "boundary": "Land surface temperature is not the same as two meter air temperature.",
    },
    {
        "id": "hls-vegetation-indices-v2",
        "name": "Harmonized Landsat Sentinel 2 Vegetation Indices",
        "mission": "HLS",
        "role": "field_scale_vegetation",
        "decision_use": "Higher resolution vegetation evidence for future parcel scale adapters.",
        "product": "HLSL30_VI and HLSS30_VI Version 2.0",
        "temporal": "daily global product stream",
        "spatial": "30 m",
        "latency": "granule availability depends on acquisition and processing",
        "coverage": "global land observations",
        "access": "NASA Earthdata / LP DAAC",
        "integration": "catalog_ready_authenticated_adapter_pending",
        "source_url": "https://cmr.earthdata.nasa.gov/search/site/collections/directory/LPCLOUD/gov.nasa.eosdis",
        "boundary": "The current demo does not invent HLS values when authenticated granule retrieval is unavailable.",
    },
    {
        "id": "ecostress-esi-v2",
        "name": "ECOSTRESS Evaporative Stress Index",
        "mission": "ECOSTRESS",
        "role": "plant_water_stress",
        "decision_use": "Plant water stress evidence for future field scale water decisions.",
        "product": "ECO_L4T_ESI Version 2",
        "temporal": "instantaneous observations",
        "spatial": "70 m",
        "latency": "orbit and processing dependent",
        "coverage": "observations between about 52 degrees north and south",
        "access": "NASA Earthdata / LP DAAC",
        "integration": "catalog_ready_authenticated_adapter_pending",
        "source_url": "https://search.earthdata.nasa.gov/search?q=C2076104650-LPCLOUD",
        "boundary": "Coverage is not continuous in space or time. Missing observations must remain missing.",
    },
)


LOCAL_SOURCE_REGISTRY: dict[str, dict[str, Any]] = {
    "bd": {
        "country": "Bangladesh",
        "coverage": "official_sources_indexed",
        "sources": [
            {
                "name": "BAMIS crop weather calendars",
                "agency": "Department of Agricultural Extension",
                "kind": "crop_calendar",
                "source_url": "https://www.bamis.gov.bd/en/calendar",
                "integration": "regional_calendar_index_ready",
            },
            {
                "name": "BARC crop zoning",
                "agency": "Bangladesh Agricultural Research Council",
                "kind": "crop_zoning",
                "source_url": "https://apps.barc.gov.bd/cropzoning/",
                "integration": "source_identified_rule_review_required",
            },
            {
                "name": "Soil Resource Development Institute",
                "agency": "Government of Bangladesh",
                "kind": "soil_testing",
                "source_url": "https://srdi.gov.bd/",
                "integration": "service_pathway_reference",
            },
        ],
    },
    "in": {
        "country": "India",
        "coverage": "official_sources_indexed",
        "sources": [
            {
                "name": "Soil Health Card Portal",
                "agency": "Ministry of Agriculture and Farmers Welfare",
                "kind": "soil_testing_and_recommendations",
                "source_url": "https://soilhealth.dac.gov.in/",
                "integration": "official_portal_reference",
            },
        ],
    },
    "us": {
        "country": "United States",
        "coverage": "official_sources_indexed",
        "sources": [
            {
                "name": "Web Soil Survey",
                "agency": "USDA Natural Resources Conservation Service",
                "kind": "soil_survey",
                "source_url": "https://www.nrcs.usda.gov/resources/data-and-reports/web-soil-survey",
                "integration": "official_portal_reference",
            },
        ],
    },
    "br": {
        "country": "Brazil",
        "coverage": "official_sources_indexed",
        "sources": [
            {
                "name": "Soil Health Platform BR",
                "agency": "Embrapa",
                "kind": "soil_health",
                "source_url": "https://saudedosolo.embrapa.gov.br/public-platform",
                "integration": "official_portal_reference",
            },
            {
                "name": "PronaSolos",
                "agency": "Embrapa and Brazilian federal partners",
                "kind": "soil_maps",
                "source_url": "https://www.embrapa.br/en/web/solos/busca-de-solucoes-tecnologicas/-/produto-servico/9076/portal-de-dados-da-plataforma-tecnologica-pronasolos-em-ambiente-sigweb",
                "integration": "official_portal_reference",
            },
        ],
    },
    "ke": {
        "country": "Kenya",
        "coverage": "official_sources_indexed",
        "sources": [
            {
                "name": "Agriculture resources and Agricultural Soil Management Policy",
                "agency": "Ministry of Agriculture and Livestock Development",
                "kind": "soil_policy_and_crop_resources",
                "source_url": "https://kilimo.go.ke/ministry-policies/agriculture/",
                "integration": "official_portal_reference",
            },
        ],
    },
    "au": {
        "country": "Australia",
        "coverage": "official_sources_indexed",
        "sources": [
            {
                "name": "ABARES agriculture, climate and crop reporting",
                "agency": "Department of Agriculture, Fisheries and Forestry",
                "kind": "agriculture_and_climate",
                "source_url": "https://www.agriculture.gov.au/abares",
                "integration": "official_portal_reference",
            },
        ],
    },
}


def nasa_data_stack() -> list[dict[str, Any]]:
    return [dict(item) for item in NASA_DATA_STACK]


def local_sources_for_country(country_code: str | None, country_name: str | None = None) -> dict[str, Any]:
    code = (country_code or "").lower().strip()
    if code in LOCAL_SOURCE_REGISTRY:
        item = LOCAL_SOURCE_REGISTRY[code]
        return {
            "country_code": code,
            "country": item["country"],
            "coverage": item["coverage"],
            "sources": [dict(source) for source in item["sources"]],
            "note": "These are manually verified official source pathways. BoponX only uses source content as decision rules after product specific review.",
        }
    return {
        "country_code": code or None,
        "country": country_name or "Unknown country",
        "coverage": "official_adapter_not_onboarded",
        "sources": [],
        "note": "NASA environmental coverage can still operate globally. Local government agricultural evidence is not invented when a verified adapter has not been onboarded.",
    }
