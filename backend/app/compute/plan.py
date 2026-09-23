"""Bilingual three-month *preparation* routine; explicitly not crop or planting advice.

NASA POWER historical context is included with its actual 2024 year. Nothing in
this module chooses a crop, predicts future rain, or authorizes a sowing date.
"""
from __future__ import annotations

from datetime import date
from typing import Any

MISSING = {
    "previous_crop": ("Previous crop", "আগের ফসল"),
    "soil_ph": ("Soil pH", "মাটির pH"),
    "soil_texture": ("Soil texture", "মাটির ধরন"),
    "irrigation_mode": ("Irrigation availability", "সেচ সুবিধা"),
    "priorities": ("Planning priority", "পরিকল্পনার অগ্রাধিকার"),
}
PRIORITIES = {
    "water": ("Water resilience", "পানি ব্যবস্থাপনা"),
    "soil": ("Soil health", "মাটির স্বাস্থ্য"),
    "production_stability": ("Production stability", "উৎপাদন স্থিতিশীলতা"),
}
TASKS = {
    "record_rain": (
        "Each week, record actual rainfall, standing water, and any irrigation used in your own field.",
        "প্রতি সপ্তাহে আপনার জমিতে বাস্তবে হওয়া বৃষ্টি, জমে থাকা পানি এবং দেওয়া সেচের তথ্য লিখে রাখুন।",
    ),
    "verify_previous_crop": (
        "Record the previous crop and its harvest date before discussing any new rotation.",
        "নতুন ফসল আবর্তনের বিষয়ে পরামর্শের আগে আগের ফসল ও কাটার তারিখ লিখে রাখুন।",
    ),
    "get_soil_test": (
        "Ask a local agricultural extension officer where to test soil pH; do not guess it.",
        "মাটির pH কোথায় পরীক্ষা করা যায়, তা স্থানীয় কৃষি সম্প্রসারণ কর্মকর্তার কাছে জেনে নিন; অনুমান করবেন না।",
    ),
    "confirm_soil_texture": (
        "Confirm your soil texture with a local agricultural adviser before choosing crop constraints.",
        "ফসলের শর্ত নির্ধারণের আগে স্থানীয় কৃষি পরামর্শকের সঙ্গে মাটির ধরন যাচাই করুন।",
    ),
    "check_water": (
        "Check locally available irrigation water and discuss realistic access with an agricultural adviser.",
        "স্থানীয় সেচের পানি কতটা পাওয়া যায়, তা যাচাই করে কৃষি পরামর্শকের সঙ্গে আলোচনা করুন।",
    ),
    "record_irrigation": (
        "Write down when you irrigate and whether water remains in the field afterward.",
        "কখন সেচ দিয়েছেন এবং পরে জমিতে পানি জমেছে কি না, তা লিখে রাখুন।",
    ),
    "soil_priority": (
        "Take your soil test and previous-crop record to a qualified adviser to discuss soil-health priorities.",
        "মাটির পরীক্ষা ও আগের ফসলের তথ্য নিয়ে যোগ্য কৃষি পরামর্শকের সঙ্গে মাটির স্বাস্থ্য নিয়ে আলোচনা করুন।",
    ),
    "water_priority": (
        "Review your rainfall and irrigation notes with a local adviser before selecting a water-dependent crop.",
        "পানির চাহিদা বেশি এমন ফসল বাছাইয়ের আগে স্থানীয় পরামর্শকের সঙ্গে বৃষ্টি ও সেচের নোট পর্যালোচনা করুন।",
    ),
    "stability_priority": (
        "Discuss locally documented crop calendars and available resources with the extension office.",
        "স্থানীয় কৃষি সম্প্রসারণ অফিসের সঙ্গে যাচাইকৃত ফসল ক্যালেন্ডার ও প্রয়োজনীয় সম্পদ নিয়ে আলোচনা করুন।",
    ),
    "review_crop": (
        "If you are considering a crop, ask an extension officer to check its local season, soil and water requirements before planting.",
        "কোনো ফসলের কথা ভাবলে রোপণের আগে কৃষি কর্মকর্তার কাছে স্থানীয় মৌসুম, মাটি ও পানির উপযোগিতা যাচাই করুন।",
    ),
    "review_notes": (
        "At month-end, review your field notes and update any information that is still unknown.",
        "মাস শেষে জমির নোটগুলো দেখুন এবং অজানা থাকা তথ্য সম্ভব হলে পূরণ করুন।",
    ),
    "no_planting_dates": (
        "Do not treat this draft as a sowing date or crop prescription. Confirm an actionable calendar locally.",
        "এই খসড়াকে বপনের তারিখ বা ফসলের প্রেসক্রিপশন মনে করবেন না। স্থানীয়ভাবে চাষের সময়সূচি যাচাই করুন।",
    ),
}


def missing_fields(profile: dict[str, Any]) -> list[str]:
    missing = []
    if profile.get("previous_crop") is None:
        missing.append("previous_crop")
    if profile.get("soil_ph") is None:
        missing.append("soil_ph")
    if profile.get("soil_texture") == "unknown":
        missing.append("soil_texture")
    if profile.get("irrigation_mode") == "unknown":
        missing.append("irrigation_mode")
    if not profile.get("priorities"):
        missing.append("priorities")
    return missing


