"""Source-indexed Bangladesh crop-calendar evidence.

This is deliberately NOT a crop recommendation database. It records which crops
have an official BAMIS crop-weather calendar for a regional evidence hub. The
calendar itself must still be reviewed before any crop/rotation rule is encoded.
"""
from __future__ import annotations

from typing import Any

BAMIS_BASE = "https://www.bamis.gov.bd/en/calendar/1"

_CALENDARS: tuple[dict[str, Any], ...] = (
    {
        "id": "rice-aman",
        "name_en": "Rice Aman",
        "name_bn": "আমন ধান",
        "bamis_crop_id": 74,
        "regions": ("Barishal","Bogura","Chattogram","Cumilla","Dhaka","Dinajpur","Faridpur","Jashore","Khulna","Mymensingh","Rajshahi","Rangamati","Rangpur","Sylhet"),
    },
    {
        "id": "rice-aus",
        "name_en": "Rice Aus",
        "name_bn": "আউশ ধান",
        "bamis_crop_id": 7,
        "regions": ("Barishal","Bogura","Chattogram","Cumilla","Dhaka","Dinajpur","Faridpur","Jashore","Khulna","Mymensingh","Rajshahi","Rangamati","Rangpur","Sylhet"),
    },
    {
        "id": "rice-boro",
        "name_en": "Rice Boro",
        "name_bn": "বোরো ধান",
        "bamis_crop_id": 75,
        "regions": ("Barishal","Bogura","Chattogram","Cumilla","Dhaka","Dinajpur","Faridpur","Jashore","Khulna","Mymensingh","Rajshahi","Rangamati","Rangpur","Sylhet"),
    },
    {
        "id": "wheat",
        "name_en": "Wheat",
        "name_bn": "গম",
        "bamis_crop_id": 9,
        "regions": ("Barishal","Bogura","Cumilla","Dhaka","Dinajpur","Faridpur","Jashore","Khulna","Mymensingh","Rajshahi","Rangpur","Sylhet"),
    },
    {
        "id": "mustard",
        "name_en": "Mustard",
        "name_bn": "সরিষা",
        "bamis_crop_id": 44,
        "regions": ("Barishal","Bogura","Chattogram","Cumilla","Dhaka","Dinajpur","Faridpur","Jashore","Khulna","Mymensingh","Rajshahi","Rangpur","Sylhet"),
    },
    {
        "id": "lentil",
        "name_en": "Lentil",
        "name_bn": "মসুর",
        "bamis_crop_id": 58,
        "regions": ("Barishal","Bogura","Chattogram","Cumilla","Dhaka","Dinajpur","Faridpur","Jashore","Khulna","Mymensingh","Rajshahi","Rangpur","Sylhet"),
    },
    {
        "id": "jute",
        "name_en": "Jute",
        "name_bn": "পাট",
        "bamis_crop_id": 10,
        "regions": ("Barishal","Bogura","Cumilla","Dhaka","Dinajpur","Faridpur","Jashore","Khulna","Mymensingh","Rajshahi","Rangpur"),
    },
    {
        "id": "maize-kharif-1",
        "name_en": "Maize (Kharif-1)",
        "name_bn": "ভুট্টা (খরিফ-১)",
        "bamis_crop_id": 78,
        "regions": ("Bogura","Cumilla","Dhaka","Dinajpur","Mymensingh","Rajshahi","Rangamati","Rangpur"),
    },
    {
        "id": "green-gram-kharif-1",
        "name_en": "Green Gram (Kharif-1)",
        "name_bn": "মুগ (খরিফ-১)",
        "bamis_crop_id": 86,
        "regions": ("Bogura","Dhaka","Khulna","Mymensingh","Rajshahi"),
    },
)


def calendar_evidence_for_region(region: str) -> list[dict[str, Any]]:
    """Return official calendar PRESENCE only, never a suitability decision."""
    out: list[dict[str, Any]] = []
    for item in _CALENDARS:
        if region not in item["regions"]:
            continue
        crop_id = item["bamis_crop_id"]
        out.append(
            {
                "id": item["id"],
                "name_en": item["name_en"],
                "name_bn": item["name_bn"],
                "evidence_type": "official_crop_weather_calendar_presence",
                "region": region,
                "source_name": "BAMIS / Department of Agricultural Extension",
                "source_url": f"{BAMIS_BASE}/{crop_id}/",
                "status": "calendar_source_identified_not_rotation_rule",
                "meaning": "BAMIS publishes a crop-weather calendar for this regional hub. This does not by itself mean the crop is suitable for the farmer's field.",
            }
        )
    return out


def supported_calendar_regions() -> list[str]:
    return sorted({region for item in _CALENDARS for region in item["regions"]})
