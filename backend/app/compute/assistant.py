from __future__ import annotations

import re
from datetime import date
from difflib import SequenceMatcher, get_close_matches
from typing import Any

from backend.app.compute.bangladesh_districts import (
    DIVISION_COORDINATES,
    list_bangladesh_districts,
)

__all__ = ["route", "suggestions"]

CROPS = {
    "rice": ("rice", "dhan", "ধান", "চাল"),
    "wheat": ("wheat", "gom", "গম"),
    "maize": ("maize", "corn", "ভুট্টা"),
    "pulse": ("pulse", "pulses", "dal", "daal", "ডাল"),
    "mustard": ("mustard", "sarisha", "shorisha", "সরিষা"),
    "vegetables": ("vegetables", "vegetable", "sobji", "সবজি"),
    "jute": ("jute", "pat", "পাট"),
    "other": ("other crop", "অন্যান্য ফসল"),
}

MONTHS = {
    "january": 1, "jan": 1, "জানুয়ারি": 1, "জানুয়ারি": 1,
    "february": 2, "feb": 2, "ফেব্রুয়ারি": 2, "ফেব্রুয়ারি": 2,
    "march": 3, "mar": 3, "মার্চ": 3,
    "april": 4, "apr": 4, "এপ্রিল": 4,
    "may": 5, "মে": 5,
    "june": 6, "jun": 6, "জুন": 6,
    "july": 7, "jul": 7, "জুলাই": 7,
    "august": 8, "aug": 8, "আগস্ট": 8,
    "september": 9, "sept": 9, "sep": 9, "সেপ্টেম্বর": 9,
    "october": 10, "oct": 10, "অক্টোবর": 10,
    "november": 11, "nov": 11, "নভেম্বর": 11,
    "december": 12, "dec": 12, "ডিসেম্বর": 12,
}

LAYERS = {
    "trueColor": ("true color", "true-colour", "true colour", "satellite view", "ট্রু কালার", "স্যাটেলাইট ছবি"),
    "rain": ("rain layer", "rain map", "show rain", "show me the rain", "show me rain", "bristi map", "bristi layer", "বৃষ্টির মানচিত্র", "বৃষ্টি স্তর"),
    "soil": ("soil moisture layer", "soil layer", "smap", "মাটির আর্দ্রতা স্তর", "মাটির স্তর"),
    "ndvi": ("ndvi", "vegetation layer", "vegetation map", "উদ্ভিদ সূচক"),
    "temp": ("temperature layer", "temperature map", "heat map", "তাপমাত্রার মানচিত্র"),
    "srtm": ("elevation layer", "terrain layer", "srtm", "উচ্চতার স্তর", "ভূপ্রকৃতি স্তর"),
}

DIVISION_ALIASES = {
    "barisal": "Barishal", "barishal": "Barishal", "বরিশাল": "Barishal",
    "chittagong": "Chattogram", "chattogram": "Chattogram", "চট্টগ্রাম": "Chattogram",
    "dhaka": "Dhaka", "ঢাকা": "Dhaka",
    "khulna": "Khulna", "খুলনা": "Khulna",
    "mymensingh": "Mymensingh", "ময়মনসিংহ": "Mymensingh", "ময়মনসিংহ": "Mymensingh",
    "rajshahi": "Rajshahi", "রাজশাহী": "Rajshahi",
    "rangpur": "Rangpur", "রংপুর": "Rangpur",
    "sylhet": "Sylhet", "সিলেট": "Sylhet",
}

FOLLOW_UPS = {
    "welcome": [
        ("Read my dashboard", "আমার ড্যাশবোর্ডের সারাংশ দিন"),
        ("How is the rain here?", "এখানে বৃষ্টি কেমন?"),
        ("Open Rotation Lab", "রোটেশন ল্যাব খুলুন"),
        ("Generate my plan", "আমার পরিকল্পনা তৈরি করুন"),
    ],
    "dashboard_summary": [
        ("Compare rainfall with baseline", "বেসলাইনের সাথে বৃষ্টি তুলনা করুন"),
        ("Explain the soil-moisture layer", "মাটির আর্দ্রতা স্তর ব্যাখ্যা করুন"),
        ("What is unavailable?", "কোন তথ্য অনুপলভ্য?"),
    ],
    "project_info": [
        ("Read my dashboard", "আমার ড্যাশবোর্ডের সারাংশ দিন"),
        ("What is SMAP?", "SMAP কী?"),
        ("What information is missing?", "কোন তথ্য বাকি আছে?"),
    ],
    "map_controls": [
        ("Set map date to 14 days ago", "মানচিত্রের তারিখ ১৪ দিন আগে করুন"),
        ("Use the village/street map", "গ্রাম/রাস্তার মানচিত্র ব্যবহার করুন"),
        ("Switch to 2D map", "2D মানচিত্রে যান"),
        ("Show the soil moisture layer", "মাটির আর্দ্রতা স্তর দেখান"),
    ],
    "conditions": [
        ("Compare with the baseline", "বেসলাইনের সাথে তুলনা করুন"),
        ("Show rain layer", "বৃষ্টির মানচিত্র দেখান"),
        ("What is SMAP?", "SMAP কী?"),
        ("Generate my plan", "আমার পরিকল্পনা তৈরি করুন"),
    ],
    "soil_limits": [
        ("What is SMAP?", "SMAP কী?"),
        ("Where can I get a soil test?", "মাটি পরীক্ষা কোথায় করাব?"),
        ("Continue with soil test unknown", "মাটি পরীক্ষা অনিশ্চিত রেখে চালান"),
    ],
    "crop_check": [
        ("Show official sources", "সরকারি উৎস দেখান"),
        ("Open Rotation Lab", "রোটেশন ল্যাব খুলুন"),
        ("Explain the evidence gate", "প্রমাণ-গেট ব্যাখ্যা করুন"),
    ],
    "select_place": [
        ("How is the rain here?", "এখানে বৃষ্টি কেমন?"),
        ("Add my last crop", "আমার আগের ফসল যোগ করুন"),
        ("What's missing?", "কী বাকি আছে?"),
    ],
    "run_plan": [
        ("Why this advice?", "এই পরামর্শ কেন?"),
        ("Print my plan", "আমার পরিকল্পনা প্রিন্ট করুন"),
        ("Show local support", "স্থানীয় সহায়তা দেখান"),
    ],
    "fallback": [
        ("How is the rain here?", "এখানে বৃষ্টি কেমন?"),
        ("Select a Bangladesh district", "বাংলাদেশের একটি জেলা নির্বাচন করুন"),
        ("Generate my plan", "আমার পরিকল্পনা তৈরি করুন"),
    ],
}


