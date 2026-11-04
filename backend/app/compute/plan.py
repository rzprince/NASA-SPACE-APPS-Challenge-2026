"""Deterministic location-aware 90-day decision support plan and 3-strategy rotation explorer.

The plan adapts dynamically to every farmer input (recent crop history, intended crop,
water source, post-rain drainage behavior, soil test report & pH, priority, equipment access,
and market/forage preference), regional BAMIS calendars, 64-district Bangladesh agro-ecological
profiles, recent NASA POWER agroclimate & soil-wetness signals, and 2001–2020 monthly climatology references.
"""
from __future__ import annotations

from typing import Any

MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
    7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December",
}

MONTH_NAMES_BN = {
    1: "জানুয়ারি", 2: "ফেব্রুয়ারি", 3: "মার্চ", 4: "এপ্রিল", 5: "মে", 6: "জুন",
    7: "জুলাই", 8: "আগস্ট", 9: "সেপ্টেম্বর", 10: "অক্টোবর", 11: "নভেম্বর", 12: "ডিসেম্বর",
}

CROP_LABELS = {
    "rice": "Rice",
    "wheat": "Wheat",
    "maize": "Maize",
    "pulse": "Pulse (Lentil / Mungbean)",
    "mustard": "Mustard",
    "vegetables": "Vegetables",
    "jute": "Jute",
    "other": "Other crop",
}

CROP_LABELS_BN = {
    "rice": "ধান",
    "wheat": "গম",
    "maize": "ভুট্টা",
    "pulse": "ডাল (মসুর / মুগ)",
    "mustard": "সরিষা",
    "vegetables": "সবজি",
    "jute": "পাট",
    "other": "অন্যান্য ফসল",
}

CROP_CALENDAR_PREFIXES = {
    "rice": ("rice-",),
    "wheat": ("wheat",),
    "maize": ("maize",),
    "pulse": ("lentil", "green-gram"),
    "mustard": ("mustard",),
    "jute": ("jute",),
}

EQUIPMENT_LABELS = {
    "manual_traditional": "Manual / Traditional Draft",
    "power_tiller_machinery": "2-Wheel Power Tiller / Tractor",
    "conservation_zero_till": "Zero-Till / Strip-Till / Bed Planter",
    "unknown": "Not specified",
}

MARKET_LABELS = {
    "household_subsistence": "Household Food Security",
    "local_cash_market": "Local Cash & Oilseed/Pulse Market",
    "high_value_commercial": "High-Value Commercial / Urban Supply",
    "forage_livestock": "Dual-Purpose Grain + Livestock Forage",
    "unknown": "Not specified",
}

# Crop-specific agronomic field guidance used to tailor the 3-stage 90-day plan
CROP_AGRONOMY_GUIDE: dict[str, dict[str, str]] = {
    "rice": {
        "m1_prep_en": "Prepare level bunds to hold 3–5 cm standing water uniformly; if following continuous rice, incorporate decomposed organic matter before puddling.",
        "m1_prep_bn": "জমিতে ৩–৫ সেমি পানি সমানভাবে ধরে রাখতে আইল মেরামত ও জমি সমতল করুন; টানা ধান চাষ হলে জমি তৈরির সময় পচা জৈব সার মেশান।",
        "m2_care_en": "Practice Alternate Wetting and Drying (AWD — irrigate when perforated PVC pipe water drops 15 cm below surface) during tillering to save 20–25% irrigation water and strengthen roots.",
        "m2_care_bn": "কুশি গজানোর পর্যায়ে পর্যায়ক্রমিক ভেজানো ও শুকানো (AWD) পদ্ধতি অনুসরণ করুন; এতে ২০–২৫% সেচের পানি সাশ্রয় হয় এবং শিকড় মজবুত হয়।",
        "m3_next_en": "At 80% panicle maturity, drain the field 10–12 days before harvest to preserve residual soil moisture (jo) for an immediate post-harvest Mustard or Pulse bridge crop.",
        "m3_next_bn": "শীষের ৮০% ধান পেকে গেলে কাটার ১০–১২ দিন আগে পানি বের করে দিন, যাতে মাটির জো/রস ব্যবহার করে পরপরই সরিষা বা ডাল বপন করা যায়।",
    },
    "wheat": {
        "m1_prep_en": "Ensure well-pulverized, well-drained seedbed with shallow drainage furrows every 3–4 meters; wheat roots suffer severely if winter rain stands for >24 hours.",
        "m1_prep_bn": "জমি ভালোভাবে চাষ দিয়ে ঝুরঝুরে করুন এবং ৩–৪ মিটার পরপর হালকা নালা রাখুন; গমের জমিতে ২৪ ঘণ্টার বেশি পানি জমে থাকলে চারা নষ্ট হয়।",
        "m2_care_en": "Apply critical first irrigation at Crown Root Initiation (CRI, 17–21 days after sowing) and second at heading/flowering; monitor NASA POWER max temperatures for February heat stress (>32°C).",
        "m2_care_bn": "বপনের ১৭–২১ দিনের মধ্যে মুকুট শিকড় (CRI) পর্যায়ে প্রথম সেচ এবং শীষ বের হওয়ার সময় দ্বিতীয় সেচ দিন; ফেব্রুয়ারির অতিরিক্ত তাপমাত্রা (>৩২°C) পর্যবেক্ষণ করুন।",
        "m3_next_en": "Harvest promptly at grain hard-dough stage before pre-monsoon storms and plan a short-duration Kharif-1 Mungbean or Jute rotation to break cereal disease carryover.",
        "m3_next_bn": "প্রাক-বর্ষার ঝড়-বৃষ্টির আগেই গম কেটে ফেলুন এবং পরবর্তীতে খরিফ-১ মৌসুমে মুগ ডাল বা পাট চাষের পরিকল্পনা করুন।",
    },
    "maize": {
        "m1_prep_en": "Form raised ridges/furrows (60 cm row spacing) so irrigation can be applied efficiently in furrows while protecting roots from sudden heavy rain.",
        "m1_prep_bn": "সারি থেকে সারি ৬০ সেমি দূরত্বে ভেলী বা বেড তৈরি করুন, যাতে নালায় পরিমিত সেচ দেওয়া যায় এবং হঠাৎ বৃষ্টিতে জলাবদ্ধতা না হয়।",
        "m2_care_en": "Avoid moisture stress during knee-high, tasseling, and silking stages; scout whorls weekly for Fall Armyworm and earthing-up soil at 30–35 days to prevent wind lodging.",
        "m2_care_bn": "হাঁটু সমান উচ্চতা, মোচা ও ফুল আসার সময় রসের ঘাটতি হতে দেবেন না; ফল আর্মিওয়ার্ম পোকা পর্যবেক্ষণ করুন এবং ৩০–৩৫ দিনে গোড়ায় মাটি তুলে দিন।",
        "m3_next_en": "Chop and incorporate maize stalks (or use green stover as high-energy livestock forage) and pair the next season with a nitrogen-fixing legume (Lentil/Mungbean) to replenish nitrogen.",
        "m3_next_bn": "ভুট্টা মাটি থেকে প্রচুর পুষ্টি টানে; তাই ভুট্টা তোলার পর জমিতে জৈব অবশিষ্টাংশ মেশান (বা গোখাদ্য হিসেবে ব্যবহার করুন) এবং পরবর্তী মৌসুমে ডাল জাতীয় ফসল যুক্ত করুন।",
    },
    "pulse": {
        "m1_prep_en": "Use residual post-harvest soil moisture (jo) for sowing; coat pulse seeds with crop-specific Rhizobium bio-inoculant in the shade just before sowing to boost root nitrogen nodules.",
        "m1_prep_bn": "আমন পরবর্তী মাটির জো অবস্থায় বীজ বপন করুন; বপনের আগে ছায়ায় ডালের বীজে রাইজোবিয়াম জীবাণুসার মাখান, যা শিকড়ে নাইট্রোজেন গুটি বাড়াতে সাহায্য করে।",
        "m2_care_en": "Do not over-irrigate pulses; keep perimeter drainage channels open because standing water causes root rot/wilt, and scout for pod borer or Stemphylium blight during foggy/humid weeks.",
        "m2_care_bn": "ডাল ফসলে অতিরিক্ত সেচ দেবেন না; জমির চারপাশে নিকাশ নালা চালু রাখুন কারণ জলাবদ্ধতায় গোড়া পচা রোগ হয়, এবং কুয়াশাচ্ছন্ন আবহাওয়ায় ব্লাইট ও ফল ছিদ্রকারী পোকা লক্ষ্য করুন।",
        "m3_next_en": "After picking mature pods, incorporate the nitrogen-rich green/dry pulse plants directly into the topsoil to save 25–30% urea fertilizer in the following cereal crop.",
        "m3_next_bn": "ডালের শুঁটি তোলার পর নাইট্রোজেন-সমৃদ্ধ গাছগুলো মাটির সাথে মিশিয়ে দিন; এতে পরবর্তী ধানে ইউরিয়া সারের খরচ ২৫–৩০% কমে।",
    },
    "mustard": {
        "m1_prep_en": "Sow short-duration mustard (75–85 days) immediately as post-monsoon topsoil reaches field capacity (jo), applying recommended sulfur and boron if supported by local soil guidance.",
        "m1_prep_bn": "বর্ষা শেষে মাটিতে জো আসার সাথে সাথে স্বল্পমেয়াদি সরিষা (৭৫–৮৫ দিন) বপন করুন এবং স্থানীয় কৃষি পরামর্শ অনুযায়ী সালফার ও বোরন ঘাটতি বিবেচনা করুন।",
        "m2_care_en": "Give one light irrigation at 20–25 days (before flowering) if soil is dry, ensure field drains within hours, and monitor humid/cloudy spells in January for aphids (joka poka) and Alternaria leaf spot.",
        "m2_care_bn": "মাটি শুষ্ক হলে ফুল আসার আগে (২০–২৫ দিনে) একটি হালকা সেচ দিন এবং জানুয়ারির মেঘলা/আর্দ্র আবহাওয়ায় জাব পোকা ও পাতার দাগ রোগ পর্যবেক্ষণ করুন।",
        "m3_next_en": "Harvest when 75–80% siliquae turn golden yellow to prevent shattering, leaving a clean turnaround window for Boro rice, Mungbean, or Aus.",
        "m3_next_bn": "৭৫–৮০% শুঁটি খড়ের রঙ ধারণ করলেই সরিষা কেটে ফেলুন, যাতে পরবর্তী বোরো, মুগ ডাল বা আউশ ফসল সময়মতো শুরু করা যায়।",
    },
    "vegetables": {
        "m1_prep_en": "Construct 15–20 cm raised beds with 30 cm drainage alleys and apply well-decomposed compost/vermicompost; never plant solanaceous vegetables repeatedly in the same bed without rotation.",
        "m1_prep_bn": "১৫–২০ সেমি উঁচু বেড ও ৩০ সেমি নিকাশ নালা তৈরি করে পচা জৈব সার/ভার্মিকম্পোস্ট মেশান; একই বেডে বারবার একই গোত্রের সবজি (যেমন বেগুন/টমেটো/আলু) চাষ করবেন না।",
        "m2_care_en": "Use mulch (straw or dry leaves) on raised beds to cut evaporation (ET0), irrigate lightly in furrows, and use pheromone/yellow sticky traps before chemical sprays.",
        "m2_care_bn": "মাটির রস ধরে রাখতে বেডে খড়ের মালচিং ব্যবহার করুন, নালায় পরিমিত সেচ দিন এবং পোকা দমনে ফেরোমন ও হলুদ আঠালো ফাঁদ ব্যবহার করুন।",
        "m3_next_en": "Remove diseased crop debris completely at harvest and rotate the bed to a cereal, pulse, or green-manure crop to break soil-borne bacterial wilt and nematode cycles.",
        "m3_next_bn": "ফসল শেষে রোগাক্রান্ত গাছের অংশ সরিয়ে ফেলুন এবং মাটিবাহিত উইল্ট ও কৃমি দমনে পরবর্তী মৌসুমে ডাল বা দানা ফসল পর্যায়ক্রমে চাষ করুন।",
    },
    "jute": {
        "m1_prep_en": "Prepare a fine seedbed with early pre-monsoon showers (Mar–Apr); jute taproots break compacted plough pans left by shallow-rooted rice.",
        "m1_prep_bn": "চৈত্র–বৈশাখের প্রথম বৃষ্টিতে জমি গভীরভাবে চাষ দিয়ে ঝুরঝুরে করুন; পাটের গভীর মূল ধানের নিচের শক্ত স্তর (প্লাউ প্যান) ভেঙে মাটির বায়ু চলাচল বাড়ায়।",
        "m2_care_en": "Thin plants to proper spacing at 25–35 days, weed twice, and drain excess standing water during early vegetative growth while monitoring for semilooper and yellow mite.",
        "m2_care_bn": "২৫–৩৫ দিনে চারা পাতলা ও আগাছা পরিষ্কার করুন; প্রাথমিক বৃদ্ধির সময় অতিরিক্ত জমে থাকা পানি বের করে দিন এবং ঘোড়া পোকা ও মাকড় পর্যবেক্ষণ করুন।",
        "m3_next_en": "Allow shed jute leaves to decompose in the field before transplanting T. Aman rice, providing 3–4 tonnes/ha of organic matter.",
        "m3_next_bn": "পাট কাটার পর ঝরে পড়া পাতা জমিতেই পচতে দিন; এটি আমন ধানের জন্য হেক্টরে ৩–৪ টন জৈব পদার্থ সরবরাহ করে।",
    },
    "other": {
        "m1_prep_en": "Match seedbed elevation (flat, ridge, or raised bed) to the crop's root tolerance for waterlogging and drought.",
        "m1_prep_bn": "ফসলের শিকড়ের সহনশীলতা অনুযায়ী সমতল, ভেলী বা উঁচু বেড পদ্ধতিতে জমি প্রস্তুত করুন।",
        "m2_care_en": "Schedule irrigation by comparing weekly field soil moisture at 10 cm depth against recent NASA POWER rainfall and evaporative demand (ET0).",
        "m2_care_bn": "মাটির ১০ সেমি গভীরে রসের অবস্থা এবং নাসা বৃষ্টিপাত ও বাষ্পীভবন (ET0) তুলনা করে সেচ প্রদান করুন।",
        "m3_next_en": "Alternate crop families in the next season so deep-rooted and shallow-rooted crops balance soil nutrients and break pest cycles.",
        "m3_next_bn": "মাটির পুষ্টি ভারসাম্য রক্ষা ও রোগ-পোকার চক্র ভাঙতে পরবর্তী মৌসুমে ভিন্ন গোত্রের ফসল নির্বাচন করুন।",
    },
}


