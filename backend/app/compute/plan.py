"""Deterministic location aware 90 day decision support plan.

The plan uses farmer supplied context, regional evidence routing, recent NASA
POWER context when available, and monthly POWER climatology references. It does
not invent crop suitability, planting dates, yield outcomes, or soil chemistry.
"""
from __future__ import annotations

from typing import Any

MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
    7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December",
}

CROP_LABELS = {
    "rice": "Rice",
    "wheat": "Wheat",
    "maize": "Maize",
    "pulse": "Pulse",
    "mustard": "Mustard",
    "vegetables": "Vegetables",
    "jute": "Jute",
    "other": "Other crop",
}

CROP_CALENDAR_PREFIXES = {
    "rice": ("rice-",),
    "wheat": ("wheat",),
    "maize": ("maize",),
    "pulse": ("lentil", "green-gram"),
    "mustard": ("mustard",),
    "jute": ("jute",),
}


def _month(start_year: int, start_month: int, offset: int) -> tuple[int, int]:
    year = start_year + (start_month - 1 + offset) // 12
    month = (start_month - 1 + offset) % 12 + 1
    return year, month


def _task(code: str, text: str, category: str, reason: str, evidence: str = "farmer_and_local_context") -> dict[str, str]:
    return {
        "code": code,
        "en": text,
        "bn": text,
        "category": category,
        "reason": reason,
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
    }
    if not isinstance(recent_environment, dict) or recent_environment.get("status") != "available":
        return result

    recent_summary = recent_environment.get("summary")
    if not isinstance(recent_summary, dict):
        return result

    recent_temp = recent_summary.get("temperature_mean_c")
    recent_rain = recent_summary.get("precipitation_total_mm")
    rain_days = recent_summary.get("precipitation_valid_days")
    result["recent_temperature_c"] = recent_temp if isinstance(recent_temp, (int, float)) else None

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


def _decision_advice(
    profile: dict[str, Any],
    context: dict[str, Any],
    condition: dict[str, Any],
) -> dict[str, Any]:
    intended = profile.get("intended_crop")
    calendars = context.get("calendar_evidence") or []
    matches = _calendar_matches(intended, calendars)
    region = context["nearest_supported_region"]["name_en"]
    crop_label = CROP_LABELS.get(intended, "the intended crop") if intended else None

    reasons: list[str] = []
    next_step = "Choose the next crop you are considering, then review the regional evidence before committing."
    status = "NEEDS_INTENTION"
    verdict = "No crop decision has been entered yet."

    if intended:
        if matches:
            status = "REASONABLE_TO_EXPLORE"
            verdict = f"{crop_label} is reasonable to explore because official crop weather calendar evidence exists for the {region} evidence hub."
            reasons.append("An official regional crop weather calendar source is indexed for this crop.")
            next_step = "Open the regional calendar source and compare it with the field water, drainage, soil test, and recent NASA context before committing."
        else:
            status = "VERIFY_BEFORE_COMMITTING"
            verdict = f"BoponX cannot confirm {crop_label} from the current regional evidence index."
            reasons.append("No matching official BAMIS crop calendar is currently indexed for this crop in the selected regional hub.")
            next_step = "Verify this crop with the local agricultural office or choose a crop that has an official regional calendar source before making a seasonal commitment."

    rain_signal = condition.get("rain_signal")
    water_source = profile.get("water_source")
    drainage = profile.get("water_after_heavy_rain")

    if drainage == "stays" and rain_signal == "wetter_than_baseline":
        status = "REVIEW_WATER_RISK_FIRST"
        reasons.append("The farmer reports persistent standing water and recent rainfall is above the selected month historical baseline.")
        next_step = "A better immediate step is to verify drainage and standing water risk before committing to the intended crop."
    elif water_source == "rainfed" and rain_signal == "drier_than_baseline":
        status = "REVIEW_WATER_ACCESS_FIRST"
        reasons.append("The field is mainly rainfed while recent rainfall is below the selected month historical baseline.")
        next_step = "A better immediate step is to confirm water access and keep monitoring rainfall before committing to the intended crop."

    if profile.get("soil_test") != "yes":
        reasons.append("No verified soil chemistry report is available, so BoponX does not judge pH or nutrient suitability.")

    history = _history(profile)
    if intended and intended in history:
        reasons.append("The intended crop also appears in the recent crop history. Rotation benefit cannot be judged until crop sequence rules are reviewed.")

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
        "boundary": "BoponX can advise on decision readiness and evidence gaps now. It does not rank crop suitability until reviewed crop requirements, soil constraints, and crop sequence rules are encoded.",
    }