def three_month_preview(
    profile: dict[str, Any],
    monthly: dict[str, Any],
    *,
    start_year: int,
    start_month: int,
    candidate_crop: str | None,
) -> dict[str, Any]:
    """Create an auditable, non-prescriptive field-observation routine."""
    if profile["location_id"] != "rajshahi-pilot":
        raise ValueError("Only the provisional Rajshahi pilot is supported")
    if not 1 <= start_month <= 12 or not 2026 <= start_year <= 2035:
        raise ValueError("Unsupported planning window")
    if monthly["schema_version"] != "boponx-monthly/v1":
        raise ValueError("Unsupported climate aggregation version")
    if monthly["location_id"] != profile["location_id"]:
        raise ValueError("Location mismatch between farm and NASA dataset")
    source_years = {row["month"][:4] for row in monthly["metrics"]}
    if len(source_years) != 1:
        raise ValueError("Preview requires a single documented historical reference year")
    source_year = source_years.pop()
    source_months = {int(row["month"][5:7]): row for row in monthly["metrics"]}
    missing = missing_fields(profile)
    priority = (profile["priorities"] or [None])[0]
    months: list[dict[str, Any]] = []
    for index in range(3):
        year = start_year + (start_month - 1 + index) // 12
        month = (start_month - 1 + index) % 12 + 1
        reference = source_months.get(month)
        task_codes = ["record_rain"]
        if index == 0:
            if "previous_crop" in missing:
                task_codes.append("verify_previous_crop")
            if "soil_ph" in missing:
                task_codes.append("get_soil_test")
            if "soil_texture" in missing:
                task_codes.append("confirm_soil_texture")
        if profile["irrigation_mode"] in ("none", "limited", "unknown"):
            task_codes.append("check_water")
        else:
            task_codes.append("record_irrigation")
        if priority:
            task_codes.append({"water": "water_priority", "soil": "soil_priority",
                               "production_stability": "stability_priority"}[priority])
        if candidate_crop:
            task_codes.append("review_crop")
        task_codes += ["review_notes", "no_planting_dates"]
        months.append({
            "month_index": index + 1,
            "planning_month": date(year, month, 1).strftime("%Y-%m"),
            "historical_reference_month": f"{source_year}-{month:02d}" if reference else None,
            "historical_temperature_c": reference["temperature_mean_c"] if reference else None,
            "historical_precipitation_mm": reference["precipitation_total_mm"] if reference else None,
            "historical_valid_days": {
                "temperature": reference["temperature_valid_days"] if reference else 0,
                "precipitation": reference["precipitation_valid_days"] if reference else 0,
                "expected": reference["days_expected"] if reference else 0,
            },
            "tasks": [
                {"code": code, "en": TASKS[code][0], "bn": TASKS[code][1]}
                for code in dict.fromkeys(task_codes)
            ],
        })
    return {
        "schema_version": "boponx-preparation-brief/v1",
        "status": "DRAFT_NOT_AN_AGRONOMIC_CROP_PLAN",
        "location_id": profile["location_id"],
        "farm": {
            "previous_crop": profile["previous_crop"],
            "soil_ph": profile["soil_ph"],
            "soil_texture": profile["soil_texture"],
            "irrigation_mode": profile["irrigation_mode"],
            "priority": priority,
            "priority_label": PRIORITIES.get(priority) if priority else None,
            "candidate_crop_farmer_entered": candidate_crop,
            "missing_inputs": [{"field": key, "en": MISSING[key][0], "bn": MISSING[key][1]}
                               for key in missing],
        },
        "planning_window": {"start": months[0]["planning_month"], "end": months[-1]["planning_month"]},
        "months": months,
        "evidence": {
            "provider": monthly["provider"],
            "source_products": monthly["source_products"],
            "snapshot_id": monthly["snapshot_id"],
            "source_request_url": monthly["source_request_url"],
            "historical_year": source_year,
            "time_standard": monthly["period"]["time_standard"],
        },
        "limitations": {
            "en": "Preparation and monitoring only. Historical 2024 regional MERRA-2 data are not a forecast or farm measurement. No crop, planting date, soil treatment or water volume is prescribed. Confirm any farm action with local agricultural extension.",
            "bn": "এটি শুধু প্রস্তুতি ও পর্যবেক্ষণের খসড়া। ২০২৪ সালের আঞ্চলিক MERRA-2 তথ্য ভবিষ্যৎ পূর্বাভাস বা নির্দিষ্ট জমির পরিমাপ নয়। এখানে কোনো ফসল, বপনের তারিখ, মাটির চিকিৎসা বা সেচের পরিমাণ নির্ধারণ করা হয়নি। মাঠপর্যায়ের সিদ্ধান্তের আগে স্থানীয় কৃষি সম্প্রসারণ কর্মকর্তার পরামর্শ নিন।",
        },
    }