def _month(start_year: int, start_month: int, offset: int) -> tuple[int, int]:
    year = start_year + (start_month - 1 + offset) // 12
    month = (start_month - 1 + offset) % 12 + 1
    return year, month


def _task(
    code: str,
    text_en: str,
    category: str,
    reason: str,
    evidence: str = "farmer_and_local_context",
    *,
    text_bn: str | None = None,
    reason_bn: str | None = None,
) -> dict[str, str]:
    return {
        "code": code,
        "en": text_en,
        "bn": text_bn or text_en,
        "category": category,
        "reason": reason,
        "reason_bn": reason_bn or reason,
        "evidence": evidence,
    }


def _history(profile: dict[str, Any]) -> list[str]:
    crops: list[str] = []
    for crop in profile.get("previous_crops") or []:
        if isinstance(crop, str) and crop and crop not in crops:
            crops.append(crop)
    last = profile.get("previous_crop")
    if isinstance(last, str) and last and last not in crops:
        crops.insert(0, last)
    return crops[:4]


def _calendar_matches(crop: str | None, calendars: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not crop:
        return []
    prefixes = CROP_CALENDAR_PREFIXES.get(crop, ())
    if not prefixes:
        return []
    return [
        item for item in calendars
        if any(str(item.get("id", "")).startswith(prefix) for prefix in prefixes)
    ]


def _baseline_summaries(
    baseline_environment: dict[str, Any] | None,
    baseline_window: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if isinstance(baseline_window, dict) and baseline_window.get("status") == "available":
        summaries = baseline_window.get("summaries")
        if isinstance(summaries, list):
            return [item for item in summaries if isinstance(item, dict)]
    if isinstance(baseline_environment, dict) and baseline_environment.get("status") == "available":
        summary = baseline_environment.get("summary")
        if isinstance(summary, dict):
            return [summary]
    return []


def _recent_condition(
    recent_environment: dict[str, Any] | None,
    first_baseline: dict[str, Any] | None,
) -> dict[str, Any]:
    result = {
        "rain_signal": "unavailable",
        "temperature_signal": "unavailable",
        "recent_daily_rain_mm": None,
        "baseline_daily_rain_mm": None,
        "recent_temperature_c": None,
        "baseline_temperature_c": None,
        "et0_daily_mm": None,
        "water_balance_daily_mm": None,
        "surface_soil_wetness_pct": None,
        "root_zone_soil_wetness_pct": None,
        "frost_risk_days": None,
        "fog_blight_risk_days": None,
    }
    if not isinstance(recent_environment, dict) or recent_environment.get("status") != "available":
        return result

    recent_summary = recent_environment.get("summary")
    if not isinstance(recent_summary, dict):
        return result

    recent_temp = recent_summary.get("temperature_mean_c")
    recent_rain = recent_summary.get("precipitation_total_mm")
    rain_days = recent_summary.get("precipitation_valid_days")
    et0 = recent_summary.get("et0_mean_daily_mm")
    wb = recent_summary.get("water_balance_daily_mm")
    surf_wet = recent_summary.get("surface_soil_wetness_pct")
    root_wet = recent_summary.get("root_zone_soil_wetness_pct")
    frost_days = recent_summary.get("frost_risk_days")
    fog_days = recent_summary.get("fog_blight_risk_days")

    result["recent_temperature_c"] = recent_temp if isinstance(recent_temp, (int, float)) else None
    result["et0_daily_mm"] = et0 if isinstance(et0, (int, float)) else None
    result["water_balance_daily_mm"] = wb if isinstance(wb, (int, float)) else None
    result["surface_soil_wetness_pct"] = surf_wet if isinstance(surf_wet, (int, float)) else None
    result["root_zone_soil_wetness_pct"] = root_wet if isinstance(root_wet, (int, float)) else None
    result["frost_risk_days"] = frost_days if isinstance(frost_days, int) else None
    result["fog_blight_risk_days"] = fog_days if isinstance(fog_days, int) else None

    if isinstance(recent_rain, (int, float)) and isinstance(rain_days, int) and rain_days > 0:
        result["recent_daily_rain_mm"] = round(float(recent_rain) / rain_days, 2)

    if not isinstance(first_baseline, dict):
        return result

    base_temp = first_baseline.get("temperature_mean_c")
    base_rain = first_baseline.get("precipitation_mean_daily_mm")
    result["baseline_temperature_c"] = base_temp if isinstance(base_temp, (int, float)) else None
    result["baseline_daily_rain_mm"] = base_rain if isinstance(base_rain, (int, float)) else None

    recent_daily = result["recent_daily_rain_mm"]
    if isinstance(recent_daily, (int, float)) and isinstance(base_rain, (int, float)) and base_rain > 0:
        ratio = recent_daily / float(base_rain)
        if ratio >= 1.3:
            result["rain_signal"] = "wetter_than_baseline"
        elif ratio <= 0.7:
            result["rain_signal"] = "drier_than_baseline"
        else:
            result["rain_signal"] = "near_baseline"

    if isinstance(recent_temp, (int, float)) and isinstance(base_temp, (int, float)):
        difference = float(recent_temp) - float(base_temp)
        if difference >= 2:
            result["temperature_signal"] = "warmer_than_baseline"
        elif difference <= -2:
            result["temperature_signal"] = "cooler_than_baseline"
        else:
            result["temperature_signal"] = "near_baseline"

    return result


def build_rotation_scenarios(
    profile: dict[str, Any],
    context: dict[str, Any],
    condition: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build at least 3 explainable rotation strategies (including existing rotation) with explicit evidence gates."""
    condition = condition or {}
    calendars = context.get("calendar_evidence") or []
    district = context.get("district_profile") if isinstance(context.get("district_profile"), dict) else None
    history = _history(profile)
    intended = profile.get("intended_crop")
    priority = profile.get("priority", "production_stability")
    water_source = profile.get("water_source", "unknown")
    drainage = profile.get("water_after_heavy_rain", "unknown")
    soil_test = profile.get("soil_test", "unknown")
    soil_ph = profile.get("soil_ph")
    equipment = profile.get("equipment_access", "unknown")
    market_pref = profile.get("market_preference", "unknown")

    cal_names_en = [str(item.get("name_en")) for item in calendars if item.get("name_en")]
    cal_names_bn = [str(item.get("name_bn") or item.get("name_en")) for item in calendars if item.get("name_en")]

    established_en = list(district.get("established_crops_en") or []) if district else []
    established_bn = list(district.get("established_crops_bn") or []) if district else []
    opp_en = list(district.get("opportunity_crops_en") or []) if district else []
    opp_bn = list(district.get("opportunity_crops_bn") or []) if district else []

    history_labels_en = [CROP_LABELS.get(c, c.title()) for c in history]
    history_labels_bn = [CROP_LABELS_BN.get(c, c) for c in history]
    intended_en = CROP_LABELS.get(intended, intended.title()) if intended else None
    intended_bn = CROP_LABELS_BN.get(intended, intended) if intended else None

    if not cal_names_en and not established_en and len(history_labels_en) == 0:
        return {
            "status": "EVIDENCE_GATE_ACTIVE",
            "ranking_approved": False,
            "bare_field_window": {
                "en": "Local crop calendar evidence is not yet indexed for this coordinate. Monitor post-harvest bare-soil periods using MODIS/Landsat vegetation cover and local extension guidance.",
                "bn": "এই স্থানাঙ্কের জন্য স্থানীয় ফসল পঞ্জিকা এখনো যুক্ত হয়নি। ফসল কাটার পর জমি খালি থাকার সময় স্থানীয় কৃষি অফিসের পরামর্শ নিন।",
            },
            "vulnerability_summary": {
                "en": "Without reviewed local crop calendars, BoponX withholds specific rotation sequences to avoid fabricating suitability.",
                "bn": "স্থানীয় ফসল পঞ্জিকা ছাড়া BoponX অনুমানভিত্তিক ফসল পর্যায় তৈরি করে না।",
            },
            "scenarios": [
                {
                    "id": "A",
                    "kind": "evidence_gate",
                    "title_en": "Rotation evidence gate (Local adapter required)",
                    "title_bn": "ফসল পর্যায় প্রমাণ গেট (স্থানীয় তথ্য প্রয়োজন)",
                    "crops_en": [
                        history_labels_en[0] if history_labels_en else "Existing field crop",
                        intended_en or "Intended seasonal crop",
                        "Local calendar verification required",
                    ],
                    "crops_bn": [
                        history_labels_bn[0] if history_labels_bn else "বিদ্যমান ফসল",
                        intended_bn or "পরিকল্পিত ফসল",
                        "স্থানীয় ফসল পঞ্জিকা যাচাই প্রয়োজন",
                    ],
                    "why_suggested_en": "BoponX withholds synthetic crop sequences here because reviewed regional crop calendars are not yet connected for this country.",
                    "why_suggested_bn": "এই অঞ্চলের জন্য যাচাইকৃত ফসল পঞ্জিকা যুক্ত না থাকায় BoponX অনুমানভিত্তিক ফসলক্রম দেখাচ্ছে না।",
                    "supporting_evidence": [
                        "NASA POWER recent & 2001–2020 climatology resolved for selected coordinates",
                        "FAO Crop Calendar global reference route available",
                    ],
                    "potential_benefits": [
                        "Prevents false confidence from unverified global crop guesses",
                        "Preserves farmer history and intention for local extension review",
                    ],
                    "information_gaps": [
                        "No reviewed national/regional crop-weather calendar adapter connected for this location",
                        "Laboratory soil test (pH, organic matter, NPK) required for parcel-level decisions" if soil_test != "yes" else "Nutrient profile beyond pH requires report review",
                    ],
                    "local_review_risks": [
                        "Verify planting windows, frost/heat thresholds, and market suitability with local agricultural authorities before changing rotations.",
                    ],
                }
            ],
        }

    base_s1_en = history_labels_en[0] if len(history_labels_en) >= 1 else (established_en[0] if len(established_en) >= 1 else (cal_names_en[0] if cal_names_en else "Rice Aman"))
    base_s2_en = history_labels_en[1] if len(history_labels_en) >= 2 else (intended_en or (established_en[1] if len(established_en) >= 2 else (cal_names_en[2] if len(cal_names_en) > 2 else "Rice Boro / Rabi Crop")))
    base_s3_en = intended_en if (intended_en and len(history_labels_en) >= 2) else (established_en[2] if len(established_en) >= 3 else "Fallow / Kharif-1 Transition")

    base_s1_bn = history_labels_bn[0] if len(history_labels_bn) >= 1 else (established_bn[0] if len(established_bn) >= 1 else (cal_names_bn[0] if cal_names_bn else "আমন ধান"))
    base_s2_bn = history_labels_bn[1] if len(history_labels_bn) >= 2 else (intended_bn or (established_bn[1] if len(established_bn) >= 2 else (cal_names_bn[2] if len(cal_names_bn) > 2 else "বোরো ধান / রবি ফসল")))
    base_s3_bn = intended_bn if (intended_bn and len(history_labels_bn) >= 2) else (established_bn[2] if len(established_bn) >= 3 else "পতিত / খরিফ-১ অন্তর্বর্তী মৌসুম")

    legume_rabi_en = "Mustard / Lentil (Pulse)" if any("Mustard" in c or "Lentil" in c for c in cal_names_en) else (opp_en[0] if opp_en else "Short-duration Pulse")
    legume_rabi_bn = "সরিষা / মসুর ডাল" if any("Mustard" in c or "Lentil" in c for c in cal_names_en) else (opp_bn[0] if opp_bn else "স্বল্পমেয়াদি ডাল ফসল")
    kharif1_en = "Green Gram (Mungbean) / Aus" if any("Green Gram" in c or "Aus" in c for c in cal_names_en) else "Legume Cover / Jute"
    kharif1_bn = "মুগ ডাল (খরিফ-১) / আউশ" if any("Green Gram" in c or "Aus" in c for c in cal_names_en) else "ডাল আচ্ছাদন / পাট"

    if market_pref == "forage_livestock":
        opp_crop_1_en = "Dual-Purpose Maize (Grain + Silage Forage)"
        opp_crop_2_en = "Cowpea / Blackgram Forage & Nitrogen Bridge"
        opp_crop_1_bn = "দ্বৈত-উদ্দেশ্য ভুট্টা (দানা ও সাইলেজ গোখাদ্য)"
        opp_crop_2_bn = "ফেলন / মাসকলাই (গোখাদ্য ও নাইট্রোজেন সংবন্ধন)"
    else:
        opp_crop_1_en = opp_en[0] if len(opp_en) >= 1 else (intended_en or (cal_names_en[1] if len(cal_names_en) > 1 else "Maize"))
        opp_crop_2_en = opp_en[1] if len(opp_en) >= 2 else (opp_en[0] if len(opp_en) >= 1 else "Pulse / Oilseed")
        opp_crop_1_bn = opp_bn[0] if len(opp_bn) >= 1 else (intended_bn or (cal_names_bn[1] if len(cal_names_bn) > 1 else "ভুট্টা"))
        opp_crop_2_bn = opp_bn[1] if len(opp_bn) >= 2 else (opp_bn[0] if len(opp_bn) >= 1 else "ডাল / তেলবীজ")

    district_label_en = f"{district['name_en']} District ({district['landform_en']})" if district else context["nearest_supported_region"]["name_en"]
    district_label_bn = f"{district['name_bn']} জেলা ({district['landform_bn']})" if district else context["nearest_supported_region"]["name_bn"]

    common_gaps = []
    if soil_test != "yes":
        common_gaps.append("No laboratory soil-test report entered; soil pH, salinity (EC), organic matter, and NPK cannot be inferred from SMAP or NASA POWER.")
    elif soil_ph is not None:
        common_gaps.append(f"Report pH ({soil_ph}) is recorded, but nitrogen, phosphorus, potassium, and micronutrient levels still require full lab sheet review.")
    if district:
        common_gaps.append(
            f"District soil & analog profile for {district['name_en']} is a preliminary estimate; soil varies across upazilas and must be verified with SRDI, BMD, BARC Crop Zoning, WorldClim, and SoilGrids."
        )
    else:
        common_gaps.append("Local upazila/county soil constraints and exact cultivar maturity windows require local extension verification.")

    rain_sig = condition.get("rain_signal", "unavailable")
    temp_sig = condition.get("temperature_signal", "unavailable")
    surf_wet = condition.get("surface_soil_wetness_pct")
    root_wet = condition.get("root_zone_soil_wetness_pct")
    wetness_note_en = (
        f" Topsoil wetness (0–5 cm) is {surf_wet:.0f}% and root-zone wetness (0–100 cm) is {root_wet:.0f}%."
        if isinstance(surf_wet, (int, float)) and isinstance(root_wet, (int, float))
        else ""
    )
    climate_vuln_en = (
        f"Recent NASA POWER rainfall signal is '{rain_sig.replace('_', ' ')}' and temperature signal is '{temp_sig.replace('_', ' ')}'.{wetness_note_en} "
        f"Field water source is '{water_source}' and post-rain drainage is '{drainage}'."
    )
    climate_vuln_bn = (
        f"সাম্প্রতিক NASA POWER বৃষ্টিপাত সংকেত '{rain_sig.replace('_', ' ')}' এবং তাপমাত্রা সংকেত '{temp_sig.replace('_', ' ')}'।"
    )

    bare_window_en = (
        district["bare_field_risk_en"]
        if district and district.get("bare_field_risk_en")
        else "Post-harvest turnaround windows (Nov–Dec and Mar–May) when bare topsoil is most vulnerable to moisture loss, erosion, or salinity rise."
    )
    bare_window_bn = (
        district["bare_field_risk_bn"]
        if district and district.get("bare_field_risk_bn")
        else "ফসল কাটার পরবর্তী অন্তর্বর্তী সময় (নভেম্বর–ডিসেম্বর ও মার্চ–মে), যখন খালি মাটিতে রস হ্রাস ও ক্ষয়ের ঝুঁকি বেশি।"
    )

    equip_note_en = (
        f"Equipment profile: {EQUIPMENT_LABELS.get(equipment, 'Not specified')}; Market/Forage focus: {MARKET_LABELS.get(market_pref, 'Not specified')}."
        if (equipment != "unknown" or market_pref != "unknown")
        else "Equipment & market constraints can be refined with local extension before seed purchase."
    )

    scenarios = [
        {
            "id": "A",
            "kind": "existing_baseline",
            "title_en": "Existing / Baseline Rotation Benchmark",
            "title_bn": "বিদ্যমান / প্রচলিত ফসল পর্যায় (তুলনামূলক ভিত্তি)",
            "crops_en": [base_s1_en, base_s2_en, base_s3_en],
            "crops_bn": [base_s1_bn, base_s2_bn, base_s3_bn],
            "why_suggested_en": (
                f"Represents the farmer's recorded crop history ({', '.join(history_labels_en) if history_labels_en else 'regional baseline'}) "
                f"and established crops in {district_label_en} as the baseline benchmark required to evaluate any shift."
            ),
            "why_suggested_bn": (
                f"কৃষকের দেওয়া পূর্ববর্তী ফসলের তথ্য ও {district_label_bn}-এর প্রতিষ্ঠিত ফসলের ওপর ভিত্তি করে এই বিদ্যমান ধারাটি তুলনার ভিত্তি হিসেবে দেখানো হয়েছে।"
            ),
            "supporting_evidence": [
                f"Farmer crop history & intention ({', '.join(history_labels_en) if history_labels_en else 'baseline'} → {intended_en or 'undecided'})",
                f"Established district crops: {', '.join(established_en) if established_en else 'Regional BAMIS staple index'}",
                f"{len(calendars)} official BAMIS crop-weather calendars indexed for {context['nearest_supported_region']['name_en']}",
                equip_note_en,
            ],
            "potential_benefits": [
                "Uses familiar seed, equipment, and established local market channels",
                "Provides a transparent baseline to compare water demand, pest carryover, and bare-soil exposure",
            ],
            "information_gaps": list(common_gaps),
            "local_review_risks": [
                "Repeating the same crop family across consecutive seasons increases pest/disease carryover and nutrient depletion.",
                "If late-season standing water stays on the field or dry-season irrigation is limited, baseline yields may face stress.",
            ],
        },
        {
            "id": "B",
            "kind": "soil_and_nitrogen",
            "title_en": "Soil-Health & Pulse/Oilseed Bridge Exploration",
            "title_bn": "মাটির স্বাস্থ্য ও ডাল/তেলবীজ সংযোজন অনুসন্ধান",
            "crops_en": [base_s1_en, legume_rabi_en, kharif1_en],
            "crops_bn": [base_s1_bn, legume_rabi_bn, kharif1_bn],
            "why_suggested_en": (
                "Explores inserting a short-duration nitrogen-fixing pulse (lentil/mungbean) or oilseed (mustard/soybean) "
                "during the bare transition window to build soil organic matter, interrupt cereal pest cycles, and reduce irrigation demand."
            ),
            "why_suggested_bn": (
                "জমি খালি থাকার সময়ে স্বল্পমেয়াদি ডাল (মসুর/মুগ) বা তেলবীজ (সরিষা/সয়াবিন) যুক্ত করে মাটিতে নাইট্রোজেন সংবন্ধন, "
                "রোগ-পোকার চক্র ভাঙা এবং সেচের পানি সাশ্রয়ের সম্ভাব্য পথ।"
            ),
            "supporting_evidence": [
                f"BAMIS regional calendar presence for pulses/oilseeds in {context['nearest_supported_region']['name_en']}",
                f"Bare-field protection window: {bare_window_en}",
                "National import-substitution priority: ~90% edible oil imported and 12.36 lakh tonne projected pulse deficit by 2030 (The Daily Star, USDA)",
            ],
            "potential_benefits": [
                "Biological nitrogen fixation (legume root nodules) and crop residue improve soil structure and infiltration",
                "Covers bare soil during dry/transitional months, reducing evaporation and surface salt accumulation",
                "Lower water demand than continuous irrigated Boro rice and adds supplemental domestic-market income",
            ],
            "information_gaps": list(common_gaps),
            "local_review_risks": [
                "Pulses and mustard are highly sensitive to waterlogging; if heavy rain stays on the field, verify surface drainage first.",
                "Verify rhizobium inoculant availability and short-duration variety maturity so the next main crop is not delayed.",
            ],
        },
        {
            "id": "C",
            "kind": "water_and_local_opportunity",
            "title_en": f"Climate-Adaptive & {district['name_en'] if district else 'Regional'} Opportunity Exploration",
            "title_bn": f"জলবায়ু-সহনশীল ও {district['name_bn'] if district else 'আঞ্চলিক'} নতুন ফসলের সুযোগ অনুসন্ধান",
            "crops_en": [
                intended_en or base_s1_en,
                opp_crop_1_en,
                opp_crop_2_en,
            ],
            "crops_bn": [
                intended_bn or base_s1_bn,
                opp_crop_1_bn,
                opp_crop_2_bn,
            ],
            "why_suggested_en": (
                f"Aligns farmer priority ({priority.replace('_', ' ')}) and recent NASA agroclimate signals with "
                f"preliminary crop opportunities identified for {district_label_en}"
                + (f" (climate analogs: {district['analog_regions_en']})." if district else ".")
            ),
            "why_suggested_bn": (
                f"কৃষকের অগ্রাধিকার ({priority}) ও নাসা জলবায়ু সংকেতের সাথে {district_label_bn}-এর সম্ভাব্য নতুন ফসলের সুযোগ "
                + (f"(মিল থাকা এলাকা: {district['analog_regions_bn']}) " if district else "")
                + "মিলিয়ে অনুসন্ধানমূলক বিকল্প।"
            ),
            "supporting_evidence": [
                climate_vuln_en,
                (
                    f"64-district agro-ecological profile ({district['name_en']}): opportunities {', '.join(opp_en)}; analogs {district['analog_regions_en']}"
                    if district
                    else f"Regional calendar index for {context['nearest_supported_region']['name_en']}"
                ),
                *(
                    [f"Published pilot/report evidence: {ev['title_en']} — {ev['detail_en']}" for ev in (district.get("online_evidence") or [])]
                    if district and district.get("online_evidence")
                    else ["Requires local DAE/BARC trial verification before field adoption"]
                ),
                equip_note_en,
            ],
            "potential_benefits": [
                "Explores higher-value, forage, or stress-adapted crops matched to regional landform (char, Barind, coastal, haor, or hill terrace)",
                "Supports climate adaptation when traditional seasonal rainfall or temperature patterns shift",
            ],
            "information_gaps": list(common_gaps),
            "local_review_risks": [
                "New or exotic crop varieties require Plant Quarantine approval and National Seed Board registration before importing seed/saplings.",
                "Distant climate-analog regions may differ in day length (photoperiod), rainfall distribution, pest pressure, and local market buyers.",
            ],
        },
    ]

    return {
        "status": "EVIDENCE_REVIEW_REQUIRED",
        "ranking_approved": False,
        "bare_field_window": {
            "en": bare_window_en,
            "bn": bare_window_bn,
        },
        "vulnerability_summary": {
            "en": climate_vuln_en,
            "bn": climate_vuln_bn,
        },
        "scenarios": scenarios,
    }


def _decision_advice(
    profile: dict[str, Any],
    context: dict[str, Any],
    condition: dict[str, Any],
) -> dict[str, Any]:
    intended = profile.get("intended_crop")
    calendars = context.get("calendar_evidence") or []
    matches = _calendar_matches(intended, calendars)
    region = context["nearest_supported_region"]["name_en"]
    district = context.get("district_profile") if isinstance(context.get("district_profile"), dict) else None
    crop_label = CROP_LABELS.get(intended, "the intended crop") if intended else None

    reasons: list[str] = []
    next_step = "Choose the next crop you are considering, then review the regional evidence and field water/soil setup before committing."
    status = "NEEDS_INTENTION"
    verdict = "No crop decision has been entered yet — select a target crop to receive tailored agronomic readiness advice."

    if intended:
        if matches:
            status = "REASONABLE_TO_EXPLORE"
            verdict = f"{crop_label} is reasonable to explore because official crop weather calendar evidence exists for the {region} evidence hub."
            reasons.append(f"Official BAMIS crop-weather calendar source is indexed for {crop_label} in the {region} hub.")
            next_step = f"Follow the Month 1–3 preparation and monitoring steps for {crop_label} below while verifying local cultivar timing with DAE (16123)."
        else:
            status = "VERIFY_BEFORE_COMMITTING"
            verdict = f"BoponX cannot confirm {crop_label} from the current regional evidence index."
            reasons.append("No matching official BAMIS crop calendar is currently indexed for this crop in the selected regional hub.")
            next_step = "Verify this crop with the local agricultural office or choose a crop that has an official regional calendar source before making a seasonal commitment."

    if district:
        reasons.append(
            f"Field resolves to {district['name_en']} District ({district['landform_en']}); established crops: {', '.join(district['established_crops_en'])}; diversification opportunities: {', '.join(district['opportunity_crops_en'])}."
        )

    rain_signal = condition.get("rain_signal")
    water_source = profile.get("water_source")
    drainage = profile.get("water_after_heavy_rain")
    soil_test = profile.get("soil_test")
    soil_ph = profile.get("soil_ph")
    equipment = profile.get("equipment_access", "unknown")
    market_pref = profile.get("market_preference", "unknown")
    history = _history(profile)

    if drainage == "stays" and rain_signal == "wetter_than_baseline":
        status = "REVIEW_WATER_RISK_FIRST"
        reasons.append("The farmer reports persistent standing water and recent rainfall is above the selected month historical baseline.")
        next_step = "A better immediate step is to clear perimeter drainage channels and use raised beds or waterlogging-tolerant varieties before committing to the intended crop."
    elif water_source == "rainfed" and rain_signal == "drier_than_baseline":
        status = "REVIEW_WATER_ACCESS_FIRST"
        reasons.append("The field is mainly rainfed while recent rainfall is below the selected month historical baseline.")
        next_step = "A better immediate step is to conserve residual topsoil moisture (mulching / minimum tillage) or confirm supplemental irrigation before committing."
    elif drainage == "stays" and intended in ("pulse", "mustard", "wheat", "maize", "vegetables"):
        reasons.append(
            f"Farmer reports water stays after heavy rain, whereas {crop_label} is sensitive to root-zone waterlogging; raised beds or drainage furrows are required."
        )

    surf_wet = condition.get("surface_soil_wetness_pct")
    root_wet = condition.get("root_zone_soil_wetness_pct")
    if isinstance(surf_wet, (int, float)) and isinstance(root_wet, (int, float)):
        reasons.append(
            f"NASA POWER root-zone moisture profile: topsoil wetness (0–5 cm) is {surf_wet:.0f}% and root-zone wetness (0–100 cm) is {root_wet:.0f}%."
        )

    if soil_test == "yes" and isinstance(soil_ph, (int, float)):
        if soil_ph < 5.5:
            reasons.append(
                f"Soil test pH is strongly acidic ({soil_ph}); phosphorus availability and legume nodulation may be restricted without agricultural lime review (SRDI/DAE)."
            )
        elif soil_ph > 7.8:
            reasons.append(
                f"Soil test pH is alkaline ({soil_ph}); monitor zinc, boron, and iron deficiency risks and incorporate organic compost."
            )
        else:
            reasons.append(
                f"Verified lab soil pH ({soil_ph}) falls within the favorable 5.5–7.8 range for most cereal, pulse, and oilseed rotations."
            )
    else:
        reasons.append("No verified soil chemistry report is available, so BoponX does not guess pH or NPK fertilizer rates from satellite data.")

    if intended and intended in history:
        reasons.append(
            f"{crop_label} also appears in recent field history ({', '.join(CROP_LABELS.get(c, c) for c in history)}); inserting a legume or broadleaf break crop helps interrupt pest and disease cycles."
        )

    if equipment != "unknown" or market_pref != "unknown":
        reasons.append(
            f"Operational fit: equipment access is '{EQUIPMENT_LABELS.get(equipment, equipment)}' and market/forage focus is '{MARKET_LABELS.get(market_pref, market_pref)}'."
        )

    alternatives = []
    intended_ids = {item.get("id") for item in matches}
    for item in calendars:
        if item.get("id") in intended_ids:
            continue
        alternatives.append({
            "id": item.get("id"),
            "name": item.get("name_en"),
            "source_url": item.get("source_url"),
            "note": "Regionally documented option to investigate. Not ranked as better or worse.",
        })
        if len(alternatives) == 4:
            break

    return {
        "status": status,
        "verdict": verdict,
        "reasons": reasons,
        "better_next_step": next_step,
        "intended_crop": intended,
        "intended_crop_label": crop_label,
        "regional_calendar_match": bool(matches),
        "regional_options_to_investigate": alternatives,
        "boundary": "BoponX advises on decision readiness, situation-specific management steps, and evidence gaps. Final crop suitability ranking remains gated until local agronomic rules are formally approved.",
    }


def _climate_task(month_index: int, region: str, region_bn: str, year: int, month: int, baseline: dict[str, Any] | None) -> dict[str, str]:
    month_name = MONTH_NAMES[month]
    month_name_bn = MONTH_NAMES_BN[month]
    if not baseline:
        return _task(
            f"m{month_index}_climate_reference",
            f"For {month_name} in {region}, keep checking the latest NASA evidence and record what is actually happening in the field. The monthly climatology is unavailable, so no baseline value is invented.",
            "nasa_context",
            "Use current evidence without fabricating a missing historical reference.",
            "NASA POWER and field observations",
            text_bn=f"{region_bn}-এ {month_name_bn} মাসের জন্য সর্বশেষ নাসা তথ্য পর্যবেক্ষণ করুন এবং মাঠে বাস্তবে কী ঘটছে তা লিখে রাখুন। মাসিক জলবায়ু গড় অনুপস্থিত থাকায় কোনো কাল্পনিক মান তৈরি করা হয়নি।",
            reason_bn="ঐতিহাসিক গড় তথ্য না থাকলে অনুমান না করে মাঠের বাস্তব পর্যবেক্ষণ ব্যবহার করুন।",
        )

    temp = baseline.get("temperature_mean_c")
    rain = baseline.get("precipitation_mean_daily_mm")
    et0 = baseline.get("et0_mean_daily_mm")
    temp_text = f"{temp:.1f}°C" if isinstance(temp, (int, float)) else "not available"
    rain_text = f"{rain:.1f} mm/day" if isinstance(rain, (int, float)) else "not available"
    et0_text = f", reference evapotranspiration (ET₀) {et0:.1f} mm/day" if isinstance(et0, (int, float)) else ""
    et0_text_bn = f", বাষ্পীভবন চাহিদা (ET₀) {et0:.1f} মিমি/দিন" if isinstance(et0, (int, float)) else ""
    return _task(
        f"m{month_index}_climate_reference",
        f"For {month_name} {year}, use the {region} NASA POWER climatology as a reference: mean temperature {temp_text}, daily rainfall {rain_text}{et0_text}. Compare field moisture against this 2001–2020 baseline rather than treating it as a forecast.",
        "nasa_context",
        "Each planning month uses its own regional 20-year climate & water-balance benchmark.",
        "NASA POWER 2001–2020 climatology",
        text_bn=f"{month_name_bn} {year}-এর জন্য {region_bn}-এর NASA POWER ঐতিহাসিক গড় (তাপমাত্রা {temp_text}, দৈনিক বৃষ্টিপাত {rain_text}{et0_text_bn}) রেফারেন্স হিসেবে ব্যবহার করুন এবং মাঠের আর্দ্রতার সাথে তুলনা করুন।",
        reason_bn="প্রতিটি পরিকল্পনা মাসের নিজস্ব ২০ বছরের আঞ্চলিক জলবায়ু ও পানির ভারসাম্য মানদণ্ড রয়েছে।",
    )


def make_90_day_plan(
    profile: dict[str, Any],
    context: dict[str, Any],
    *,
    start_year: int,
    start_month: int,
    recent_environment: dict[str, Any] | None = None,
    baseline_environment: dict[str, Any] | None = None,
    baseline_window: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not 1 <= start_month <= 12:
        raise ValueError("Unsupported start month")
    if not 2026 <= start_year <= 2035:
        raise ValueError("Unsupported start year")

    region = context["nearest_supported_region"]
    region_name = region["name_en"]
    region_name_bn = region.get("name_bn") or region_name
    district = context.get("district_profile") if isinstance(context.get("district_profile"), dict) else None
    history = _history(profile)
    intended = profile.get("intended_crop")
    soil_test = profile.get("soil_test", "unknown")
    soil_ph = profile.get("soil_ph")
    priority = profile.get("priority", "production_stability")
    water_source = profile.get("water_source", "unknown")
    drainage = profile.get("water_after_heavy_rain", "unknown")

    crop_guide = CROP_AGRONOMY_GUIDE.get(intended or "other", CROP_AGRONOMY_GUIDE["other"])
    intended_en = CROP_LABELS.get(intended, intended.title()) if intended else "Next Seasonal Crop"
    intended_bn = CROP_LABELS_BN.get(intended, intended) if intended else "পরবর্তী মৌসুমি ফসল"

    baseline_summaries = _baseline_summaries(baseline_environment, baseline_window)
    first_baseline = baseline_summaries[0] if baseline_summaries else None
    condition = _recent_condition(recent_environment, first_baseline)
    advice = _decision_advice(profile, context, condition)
    rotation_bundle = build_rotation_scenarios(profile, context, condition)

    district_landform_en = f" in {district['name_en']} ({district['landform_en']})" if district else f" in {region_name}"
    district_landform_bn = f" {district['name_bn']} জেলায় ({district['landform_bn']})" if district else f" {region_name_bn}-এ"

    months: list[dict[str, Any]] = []

    for offset in range(3):
        index = offset + 1
        year, month = _month(start_year, start_month, offset)
        baseline = baseline_summaries[offset] if offset < len(baseline_summaries) else None
        tasks: list[dict[str, str]] = [_climate_task(index, region_name, region_name_bn, year, month, baseline)]

        if index == 1:
            # Days 1–30: Field Readiness, Residue/History & Land/Soil/Water Setup
            history_text = ", ".join(CROP_LABELS.get(crop, crop.title()) for crop in history) if history else "no prior crop recorded"
            history_text_bn = ", ".join(CROP_LABELS_BN.get(crop, crop) for crop in history) if history else "পূর্ববর্তী ফসল উল্লেখ নেই"
            same_crop_warning_en = (
                f" Since {intended_en} was also grown recently, clear diseased stubble and consider a legume/broadleaf break plot to prevent pest carryover."
                if intended and intended in history
                else " Incorporate clean crop residue into the topsoil 10–14 days before seeding to improve soil organic matter."
            )
            same_crop_warning_bn = (
                f" যেহেতু সম্প্রতি {intended_bn} চাষ হয়েছে, রোগাক্রান্ত নাড়া পরিষ্কার করুন এবং পোকার চক্র ভাঙতে ডাল বা ভিন্ন গোত্রের ফসল বিবেচনা করুন।"
                if intended and intended in history
                else " বপনের ১০–১৪ দিন আগে পূর্ববর্তী ফসলের পরিষ্কার অবশিষ্টাংশ মাটিতে মিশিয়ে জৈব পদার্থের পরিমাণ বাড়ান।"
            )
            tasks.append(_task(
                "m1_crop_history",
                f"Days 1–10 (Residue & Rotation Hygiene): Previous field sequence is [{history_text}]{district_landform_en}.{same_crop_warning_en}",
                "field_history",
                "Tailors land preparation to the farmer's actual crop history and district landform.",
                text_bn=f"দিন ১–১০ (ফসলের অবশিষ্টাংশ ও পর্যায় প্রস্তুতি):{district_landform_bn} পূর্ববর্তী ফসল ছিল [{history_text_bn}]।{same_crop_warning_bn}",
                reason_bn="পূর্ববর্তী ফসলের ইতিহাস ও জেলার ভূমিরূপ অনুযায়ী জমি প্রস্তুতির পদক্ষেপ।",
            ))

            if intended:
                tasks.append(_task(
                    "m1_intention",
                    f"Days 10–20 ({intended_en} Land & Seedbed Setup): {crop_guide['m1_prep_en']}",
                    "farmer_intention",
                    f"Specific seedbed and land preparation required for {intended_en}.",
                    text_bn=f"দিন ১০–২০ ({intended_bn} বীজতলা ও জমি প্রস্তুতি): {crop_guide['m1_prep_bn']}",
                    reason_bn=f"{intended_bn} চাষের জন্য সুনির্দিষ্ট জমি ও বীজতলা প্রস্তুতি।",
                ))
            else:
                tasks.append(_task(
                    "m1_intention",
                    "Days 10–20 (Target Crop Selection): Select your target crop in Rotation Lab and match seedbed layout (flat, ridge-furrow, or raised bed) to the local BAMIS window.",
                    "farmer_intention",
                    "Seedbed geometry depends on the target crop's root zone requirements.",
                    text_bn="দিন ১০–২০ (লক্ষ্য ফসল নির্বাচন): রোটেশন ল্যাবে আপনার কাঙ্ক্ষিত ফসল নির্বাচন করুন এবং ফসলের শিকড়ের ধরন অনুযায়ী সমতল বা বেড পদ্ধতিতে জমি তৈরি করুন।",
                    reason_bn="ফসলের শিকড়ের সহনশীলতার ওপর জমি তৈরির পদ্ধতি নির্ভর করে।",
                ))

            # Water & drainage situation-specific task
            if drainage == "stays":
                water_task_en = (
                    f"Days 15–25 (Standing-Water & Drainage Action): Because water stays on this field after heavy rain (water source: {water_source}), "
                    "excavate 25–30 cm perimeter drainage channels and form raised beds/ridges before sowing so sudden storms do not rot seeds or roots."
                )
                water_task_bn = (
                    f"দিন ১৫–২৫ (জলাবদ্ধতা ও নিষ্কাশন ব্যবস্থা): ভারী বৃষ্টির পর এই জমিতে পানি জমে থাকে (পানির উৎস: {water_source})। "
                    "তাই বপনের আগেই জমির চারপাশে ২৫–৩০ সেমি গভীর নিকাশ নালা ও উঁচু বেড তৈরি করুন যাতে বীজ বা শিকড় পচে না যায়।"
                )
            elif water_source == "rainfed":
                water_task_en = (
                    f"Days 15–25 (Rainfed Moisture Conservation): Because this field is rainfed (drainage: {drainage}), "
                    "use minimum tillage to lock in post-harvest soil moisture (jo) and prepare straw/leaf mulch to cut surface evaporation."
                )
                water_task_bn = (
                    f"দিন ১৫–২৫ (বৃষ্টিনির্ভর জমির রস সংরক্ষণ): জমিটি মূলত বৃষ্টিনির্ভর (নিষ্কাশন: {drainage})। "
                    "তাই ন্যূনতম চাষে মাটির জো/রস ধরে রাখুন এবং বাষ্পীভবন কমাতে খড় বা পাতার মালচিং প্রস্তুত রাখুন।"
                )
            else:
                water_task_en = (
                    f"Days 15–25 (Irrigation & Channel Check): Field water source is '{water_source}' and drainage is '{drainage}'. "
                    "Inspect irrigation furrows and bunds so water reaches the root zone evenly without tail-end ponding."
                )
                water_task_bn = (
                    f"দিন ১৫–২৫ (সেচ ও নালা পরীক্ষা): জমির পানির উৎস '{water_source}' এবং নিষ্কাশন '{drainage}'। "
                    "সেচের নালা ও আইল পরীক্ষা করুন যাতে পুরো জমিতে সমানভাবে পানি পৌঁছায় এবং নিচু কোণায় পানি জমে না থাকে।"
                )
            tasks.append(_task(
                "m1_water_drainage",
                water_task_en,
                "field_observation",
                "Directly addresses the farmer's reported water source and post-rain drainage behavior.",
                text_bn=water_task_bn,
                reason_bn="কৃষকের দেওয়া পানির উৎস ও নিষ্কাশন তথ্যের ভিত্তিতে সুনির্দিষ্ট ব্যবস্থা।",
            ))

            # Soil test & pH situation-specific task
            if soil_test == "yes" and isinstance(soil_ph, (int, float)):
                if soil_ph < 5.5:
                    soil_en = f"Days 20–30 (Acidic Soil pH {soil_ph} Management): Use your lab report values for basal NPK, and consult DAE/SRDI on applying agricultural dolomite lime (typically 4–6 kg/decimal) at least 14 days before sowing to unlock phosphorus."
                    soil_bn = f"দিন ২০–৩০ (অম্লীয় মাটি pH {soil_ph} ব্যবস্থাপনা): রিপোর্টের মাত্রা অনুযায়ী মূল সার দিন এবং ফসফরাস সারের কার্যকারিতা বাড়াতে বপনের ১৪ দিন আগে ডলোমাইট চুন প্রয়োগের বিষয়ে কৃষি কর্মকর্তার পরামর্শ নিন।"
                elif soil_ph > 7.8:
                    soil_en = f"Days 20–30 (Alkaline Soil pH {soil_ph} Management): Follow your lab report for basal fertilizer, incorporate well-rotted organic manure, and check zinc/boron availability with your local extension officer."
                    soil_bn = f"দিন ২০–৩০ (ক্ষারীয় মাটি pH {soil_ph} ব্যবস্থাপনা): মাটি পরীক্ষার রিপোর্ট অনুযায়ী মূল সার ও পচা জৈব সার প্রয়োগ করুন এবং দস্তা ও বোরন সারের প্রাপ্যতা নিশ্চিত করুন।"
                else:
                    soil_en = f"Days 20–30 (Lab-Verified Soil pH {soil_ph} Basal Application): Soil pH ({soil_ph}) is in a favorable range. Apply basal phosphorus, potassium, sulfur, and organic compost strictly according to your printed soil test report."
                    soil_bn = f"দিন ২০–৩০ (পরীক্ষিত মাটি pH {soil_ph} ও মূল সার প্রয়োগ): মাটির pH ({soil_ph}) অনুকূল পর্যায়ে আছে। রিপোর্টে উল্লেখিত মাত্রা অনুযায়ী মূল সার ও জৈব সার প্রয়োগ করুন।"
            elif soil_test == "yes":
                soil_en = "Days 20–30 (Lab Report Basal Application): Keep the soil test report with this field record and apply basal nutrients strictly from the printed report values."
                soil_bn = "দিন ২০–৩০ (রিপোর্ট অনুযায়ী মূল সার): মাটি পরীক্ষার রিপোর্টটি সংরক্ষণ করুন এবং কেবল রিপোর্টে উল্লেখিত মাত্রা অনুযায়ী সার ব্যবহার করুন।"
            else:
                soil_en = "Days 20–30 (Composite Soil Sampling): Do not guess pH or NPK from satellite layers. Collect a 0–15 cm topsoil sample from 5–7 V-shaped spots across the plot for SRDI/upazila testing before heavy fertilizer investment."
                soil_bn = "দিন ২০–৩০ (মাটি নমুনা সংগ্রহ ও পরীক্ষা): উপগ্রহ ডেটা থেকে মাটির pH বা সার অনুমান করবেন না। জমির ৫–৭টি স্থান থেকে ০–১৫ সেমি গভীরতার মাটি সংগ্রহ করে স্থানীয় SRDI বা উপজেলা পরীক্ষাগারে পরীক্ষা করান।"

            tasks.append(_task(
                "m1_soil_evidence",
                soil_en,
                "soil_evidence",
                "Soil chemistry decisions must come from laboratory measurement, not satellite inference.",
                text_bn=soil_bn,
                reason_bn="মাটির রাসায়নিক সিদ্ধান্ত অবশ্যই পরীক্ষাগারের মাটি পরীক্ষা থেকে আসতে হবে।",
            ))

            if condition["rain_signal"] == "wetter_than_baseline":
                tasks.append(_task(
                    "m1_recent_wet_signal",
                    "NASA Wet-Anomaly Alert (Days 1–30): Recent NASA POWER rainfall is >30% above the historical baseline. Delay basal urea top-dressing during heavy rain bursts and keep drainage outlets open.",
                    "recent_conditions",
                    "Recent regional rainfall is wetter than the historical monthly reference.",
                    "NASA POWER recent context and climatology",
                    text_bn="নাসা অতিবৃষ্টি সতর্কতা (দিন ১–৩০): সাম্প্রতিক বৃষ্টিপাত ঐতিহাসিক গড়ের চেয়ে ৩০%-এর বেশি। ভারী বৃষ্টির সময় ইউরিয়া প্রয়োগ স্থগিত রাখুন এবং নিকাশ নালা খোলা রাখুন।",
                    reason_bn="সাম্প্রতিক আঞ্চলিক বৃষ্টিপাত ঐতিহাসিক মাসিক গড়ের তুলনায় বেশি।",
                ))
            elif condition["rain_signal"] == "drier_than_baseline":
                tasks.append(_task(
                    "m1_recent_dry_signal",
                    "NASA Dry-Anomaly Alert (Days 1–30): Recent NASA POWER rainfall is >30% below baseline. Sow immediately after land preparation to prevent seed-zone desiccation and verify pre-sowing irrigation access.",
                    "recent_conditions",
                    "Recent regional rainfall is drier than the historical monthly reference.",
                    "NASA POWER recent context and climatology",
                    text_bn="নাসা শুষ্কতা সতর্কতা (দিন ১–৩০): সাম্প্রতিক বৃষ্টিপাত ঐতিহাসিক গড়ের চেয়ে ৩০%-এর কম। মাটির রস শুকিয়ে যাওয়ার আগেই দ্রুত বপন সম্পন্ন করুন এবং সেচের প্রাপ্যতা নিশ্চিত করুন।",
                    reason_bn="সাম্প্রতিক আঞ্চলিক বৃষ্টিপাত ঐতিহাসিক মাসিক গড়ের তুলনায় কম।",
                ))

            phase = "Know the field"
            phase_bn = "মাঠের প্রস্তুতি ও ভিত্তি (দিন ১–৩০)"
            objective = f"Days 1–30: Prepare the {region_name} seedbed, drainage/moisture setup, and soil baseline for {intended_en}."
            objective_bn = f"দিন ১–৩০: {region_name_bn}-এ {intended_bn}-এর জন্য জমি, পানি নিষ্কাশন/রস সংরক্ষণ এবং মাটির প্রাথমিক প্রস্তুতি সম্পন্ন করুন।"

        elif index == 2:
            # Days 31–60: Active Vegetative Growth, Priority-Driven Management & BAMIS Check
            tasks.append(_task(
                "m2_weekly_observation",
                f"Days 31–45 ({intended_en} Vegetative Care & Weekly Log): {crop_guide['m2_care_en']} Log weekly field rainfall, irrigation hours, and root-zone moisture at 10 cm depth.",
                "monitoring",
                "Combines crop-specific vegetative care with weekly ground-truth logging.",
                text_bn=f"দিন ৩১–৪৫ ({intended_bn} পরিচর্যা ও সাপ্তাহিক পর্যবেক্ষণ): {crop_guide['m2_care_bn']} প্রতি সপ্তাহে বৃষ্টি, সেচ ও ১০ সেমি গভীরে মাটির আর্দ্রতা লিখে রাখুন।",
                reason_bn="ফসলের বৃদ্ধির পর্যায়ে সুনির্দিষ্ট পরিচর্যা ও মাঠের বাস্তব তথ্য লিপিবদ্ধকরণ।",
            ))

            if priority == "water":
                tasks.append(_task(
                    "water_priority_check",
                    f"Days 40–55 (Water-Saving Priority Execution): Check NASA POWER evaporative demand (ET₀) and SMAP context before each irrigation; apply water only at critical growth stages of {intended_en} and maintain surface mulch to cut evaporation by 25–30%.",
                    "farmer_priority",
                    "The farmer selected water conservation as the primary operational priority.",
                    "NASA POWER ET0, rainfall context and farmer observations",
                    text_bn=f"দিন ৪০–৫৫ (পানি সাশ্রয় অগ্রাধিকার): প্রতিবার সেচের আগে নাসা বাষ্পীভবন চাহিদা (ET₀) ও মাটির রস যাচাই করুন; {intended_bn}-এর কেবল সংকটময় বৃদ্ধির পর্যায়ে সেচ দিন এবং মালচিং বজায় রাখুন।",
                    reason_bn="কৃষক পানি সাশ্রয়কে প্রধান অগ্রাধিকার হিসেবে নির্বাচন করেছেন।",
                ))
            elif priority == "soil":
                tasks.append(_task(
                    "soil_priority_check",
                    f"Days 40–55 (Soil-Health Priority Execution): Protect topsoil structure around {intended_en} with organic mulch/intercrop cover, avoid excess synthetic nitrogen that acidifies soil, and check root nodulation/earthworm activity and surface crusting.",
                    "farmer_priority",
                    "The farmer selected soil health restoration as the primary operational priority.",
                    text_bn=f"দিন ৪০–৫৫ (মাটির স্বাস্থ্য সুরক্ষা অগ্রাধিকার): {intended_bn}-এর জমিতে জৈব আচ্ছাদন বজায় রাখুন, অতিরিক্ত রাসায়নিক ইউরিয়া পরিহার করুন এবং মাটির উপরিভাগের ফাটল, ক্ষয় বা লবণাক্ততা পর্যবেক্ষণ করুন।",
                    reason_bn="কৃষক মাটির স্বাস্থ্য সুরক্ষাকে প্রধান অগ্রাধিকার হিসেবে নির্বাচন করেছেন।",
                ))
            else:
                tasks.append(_task(
                    "stability_priority_check",
                    f"Days 40–55 (Production-Stability Priority Execution): Scout {intended_en} twice weekly for pest/disease thresholds and weather stress (heat spikes ≥35°C or sudden downpours), keeping drainage/irrigation buffers ready so yield stability is protected.",
                    "farmer_priority",
                    "The farmer selected production stability as the primary operational priority.",
                    text_bn=f"দিন ৪০–৫৫ (উৎপাদন স্থিতিশীলতা অগ্রাধিকার): {intended_bn}-এর জমিতে সপ্তাহে দুইবার রোগ-পোকা ও আবহাওয়াজনিত চাপ (তাপপ্রবাহ বা অতিবৃষ্টি) পর্যবেক্ষণ করুন এবং জরুরি সেচ/নিষ্কাশন প্রস্তুতি রাখুন।",
                    reason_bn="কৃষক উৎপাদন স্থিতিশীলতাকে প্রধান অগ্রাধিকার হিসেবে নির্বাচন করেছেন।",
                ))

            intended_matches = _calendar_matches(intended, context.get("calendar_evidence") or [])
            if intended and intended_matches:
                cal_window_en = intended_matches[0].get("window_en", "official seasonal window")
                cal_window_bn = intended_matches[0].get("window_bn", "সরকারি মৌসুমি সময়কাল")
                tasks.append(_task(
                    "m2_calendar_review",
                    f"Days 45–60 (BAMIS Stage Alignment): Cross-check {intended_en} growth stage against the official {region_name} BAMIS calendar ({cal_window_en}) and DAE weather advisories before flowering/reproductive phase.",
                    "local_evidence",
                    "The intended crop has an indexed official BAMIS calendar source for this regional hub.",
                    "BAMIS crop weather calendar",
                    text_bn=f"দিন ৪৫–৬০ (BAMIS পঞ্জিকা সমন্বয়): ফুল ও ফল আসার আগে {region_name_bn}-এর সরকারি BAMIS ফসল পঞ্জিকা ({cal_window_bn}) এবং কৃষি আবহাওয়া পরামর্শের সাথে মাঠের ফসলের বৃদ্ধি মিলিয়ে দেখুন।",
                    reason_bn="নির্বাচিত ফসলটির জন্য এই অঞ্চলে সরকারি BAMIS ফসল-আবহাওয়া পঞ্জিকা রয়েছে।",
                ))
            elif intended:
                tasks.append(_task(
                    "m2_calendar_gap",
                    f"Days 45–60 (Local Extension Verification): Because no BAMIS calendar is indexed for {intended_en} in {region_name}, review mid-season pest, irrigation, and fertilizer timing with your Upazila Agriculture Office (or call 16123).",
                    "local_evidence",
                    "The current regional evidence index requires local extension verification for this crop.",
                    "BAMIS evidence index & DAE",
                    text_bn=f"দিন ৪৫–৬০ (স্থানীয় কৃষি অফিস যাচাই): {region_name_bn}-এ {intended_bn}-এর BAMIS পঞ্জিকা সূচিবদ্ধ না থাকায় মধ্য-মৌসুমের পরিচর্যা ও সেচের বিষয়ে উপজেলা কৃষি অফিস বা ১৬১২৩-এ পরামর্শ নিন।",
                    reason_bn="বর্তমান আঞ্চলিক সূচিতে এই ফসলটির জন্য স্থানীয় কৃষি কর্মকর্তার যাচাই প্রয়োজন।",
                ))

            phase = "Watch the change"
            phase_bn = "ফসলের বৃদ্ধি ও পর্যবেক্ষণ (দিন ৩১–৬০)"
            objective = f"Days 31–60: Manage {MONTH_NAMES[month]} vegetative growth, execute your '{priority.replace('_', ' ')}' priority actions, and protect root-zone moisture."
            objective_bn = f"দিন ৩১–৬০: {MONTH_NAMES_BN[month]} মাসে ফসলের বৃদ্ধি ব্যবস্থাপনা, কৃষকের অগ্রাধিকার বাস্তবায়ন এবং শিকড় অঞ্চলের আর্দ্রতা রক্ষা করুন।"

        else:
            # Days 61–90: Reproductive/Harvest Window & Next-Season Rotation Bridge
            tasks.append(_task(
                "m3_advice_review",
                f"Days 61–75 (Decision Verdict & Field Readiness Check): {advice['verdict']} Immediate action: {advice['better_next_step']}",
                "decision_advice",
                "Translates the combined NASA + local agronomic diagnosis into a concrete Month 3 checkpoint.",
                text_bn=f"দিন ৬১–৭৫ (সিদ্ধান্ত পর্যালোচনা ও মাঠের প্রস্তুতি): {advice['verdict']} করণীয়: {advice['better_next_step']}",
                reason_bn="নাসা ও স্থানীয় তথ্যের সমন্বিত বিশ্লেষণকে তৃতীয় মাসের সুনির্দিষ্ট পদক্ষেপে রূপান্তর করে।",
            ))
            tasks.append(_task(
                "m3_compare_evidence",
                f"Days 70–85 (Transition & Bare-Field Protection): {crop_guide['m3_next_en']} Compare Strategy A (Baseline), Strategy B (Pulse/Oilseed Bridge), and Strategy C ({district['name_en'] if district else region_name} Opportunity) so the field does not stay bare.",
                "local_evidence",
                "Connects harvest timing directly to the 3 explored rotation strategies and bare-soil protection.",
                "BAMIS calendars & 64-district profile",
                text_bn=f"দিন ৭০–৮৫ (পরবর্তী মৌসুমের সংযোগ ও খালি জমি সুরক্ষা): {crop_guide['m3_next_bn']} জমি খালি না রাখতে কৌশল A (বিদ্যমান), কৌশল B (ডাল/তেলবীজ সংযোজন) ও কৌশল C তুলনা করুন।",
                reason_bn="ফসল কাটার সময়ের সাথে পরবর্তী মৌসুমের ফসল পর্যায় ও মাটির সুরক্ষার সরাসরি সংযোগ।",
            ))
            tasks.append(_task(
                "m3_decision_record",
                "Days 80–90 (Extension Sign-Off & Seed/Quarantine Check): Before buying seed for the next rotation season, verify upazila suitability with DAE/SRDI (Call 16123), confirm National Seed Board registration, and keep this printed 90-day record.",
                "decision_record",
                "Ensures human-in-the-loop extension verification and seed quality compliance before the next season.",
                text_bn="দিন ৮০–৯০ (কৃষি কর্মকর্তার পরামর্শ ও বীজ প্রত্যয়ন): পরবর্তী ফসলের বীজ কেনার আগে উপজেলা কৃষি অফিস/SRDI (কল সেন্টার ১৬১২৩)-এর সাথে যাচাই করুন, জাতীয় বীজ বোর্ডের নিবন্ধন নিশ্চিত করুন এবং এই কার্ডটি সংরক্ষণ করুন।",
                reason_bn="পরবর্তী মৌসুম শুরুর আগে স্থানীয় কৃষি বিশেষজ্ঞের যাচাই ও অনুমোদিত বীজ নিশ্চিতকরণ।",
            ))
            phase = "Decide the next move"
            phase_bn = "পরিপক্বতা ও পরবর্তী ফসল পর্যায় (দিন ৬১–৯০)"
            objective = f"Days 61–90: Complete {MONTH_NAMES[month]} reproductive/harvest management and lock in a verified next-season rotation crop to eliminate bare-field loss."
            objective_bn = f"দিন ৬১–৯০: {MONTH_NAMES_BN[month]} মাসে ফসল সংগ্রহ/পরিপক্বতা ব্যবস্থাপনা সম্পন্ন করুন এবং জমি পতিত না রেখে পরবর্তী ফসল পর্যায় চূড়ান্ত করুন।"

        months.append({
            "index": index,
            "planning_month": f"{year:04d}-{month:02d}",
            "month_name": {"en": MONTH_NAMES[month], "bn": MONTH_NAMES_BN[month]},
            "phase": {"en": phase, "bn": phase_bn},
            "objective": {"en": objective, "bn": objective_bn},
            "context": {
                "region": region_name,
                "baseline": baseline,
                "recent_rain_signal": condition["rain_signal"] if index == 1 else "use_latest_available_at_review",
                "farmer_priority": priority,
                "intended_crop": intended,
            },
            "tasks": tasks,
        })

    return {
        "status": "DECISION_PREPARATION_READY",
        "location": {
            "coordinates": context["coordinates"],
            "region_id": region["id"],
            "region_name_en": region["name_en"],
            "region_name_bn": region_name_bn,
            "distance_to_reference_km": region["distance_km"],
            "district_profile": district,
        },
        "farmer_context": profile,
        "planning_window": {"start": months[0]["planning_month"], "end": months[-1]["planning_month"]},
        "conditions": condition,
        "decision_advice": advice,
        "months": months,
        "recent_environment": recent_environment,
        "historical_baseline": baseline_environment,
        "historical_baseline_window": baseline_window,
        "rotation_explorer": {
            "status": "EVIDENCE_REVIEW_REQUIRED",
            "message_en": "BoponX evaluates farmer intention, water and drainage risk, regional crop calendar evidence, 64-district agro-ecological context, and NASA climate signals. Final crop suitability ranking remains locked until reviewed crop requirements, soil constraints, and crop sequence rules are encoded.",
            "message_bn": "BoponX কৃষকের লক্ষ্য, পানি ও নিষ্কাশন ঝুঁকি, আঞ্চলিক ফসল পঞ্জিকা, ৬৪ জেলার মাটি ও ফসলের প্রাথমিক তথ্য এবং নাসা জলবায়ু সংকেত মূল্যায়ন করে। তবে স্থানীয় কৃষিবিদ ও SRDI/BARC দ্বারা ফসল-পর্যায় নিয়ম চূড়ান্ত অনুমোদিত না হওয়া পর্যন্ত চূড়ান্ত র‍্যাঙ্কিং বন্ধ রাখা হয়েছে।",
            "bare_field_window": rotation_bundle["bare_field_window"],
            "vulnerability_summary": rotation_bundle["vulnerability_summary"],
            "scenarios": rotation_bundle["scenarios"],
        },
        "evidence": {
            "nasa_sources": context["nasa_sources"],
            "agricultural_sources": context["agricultural_sources"],
            "calendar_evidence": context.get("calendar_evidence", []),
            "multi_resolution_harmonization": context.get("multi_resolution_harmonization"),
            "scientific_glossary": context.get("scientific_glossary"),
            "functional_crop_roles": context.get("functional_crop_roles"),
            "si_modeling_methods": context.get("si_modeling_methods"),
        },
        "limitations": {
            "en": "This is location aware decision support, not a crop prescription or weather forecast. The plan uses recent regional NASA context, monthly historical climatology, farmer observations, official regional calendar evidence, and preliminary district profiles (requiring SRDI, BMD, BARC, WorldClim, and SoilGrids verification). Crop suitability ranking still requires reviewed local agronomic rules.",
            "bn": "এটি অবস্থান-সচেতন সিদ্ধান্ত সহায়তা, কোনো চূড়ান্ত ফসল প্রেসক্রিপশন বা আবহাওয়ার পূর্বাভাস নয়। এতে সাম্প্রতিক নাসা তথ্য, মাসিক ঐতিহাসিক জলবায়ু গড়, কৃষকের পর্যবেক্ষণ, সরকারি ফসল পঞ্জিকা এবং ৬৪ জেলার প্রাথমিক তথ্য (যা SRDI, BMD, BARC, WorldClim ও SoilGrids দিয়ে যাচাইযোগ্য) ব্যবহৃত হয়েছে।",
        },
    }