def _climate_task(month_index: int, region: str, year: int, month: int, baseline: dict[str, Any] | None) -> dict[str, str]:
    month_name = MONTH_NAMES[month]
    if not baseline:
        return _task(
            f"m{month_index}_climate_reference",
            f"For {month_name} in {region}, keep checking the latest NASA evidence and record what is actually happening in the field. The monthly climatology is unavailable, so no baseline value is invented.",
            "nasa_context",
            "Use current evidence without fabricating a missing historical reference.",
            "NASA POWER and field observations",
        )

    temp = baseline.get("temperature_mean_c")
    rain = baseline.get("precipitation_mean_daily_mm")
    temp_text = f"{temp:.1f}°C" if isinstance(temp, (int, float)) else "not available"
    rain_text = f"{rain:.1f} mm per day" if isinstance(rain, (int, float)) else "not available"
    return _task(
        f"m{month_index}_climate_reference",
        f"For {month_name} {year}, use the {region} NASA POWER climatology as a reference: temperature {temp_text} and daily rainfall {rain_text}. Compare the field with this historical context instead of treating it as a forecast.",
        "nasa_context",
        "Each planning month should use its own regional historical climate reference.",
        "NASA POWER climatology",
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
    history = _history(profile)
    intended = profile.get("intended_crop")
    soil_test = profile.get("soil_test", "unknown")
    priority = profile.get("priority", "production_stability")
    water_source = profile.get("water_source", "unknown")
    drainage = profile.get("water_after_heavy_rain", "unknown")

    baseline_summaries = _baseline_summaries(baseline_environment, baseline_window)
    first_baseline = baseline_summaries[0] if baseline_summaries else None
    condition = _recent_condition(recent_environment, first_baseline)
    advice = _decision_advice(profile, context, condition)

    months: list[dict[str, Any]] = []

    for offset in range(3):
        index = offset + 1
        year, month = _month(start_year, start_month, offset)
        baseline = baseline_summaries[offset] if offset < len(baseline_summaries) else None
        tasks: list[dict[str, str]] = [_climate_task(index, region_name, year, month, baseline)]

        if index == 1:
            history_text = ", ".join(CROP_LABELS.get(crop, crop.title()) for crop in history) if history else "not known"
            tasks.append(_task(
                "m1_crop_history",
                f"Confirm the recent crop history for this field. Current record: {history_text}. Keep this with any soil test report so an adviser can interpret field history and soil results together.",
                "field_history",
                "Previous crops are part of rotation context and help a local adviser interpret soil information.",
            ))
            if intended:
                tasks.append(_task(
                    "m1_intention",
                    f"Record the farmer's current intention: explore {CROP_LABELS.get(intended, intended.title())}. Treat this as a choice to evaluate, not an approved recommendation.",
                    "farmer_intention",
                    "The plan should respond to what the farmer wants to do now.",
                ))
            else:
                tasks.append(_task(
                    "m1_intention",
                    "Choose the crop or seasonal action you are considering next. BoponX cannot evaluate a decision that has not been stated.",
                    "farmer_intention",
                    "The farmer intention is needed for useful decision support.",
                ))
            tasks.append(_task(
                "m1_water_drainage",
                f"Verify water conditions in the field. Water source is recorded as {water_source}; heavy rain behavior is recorded as {drainage}. Correct these answers if field conditions differ.",
                "field_observation",
                "Water access and drainage can change which risks need attention first.",
            ))
            tasks.append(_task(
                "m1_soil_evidence",
                "Keep the soil test report with this field record and use only values printed on that report." if soil_test == "yes"
                else "Do not guess pH or nutrients. If the next crop decision depends on soil chemistry, arrange a local soil test before treating chemistry as known.",
                "soil_evidence",
                "Soil chemistry must come from a real test, not satellite inference.",
            ))

            if condition["rain_signal"] == "wetter_than_baseline":
                tasks.append(_task(
                    "m1_recent_wet_signal",
                    "Recent NASA POWER rainfall is above the selected month historical baseline. Compare that signal with standing water and drainage observations before making a water sensitive field decision.",
                    "recent_conditions",
                    "Recent regional rainfall is wetter than the historical monthly reference.",
                    "NASA POWER recent context and climatology",
                ))
            elif condition["rain_signal"] == "drier_than_baseline":
                tasks.append(_task(
                    "m1_recent_dry_signal",
                    "Recent NASA POWER rainfall is below the selected month historical baseline. If the field depends mainly on rain, confirm water access before committing to the next crop.",
                    "recent_conditions",
                    "Recent regional rainfall is drier than the historical monthly reference.",
                    "NASA POWER recent context and climatology",
                ))

            phase = "Know the field"
            objective = f"Build a reliable {region_name} field record and check whether the farmer's intended next move has enough evidence to continue."

        elif index == 2:
            tasks.append(_task(
                "m2_weekly_observation",
                "Once each week, record rainfall seen at the field, irrigation used, standing water, and any major change in field condition as separate observations.",
                "monitoring",
                "A second month should track change, not repeat the first month baseline.",
            ))

            if priority == "water":
                tasks.append(_task(
                    "water_priority_check",
                    "Before each irrigation decision, compare recent NASA rainfall context with the field water record. Use the satellite signal as context, not as a replacement for what the farmer sees.",
                    "farmer_priority",
                    "The farmer selected water management as the main priority.",
                    "NASA rainfall context and farmer observations",
                ))
            elif priority == "soil":
                tasks.append(_task(
                    "soil_priority_check",
                    "Track visible surface changes, crop residue, cracking, erosion signs, and persistent standing water so a local adviser can review soil condition with actual field evidence.",
                    "farmer_priority",
                    "The farmer selected soil protection as the main priority.",
                ))
            else:
                tasks.append(_task(
                    "stability_priority_check",
                    "Record any week when rainfall, water access, labour, or field condition interrupts normal work. Use those interruptions as constraints when comparing the next seasonal option.",
                    "farmer_priority",
                    "The farmer selected production stability as the main priority.",
                ))

            intended_matches = _calendar_matches(intended, context.get("calendar_evidence") or [])
            if intended and intended_matches:
                tasks.append(_task(
                    "m2_calendar_review",
                    f"Review the official {region_name} crop weather calendar source for {CROP_LABELS.get(intended, intended.title())}. Check the calendar with a local adviser before choosing a planting date.",
                    "local_evidence",
                    "The intended crop has an indexed official calendar source for this regional evidence hub.",
                    "BAMIS crop weather calendar",
                ))
            elif intended:
                tasks.append(_task(
                    "m2_calendar_gap",
                    f"No matching official regional calendar is currently indexed for {CROP_LABELS.get(intended, intended.title())}. Verify the crop locally before treating it as a supported seasonal option.",
                    "local_evidence",
                    "The current regional evidence index does not support a confident crop decision.",
                    "BAMIS evidence index",
                ))

            phase = "Watch the change"
            objective = f"Use {MONTH_NAMES[month]} evidence, the farmer priority, and field observations to reduce the biggest uncertainty before committing."

        else:
            tasks.append(_task(
                "m3_advice_review",
                f"Review the decision advice: {advice['verdict']} Better next step: {advice['better_next_step']}",
                "decision_advice",
                "The third month should turn evidence into a clear next action.",
            ))
            tasks.append(_task(
                "m3_compare_evidence",
                "Compare the intended crop with official regional calendar sources and the three months of field notes. Treat other regional crop calendars as options to investigate, not as ranked recommendations.",
                "local_evidence",
                "BoponX can show documented options without claiming one is agronomically better before rule review.",
                "BAMIS crop weather calendars",
            ))
            tasks.append(_task(
                "m3_decision_record",
                "Write down the final decision, the evidence used, the important unknowns, and which local adviser or source was consulted. Save or print the field brief with this record.",
                "decision_record",
                "A decision support tool should leave an auditable reason for the next move.",
            ))
            phase = "Decide the next move"
            objective = f"Turn the {region_name} climate context, farmer observations, intention, and local evidence into a documented next step."

        months.append({
            "index": index,
            "planning_month": f"{year:04d}-{month:02d}",
            "month_name": {"en": MONTH_NAMES[month], "bn": MONTH_NAMES[month]},
            "phase": {"en": phase, "bn": phase},
            "objective": {"en": objective, "bn": objective},
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
            "region_name_bn": region["name_bn"],
            "distance_to_reference_km": region["distance_km"],
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
            "message_en": "BoponX now evaluates farmer intention, water and drainage risk, regional crop calendar evidence, and NASA climate context. Final crop suitability ranking and rotation alternatives stay locked until reviewed crop requirements, soil constraints, and crop sequence rules are encoded.",
            "message_bn": "Final crop suitability ranking remains locked until reviewed agronomic rules are encoded.",
        },
        "evidence": {
            "nasa_sources": context["nasa_sources"],
            "agricultural_sources": context["agricultural_sources"],
            "calendar_evidence": context.get("calendar_evidence", []),
        },
        "limitations": {
            "en": "This is location aware decision support, not a crop prescription or weather forecast. The plan uses recent regional NASA context, monthly historical climatology, farmer observations, and official regional calendar evidence. Crop suitability ranking still requires reviewed local agronomic rules.",
            "bn": "This is location aware decision support, not a crop prescription or weather forecast.",
        },
    }
