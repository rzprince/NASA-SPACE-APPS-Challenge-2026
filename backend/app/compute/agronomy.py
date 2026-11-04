"""Source-indexed Bangladesh crop-calendar evidence with seasonal windows and agronomic roles.

This is deliberately NOT an unreviewed prescriptive recommender. It records which crops
have an official BAMIS crop-weather calendar for a regional evidence hub alongside
standard seasonal windows (Kharif-1, Kharif-2/Aman, Rabi/Boro) and water/soil roles.
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
        "season_code": "kharif-2",
        "window_en": "Jul – Nov (Kharif-2 / Monsoon)",
        "window_bn": "জুলাই – নভেম্বর (খরিফ-২ / বর্ষা)",
        "months": (7, 8, 9, 10, 11),
        "water_need_class": "moderate_rainfed",
        "water_need_note_en": "Primarily monsoon-rainfed (~600–900 mm); supplemental irrigation needed if Oct drought occurs",
        "water_need_note_bn": "মূলত বর্ষানির্ভর; অক্টোবরে খরা হলে সম্পূরক সেচ প্রয়োজন",
        "soil_role_en": "Main monsoon cereal; repeated puddling requires post-harvest pulse/oilseed break",
        "soil_role_bn": "প্রধান বর্ষা মৌসুমের ধান; মাটির স্বাস্থ্য রক্ষায় পরবর্তী রবিতে ডাল/তেলবীজ উপকারী",
        "regions": ("Barishal","Bogura","Chattogram","Cumilla","Dhaka","Dinajpur","Faridpur","Jashore","Khulna","Mymensingh","Rajshahi","Rangamati","Rangpur","Sylhet"),
    },
    {
        "id": "rice-aus",
        "name_en": "Rice Aus",
        "name_bn": "আউশ ধান",
        "bamis_crop_id": 7,
        "season_code": "kharif-1",
        "window_en": "Apr – Jul (Kharif-1 / Pre-Monsoon)",
        "window_bn": "এপ্রিল – জুলাই (খরিফ-১ / প্রাক-বর্ষা)",
        "months": (4, 5, 6, 7),
        "water_need_class": "moderate",
        "water_need_note_en": "Pre-monsoon showers + partial irrigation (~450–650 mm); lower groundwater draw than Boro",
        "water_need_note_bn": "প্রাক-বর্ষার বৃষ্টি ও আংশিক সেচনির্ভর; বোরোর তুলনায় ভূগর্ভস্থ পানি কম লাগে",
        "soil_role_en": "Short-duration Kharif-1 cereal; leaves narrower turnaround before Aman",
        "soil_role_bn": "স্বল্পমেয়াদি খরিফ-১ ফসল",
        "regions": ("Barishal","Bogura","Chattogram","Cumilla","Dhaka","Dinajpur","Faridpur","Jashore","Khulna","Mymensingh","Rajshahi","Rangamati","Rangpur","Sylhet"),
    },
    {
        "id": "rice-boro",
        "name_en": "Rice Boro",
        "name_bn": "বোরো ধান",
        "bamis_crop_id": 75,
        "season_code": "rabi",
        "window_en": "Dec – May (Rabi / Dry Winter-Spring)",
        "window_bn": "ডিসেম্বর – মে (রবি / শুষ্ক মৌসুম)",
        "months": (12, 1, 2, 3, 4, 5),
        "water_need_class": "high",
        "water_need_note_en": "High irrigation demand (~900–1,200 mm); AWD (Alternate Wetting & Drying) saves 20–25% water",
        "water_need_note_bn": "উচ্চ সেচ চাহিদা (~৯০০–১২০০ মিমি); পর্যায়ক্রমিক ভেজানো ও শুকানো (AWD) পদ্ধতিতে পানি সাশ্রয় হয়",
        "soil_role_en": "High nutrient draw; continuous Boro-Aman monoculture depletes zinc, sulfur & organic matter",
        "soil_role_bn": "একটানা বোরো-আমন চাষে মাটির জৈব পদার্থ, দস্তা ও গন্ধকের ঘাটতি হতে পারে",
        "regions": ("Barishal","Bogura","Chattogram","Cumilla","Dhaka","Dinajpur","Faridpur","Jashore","Khulna","Mymensingh","Rajshahi","Rangamati","Rangpur","Sylhet"),
    },
    {
        "id": "wheat",
        "name_en": "Wheat",
        "name_bn": "গম",
        "bamis_crop_id": 9,
        "season_code": "rabi",
        "window_en": "Nov – Mar (Rabi / Cool Winter)",
        "window_bn": "নভেম্বর – মার্চ (রবি / শীতকাল)",
        "months": (11, 12, 1, 2, 3),
        "water_need_class": "low_moderate",
        "water_need_note_en": "Requires only 2–3 irrigations (~250–350 mm), ~70% less water than Boro rice",
        "water_need_note_bn": "বোরো ধানের তুলনায় প্রায় ৭০% কম পানি লাগে (২–৩টি সেচ, ~২৫০–৩৫০ মিমি)",
        "soil_role_en": "Upland winter cereal; sensitive to waterlogging and late-sowing terminal heat (>32°C in Feb)",
        "soil_role_bn": "জলাবদ্ধতা ও দেরিতে বপনজনিত ফাল্গুনের অতিরিক্ত তাপমাত্রার প্রতি সংবেদনশীল",
        "regions": ("Barishal","Bogura","Cumilla","Dhaka","Dinajpur","Faridpur","Jashore","Khulna","Mymensingh","Rajshahi","Rangpur","Sylhet"),
    },
    {
        "id": "mustard",
        "name_en": "Mustard",
        "name_bn": "সরিষা",
        "bamis_crop_id": 44,
        "season_code": "rabi",
        "window_en": "Nov – Feb (Short-Duration Early Rabi)",
        "window_bn": "নভেম্বর – ফেব্রুয়ারি (স্বল্পমেয়াদি আগাম রবি)",
        "months": (11, 12, 1, 2),
        "water_need_class": "low",
        "water_need_note_en": "Low water demand (~180–240 mm; 1–2 light irrigations); uses post-Aman residual soil moisture",
        "water_need_note_bn": "কম পানি লাগে (~১৮০–২৪০ মিমি); আমন পরবর্তী মাটির জো/রস ব্যবহার করে চাষ করা যায়",
        "soil_role_en": "75–85 day bridge crop between Aman and Boro; leaf drop adds organic matter and breaks cereal pests",
        "soil_role_bn": "আমন ও বোরোর মধ্যবর্তী ৭৫–৮৫ দিনের ফসল; ঝরা পাতা জৈব সার যোগ করে এবং পোকার চক্র ভাঙে",
        "regions": ("Barishal","Bogura","Chattogram","Cumilla","Dhaka","Dinajpur","Faridpur","Jashore","Khulna","Mymensingh","Rajshahi","Rangpur","Sylhet"),
    },
    {
        "id": "lentil",
        "name_en": "Lentil",
        "name_bn": "মসুর",
        "bamis_crop_id": 58,
        "season_code": "rabi",
        "window_en": "Nov – Mar (Rabi Pulse)",
        "window_bn": "নভেম্বর – মার্চ (রবি ডাল মৌসুম)",
        "months": (11, 12, 1, 2, 3),
        "water_need_class": "low",
        "water_need_note_en": "Very low water demand (~150–220 mm); thrives on residual moisture in well-drained loam",
        "water_need_note_bn": "অতি কম পানি লাগে (~১৫০–২২০ মিমি); সুনিষ্কাশিত দোআঁশ মাটিতে অবশিষ্ট রসে ভালো হয়",
        "soil_role_en": "Nitrogen-fixing legume (+30–50 kg N/ha biological fixation); highly sensitive to standing water",
        "soil_role_bn": "নাইট্রোজেন সংবন্ধনকারী ডাল ফসল (হেক্টরে ৩০–৫০ কেজি N যোগ করে); জলাবদ্ধতা একেবারেই সহ্য পারে না",
        "regions": ("Barishal","Bogura","Chattogram","Cumilla","Dhaka","Dinajpur","Faridpur","Jashore","Khulna","Mymensingh","Rajshahi","Rangpur","Sylhet"),
    },
    {
        "id": "jute",
        "name_en": "Jute",
        "name_bn": "পাট",
        "bamis_crop_id": 10,
        "season_code": "kharif-1",
        "window_en": "Mar – Jul (Kharif-1 Fibre Crop)",
        "window_bn": "মার্চ – জুলাই (খরিফ-১ আঁশ ফসল)",
        "months": (3, 4, 5, 6, 7),
        "water_need_class": "moderate",
        "water_need_note_en": "Uses pre-monsoon and early monsoon rain (~500–700 mm); requires retting water in Jul–Aug",
        "water_need_note_bn": "প্রাক-বর্ষার বৃষ্টিতে বৃদ্ধি পায়; জুলাই–আগস্টে পাট পচানোর জন্য পানির প্রয়োজন হয়",
        "soil_role_en": "Deep taproot breaks plough pan and sheds 3–4 tonnes/ha dry leaf litter before Aman rice",
        "soil_role_bn": "গভীর মূল মাটির শক্ত স্তর (প্লাউ প্যান) ভাঙে এবং পাতা ঝরে মাটিতে প্রচুর জৈব পদার্থ যোগ করে",
        "regions": ("Barishal","Bogura","Cumilla","Dhaka","Dinajpur","Faridpur","Jashore","Khulna","Mymensingh","Rajshahi","Rangpur"),
    },
    {
        "id": "maize-kharif-1",
        "name_en": "Maize (Kharif-1)",
        "name_bn": "ভুট্টা (খরিফ-১)",
        "bamis_crop_id": 78,
        "season_code": "kharif-1",
        "window_en": "Feb – Jun (Late Rabi / Kharif-1)",
        "window_bn": "ফেব্রুয়ারি – জুন (নাবী রবি / খরিফ-১)",
        "months": (2, 3, 4, 5, 6),
        "water_need_class": "moderate",
        "water_need_note_en": "Moderate water use (~400–550 mm); much higher water-use efficiency than Boro rice",
        "water_need_note_bn": "মাঝারি পানির চাহিদা (~৪০০–৫৫০ মিমি); বোরো ধানের চেয়ে পানির ব্যবহার দক্ষতা অনেক বেশি",
        "soil_role_en": "High-biomass C4 crop; requires balanced NPK and good drainage during May storms",
        "soil_role_bn": "উচ্চ জৈবভর সম্পন্ন ফসল; সুষম সার এবং মে মাসের ঝড়-বৃষ্টিতে পানি নিষ্কাশন প্রয়োজন",
        "regions": ("Bogura","Cumilla","Dhaka","Dinajpur","Mymensingh","Rajshahi","Rangamati","Rangpur"),
    },
    {
        "id": "green-gram-kharif-1",
        "name_en": "Green Gram (Kharif-1)",
        "name_bn": "মুগ (খরিফ-১)",
        "bamis_crop_id": 86,
        "season_code": "kharif-1",
        "window_en": "Feb – May (Short-Duration Kharif-1 Pulse)",
        "window_bn": "ফেব্রুয়ারি – মে (স্বল্পমেয়াদি খরিফ-১ মুগ ডাল)",
        "months": (2, 3, 4, 5),
        "water_need_class": "low",
        "water_need_note_en": "Low water demand (~200–280 mm; 60–65 days); ideal dry-to-monsoon bridge crop",
        "water_need_note_bn": "কম পানি লাগে (~২০০–২৮০ মিমি; ৬০–৬৫ দিন); শুষ্ক মৌসুম ও আমনের মধ্যবর্তী আদর্শ ডাল ফসল",
        "soil_role_en": "Fixes atmospheric nitrogen and green biomass can be incorporated directly into soil before Aman",
        "soil_role_bn": "বায়ুমণ্ডলীয় নাইট্রোজেন সংবন্ধন করে এবং শুঁটি তোলার পর গাছ মাটিতে মিশিয়ে সবুজ সার করা যায়",
        "regions": ("Bogura","Dhaka","Khulna","Mymensingh","Rajshahi"),
    },
)


def calendar_evidence_for_region(region: str) -> list[dict[str, Any]]:
    """Return official calendar PRESENCE and agronomic reference metadata, never an unverified suitability rank."""
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
                "season_code": item["season_code"],
                "window_en": item["window_en"],
                "window_bn": item["window_bn"],
                "months": list(item["months"]),
                "water_need_class": item["water_need_class"],
                "water_need_note_en": item["water_need_note_en"],
                "water_need_note_bn": item["water_need_note_bn"],
                "soil_role_en": item["soil_role_en"],
                "soil_role_bn": item["soil_role_bn"],
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
