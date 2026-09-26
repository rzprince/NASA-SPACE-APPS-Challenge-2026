"""Deterministic, stage-aware 90-day preparation plan.

The routine is intentionally useful without pretending to be a crop prescription.
Every month has a different objective. Crop-specific instructions remain blocked
until source-reviewed agronomic rules are integrated.
"""
from __future__ import annotations

from datetime import date
from typing import Any

MONTH_NAMES = {
    1: ("January", "জানুয়ারি"), 2: ("February", "ফেব্রুয়ারি"), 3: ("March", "মার্চ"),
    4: ("April", "এপ্রিল"), 5: ("May", "মে"), 6: ("June", "জুন"),
    7: ("July", "জুলাই"), 8: ("August", "আগস্ট"), 9: ("September", "সেপ্টেম্বর"),
    10: ("October", "অক্টোবর"), 11: ("November", "নভেম্বর"), 12: ("December", "ডিসেম্বর"),
}

TASKS = {
    "baseline_crop": (
        "Write down the last crop and roughly when it left the field. If you are unsure, ask the person who worked the field last season.",
        "শেষবার কোন ফসল ছিল এবং আনুমানিক কখন জমি খালি হয়েছে তা লিখুন। নিশ্চিত না হলে আগের মৌসুমে যিনি জমিতে কাজ করেছেন তাঁর কাছে জেনে নিন।",
    ),
    "baseline_water": (
        "For two weeks, note where the field gets water from and whether irrigation was actually needed.",
        "দুই সপ্তাহ ধরে জমির পানি কোথা থেকে আসে এবং বাস্তবে সেচ দিতে হয়েছে কি না তা লিখে রাখুন।",
    ),
    "baseline_drainage": (
        "After the next heavy rain, note whether water drains quickly, stays for hours, or remains into the next day.",
        "পরবর্তী ভারী বৃষ্টির পর পানি দ্রুত নেমে যায়, কয়েক ঘণ্টা থাকে, নাকি পরের দিনও থাকে—তা লিখে রাখুন।",
    ),
    "soil_test_path": (
        "Do not guess soil pH. If a future crop choice depends on soil chemistry, ask the local extension office where a soil test can be done.",
        "মাটির pH অনুমান করবেন না। ভবিষ্যৎ ফসল বাছাইয়ে মাটির রাসায়নিক তথ্য দরকার হলে স্থানীয় কৃষি অফিসে মাটি পরীক্ষা কোথায় করা যায় জেনে নিন।",
    ),
    "soil_report_record": (
        "Keep the soil-test report date and source with the farm notes; only use the numbers that actually appear on that report.",
        "মাটি পরীক্ষার রিপোর্টের তারিখ ও উৎস জমির নোটের সঙ্গে রাখুন; রিপোর্টে যে সংখ্যাগুলো আছে শুধু সেগুলোই ব্যবহার করুন।",
    ),
    "recent_rain_context": (
        "Check the latest available NASA rainfall layer for your selected area, then compare it with what you actually saw in the field.",
        "নির্বাচিত এলাকার সর্বশেষ পাওয়া NASA বৃষ্টির স্তর দেখুন এবং মাঠে বাস্তবে যা দেখেছেন তার সঙ্গে মিলিয়ে নিন।",
    ),
    "weekly_water_log": (
        "Once each week, record rain, irrigation, and standing water as three separate observations.",
        "প্রতি সপ্তাহে বৃষ্টি, সেচ এবং জমে থাকা পানি—এই তিনটি বিষয় আলাদা করে লিখুন।",
    ),
    "water_priority_check": (
        "Before the next irrigation decision, review recent rain and your field notes together instead of relying on the satellite layer alone.",
        "পরবর্তী সেচের সিদ্ধান্তের আগে শুধু স্যাটেলাইট স্তরের ওপর নির্ভর না করে সাম্প্রতিক বৃষ্টি ও নিজের মাঠের নোট একসঙ্গে দেখুন।",
    ),
    "soil_priority_check": (
        "Photograph or note visible surface changes, crop residue, cracking, or persistent standing water so a local adviser has field evidence to review.",
        "মাটির ওপরের দৃশ্যমান পরিবর্তন, ফসলের অবশিষ্টাংশ, ফাটল বা দীর্ঘ সময় পানি জমে থাকা ছবি বা নোটে রাখুন যাতে স্থানীয় পরামর্শক মাঠের প্রমাণ দেখতে পারেন।",
    ),
    "stability_priority_check": (
        "Record any week when water access, heavy rain, labour, or field condition disrupted normal farm work.",
        "যে সপ্তাহে পানি, ভারী বৃষ্টি, শ্রম বা জমির অবস্থার কারণে স্বাভাবিক কাজ ব্যাহত হয়েছে তা লিখে রাখুন।",
    ),
    "decision_review": (
        "At the end of the third month, review the field notes and mark which facts are known, uncertain, or still missing.",
        "তৃতীয় মাসের শেষে মাঠের নোট দেখে কোন তথ্য জানা, অনিশ্চিত বা এখনও অনুপস্থিত তা চিহ্নিত করুন।",
    ),
    "calendar_check": (
        "Use the crop-weather calendar for your region as evidence to discuss the next seasonal option; BoponX will not invent a planting date.",
        "পরবর্তী মৌসুমের বিকল্প নিয়ে আলোচনায় আপনার অঞ্চলের ফসল-আবহাওয়া ক্যালেন্ডারকে প্রমাণ হিসেবে ব্যবহার করুন; BoponX নিজে কোনো বপনের তারিখ বানাবে না।",
    ),
    "rotation_gate": (
        "Do not lock a crop rotation until the selected area's crop calendars and sequence rules have passed source review.",
        "নির্বাচিত এলাকার ফসল ক্যালেন্ডার ও আবর্তন নিয়ম উৎস-পর্যালোচনা না হওয়া পর্যন্ত ফসল আবর্তন চূড়ান্ত করবেন না।",
    ),
    "export_report": (
        "Print or save this report with the location, timestamps, field notes, and evidence links before discussing the next decision.",
        "পরবর্তী সিদ্ধান্ত নিয়ে আলোচনার আগে অবস্থান, সময়, মাঠের নোট ও প্রমাণের লিংকসহ এই রিপোর্টটি প্রিন্ট বা সংরক্ষণ করুন।",
    ),
}