def _normalize(value: str) -> str:
    value = value.lower().replace("’", "'").translate(str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789"))
    value = re.sub(r"[^a-z0-9.\s\u0980-\u09ff'-]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _has(text: str, *terms: str) -> bool:
    normalized = _normalize(text)
    return any(_normalize(term) in normalized for term in terms)


def _is_greeting(message: str) -> bool:
    normalized = _normalize(message).strip(" .,!?'")
    return normalized in {
        "hi",
        "hi there",
        "hello",
        "hello there",
        "hey",
        "hey there",
        "good morning",
        "good afternoon",
        "good evening",
        "salam",
        "assalamu alaikum",
        "assalamu alaikum wa rahmatullah",
        "হাই",
        "হ্যালো",
        "হ্যালো সহকারী",
        "সালাম",
        "আসসালামু আলাইকুম",
    }


def _language(message: str, default: str) -> str:
    if re.search(r"[\u0980-\u09ff]", message):
        return "bn"
    if _has(message, "amar", "jomi", "dhan", "bristi", "tapmatra", "chash", "korbo", "chai", "kori", "ki obostha"):
        return "bn"
    return default if default in {"en", "bn"} else "en"


def _make_action(name: str, **payload: Any) -> dict[str, Any]:
    return {"type": name, "payload": payload}


def _area_names() -> list[tuple[str, str]]:
    names = [(d["name_en"], d["name_en"]) for d in list_bangladesh_districts()]
    names.extend((d["name_bn"], d["name_en"]) for d in list_bangladesh_districts())
    names.extend((name.lower(), name.title()) for name in DIVISION_COORDINATES)
    names.extend((alias, canonical) for alias, canonical in DIVISION_ALIASES.items())
    return names


def _find_area(message: str) -> tuple[str | None, list[str]]:
    normalized = _normalize(message)
    for alias, canonical in sorted(_area_names(), key=lambda item: len(item[0]), reverse=True):
        if _normalize(alias) and _normalize(alias) in normalized:
            return canonical, []

    tokens = normalized.split()
    names = _area_names()
    choices: list[tuple[float, str]] = []
    for token in tokens:
        if len(token) < 4:
            continue
        matches = get_close_matches(token, [_normalize(alias) for alias, _ in names], n=2, cutoff=0.78)
        for match in matches:
            canonical = next((name for alias, name in names if _normalize(alias) == match), None)
            if canonical:
                ratio = __import__("difflib").SequenceMatcher(None, token, match).ratio()
                choices.append((ratio, canonical))
    choices.sort(reverse=True)
    unique = list(dict.fromkeys(name for _, name in choices))
    if choices and (len(unique) == 1 or choices[0][0] - next((score for score, name in choices if name != choices[0][1]), 0) > 0.08):
        return choices[0][1], []
    return None, unique[:3]


def _crop_from(message: str) -> str | None:
    normalized = _normalize(message)
    found = [(len(term), crop) for crop, terms in CROPS.items() for term in terms if _normalize(term) in normalized]
    if found:
        return max(found)[1]
    crop_aliases = {
        _normalize(alias): crop
        for crop, terms in CROPS.items()
        for alias in terms
        if " " not in alias and len(alias) >= 4
    }
    for token in normalized.split():
        match = get_close_matches(token, crop_aliases, n=1, cutoff=0.82)
        if match:
            return crop_aliases[match[0]]
    return None


def _split(message: str) -> list[str]:
    parts = re.split(
        r"[,;]|\band then\b|\bthen\b|\band(?=\s+(?:i\b|we\b|my\b|set\b|select\b|open\b|generate\b|add\b|remove\b|choose\b|switch\b|show\b|want\b|grew\b|have\b|rice\b|wheat\b|maize\b|pulse\b|mustard\b|jute\b))|\bতারপর\b| এবং (?=(?:আমি|আমার|নির্বাচন|খুলুন|তৈরি|চাই))",
        message,
        flags=re.IGNORECASE,
    )
    return [part.strip() for part in parts if part.strip()]


def _translate_suggestions(intent: str, lang: str) -> list[str]:
    choices = FOLLOW_UPS.get(intent, FOLLOW_UPS["fallback"])
    return [bn if lang == "bn" else en for en, bn in choices]


def suggestions(
    intent: str,
    state: dict[str, Any] | None = None,
    lang: str = "en",
    query: str = "",
) -> list[str]:
    state = state or {}
    if intent == "fallback" and query:
        query_tokens = [token for token in _normalize(query).split() if len(token) > 2]
        keyword_groups = {
            "conditions": {"rain", "rainfall", "bristi", "weather", "temperature", "tapmatra"},
            "soil_limits": {"soil", "smap", "ph", "test", "matti"},
            "crop_check": {"crop", "rice", "dhan", "wheat", "gom", "rotation"},
            "select_place": {"place", "location", "district", "field", "area"},
            "run_plan": {"plan", "planning", "generate", "advice"},
        }
        closest_intent = None
        best_score = 0.0
        for candidate, keywords in keyword_groups.items():
            score = max(
                (SequenceMatcher(None, token, keyword).ratio() for token in query_tokens for keyword in keywords),
                default=0.0,
            )
            if score > best_score:
                closest_intent, best_score = candidate, score
        if closest_intent and best_score >= 0.76:
            intent = closest_intent
    items = _translate_suggestions(intent, lang)
    if intent == "crop_check" and state.get("requestedCrop"):
        crop = str(state["requestedCrop"])
        crop_bn = {"rice": "ধান", "wheat": "গম", "maize": "ভুট্টা", "pulse": "ডাল", "mustard": "সরিষা", "vegetables": "সবজি", "jute": "পাট", "other": "অন্যান্য"}.get(crop, crop)
        if state.get("intendedCrop") != crop:
            localized = [
                (f"Set {crop} as my crop", f"আমার ফসল {crop_bn} নির্ধারণ করুন"),
                ("Show official sources", "সরকারি উৎস দেখান"),
                ("Open Rotation Lab", "রোটেশন ল্যাব খুলুন"),
            ]
            items = [bn if lang == "bn" else en for en, bn in localized]
    if intent in {"fallback", "welcome"}:
        view = state.get("view")
        if view == "earth":
            items = [
                "আমার ড্যাশবোর্ডের সারাংশ দিন" if lang == "bn" else "Read my dashboard",
                "এখানে বৃষ্টি কেমন?" if lang == "bn" else "How is the rain here?",
                "রোটেশন ল্যাব খুলুন" if lang == "bn" else "Open Rotation Lab",
                "আমার পরিকল্পনা তৈরি করুন" if lang == "bn" else "Generate my plan",
            ]
            if not state.get("selectedArea") and not state.get("selectedPoint"):
                items.insert(0, "মাঠ নির্বাচন করুন" if lang == "bn" else "Select a field")
        elif view == "rotation":
            items = [
                "আমার আগের ফসল যোগ করুন" if lang == "bn" else "Add my last crop",
                "কোন তথ্য বাকি?" if lang == "bn" else "What information is missing?",
                "প্রমাণ-গেট ব্যাখ্যা করুন" if lang == "bn" else "Explain the evidence gate",
                "আমার পরিকল্পনা তৈরি করুন" if lang == "bn" else "Generate my plan",
            ]
        elif view == "plan":
            items = [
                "এই পরামর্শ কেন?" if lang == "bn" else "Why this advice?",
                "আমার পরিকল্পনা প্রিন্ট করুন" if lang == "bn" else "Print my plan",
                "স্থানীয় সহায়তা দেখান" if lang == "bn" else "Show local support",
                "ড্যাশবোর্ডের সারাংশ দিন" if lang == "bn" else "Read my dashboard",
            ]
    layer = state.get("activeLayer")
    layer_phrases = {
        "trueColor": ("true color layer", "ট্রু কালার"),
        "rain": ("rain layer", "বৃষ্টি"),
        "soil": ("soil moisture layer", "মাটির আর্দ্রতা স্তর"),
        "ndvi": ("vegetation layer", "উদ্ভিদ সূচক"),
        "temp": ("temperature layer", "তাপমাত্রার মানচিত্র"),
        "srtm": ("elevation layer", "উচ্চতার স্তর"),
    }
    intended = state.get("intendedCrop")
    previous = state.get("previousCrops") or []

    def already_satisfied(item: str) -> bool:
        normalized = _normalize(item)
        if query and normalized in _normalize(query):
            return True
        if layer and any(phrase in normalized for phrase in layer_phrases.get(layer, ())):
            return True
        if state.get("mapBaseStyle") == "streets" and any(term in normalized for term in ("village", "street map", "গ্রাম রাস্তার")):
            return True
        if state.get("mapBaseStyle") == "satellite" and "satellite base map" in normalized:
            return True
        if state.get("mapIsGlobe") is False and ("switch to 2d map" in normalized or "2d মানচিত্রে যান" in normalized):
            return True
        if state.get("mapIsGlobe") is True and ("switch to 3d globe" in normalized or "3d গ্লোবে যান" in normalized):
            return True
        if state.get("selectedArea") and any(
            phrase in normalized
            for phrase in ("select a field", "select a bangladesh district", "মাঠ নির্বাচন", "জেলা নির্বাচন")
        ):
            return True
        if intended and ("set this as my crop" in normalized or "এটিকে আমার ফসল" in normalized):
            return True
        return bool(previous and ("add my last crop" in normalized or "আমার আগের ফসল" in normalized))

    filtered: list[str] = []
    for item in items:
        if already_satisfied(item):
            continue
        if item not in filtered:
            filtered.append(item)
    fallbacks = _translate_suggestions("fallback", lang)
    for item in fallbacks:
        if not already_satisfied(item) and item not in filtered:
            filtered.append(item)
        if len(filtered) >= 3:
            break
    return filtered[:4]


def _action_for_clause(
    clause: str,
    state: dict[str, Any],
    lang: str,
    pending: str | None,
    urls: list[str],
) -> tuple[dict[str, Any] | None, str | None, str | None, list[str] | None]:
    text = _normalize(clause)
    bn = lang == "bn"

    if not pending and _is_greeting(clause):
        return None, (
            "হ্যালো! BoponX ব্যবহার, মাঠের তথ্য দেখা, ফসলের তথ্য যোগ করা বা পরিকল্পনা তৈরিতে সাহায্য করতে পারি। নিচের কোনো একটি বেছে নিন, অথবা স্বাভাবিকভাবে লিখুন।"
            if bn
            else "Hi! I can help you use BoponX, check your field dashboard, add crop details, or build a plan. Choose a suggestion below or just ask naturally."
        ), "welcome", None

    if pending and _has(text, "yes", "yes please", "do it", "confirm", "হ্যাঁ", "জি", "করুন", "করো"):
        if pending == "reset_farm":
            return _make_action("resetFarmForm", confirmed=True), "ফর্ম রিসেট করা হচ্ছে।" if bn else "Resetting the farm form.", "reset_farm", None
        if pending == "clear_previous_crops":
            return _make_action("clearPreviousCrops", confirmed=True), "আগের ফসল মুছে দেওয়া হচ্ছে।" if bn else "Clearing previous crops.", "clear_previous_crops", None
        if pending == "clear_intended_crop":
            return _make_action("clearIntendedCrop", confirmed=True), "পরিকল্পিত ফসল মুছে দেওয়া হচ্ছে।" if bn else "Clearing the intended crop.", "clear_intended_crop", None

    if pending and _has(text, "no", "cancel", "থাক", "না"):
        if pending == "set_soil_ph":
            return _make_action("setSoilTest", soil_test="no"), "মাটি পরীক্ষার রিপোর্ট নেই হিসেবে নথিভুক্ত হয়েছে।" if bn else "Soil-test report recorded as unavailable.", "soil_test", None
        return None, "ঠিক আছে, কোনো পরিবর্তন করা হয়নি।" if bn else "Okay, no changes were made.", "confirmation_cancelled", None
    if pending == "set_soil_ph" and _has(text, "yes", "হ্যাঁ", "জি"):
        state["soilTest"] = "yes"
        return _make_action("setSoilTest", soil_test="yes"), "রিপোর্ট আছে হিসেবে নথিভুক্ত হয়েছে। pH মানটি লিখুন।" if bn else "Report confirmed. Now enter the pH value printed on it.", "soil_test", None

    if _has(text, "show me around", "guided tour", "পরিচিতি দেখাও", "ঘুরিয়ে দেখান", "সাইট দেখাও"):
        return _make_action("guidedTour"), "চলুন, ধাপে ধাপে সাইটটি দেখে নিই।" if bn else "Let’s take a short guided tour of the site.", "guided_tour", None

    if _has(text, "reset the whole farm", "reset the farm form", "reset farm form", "reset form", "সব তথ্য মুছ", "ফর্ম রিসেট", "খামার রিসেট"):
        return None, "খামারের সব ফর্ম তথ্য মুছব—নিশ্চিত করবেন?" if bn else "This will clear the farm form. Do you want to continue?", "reset_farm", ["হ্যাঁ", "না"] if bn else ["Yes", "No"]

    if _has(text, "clear all previous crop", "clear previous crop", "remove all previous crop", "সব আগের ফসল মুছ", "পূর্বের ফসল মুছ"):
        return None, "আগের সব ফসল মুছব—নিশ্চিত করবেন?" if bn else "This will remove all previous crops. Continue?", "clear_previous_crops", ["হ্যাঁ", "না"] if bn else ["Yes", "No"]

    if _has(text, "clear intended crop", "remove intended crop", "clear my crop", "পরিকল্পিত ফসল মুছ", "ফসল মুছ"):
        return None, "পরিকল্পিত ফসল মুছব—নিশ্চিত করবেন?" if bn else "This will clear the intended crop. Continue?", "clear_intended_crop", ["হ্যাঁ", "না"] if bn else ["Yes", "No"]

    if _has(text, "undo", "আগের অবস্থায় ফিরে", "আগের অবস্থায় ফিরে", "পূর্বাবস্থায়", "পূর্বাবস্থায়"):
        return _make_action("undo"), "শেষ চ্যাট পরিবর্তনটি ফিরিয়ে নিচ্ছি।" if bn else "Undoing the last chat change.", "undo", None

    if _has(text, "gps", "my location", "current location", "আমার অবস্থান", "বর্তমান অবস্থান", "নিজের অবস্থান"):
        return _make_action("locateMe"), "GPS অবস্থান চাইছি।" if bn else "Requesting your device location.", "locate_me", None

    strategy_match = re.search(r"\b(?:strategy|কৌশল)\s*([abc])\b", text)
    if strategy_match:
        strategy_id = strategy_match.group(1).upper()
        return _make_action("selectStrategy", strategy_id=strategy_id), f"রোটেশন ল্যাবে কৌশল {strategy_id} নির্বাচন করছি।" if bn else f"Selecting Strategy {strategy_id} in the Rotation Lab.", "select_strategy", None

    area, area_choices = _find_area(clause)
    if area and (
        pending == "select_place"
        or len(text.split()) <= 2
        or _has(text, "select", "choose", "set location", "go to", "what about", "district", "division", "জেলা", "বিভাগ", "নির্বাচন", "যাও", "এলাকা", "জমি", "জমিতে")
    ):
        return _make_action("selectPlace", area=area), f"{area} নির্বাচন করা হচ্ছে।" if bn else f"Selecting {area}.", "select_place", None
    if area_choices and _has(text, "select", "choose", "district", "জেলা", "নির্বাচন"):
        return None, "কোন এলাকাটি বোঝাচ্ছেন?" if bn else "Which area did you mean?", "select_place", area_choices
    if not area and _has(text, "select", "choose", "find", "locate", "select place", "জায়গা খুঁজ", "স্থান নির্বাচন"):
        place_query = re.sub(
            r"^(?:please\s+)?(?:select|choose|find|locate)\s+(?:(?:a|the)\s+)?(?:(?:place|field|location)\s+)?(?:in\s+)?",
            "",
            clause,
            flags=re.IGNORECASE,
        ).strip(" ,.")
        if place_query and len(place_query) >= 2:
            return _make_action("searchPlace", query=place_query), "জায়গাটি খুঁজছি।" if bn else f"Searching for {place_query}.", "select_place", None

    point_match = re.search(r"(-?\d{1,2}(?:\.\d+)?)\s*[, ]\s*(-?\d{1,3}(?:\.\d+)?)", text)
    if point_match and _has(text, "select point", "coordinates", "স্থানাঙ্ক", "বিন্দু"):
        latitude, longitude = float(point_match.group(1)), float(point_match.group(2))
        if -90 <= latitude <= 90 and -180 <= longitude <= 180:
            return _make_action("selectPoint", latitude=latitude, longitude=longitude), "স্থানাঙ্ক নির্বাচন করা হচ্ছে।" if bn else "Selecting those coordinates.", "select_point", None
        return None, "স্থানাঙ্ক অক্ষাংশ −৯০ থেকে ৯০ এবং দ্রাঘিমাংশ −১৮০ থেকে ১৮০ হতে হবে।" if bn else "Coordinates must be within latitude −90..90 and longitude −180..180.", "select_point", None

    if _has(text, "open rotation", "rotation lab", "analysis page", "ফসল পর্যায় ল্যাব", "রোটেশন ল্যাব", "বিশ্লেষণ"):
        return _make_action("navigate", view="rotation"), "রোটেশন ল্যাব খুলছি।" if bn else "Opening the Rotation Lab.", "navigate", None
    if _has(text, "open plan", "plan page", "90 day plan", "৯০ দিনের পরিকল্পনা", "পরিকল্পনা পাতা"):
        return _make_action("navigate", view="plan"), "পরিকল্পনা পাতা খুলছি।" if bn else "Opening the plan page.", "navigate", None
    if _has(text, "open map", "earth view", "location page", "মানচিত্র খোলো", "অবস্থান পাতা", "পৃথিবী দেখাও"):
        return _make_action("navigate", view="earth"), "মাঠের মানচিত্র খুলছি।" if bn else "Opening the field map.", "navigate", None

    if _has(text, "switch to bangla", "বাংলা কর", "বাংলায়", "বাংলায়", "bangla language"):
        return _make_action("setLanguage", lang="bn"), "বাংলা ভাষা নির্বাচন করা হয়েছে।" if bn else "Switching the interface to Bangla.", "set_language", None
    if _has(text, "switch to english", "ইংরেজি কর", "english language"):
        return _make_action("setLanguage", lang="en"), "ইংরেজি ভাষা নির্বাচন করা হয়েছে।" if bn else "Switching the interface to English.", "set_language", None

    if _has(text, "retry", "reload data", "retry nasa", "আবার চেষ্টা", "পুনরায় লোড", "পুনরায় লোড"):
        return _make_action("retryLoad"), "NASA তথ্য আবার লোড করছি।" if bn else "Retrying the NASA data load.", "retry_load", None

    if _has(text, "print", "print plan", "প্রিন্ট", "ছাপান", "ছাপাও"):
        return _make_action("print"), "প্রিন্ট ডায়ালগ খুলছি।" if bn else "Opening the print dialog.", "print", None

    if _has(text, "zoom field", "focus field", "মাঠে জুম", "জুম কর"):
        return _make_action("zoomField"), "নির্বাচিত মাঠে জুম করছি।" if bn else "Zooming to the selected field.", "zoom_field", None

    if _has(text, "official source", "source link", "helpline", "support", "সরকারি উৎস", "হেল্পলাইন", "সহায়তা", "সহায়তা", "dae"):
        if _has(text, "helpline", "হেল্পলাইন") and state.get("countryCode") == "bd":
            return _make_action("callHelpline", phone="16123"), "কৃষি পরামর্শ হেল্পলাইন ১৬১২৩-এ কল করার ব্যবস্থা করছি।" if bn else "Opening the DAE agricultural helpline at 16123.", "open_sources", None
        url = urls[0] if urls else "https://dae.gov.bd/"
        return _make_action("openSourceLink", url=url), "সরকারি কৃষি সহায়তার লিংক খুলছি।" if bn else "Opening an official agricultural support link.", "open_sources", None

    if _has(text, "what is smap", "smap কী", "smap ki"):
        return None, ("SMAP হলো NASA-এর মাটির আর্দ্রতা পর্যবেক্ষণ মিশন। এর উপগ্রহ তথ্য আঞ্চলিক আর্দ্রতার প্রেক্ষাপট দেয়—এটি মাঠের pH বা NPK পরীক্ষা নয়।" if bn else "SMAP is NASA’s soil-moisture mission. Its satellite data provides regional moisture context, not field-level pH or NPK measurements."), "soil_limits", None

    if _has(text, "what is ndvi", "ndvi কী", "ndvi ki"):
        return None, (
            "NDVI হলো লাল ও নিকট-ইনফ্রারেড আলো থেকে গণনা করা উদ্ভিদ-সবুজত্বের সূচক। এটি ক্যানোপির প্রেক্ষাপট দেয়, একা ফসলের ধরন, ফলন বা জমির স্বাস্থ্য নিশ্চিত করে না।"
            if bn
            else "NDVI is a vegetation-greenness index derived from red and near-infrared light. It provides canopy context, but alone cannot confirm crop type, yield, or field health."
        ), "project_info", None

    if _has(text, "what is gpm", "gpm কী", "what is nasa power", "power data", "nasa power কী", "what is srtm", "srtm কী"):
        if _has(text, "gpm", "বৃষ্টি"):
            answer = "GPM হলো NASA-এর বৈশ্বিক বৃষ্টিপাত পর্যবেক্ষণ মিশন; মানচিত্রের বৃষ্টি স্তর বর্তমান/সাম্প্রতিক পর্যবেক্ষণ দেখাতে পারে, পূর্বাভাস নয়।" if bn else "GPM is NASA’s global precipitation-observing mission; the map’s rainfall layer can show observed or recent precipitation, not a forecast."
        elif _has(text, "srtm"):
            answer = "SRTM হলো শাটল রাডার টপোগ্রাফি মিশন; এর উচ্চতা/ভূপ্রকৃতি স্তর ভূমিরূপের প্রেক্ষাপট দেয়, মাঠের নিষ্কাশন নিশ্চিত করে না।" if bn else "SRTM is the Shuttle Radar Topography Mission; its elevation/terrain layer provides landform context but does not confirm a field’s drainage."
        else:
            answer = "NASA POWER হলো NASA-এর Prediction Of Worldwide Energy Resources ডেটা পরিষেবা। এখানে প্রদর্শিত আবহাওয়া-সম্পর্কিত মানকে পর্যবেক্ষণ/ঐতিহাসিক প্রেক্ষাপট হিসেবে দেখুন, মাঠ-স্তরের সেন্সর বা পূর্বাভাস হিসেবে নয়।" if bn else "NASA POWER is NASA’s Prediction Of Worldwide Energy Resources data service. Treat values shown here as observational or historical context, not as a field sensor reading or forecast."
        return None, answer, "project_info", None

    if _has(text, "weather forecast", "rain forecast", "will it rain", "forecast tomorrow", "আগামীকাল বৃষ্টি", "আবহাওয়ার পূর্বাভাস", "আবহাওয়ার পূর্বাভাস", "বৃষ্টির পূর্বাভাস"):
        return None, (
            "এই ড্যাশবোর্ড আবহাওয়ার পূর্বাভাস দেয় না। এটি সাম্প্রতিক পর্যবেক্ষণ ও ঐতিহাসিক বেসলাইন দেখায়; ভবিষ্যৎ আবহাওয়ার জন্য সরকারি আবহাওয়া পূর্বাভাস দেখুন।"
            if bn
            else "This dashboard does not provide weather forecasts. It shows recent observations and historical baselines; use your official meteorological service for future weather."
        ), "conditions", None

    if _has(text, "how accurate", "spatial resolution", "pixel size", "field level", "parcel level", "কতটা নির্ভুল", "রেজোলিউশন", "জমির মাপ"):
        return None, (
            "স্যাটেলাইট পিক্সেল ও সময়-ব্যাপ্তি উৎসভেদে ভিন্ন, তাই মানগুলো মাঠের প্রতিটি অংশের সরাসরি মাপ নয়। মানচিত্রের লেজেন্ডে নির্বাচিত স্তরের রেজোলিউশন দেখুন; pH/NPK-এর জন্য বাস্তব মাটি পরীক্ষা দরকার।"
            if bn
            else "Satellite pixel size and time coverage vary by source, so these values are not direct measurements of every part of a field. Check the selected layer’s legend for its resolution; pH/NPK requires a real soil test."
        ), "project_info", None

    if _has(text, "where can i get a soil test", "soil test center", "মাটি পরীক্ষা কোথায়", "মাটি পরীক্ষা কোথায়"):
        url = next((value for value in urls if "srdi" in value.lower()), "https://srdi.gov.bd/")
        return _make_action("openSourceLink", url=url), ("SRDI বা স্বীকৃত পরীক্ষাগারে মাটি পরীক্ষা করান।" if bn else "Use SRDI or an accredited laboratory for a soil test."), "soil_limits", None

    if _has(text, "what is boponx", "about boponx", "about this project", "what is this project", "project overview", "project purpose", "purpose of this app", "why was this app made", "বপনএক্স কী", "এই প্রকল্প কী", "প্রকল্প সম্পর্কে", "এই অ্যাপের উদ্দেশ্য"):
        return None, (
            "বপনএক্স একটি কৃষক-কেন্দ্রিক সিদ্ধান্ত-সহায়ক ওয়েব অ্যাপ। এটি মাঠের অবস্থান, কৃষকের দেওয়া তথ্য, NASA পর্যবেক্ষণ এবং উপলভ্য স্থানীয় কৃষি-প্রমাণ এক জায়গায় এনে মাঠ বোঝা ও পরিকল্পনা করতে সাহায্য করে। এটি কৃষিবিদের বিকল্প নয়; অনিশ্চিত বা মাঠ-স্তরের সিদ্ধান্ত স্থানীয় কৃষি সম্প্রসারণ কর্মকর্তার সাথে যাচাই করুন।"
            if bn
            else "BoponX is a farmer-focused decision-support website. It brings together a field location, farmer-provided information, NASA observations, and available local agricultural evidence to help explore a field and prepare a plan. It is not a substitute for an agronomist; verify uncertain or field-specific decisions with local agricultural extension staff."
        ), "project_info", None

    if _has(
        text,
        "who made boponx",
        "who made this project",
        "who created boponx",
        "who created this project",
        "who built boponx",
        "who developed boponx",
        "who developed this project",
        "who is behind boponx",
        "project creator",
        "project developer",
        "project team",
        "কে বপনএক্স তৈরি",
        "কে এই প্রকল্প তৈরি",
        "কারা বপনএক্স তৈরি",
        "কারা এই প্রকল্প তৈরি",
        "বপনএক্স কে বানিয়েছে",
        "বপনএক্স কে বানিয়েছে",
        "প্রকল্পের নির্মাতা",
        "প্রকল্পের ডেভেলপার",
        "কোন দল তৈরি করেছে",
    ):
        return None, (
            "বপনএক্স তৈরি করেছেন টিম লিডার রেজওয়ান হোসেন প্রিন্স এবং Team EARTH.exe, ২০২৬ সালের NASA International Space Apps Challenge-এর জন্য।"
            if bn
            else "BoponX was developed by Rezwan Hossain Prince (team leader) and Team EARTH.exe for the 2026 NASA International Space Apps Challenge."
        ), "project_info", None

    if _has(
        text,
        "how do i use boponx",
        "how can i use boponx",
        "how to use boponx",
        "how do i use this app",
        "how does boponx work",
        "how does this app work",
        "getting started with boponx",
        "বপনএক্স কীভাবে ব্যবহার",
        "বপনএক্স কিভাবে ব্যবহার",
        "এই অ্যাপ কীভাবে ব্যবহার",
        "এই অ্যাপ কিভাবে ব্যবহার",
        "কীভাবে শুরু করব",
        "কিভাবে শুরু করব",
    ):
        return None, (
            "শুরু করতে মানচিত্রে আপনার মাঠ বা জেলা নির্বাচন করুন। ড্যাশবোর্ডের NASA ডেটা ও মানচিত্রের স্তর দেখুন, তারপর রোটেশন ল্যাবে ফসল এবং কৃষি-তথ্য দিন। শেষে ৯০ দিনের পরিকল্পনা তৈরি করে এর প্রমাণ ও স্থানীয় পরামর্শ যাচাই করুন।"
            if bn
            else "Start by selecting your field or district on the map. Explore the dashboard and map layers, then enter your crops and farm details in Rotation Lab. Generate a 90-day plan and check its evidence with local agricultural guidance."
        ), "project_info", None

    if _has(
        text,
        "what data do you use",
        "what data does boponx use",
        "what does boponx use",
        "what data does this app use",
        "boponx uses what",
        "which data sources",
        "data sources",
        "which nasa data",
        "which satellite data",
        "what does nasa measure",
        "satellite data sources",
        "ডেটার উৎস",
        "কোন ডেটা ব্যবহার",
        "বপনএক্স কী ডেটা ব্যবহার",
        "বপনএক্স কোন তথ্য ব্যবহার",
        "নাসার তথ্য কী",
    ):
        return None, (
            "ড্যাশবোর্ডে উপলভ্য হলে NASA POWER বৃষ্টি/তাপমাত্রার সাম্প্রতিক ও ঐতিহাসিক প্রেক্ষাপট, GPM বৃষ্টিপাত, SMAP মাটির আর্দ্রতা, MODIS ভূমির রং/NDVI/পৃষ্ঠতাপ এবং SRTM উচ্চতা দেখানো হয়। কিছু দৃশ্যে EONET দুর্যোগ-সংক্রান্ত তথ্য ও সরকারি কৃষি উৎসও থাকে। কভারেজ, রেজোলিউশন ও সময়কাল ভিন্ন; কোনো স্যাটেলাইট স্তরই একক জমির pH/NPK মাপে না, আর ঐতিহাসিক বেসলাইন পূর্বাভাস নয়।"
            if bn
            else "When available, the dashboard shows NASA POWER recent and historical rainfall/temperature context, GPM precipitation, SMAP soil moisture, MODIS true color/NDVI/land-surface temperature, and SRTM elevation. Some views also include EONET hazard context and official agricultural sources. Coverage, resolution, and time windows differ; no satellite layer measures a parcel’s pH/NPK, and a historical baseline is not a forecast."
        ), "project_info", None

    if _has(text, "read dashboard", "read my dashboard", "dashboard summary", "summarize dashboard", "what does the dashboard show", "what is on the dashboard", "current dashboard", "surface dashboard", "ড্যাশবোর্ড পড়", "ড্যাশবোর্ডে কী আছে", "ড্যাশবোর্ডের সারাংশ", "ড্যাশবোর্ড কী দেখায়"):
        data = state.get("fieldData") or {}
        status = data.get("dataStatus", "unavailable")
        status_text = (
            ("লোড হচ্ছে" if bn else "loading")
            if status == "loading"
            else ("উপলভ্য" if bn else "available")
            if status == "available"
            else ("অনুপলভ্য" if bn else "unavailable")
        )
        values = [
            ("সাম্প্রতিক বৃষ্টি" if bn else "Recent rainfall", data.get("rainfall", "unavailable")),
            ("দৈনিক বৃষ্টির পার্থক্য" if bn else "Daily rainfall anomaly", data.get("rainAnomaly", "unavailable")),
            ("তাপমাত্রা" if bn else "Temperature", data.get("temperature", "unavailable")),
            ("মাটির আর্দ্রতা" if bn else "Soil moisture", data.get("soilMoisture", "unavailable")),
            ("বাষ্পীভবন চাহিদা" if bn else "Evapotranspiration", data.get("evapotranspiration", "unavailable")),
            ("পানি ভারসাম্য" if bn else "Water balance", data.get("waterBalance", "unavailable")),
            ("হিমঝুঁকি" if bn else "Frost risk", data.get("frostRisk", "unavailable")),
            ("কুয়াশা/ব্লাইট ঝুঁকি" if bn else "Fog/blight risk", data.get("fogBlightRisk", "unavailable")),
            ("আর্দ্রতা" if bn else "Relative humidity", data.get("humidity", "unavailable")),
            ("দুর্যোগ সতর্কতা" if bn else "Hazard context", data.get("hazards", "unavailable")),
            ("প্রমাণ প্রস্তুতি" if bn else "Evidence readiness", data.get("readiness", "unavailable")),
            ("তথ্যের সতেজতা" if bn else "Data freshness", data.get("dataFreshness", "unavailable")),
        ]
        location = state.get("selectedArea") or ("নির্বাচিত মাঠ" if bn else "selected field")
        layer = state.get("activeLayer") or ("কোনো ওভারলে চালু নেই" if bn else "no overlay selected")
        summary = " · ".join(f"{label}: {value}" for label, value in values)
        if status == "loading":
            status_note = "ডেটা লোড হচ্ছে; মানগুলো এখনও পরিবর্তিত হতে পারে।" if bn else "Data is still loading; values may update."
        elif status == "unavailable":
            status_note = "অনুপলভ্য মানকে শূন্য বা মাপা মান হিসেবে ধরা হয়নি। চাইলে ডেটা আবার লোড করতে বলুন।" if bn else "Unavailable values are not treated as zero or as measurements. Ask me to retry the data load if appropriate."
        else:
            status_note = "এগুলো অ্যাপে বর্তমানে দেখানো মান; পূর্বাভাস নয়।" if bn else "These are values currently shown in the app, not a forecast."
        plan = state.get("planContext") or {}
        verdict = plan.get("verdictBn" if bn else "verdict")
        plan_line = f" · {'পরিকল্পনার অবস্থা' if bn else 'Plan'}: {verdict}" if verdict else ""
        coordinates = data.get("fieldCoordinates", "unavailable")
        return None, (
            f"{'ড্যাশবোর্ড সারাংশ' if bn else 'Dashboard summary'} — {location} ({coordinates}); {'ডেটা' if bn else 'recent data'} {status_text}; {summary}; {'সক্রিয় স্তর' if bn else 'active layer'}: {layer}; {'নিকটতম ইভেন্ট' if bn else 'nearby events'}: {'; '.join(data.get('hazardEvents') or []) or ('কোনোটি তালিকাভুক্ত নয়' if bn else 'none listed')}; {('ঐতিহাসিক জলবায়ু' if bn else 'historical climatology')}: {data.get('climatology', 'unavailable')}{plan_line}. {status_note}"
        ), "dashboard_summary", None

    if _has(text, "what should i do", "what do you recommend", "give me a decision", "your decision", "what is your advice", "এখন কী করব", "কী পরামর্শ", "আপনার সিদ্ধান্ত"):
        plan = state.get("planContext") or {}
        reasons = plan.get("reasonsBn" if bn else "reasons") or []
        verdict = plan.get("verdictBn" if bn else "verdict")
        boundary = plan.get("boundaryBn" if bn else "boundary")
        if verdict or reasons:
            parts = [str(verdict)] if verdict else []
            parts.extend(str(reason) for reason in reasons[:3])
            if boundary:
                parts.append(str(boundary))
            return None, " ".join(parts), "run_plan", None
        return None, (
            "এখনও প্রদর্শিত পরিকল্পনা নেই, তাই নির্দিষ্ট সিদ্ধান্ত দেব না। মাঠ ও কৃষকের তথ্য দিয়ে পরিকল্পনা তৈরি করুন; প্রমাণ বা তথ্য অনুপলভ্য থাকলে তা স্পষ্ট দেখানো হবে।"
            if bn
            else "There is no displayed plan yet, so I won’t invent a recommendation. Select a field, add the farmer details you know, and generate a plan; missing evidence or data will remain explicit."
        ), "run_plan", None

    if _has(text, "how do i use this website", "how to use this website", "how do i use the site", "help me use the website", "ওয়েবসাইট কীভাবে ব্যবহার", "ওয়েবসাইট কীভাবে ব্যবহার", "সাইট কীভাবে ব্যবহার"):
        return None, (
            "মাঠ/জেলা বেছে নিতে Field map ব্যবহার করুন; Data layer, তারিখ ও মানচিত্রের ধরন বদলে পর্যবেক্ষণ দেখুন; Rotation Lab-এ ফসলের ইতিহাস ও কৃষকের তথ্য দিন; তারপর 90-Day Plan তৈরি করে কারণ ও উৎস দেখুন বা প্রিন্ট করুন। সহকারী উইন্ডোর ⠿ হ্যান্ডেল ধরে টেনে সরানো যায়।"
            if bn
            else "Use the Field map to choose a location; use Data controls to change layers, dates, and map style; enter crop history and farmer details in the Rotation Lab; then generate a 90-Day Plan to review its reasons and sources or print it. Drag the assistant by its ⠿ handle to move it."
        ), "project_info", None

    if _has(text, "map date", "observation date", "satellite date", "imagery date", "মানচিত্রের তারিখ", "স্যাটেলাইটের তারিখ") or _has(text, "latest satellite image", "days ago", "দিন আগে"):
        date_match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", text)
        if date_match:
            return _make_action("setMapDate", date=date_match.group(1)), "মানচিত্রের পর্যবেক্ষণ তারিখ বদলানো হচ্ছে।" if bn else "Changing the map observation date.", "map_controls", None
        days_match = re.search(r"\b(2|14|30|90|180)\s*(?:days?|দিন)\s*(?:ago|আগে)?\b", text)
        if days_match:
            days_ago = int(days_match.group(1))
            return _make_action("setMapDate", days_ago=days_ago), "স্যাটেলাইট মানচিত্রের সময় বদলানো হচ্ছে।" if bn else f"Showing the satellite map from {days_ago} days ago.", "map_controls", None
        if _has(text, "latest", "সর্বশেষ", "আজকের"):
            return _make_action("setMapDate", days_ago=2), "সর্বশেষ উপলভ্য মানচিত্রের তারিখ দেখাচ্ছি।" if bn else "Showing the latest available map date.", "map_controls", None
        return None, ("তারিখ হিসেবে ২, ১৪, ৩০, ৯০ বা ১৮০ দিন আগে বলুন, অথবা YYYY-MM-DD দিন।" if bn else "Choose 2, 14, 30, 90, or 180 days ago, or give a YYYY-MM-DD date."), "map_controls", None

    if _has(text, "base map", "basemap", "street map", "village map", "osm map", "ওএসএম মানচিত্র", "গ্রামের মানচিত্র", "switch to satellite", "use satellite map"):
        if _has(text, "street", "village", "osm", "গ্রামের"):
            style = "streets"
        elif _has(text, "satellite", "স্যাটেলাইট"):
            style = "satellite"
        else:
            return None, ("স্যাটেলাইট নাকি গ্রামের রাস্তার মানচিত্র চান?" if bn else "Would you like the satellite or village/street map?"), "map_controls", ["Satellite", "Village / street map"] if not bn else ["স্যাটেলাইট", "গ্রাম/রাস্তার মানচিত্র"]
        return _make_action("setMapStyle", style=style), "ভিত্তি মানচিত্র বদলানো হচ্ছে।" if bn else f"Changing the base map to {style}.", "map_controls", None

    if _has(text, "3d globe", "3d earth", "2d map", "flat map", "গ্লোব দেখাও", "3d পৃথিবী", "সমতল মানচিত্র", "2d মানচিত্র"):
        is_globe = _has(text, "3d globe", "3d earth", "গ্লোব দেখাও", "3d পৃথিবী")
        return _make_action("setMapProjection", is_globe=is_globe), "মানচিত্রের দৃশ্য বদলানো হচ্ছে।" if bn else f"Switching to the {'3D globe' if is_globe else '2D map'}.", "map_controls", None

    if _has(text, "zoom to space", "zoom out to space", "show earth from space", "মহাকাশে জুম", "স্পেস ভিউ"):
        return _make_action("setCameraPreset", mode="space"), "মহাকাশের মানচিত্র দৃশ্য দেখাচ্ছি।" if bn else "Showing the space view.", "map_controls", None
    if _has(text, "zoom to bangladesh", "show bangladesh", "বাংলাদেশে জুম", "বাংলাদেশ দেখাও"):
        return _make_action("setCameraPreset", mode="bangladesh"), "বাংলাদেশের মানচিত্রে জুম করছি।" if bn else "Zooming to Bangladesh.", "map_controls", None
    if _has(text, "zoom to field", "zoom to my field", "focus my field", "selected plot", "জমিতে জুম", "মাঠে জুম"):
        return _make_action("setCameraPreset", mode="field"), "নির্বাচিত মাঠে জুম করছি।" if bn else "Zooming to the selected field.", "map_controls", None

    start_date_match = re.search(r"\b(20\d{2})-(\d{2})-(\d{2})\b", text)
    if start_date_match and _has(text, "plan", "start date", "পরিকল্পনা", "শুরুর তারিখ"):
        year, month, day = (int(value) for value in start_date_match.groups())
        try:
            date(year, month, day)
        except ValueError:
            return None, "তারিখটি বৈধ নয়। YYYY-MM-DD আকারে সঠিক তারিখ দিন।" if bn else "That is not a valid date. Enter a real date in YYYY-MM-DD format.", "set_plan_date", None
        if 2026 <= year <= 2035:
            return _make_action("setPlanStartDate", year=year, month=month, day=day), "পরিকল্পনার শুরুর তারিখ বদলানো হচ্ছে।" if bn else "Changing the plan start date.", "set_plan_date", None
        return None, "তারিখটি ২০২৬–২০৩৫ সালের মধ্যে হতে হবে।" if bn else "The plan date must be between 2026 and 2035.", "set_plan_date", None

    if _has(text, "reset climate scenario", "reset what if", "reset what-if", "সিমুলেশন রিসেট", "জলবায়ু পরিস্থিতি রিসেট"):
        return _make_action("setClimateScenario", rain_shift_pct=0, temperature_shift_c=0), "জলবায়ু সিমুলেশন শূন্যে ফিরিয়ে নিচ্ছি।" if bn else "Resetting the climate scenario to zero shifts.", "climate_scenario", None
    if _has(text, "rainfall shift", "rain shift", "rainfall change", "temperature shift", "heat shift", "scenario", "বৃষ্টির পরিবর্তন", "বৃষ্টিপাত পরিবর্তন", "তাপমাত্রা বৃদ্ধি"):
        rain_shift = state.get("scenarioRainShiftPct", 0)
        temperature_shift = state.get("scenarioTempShiftC", 0)
        rain_match = re.search(r"([+-]?\d{1,2})\s*%", clause)
        temperature_match = re.search(r"([+]?\d+(?:\.\d+)?)\s*(?:°\s*)?(?:c\b|celsius\b|ডিগ্রি)", text)
        if _has(text, "rainfall shift", "rain shift", "rainfall change", "বৃষ্টির পরিবর্তন", "বৃষ্টিপাত পরিবর্তন") and rain_match:
            rain_shift = int(rain_match.group(1))
        if _has(text, "temperature shift", "heat shift", "তাপমাত্রা বৃদ্ধি") and temperature_match:
            temperature_shift = float(temperature_match.group(1))
        if not rain_match and not temperature_match:
            return None, ("বৃষ্টি পরিবর্তন −৫০% থেকে +৫০% (৫% ধাপে), অথবা তাপমাত্রা ০ থেকে +৪°C (০.৫° ধাপে) বলুন।" if bn else "Set rainfall from −50% to +50% in 5% steps, or temperature from 0 to +4°C in 0.5° steps."), "climate_scenario", None
        if rain_shift < -50 or rain_shift > 50 or rain_shift % 5 != 0:
            return None, ("বৃষ্টির পরিবর্তন −৫০% থেকে +৫০% এবং ৫% ধাপে হতে হবে।" if bn else "Rainfall shift must be from −50% to +50% in 5% steps."), "climate_scenario", None
        if temperature_shift < 0 or temperature_shift > 4 or temperature_shift * 2 % 1 != 0:
            return None, ("তাপমাত্রা পরিবর্তন ০ থেকে +৪°C এবং ০.৫°C ধাপে হতে হবে।" if bn else "Temperature shift must be from 0 to +4°C in 0.5°C steps."), "climate_scenario", None
        return _make_action("setClimateScenario", rain_shift_pct=rain_shift, temperature_shift_c=temperature_shift), "সিমুলেটেড জলবায়ু পরিস্থিতি আপডেট হয়েছে; এটি পূর্বাভাস নয়।" if bn else "The simulated climate scenario was updated; this is not a forecast.", "climate_scenario", None

    if _has(text, "opacity", "overlay transparency", "অপাসিটি", "স্বচ্ছতা"):
        opacity_match = re.search(
            r"\b(\d{1,3})\s*%",
            clause.translate(str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")),
        )
        if not opacity_match:
            return None, ("স্বচ্ছতা ২০% থেকে ৯৫%-এর মধ্যে বলুন।" if bn else "Choose an overlay opacity from 20% to 95%."), "map_controls", None
        opacity = int(opacity_match.group(1))
        if not 20 <= opacity <= 95:
            return None, ("ওভারলে স্বচ্ছতা ২০% থেকে ৯৫%-এর মধ্যে হতে হবে।" if bn else "Overlay opacity must be from 20% to 95%."), "map_controls", None
        return _make_action("setMapOpacity", opacity=opacity / 100), "ওভারলে স্বচ্ছতা বদলানো হচ্ছে।" if bn else f"Setting map overlay opacity to {opacity}%.", "map_controls", None

    layer = next((key for key, terms in LAYERS.items() if any(_normalize(term) in text for term in terms)), None)
    if layer or _has(text, "clear layer", "hide layer", "turn layer off", "map overlay off", "স্তর বন্ধ", "লেয়ার বন্ধ"):
        if _has(text, "off", "hide", "clear", "বন্ধ", "সরাও"):
            new_layer = None
        elif _has(text, "toggle", "switch", "change", "বদল", "পরিবর্তন"):
            new_layer = None if state.get("activeLayer") == layer else layer
        else:
            new_layer = layer
        return _make_action("setActiveLayer", layer=new_layer), "মানচিত্র স্তর আপডেট করা হয়েছে।" if bn else "Map layer updated.", "set_active_layer", None

    month = next((number for name, number in MONTHS.items() if name in text), None)
    if month and _has(text, "plan", "start", "from", "month", "মাস", "থেকে", "শুরু"):
        return _make_action("setStartMonth", month=month), "পরিকল্পনার শুরুর মাস বদলানো হয়েছে।" if bn else "Planning month updated.", "set_start_month", None
    year_match = re.search(r"\b20\d{2}\b", text)
    if year_match and _has(text, "plan", "year", "সাল", "বছর", "থেকে"):
        year = int(year_match.group())
        if 2026 <= year <= 2035:
            return _make_action("setStartYear", year=year), "পরিকল্পনার বছর বদলানো হয়েছে।" if bn else "Planning year updated.", "set_start_year", None
        return None, "পরিকল্পনার বছর ২০২৬ থেকে ২০৩৫-এর মধ্যে হতে হবে।" if bn else "The planning year must be between 2026 and 2035.", "set_start_year", None

    soil_status = None
    if _has(text, "soil test yes", "have a soil test", "soil report yes", "মাটি পরীক্ষা আছে", "রিপোর্ট আছে"):
        soil_status = "yes"
    elif _has(text, "soil test no", "no soil test", "no report", "মাটি পরীক্ষা নেই", "রিপোর্ট নেই"):
        soil_status = "no"
    elif _has(text, "soil test unknown", "not sure soil test", "মাটি পরীক্ষা নিশ্চিত নই"):
        soil_status = "unknown"
    if soil_status:
        state["soilTest"] = soil_status
        return _make_action("setSoilTest", soil_test=soil_status), "মাটি পরীক্ষার অবস্থা আপডেট হয়েছে।" if bn else "Soil-test status updated.", "soil_test", None

    ph_match = re.search(r"(?:\bp\s*h\s*=?\s*|\bph\s*=?\s*|(\d+(?:\.\d+)?)\s*p\s*h\b)(\d+(?:\.\d+)?)?", text)
    if ph_match and _has(text, "soil", "মাটি", "report", "পরীক্ষা", "ph"):
        value_text = ph_match.group(2) or ph_match.group(1)
        if not value_text:
            return None, "মাটি পরীক্ষার রিপোর্টে থাকা pH মানটি বলুন।" if bn else "Tell me the pH value printed on the soil-test report.", "set_soil_ph", None
        value = float(value_text)
        if not 0 <= value <= 14:
            return None, "pH অবশ্যই ০ থেকে ১৪-এর মধ্যে হতে হবে।" if bn else "Soil pH must be between 0 and 14.", "set_soil_ph", None
        if state.get("soilTest") != "yes":
            if _has(text, "have a soil test", "soil test report", "মাটি পরীক্ষা আছে", "রিপোর্ট আছে"):
                return _make_action("setSoilTest", soil_test="yes"), "বাস্তব মাটি পরীক্ষার রিপোর্ট আছে হিসেবে নথিভুক্ত করুন, এরপর pH দিন।" if bn else "Your soil-test report is noted; enter its pH in a separate message.", "soil_test", None
            return None, "pH সেট করার আগে নিশ্চিত করুন যে আপনার বাস্তব মাটি পরীক্ষার রিপোর্ট আছে।" if bn else "I can only set pH if you confirm a real soil-test report exists. Do you have one?", "set_soil_ph", ["হ্যাঁ", "না"] if bn else ["Yes", "No"]
        return _make_action("setSoilPh", soil_ph=value), "রিপোর্টের pH মান সেট করা হয়েছে।" if bn else "Soil-test pH recorded.", "set_soil_ph", None

    if _has(text, "not sure", "unknown", "নিশ্চিত নই", "জানি না", "অনিশ্চিত"):
        if _has(text, "water", "পানি", "সেচ"):
            return _make_action("setWaterSource", water_source="unknown"), "পানির উৎস অনিশ্চিত রাখা হয়েছে।" if bn else "Water source set to not sure.", "farmer_input", None
        if _has(text, "drain", "standing water", "পানি জম", "নিকাশ"):
            return _make_action("setDrainage", drainage="unknown"), "নিকাশের অবস্থা অনিশ্চিত রাখা হয়েছে।" if bn else "Drainage set to not sure.", "farmer_input", None
        if _has(text, "soil test", "মাটি পরীক্ষা"):
            return _make_action("setSoilTest", soil_test="unknown"), "মাটি পরীক্ষার অবস্থা অনিশ্চিত রাখা হয়েছে।" if bn else "Soil-test status set to not sure.", "soil_test", None
        return _make_action("setNotSure"), "তথ্যটি অনিশ্চিত রাখা হয়েছে।" if bn else "I’ll leave that answer as not sure.", "farmer_input", None

    if _has(text, "rainfed", "rain fed", "বৃষ্টিনির্ভর", "বৃষ্টির উপর"):
        return _make_action("setWaterSource", water_source="rainfed"), "পানির উৎস বৃষ্টিনির্ভর করা হয়েছে।" if bn else "Water source set to rainfed.", "farmer_input", None
    if _has(text, "both rain and irrigation", "rain and irrigation", "বৃষ্টি ও সেচ"):
        return _make_action("setWaterSource", water_source="both"), "বৃষ্টি ও সেচ উভয় উৎস নির্ধারণ করা হয়েছে।" if bn else "Water source set to both rain and irrigation.", "farmer_input", None
    if _has(text, "irrigated", "irrigation", "সেচনির্ভর", "সেচ"):
        return _make_action("setWaterSource", water_source="irrigated"), "পানির উৎস সেচনির্ভর করা হয়েছে।" if bn else "Water source set to irrigated.", "farmer_input", None
    if _has(text, "water drains", "drains quickly", "দ্রুত পানি নেমে", "পানি দ্রুত সরে"):
        return _make_action("setDrainage", drainage="drains"), "নিকাশ দ্রুত হয় হিসেবে সেট করা হয়েছে।" if bn else "Drainage set to drains quickly.", "farmer_input", None
    if _has(text, "water stays", "standing water", "জলাবদ্ধ", "পানি জমে থাকে"):
        return _make_action("setDrainage", drainage="stays"), "পানি জমে থাকে হিসেবে সেট করা হয়েছে।" if bn else "Drainage set to standing water.", "farmer_input", None
    if _has(text, "water sometimes", "sometimes drains", "মাঝে মাঝে পানি"):
        return _make_action("setDrainage", drainage="sometimes"), "নিকাশের অবস্থা মাঝে মাঝে হিসেবে সেট করা হয়েছে।" if bn else "Drainage set to sometimes.", "farmer_input", None

    priority = None
    if _has(text, "priority water", "water saving", "prioritize water", "পানি সাশ্রয়", "পানিকে অগ্রাধিকার"):
        priority = "water"
    elif _has(text, "priority soil", "soil health priority", "prioritize soil", "মাটির স্বাস্থ্যকে অগ্রাধিকার"):
        priority = "soil"
    elif _has(text, "production stability", "priority stability", "স্থিতিশীল উৎপাদন", "উৎপাদন স্থিতিশীলতা"):
        priority = "production_stability"
    if priority:
        return _make_action("setPriority", priority=priority), "কৃষকের অগ্রাধিকার আপডেট হয়েছে।" if bn else "Farmer priority updated.", "farmer_input", None

    equipment = None
    if _has(text, "manual", "traditional", "হাতে", "সনাতন"):
        equipment = "manual_traditional"
    elif _has(text, "zero till", "bed planter", "জিরো টিল"):
        equipment = "conservation_zero_till"
    elif _has(text, "tractor", "power tiller", "যন্ত্রপাতি", "ট্রাক্টর"):
        equipment = "power_tiller_machinery"
    if equipment:
        return _make_action("setEquipmentAccess", equipment_access=equipment), "যন্ত্রপাতির তথ্য আপডেট হয়েছে।" if bn else "Equipment access updated.", "farmer_input", None

    market = None
    if _has(text, "household", "family food", "পরিবারের খাদ্য"):
        market = "household_subsistence"
    elif _has(text, "high value", "commercial", "উচ্চমূল্যের"):
        market = "high_value_commercial"
    elif _has(text, "forage", "livestock", "গোখাদ্য", "পশুখাদ্য"):
        market = "forage_livestock"
    elif _has(text, "local market", "cash market", "স্থানীয় বাজার", "স্থানীয় বাজার"):
        market = "local_cash_market"
    if market:
        return _make_action("setMarketPreference", market_preference=market), "বাজারের পছন্দ আপডেট হয়েছে।" if bn else "Market preference updated.", "farmer_input", None

    if _has(
        text,
        "should i plant",
        "can i plant",
        "can i grow",
        "is this crop suitable",
        "which crop should i",
        "what crop should i",
        "what should i plant",
        "কোন ফসল লাগাব",
        "কোন ফসল চাষ করব",
        "এই ফসল চাষ করা যাবে",
        "ফসলটি উপযোগী",
    ):
        plan = state.get("planContext") or {}
        reasons = plan.get("reasonsBn" if bn else "reasons") or []
        verdict = plan.get("verdictBn" if bn else "verdict")
        if verdict or reasons:
            parts = [str(verdict)] if verdict else []
            parts.extend(str(reason) for reason in reasons[:3])
            return None, " ".join(parts), "run_plan", None
        answer = (
            "শুধু ফসলের নাম বা উপগ্রহ তথ্য থেকে উপযোগিতা নির্ধারণ করা যায় না; এই অ্যাপের রোটেশন র‌্যাঙ্কিং প্রমাণ-গেটে লক থাকে। মাঠ ও কৃষকের তথ্য দিয়ে পরিকল্পনা তৈরি করুন, তারপর প্রদর্শিত প্রমাণ স্থানীয় কৃষি কর্মকর্তার সাথে যাচাই করুন।"
            if bn
            else "Crop suitability cannot be established from a crop name or satellite data alone; this app keeps rotation rankings behind an evidence gate. Generate a plan using your field and farmer details, then verify its displayed evidence with local agricultural extension staff."
        )
        return None, answer, "crop_check", None

    crop = _crop_from(clause)
    if crop:
        if _has(text, "remove", "delete", "remove my last", "আগের ফসল সরাও", "ফসল বাদ"):
            return _make_action("removePreviousCrop", crop=crop), "আগের ফসলের তালিকা আপডেট হচ্ছে।" if bn else "Removing that previous crop.", "crop_check", None
        if _has(text, "grew", "grown", "last season", "previous crop", "আগে চাষ", "গত মৌসুম", "গত মরসুম", "আগের ফসল"):
            return _make_action("addPreviousCrop", crop=crop), "আগের ফসল যোগ করা হচ্ছে।" if bn else f"Recording {crop} as a previous crop.", "crop_check", None
        if pending == "set_intended_crop" or _has(text, "want", "intend", "plant", "grow", "set crop", "my crop", "set ", "chash", "korbo", "amar jomite", "চাষ করব", "চাষ করতে", "আমার ফসল", "পরিকল্পিত ফসল", "ফসল হিসেবে"):
            return _make_action("setIntendedCrop", crop=crop), "পরিকল্পিত ফসল আপডেট হয়েছে।" if bn else f"Setting {crop} as the intended crop.", "crop_check", None

    if _has(text, "want to grow", "which crop", "choose a crop", "কোন ফসল", "ফসল বেছে"):
        crop_names = list(CROPS.keys())
        translated = {"rice": "ধান", "wheat": "গম", "maize": "ভুট্টা", "pulse": "ডাল", "mustard": "সরিষা", "vegetables": "সবজি", "jute": "পাট", "other": "অন্যান্য"}
        choices = [translated[crop] for crop in crop_names] if bn else crop_names
        return None, "কোন ফসলটি চান?" if bn else "Which crop would you like?", "set_intended_crop", choices

    if _has(text, "generate plan", "make plan", "create plan", "run plan", "generate my plan", "পরিকল্পনা তৈরি", "পরিকল্পনা বানাও", "প্ল্যান তৈরি"):
        return _make_action("runPlan"), "আপনার পরিকল্পনা তৈরি করছি।" if bn else "Generating your plan.", "run_plan", None

    if _has(
        text,
        "wetter than usual",
        "compare with baseline",
        "compare with the baseline",
        "baseline comparison",
        "how is the rain",
        "rainfall",
        "precipitation",
        "bristi",
        "বৃষ্টির পরিমাণ",
        "বৃষ্টি কেমন",
        "তাপমাত্রা",
        "tapmatra",
        "temperature",
        "soil moisture",
        "smap",
        "matti",
        "মাটির আর্দ্রতা",
        "hazard",
        "দুর্যোগ",
        "fog",
        "blight",
        "frost",
        "humidity",
        "relative humidity",
        "dew point",
        "vpd",
        "vapor pressure",
        "evapotranspiration",
        "et0",
        "water balance",
        "heat stress",
        "heat-stress",
        "cold stress",
        "cold-stress",
        "heavy rain",
        "heavy-rain",
        "dry days",
        "wind",
        "baseline",
        "climatology",
        "data freshness",
        "data through",
        "where is this data from",
        "উৎস ও সতেজতা",
        "শিশিরাঙ্ক",
        "আর্দ্রতা",
        "হিমঝুঁকি",
        "কুয়াশা",
        "কুয়াশা",
        "বাষ্পীভবন",
        "পানির ভারসাম্য",
        "ডেটার তারিখ",
        "বাতাস",
        "তাপ চাপ",
        "ঠান্ডার চাপ",
    ):
        data = state.get("fieldData") or {}
        if _has(text, "compare with baseline", "compare with the baseline", "baseline comparison", "wetter than usual"):
            if _has(text, "temperature", "তাপমাত্রা", "tapmatra"):
                recent = data.get("temperature", "unavailable")
                baseline = data.get("baselineTemperature", "unavailable")
                delta = data.get("temperatureDelta", "unavailable")
                return None, (
                    f"সাম্প্রতিক গড় তাপমাত্রা: {recent}; ঐতিহাসিক বেসলাইন: {baseline}; ড্যাশবোর্ডের পার্থক্য: {delta}. এটি পূর্বাভাস নয়।"
                    if bn
                    else f"Recent mean temperature: {recent}; historical baseline: {baseline}; dashboard difference: {delta}. This is not a forecast."
                ), "conditions", None
            recent = data.get("rainfallDaily", "unavailable")
            baseline = data.get("baselineRainfall", "unavailable")
            anomaly = data.get("rainAnomaly", "unavailable")
            return None, (
                f"সাম্প্রতিক দৈনিক গড় বৃষ্টি: {recent}; ঐতিহাসিক দৈনিক বেসলাইন: {baseline}; ড্যাশবোর্ডে গণনা করা পার্থক্য: {anomaly}. বেসলাইন পূর্বাভাস নয়।"
                if bn
                else f"Recent mean daily rainfall: {recent}; historical daily baseline: {baseline}; dashboard-calculated difference: {anomaly}. The baseline is not a forecast."
            ), "conditions", None
        if _has(text, "rain", "bristi", "বৃষ্টি") and not _has(text, "heavy rain", "heavy-rain", "ভারী বৃষ্টি"):
            value = data.get("rainfall", "unavailable")
            return None, (f"বর্তমান নির্বাচিত মাঠ ({state.get('selectedArea') or 'অবস্থান'})-এর দেখানো সাম্প্রতিক বৃষ্টি: {value}. এটি পর্যবেক্ষিত/উপলভ্য তথ্য, পূর্বাভাস নয়।" if bn else f"Recent rainfall shown for the selected field ({state.get('selectedArea') or 'location'}): {value}. This is available observed data, not a forecast."), "conditions", None
        if _has(text, "temperature", "tapmatra", "তাপমাত্রা"):
            value = data.get("temperature", "unavailable")
            return None, (f"ড্যাশবোর্ডে দেখানো তাপমাত্রা: {value}. এটি পূর্বাভাস নয়।" if bn else f"Temperature currently shown on the dashboard: {value}. This is not a forecast."), "conditions", None
        if _has(text, "soil", "smap", "মাটি"):
            value = data.get("soilMoisture", "unavailable")
            return None, (f"ড্যাশবোর্ডে দেখানো মাটির আর্দ্রতা: {value}. এটি pH বা NPK মাপে না।" if bn else f"Soil moisture shown on the dashboard: {value}. This does not measure pH or NPK."), "soil_limits", None
        metric_groups = [
            (("fog", "blight", "কুয়াশা", "কুয়াশা"), "fogBlightRisk", "কুয়াশা/ব্লাইট-ঝুঁকির দিন", "Fog/blight-risk days"),
            (("frost", "frost risk", "হিমঝুঁকি"), "frostRisk", "হিমঝুঁকির দিন", "Frost-risk days"),
            (("relative humidity", "humidity", "আর্দ্রতা"), "humidity", "আপেক্ষিক আর্দ্রতা", "Relative humidity"),
            (("dew point", "dewpoint", "শিশিরাঙ্ক"), "dewPoint", "শিশিরাঙ্ক", "Dew point"),
            (("vpd", "vapor pressure", "বাষ্পচাপ"), "vaporPressureDeficit", "বাষ্পচাপ ঘাটতি (VPD)", "Vapor-pressure deficit (VPD)"),
            (("evapotranspiration", "et0", "evaporation demand", "বাষ্পীভবন"), "evapotranspiration", "বাষ্পীভবন চাহিদা (ET₀)", "Evapotranspiration demand (ET₀)"),
            (("water balance", "পানির ভারসাম্য"), "waterBalance", "দৈনিক পানি ভারসাম্য (বৃষ্টি − ET₀)", "Daily water balance (rain − ET₀)"),
            (("heat stress", "heat-stress", "তাপ চাপ"), "heatStress", "তাপচাপের দিন", "Heat-stress days"),
            (("cold stress", "cold-stress", "ঠান্ডার চাপ"), "coldStress", "শৈত্যচাপের দিন", "Cold-stress days"),
            (("heavy rain", "heavy-rain", "ভারী বৃষ্টি"), "heavyRain", "ভারী বৃষ্টির দিন", "Heavy-rain days"),
            (("dry days", "শুষ্ক দিন"), "dryDays", "শুষ্ক দিন", "Dry days"),
            (("wind", "বাতাস"), "wind", "গড় বাতাস", "Mean wind"),
        ]
        for terms, key, label_bn, label_en in metric_groups:
            if _has(text, *terms):
                value = data.get(key, "unavailable")
                return None, f"{label_bn if bn else label_en}: {value}.", "conditions", None
        if _has(text, "baseline", "climatology", "90-day outlook", "ঐতিহাসিক বেসলাইন", "জলবায়ু তালিকা"):
            return None, (
                f"ড্যাশবোর্ডের ৯০ দিনের ঐতিহাসিক জলবায়ু সারাংশ: {data.get('climatology', 'unavailable')}. এটি পূর্বাভাস নয়।"
                if bn
                else f"Displayed 90-day historical climatology: {data.get('climatology', 'unavailable')}. This is not a forecast."
            ), "conditions", None
        if _has(text, "data freshness", "data through", "where is this data from", "origin", "freshness", "উৎস ও সতেজতা", "ডেটার তারিখ", "তথ্যের উৎস"):
            return None, (
                f"তথ্যের উৎস: {data.get('evidenceOrigin', 'unavailable')}; সর্বশেষ সময়: {data.get('dataFreshness', 'unavailable')}."
                if bn
                else f"Evidence origin: {data.get('evidenceOrigin', 'unavailable')}; latest-data status: {data.get('dataFreshness', 'unavailable')}."
            ), "conditions", None
        if _has(text, "hazard", "eonet", "alert", "দুর্যোগ", "সতর্কতা"):
            events = data.get("hazardEvents") or []
            event_text = "; ".join(str(item) for item in events) if events else ("কোনো ইভেন্ট দেখানো হয়নি" if bn else "no events listed")
            return None, (
                f"ড্যাশবোর্ডে দুর্যোগ তথ্য: {data.get('hazards', 'unavailable')}; নিকটতম প্রদর্শিত ইভেন্ট: {event_text}. স্থানীয় সতর্কতা যাচাই করুন।"
                if bn
                else f"Dashboard hazard context: {data.get('hazards', 'unavailable')}; nearest displayed events: {event_text}. Verify local advisories."
            ), "conditions", None
        return None, ("এই ডেটা বর্তমানে অনুপলভ্য। ড্যাশবোর্ডে কোনো মান দেখানো হয়নি।" if bn else "This data is currently unavailable; no value is being shown."), "conditions", None

    if _has(text, "rotation", "crop ranking", "suitability", "evidence gate", "ফসল পর্যায়", "ফসল উপযোগিতা", "প্রমাণ গেট", "প্রমাণ-গেট"):
        return None, ("ফসলের উপযোগিতা ও রোটেশন র‌্যাঙ্কিং প্রমাণ-গেটের কারণে লক থাকে। উপগ্রহ তথ্য একা মাঠের উপযোগিতা নির্ধারণ করে না; স্থানীয় কৃষি কর্মকর্তার সাথে যাচাই করুন।" if bn else "Crop-suitability and rotation rankings remain locked behind the evidence gate. Satellite data alone cannot establish field suitability; verify with local agricultural extension staff."), "crop_check", None

    if _has(text, "what is missing", "what information is missing", "what do you need", "কী বাকি", "কোন তথ্য বাকি"):
        missing = []
        if not state.get("selectedArea"):
            missing.append(("field", "মাঠ"))
        if not state.get("previousCrops"):
            missing.append(("previous crop history", "আগের ফসলের তথ্য"))
        if not state.get("intendedCrop"):
            missing.append(("intended crop", "পরিকল্পিত ফসল"))
        if state.get("waterSource") in {None, "unknown"}:
            missing.append(("water source", "পানির উৎস"))
        if state.get("drainage") in {None, "unknown"}:
            missing.append(("drainage", "নিকাশের অবস্থা"))
        if state.get("soilTest") in {None, "unknown"}:
            missing.append(("soil-test status", "মাটি পরীক্ষার অবস্থা"))
        return None, (
            "এখনও জানা দরকার: " + ", ".join(item[1] for item in missing) + "।" if bn and missing
            else "আর কোনো প্রোফাইল তথ্য বাধ্যতামূলক নয়; অজানা তথ্য এভাবেই রাখা যাবে।" if bn
            else "Still helpful to know: " + ", ".join(item[0] for item in missing) + "." if missing
            else "No additional profile information is required; unknown answers can remain unknown."
        ), "farm_gaps", None

    if _has(text, "why this advice", "why this plan", "explain this advice", "এই পরামর্শ কেন", "পরামর্শ ব্যাখ্যা"):
        plan = state.get("planContext") or {}
        reasons = plan.get("reasonsBn" if bn else "reasons") or []
        if reasons:
            return None, " ".join(str(reason) for reason in reasons[:3]), "run_plan", None
        return None, ("পরিকল্পনা তৈরি হলে এর প্রদর্শিত কারণ ও উৎস ব্যাখ্যা করতে পারব।" if bn else "Generate a plan first, and I can explain its displayed reasons and sources."), "run_plan", None

    if _has(text, "what can you do", "help", "commands", "সাহায্য", "কী করতে পারো", "কী করতে পারেন"):
        return None, ("আমি মানচিত্র ও এলাকা নির্বাচন, স্তর বদল, ফসল/মাটি/পানি তথ্য, পরিকল্পনা, প্রিন্ট এবং সরকারি উৎস খুলতে পারি।" if bn else "I can select a field or map layer, update crop/soil/water details, generate or print a plan, and open official support links."), "fallback", None

    return None, None, "fallback", None


def route(
    message: str,
    lang: str = "en",
    history: list[dict[str, Any]] | None = None,
    snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    raw = (message or "").strip()
    active_lang = _language(raw, lang)
    state = dict(snapshot or {})
    pending = None
    previous_intent = None
    if history:
        for item in reversed(history):
            if isinstance(item, dict):
                if item.get("pending") and pending is None:
                    pending = str(item["pending"])
                if item.get("role") == "assistant" and item.get("intent") and previous_intent is None:
                    previous_intent = str(item["intent"])
            if pending and previous_intent:
                break
    if (
        not pending
        and previous_intent == "crop_check"
        and _has(raw, "and for", "what about", "আর", "তাহলে")
        and _crop_from(raw)
    ):
        pending = "set_intended_crop"

    actions: list[dict[str, Any]] = []
    replies: list[str] = []
    choices: list[str] | None = None
    intent = "fallback"
    next_pending: str | None = None
    for clause in _split(raw):
        action, reply, clause_intent, clause_choices = _action_for_clause(
            clause, state, active_lang, pending, state.get("officialSourceUrls") or []
        )
        if action:
            actions.append(action)
            payload = action.get("payload", {})
            if action["type"] == "setSoilTest":
                state["soilTest"] = payload.get("soil_test")
            elif action["type"] == "setIntendedCrop":
                state["intendedCrop"] = payload.get("crop")
            elif action["type"] == "setActiveLayer":
                state["activeLayer"] = payload.get("layer")
            elif action["type"] == "addPreviousCrop":
                state["previousCrops"] = [*(state.get("previousCrops") or []), payload.get("crop")]
            elif action["type"] == "setStartMonth":
                state["startMonth"] = payload.get("month")
            elif action["type"] == "setStartYear":
                state["startYear"] = payload.get("year")
            elif action["type"] == "setPlanStartDate":
                state["startYear"] = payload.get("year")
                state["startMonth"] = payload.get("month")
                state["startDay"] = payload.get("day")
            elif action["type"] == "selectStrategy":
                state["selectedStrategyId"] = payload.get("strategy_id")
            elif action["type"] == "setClimateScenario":
                state["scenarioRainShiftPct"] = payload.get("rain_shift_pct")
                state["scenarioTempShiftC"] = payload.get("temperature_shift_c")
            elif action["type"] == "setMapStyle":
                state["mapBaseStyle"] = payload.get("style")
            elif action["type"] == "setMapProjection":
                state["mapIsGlobe"] = payload.get("is_globe")
            if action["type"] == "runPlan":
                intent = "run_plan"
            else:
                intent = clause_intent or intent
            pending = None
        if reply:
            replies.append(reply)
            if not action and clause_intent:
                intent = clause_intent
        if not action and clause_intent == "crop_check":
            mentioned_crop = _crop_from(clause)
            if mentioned_crop:
                state["requestedCrop"] = mentioned_crop
        if clause_choices:
            choices = clause_choices
        if clause_intent in {"reset_farm", "clear_previous_crops", "clear_intended_crop"} and not action:
            next_pending = clause_intent
            intent = clause_intent
            break
        if clause_choices:
            next_pending = clause_intent
            break
        if not action and not reply and clause_intent == "fallback":
            intent = "fallback"

    if not actions and not replies and raw:
        _area, area_choices = _find_area(raw)
        if area_choices:
            choices = area_choices
            replies = ["Which Bangladesh area did you mean?" if active_lang == "en" else "আপনি বাংলাদেশের কোন এলাকাটি বোঝাচ্ছেন?"]
            intent = "select_place"
            next_pending = "select_place"
        else:
            replies = [
                "I’m not sure I understood. Try selecting a field, changing a layer, updating a farm answer, or asking for a plan."
                if active_lang == "en"
                else "আপনার কথাটি বুঝতে পারিনি। মাঠ বা মানচিত্র স্তর নির্বাচন, কৃষি-তথ্য পরিবর্তন, অথবা পরিকল্পনা চাইতে পারেন।"
            ]

    if not raw:
        replies = ["আমি শুনছি। কী করতে চান?" if active_lang == "bn" else "I’m listening. What would you like to do?"]

    return {
        "reply": " ".join(dict.fromkeys(replies)),
        "intent": intent,
        "mode": "deterministic",
        "lang": active_lang,
        "actions": actions,
        "suggestions": suggestions(intent, state, active_lang, raw),
        "pending": next_pending,
        "choices": choices,
    }