def _month(start_year: int, start_month: int, offset: int) -> tuple[int, int]:
    year = start_year + (start_month - 1 + offset) // 12
    month = (start_month - 1 + offset) % 12 + 1
    return year, month


def make_90_day_plan(
    profile: dict[str, Any],
    context: dict[str, Any],
    *,
    start_year: int,
    start_month: int,
    recent_environment: dict[str, Any] | None = None,
    baseline_environment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not 1 <= start_month <= 12:
        raise ValueError("Unsupported start month")
    if not 2026 <= start_year <= 2035:
        raise ValueError("Unsupported start year")

    soil_test = profile.get("soil_test", "unknown")
    priority = profile.get("priority", "production_stability")

    month1 = ["baseline_crop", "baseline_water", "baseline_drainage"]
    month1.append("soil_report_record" if soil_test == "yes" else "soil_test_path")

    month2 = ["recent_rain_context", "weekly_water_log"]
    month2.append({
        "water": "water_priority_check",
        "soil": "soil_priority_check",
        "production_stability": "stability_priority_check",
    }[priority])

    month3 = ["decision_review", "calendar_check", "rotation_gate", "export_report"]

    phases = [
        ("Know the field", "জমিকে বুঝুন", "Build a trustworthy baseline before making a seasonal choice.", "মৌসুমি সিদ্ধান্তের আগে মাঠের নির্ভরযোগ্য ভিত্তি তৈরি করুন।", month1),
        ("Watch the change", "পরিবর্তন দেখুন", "Compare recent Earth-observation context with what is actually happening in the field.", "সাম্প্রতিক Earth observation তথ্যের সঙ্গে মাঠের বাস্তব অবস্থা মিলিয়ে দেখুন।", month2),
        ("Decide the next move", "পরবর্তী পদক্ষেপ ঠিক করুন", "Turn three months of evidence into questions and constraints for the next seasonal decision.", "তিন মাসের প্রমাণকে পরবর্তী মৌসুমি সিদ্ধান্তের প্রশ্ন ও সীমাবদ্ধতায় রূপ দিন।", month3),
    ]

    months = []
    for index, (title_en, title_bn, objective_en, objective_bn, task_codes) in enumerate(phases):
        year, month = _month(start_year, start_month, index)
        months.append({
            "index": index + 1,
            "planning_month": f"{year:04d}-{month:02d}",
            "month_name": {"en": MONTH_NAMES[month][0], "bn": MONTH_NAMES[month][1]},
            "phase": {"en": title_en, "bn": title_bn},
            "objective": {"en": objective_en, "bn": objective_bn},
            "tasks": [{"code": code, "en": TASKS[code][0], "bn": TASKS[code][1]} for code in task_codes],
        })

    region = context["nearest_supported_region"]
    return {
        "status": "DECISION_PREPARATION_READY",
        "location": {
            "coordinates": context["coordinates"],
            "region_id": region["id"],
            "region_name_en": region["name_en"],
            "region_name_bn": region["name_bn"],
            "distance_to_reference_km": region["distance_km"],
        },
        "farmer_context": profile,
        "planning_window": {"start": months[0]["planning_month"], "end": months[-1]["planning_month"]},
        "months": months,
        "recent_environment": recent_environment,
        "historical_baseline": baseline_environment,
        "rotation_explorer": {
            "status": "EVIDENCE_REVIEW_REQUIRED",
            "message_en": "Rotation alternatives stay locked until crop calendars, crop requirements, soil constraints and crop-sequence rules for this region are source-reviewed.",
            "message_bn": "এই অঞ্চলের ফসল ক্যালেন্ডার, ফসলের চাহিদা, মাটির সীমাবদ্ধতা ও ফসল-ক্রমের নিয়ম উৎস-পর্যালোচনা না হওয়া পর্যন্ত আবর্তন বিকল্প দেখানো হবে না।",
        },
        "evidence": {
            "nasa_sources": context["nasa_sources"],
            "agricultural_sources": context["agricultural_sources"],
            "calendar_evidence": context.get("calendar_evidence", []),
        },
        "limitations": {
            "en": "This is a location-aware preparation and decision-support routine, not a crop prescription or forecast. Satellite and reanalysis data describe regional context; field observations and locally reviewed agricultural rules are still required for crop-specific decisions.",
            "bn": "এটি অবস্থানভিত্তিক প্রস্তুতি ও সিদ্ধান্ত-সহায়তা রুটিন; এটি ফসলের প্রেসক্রিপশন বা আবহাওয়ার পূর্বাভাস নয়। স্যাটেলাইট ও পুনর্বিশ্লেষণ তথ্য আঞ্চলিক প্রেক্ষাপট দেয়; ফসলভিত্তিক সিদ্ধান্তে মাঠের পর্যবেক্ষণ ও স্থানীয়ভাবে যাচাইকৃত কৃষি নিয়ম এখনও প্রয়োজন।",
        },
    }
