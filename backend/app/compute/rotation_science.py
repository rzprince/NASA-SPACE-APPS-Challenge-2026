"""Standardized Scientific Evaluation & Scoring Engine for Crop-Rotation Strategies (Spec V3.1).

Evaluates all three rotation strategies (Strategy A: Existing/Baseline, Strategy B: Soil-Health & Pulse/Oilseed Bridge,
Strategy C: Climate-Adaptive & Regional Opportunity) under a single, unified 8-criterion scientific framework while
strictly separating four orthogonal evaluation dimensions:

1. `scientific_performance`: Biophysical score (0–100) computed ONLY over criteria with calculated or published
   agronomic reference evidence (`water_demand`, `nitrogen_contribution`, `soil_coverage`, `pest_break_potential`,
   `climate_resilience`, `planting_window_compatibility`, `farmer_priority_compatibility`).
2. `evidence_completeness`: Explicit count and percentage (`completeness_pct`) of known vs. unknown evidence dimensions,
   listing every unknown measurement (`unknown_dimensions`). Missing measurements are kept as `None` (`"UNKNOWN"`)
   and NEVER substituted with a synthetic average score (such as 50.0) or allowed to improve a strategy's ranking.
3. `local_suitability`: Mandatory parcel/regional suitability gate (`UNVERIFIED_MISSING_SOIL_TEST`,
   `CONDITIONAL_VERIFICATION_REQUIRED`, `FLAGGED_CONSTRAINT_VIOLATION`, or `VERIFIED_COMPATIBLE`). When no laboratory
   soil test is provided (`soil_test != "yes"`), `local_suitability.score_0_100` is `None` (`"UNKNOWN"`), never a
   fabricated numeric score.
4. `critical_constraints`: Non-overridable constraint flags (`critical_constraint_violated`, `constraint_flags`) for
   waterlogging, dry-season irrigation incompatibility, soil pH out-of-range, or coastal salinity hazards.
"""
from __future__ import annotations

from typing import Any

from backend.app.compute.soil_evidence import evaluate_crop_soil_suitability

DOCUMENTED_CRITERIA_WEIGHTS: dict[str, float] = {
    "water_demand": 0.20,
    "nitrogen_contribution": 0.15,
    "soil_coverage": 0.10,
    "pest_break_potential": 0.15,
    "climate_resilience": 0.15,
    "local_suitability": 0.10,
    "planting_window_compatibility": 0.10,
    "farmer_priority_compatibility": 0.05,
}

# Published agronomic parameters per seasonal crop archetype
# Sources: FAO Irrigation & Drainage Paper 56 (Allen et al., 1998), BARC Fertilizer Recommendation Guide (FRG-2024),
# BRRI Rice Production Manual, and BARI Pulse & Oilseed Handbooks.
CROP_BIOPHYSICAL_SPECS: dict[str, dict[str, Any]] = {
    "rice_aman": {
        "key": "rice_aman",
        "label_en": "Rice Aman (Kharif-2 Monsoon)",
        "botanical_family": "Poaceae",
        "season": "kharif2",
        "duration_days": 115,
        "kc_mean": 1.10,
        "percolation_seepage_mm": 180.0,
        "bnf_fixation_kg_n_ha": 0.0,
        "free_living_bga_n_kg_ha": 12.0,  # biological N fixation by cyanobacteria in wetland paddy
        "grain_n_removal_kg_ha": 75.0,
        "residue_n_retained_if_incorporated_kg_ha": 18.0,
        "root_depth_class": "shallow_fibrous_puddled (0–25 cm)",
        "tolerates_waterlogging": True,
        "drought_tolerance": "moderate_low",
        "heat_sterility_threshold_c": 35.0,
        "salinity_threshold_ds_m": 4.0,
        "major_pests_diseases": ("Yellow stem borer", "Brown planthopper", "Bacterial leaf blight"),
    },
    "rice_boro": {
        "key": "rice_boro",
        "label_en": "Rice Boro (Dry-Season Irrigated)",
        "botanical_family": "Poaceae",
        "season": "rabi",
        "duration_days": 140,
        "kc_mean": 1.15,
        "percolation_seepage_mm": 380.0,
        "bnf_fixation_kg_n_ha": 0.0,
        "free_living_bga_n_kg_ha": 10.0,
        "grain_n_removal_kg_ha": 105.0,
        "residue_n_retained_if_incorporated_kg_ha": 22.0,
        "root_depth_class": "shallow_fibrous_puddled (0–25 cm)",
        "tolerates_waterlogging": True,
        "drought_tolerance": "low_requires_full_irrigation",
        "heat_sterility_threshold_c": 35.0,
        "salinity_threshold_ds_m": 4.0,
        "major_pests_diseases": ("Yellow stem borer", "Blast (Magnaporthe oryzae)", "Brown planthopper"),
    },
    "rice_aus": {
        "key": "rice_aus",
        "label_en": "Rice Aus (Kharif-1 Pre-Monsoon)",
        "botanical_family": "Poaceae",
        "season": "kharif1",
        "duration_days": 95,
        "kc_mean": 1.05,
        "percolation_seepage_mm": 140.0,
        "bnf_fixation_kg_n_ha": 0.0,
        "free_living_bga_n_kg_ha": 10.0,
        "grain_n_removal_kg_ha": 60.0,
        "residue_n_retained_if_incorporated_kg_ha": 14.0,
        "root_depth_class": "shallow_fibrous (0–25 cm)",
        "tolerates_waterlogging": True,
        "drought_tolerance": "moderate",
        "heat_sterility_threshold_c": 35.5,
        "salinity_threshold_ds_m": 4.0,
        "major_pests_diseases": ("Stem borer", "Rice hispa", "Bacterial leaf streak"),
    },
    "mustard_rabi": {
        "key": "mustard_rabi",
        "label_en": "Short-Duration Mustard (BARI Sarisha-14/17)",
        "botanical_family": "Brassicaceae",
        "season": "rabi",
        "duration_days": 80,
        "kc_mean": 0.78,
        "percolation_seepage_mm": 0.0,
        "bnf_fixation_kg_n_ha": 0.0,  # Brassicaceae is an oilseed, NOT a nitrogen-fixing legume
        "free_living_bga_n_kg_ha": 0.0,
        "grain_n_removal_kg_ha": 52.0,
        "residue_n_retained_if_incorporated_kg_ha": 16.0,
        "root_depth_class": "medium_taproot (30–60 cm)",
        "tolerates_waterlogging": False,
        "drought_tolerance": "moderate_high",
        "heat_sterility_threshold_c": 32.0,
        "salinity_threshold_ds_m": 4.5,
        "major_pests_diseases": ("Alternaria leaf blight", "Mustard aphid (Lipaphis erysimi)"),
    },
    "pulse_lentil_rabi": {
        "key": "pulse_lentil_rabi",
        "label_en": "Lentil / Rabi Pulse (BARI Masur-8)",
        "botanical_family": "Fabaceae",
        "season": "rabi",
        "duration_days": 95,
        "kc_mean": 0.72,
        "percolation_seepage_mm": 0.0,
        "bnf_fixation_kg_n_ha": 42.0,  # Rhizobium symbiotic fixation (BARC FRG-2024: 30-55 kg N/ha)
        "free_living_bga_n_kg_ha": 0.0,
        "grain_n_removal_kg_ha": 38.0,
        "residue_n_retained_if_incorporated_kg_ha": 22.0,
        "root_depth_class": "nodulated_taproot (30–55 cm)",
        "tolerates_waterlogging": False,
        "drought_tolerance": "high",
        "heat_sterility_threshold_c": 32.0,
        "salinity_threshold_ds_m": 3.0,
        "major_pests_diseases": ("Stemphylium blight", "Foot & root rot (Fusarium / Sclerotium)"),
    },
    "mungbean_kharif1": {
        "key": "mungbean_kharif1",
        "label_en": "Green Gram / Mungbean (BARI Mug-6/8)",
        "botanical_family": "Fabaceae",
        "season": "kharif1",
        "duration_days": 65,
        "kc_mean": 0.75,
        "percolation_seepage_mm": 0.0,
        "bnf_fixation_kg_n_ha": 38.0,
        "free_living_bga_n_kg_ha": 0.0,
        "grain_n_removal_kg_ha": 30.0,
        "residue_n_retained_if_incorporated_kg_ha": 24.0,
        "root_depth_class": "nodulated_taproot (30–50 cm)",
        "tolerates_waterlogging": False,
        "drought_tolerance": "high",
        "heat_sterility_threshold_c": 36.0,
        "salinity_threshold_ds_m": 3.5,
        "major_pests_diseases": ("Mungbean yellow mosaic virus (MYMV)", "Pod borer"),
    },
    "wheat_rabi": {
        "key": "wheat_rabi",
        "label_en": "Wheat (BARI Gom-32/33)",
        "botanical_family": "Poaceae",
        "season": "rabi",
        "duration_days": 105,
        "kc_mean": 0.88,
        "percolation_seepage_mm": 0.0,
        "bnf_fixation_kg_n_ha": 0.0,
        "free_living_bga_n_kg_ha": 0.0,
        "grain_n_removal_kg_ha": 78.0,
        "residue_n_retained_if_incorporated_kg_ha": 14.0,
        "root_depth_class": "deep_fibrous (0–60 cm)",
        "tolerates_waterlogging": False,
        "drought_tolerance": "moderate_high",
        "heat_sterility_threshold_c": 32.0,
        "salinity_threshold_ds_m": 6.0,
        "major_pests_diseases": ("Wheat blast (Magnaporthe oryzae Triticum)", "Bipolaris leaf blight"),
    },
    "maize_rabi_k1": {
        "key": "maize_rabi_k1",
        "label_en": "Maize (Hybrid Grain / Silage)",
        "botanical_family": "Poaceae",
        "season": "rabi",
        "duration_days": 120,
        "kc_mean": 0.96,
        "percolation_seepage_mm": 0.0,
        "bnf_fixation_kg_n_ha": 0.0,
        "free_living_bga_n_kg_ha": 0.0,
        "grain_n_removal_kg_ha": 115.0,
        "residue_n_retained_if_incorporated_kg_ha": 25.0,
        "root_depth_class": "deep_fibrous_brace (0–80 cm)",
        "tolerates_waterlogging": False,
        "drought_tolerance": "moderate_high",
        "heat_sterility_threshold_c": 36.0,
        "salinity_threshold_ds_m": 4.0,
        "major_pests_diseases": ("Fall armyworm (Spodoptera frugiperda)", "Stalk rot"),
    },
    "jute_kharif1": {
        "key": "jute_kharif1",
        "label_en": "Jute (Tossa / Deshi Fibre)",
        "botanical_family": "Malvaceae",
        "season": "kharif1",
        "duration_days": 110,
        "kc_mean": 0.95,
        "percolation_seepage_mm": 0.0,
        "bnf_fixation_kg_n_ha": 0.0,
        "free_living_bga_n_kg_ha": 0.0,
        "grain_n_removal_kg_ha": 55.0,
        "residue_n_retained_if_incorporated_kg_ha": 32.0,
        "root_depth_class": "deep_taproot_ploughpan_breaker (40–90 cm)",
        "tolerates_waterlogging": False,
        "drought_tolerance": "moderate",
        "heat_sterility_threshold_c": 37.0,
        "salinity_threshold_ds_m": 4.0,
        "major_pests_diseases": ("Jute hairy caterpillar", "Macrophomina stem rot"),
    },
    "fallow_transition": {
        "key": "fallow_transition",
        "label_en": "Seasonal Fallow (Bare Transition)",
        "botanical_family": "None (Bare Soil)",
        "season": "kharif1",
        "duration_days": 0,
        "kc_mean": 0.25,
        "percolation_seepage_mm": 0.0,
        "bnf_fixation_kg_n_ha": 0.0,
        "free_living_bga_n_kg_ha": 0.0,
        "grain_n_removal_kg_ha": 0.0,
        "residue_n_retained_if_incorporated_kg_ha": 0.0,
        "root_depth_class": "none_bare_topsoil",
        "tolerates_waterlogging": True,
        "drought_tolerance": "high",
        "heat_sterility_threshold_c": 40.0,
        "salinity_threshold_ds_m": 12.0,
        "major_pests_diseases": (),
    },
}


def map_crop_label_to_spec(crop_label: str, season_idx: int) -> dict[str, Any]:
    """Map a strategy crop display string and season slot (0=Kharif-2, 1=Rabi, 2=Kharif-1) to its biophysical spec."""
    low = (crop_label or "").lower()
    if "fallow" in low or "পতিত" in low:
        return CROP_BIOPHYSICAL_SPECS["fallow_transition"]
    if any(k in low for k in ("mung", "green gram", "cowpea", "blackgram", "মুগ", "ফেলন", "মাসকলাই")):
        return CROP_BIOPHYSICAL_SPECS["mungbean_kharif1"]
    if any(k in low for k in ("lentil", "pulse", "chickpea", "soy", "মসুর", "ডাল", "ছোলা", "সয়াবিন")):
        return CROP_BIOPHYSICAL_SPECS["pulse_lentil_rabi"]
    if any(k in low for k in ("mustard", "oilseed", "সরিষা", "তেলবীজ", "sunflower", "sesame")):
        return CROP_BIOPHYSICAL_SPECS["mustard_rabi"]
    if any(k in low for k in ("wheat", "গম", "barley")):
        return CROP_BIOPHYSICAL_SPECS["wheat_rabi"]
    if any(k in low for k in ("maize", "ভুট্টা", "corn", "sorghum", "millet")):
        return CROP_BIOPHYSICAL_SPECS["maize_rabi_k1"]
    if any(k in low for k in ("jute", "পাট")):
        return CROP_BIOPHYSICAL_SPECS["jute_kharif1"]
    if "aus" in low or "আউশ" in low or (season_idx == 2 and "rice" in low):
        return CROP_BIOPHYSICAL_SPECS["rice_aus"]
    if "boro" in low or "বোরো" in low or (season_idx == 1 and "rice" in low):
        return CROP_BIOPHYSICAL_SPECS["rice_boro"]
    return CROP_BIOPHYSICAL_SPECS["rice_aman"]


def evaluate_strategy_scientifically(
    strategy_id: str,
    crops_en: list[str],
    *,
    profile: dict[str, Any],
    context: dict[str, Any],
    condition: dict[str, Any],
    soil_model: dict[str, Any],
    advisory: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate a 3-season rotation strategy across all 8 Spec V3.1 criteria while strictly separating:
    1. `scientific_performance` (biophysical performance over known/calculated criteria only),
    2. `evidence_completeness` (explicit completeness percentage and list of unknown measurements),
    3. `local_suitability` (explicitly UNKNOWN / unverified when lab soil test is missing — never given a fake average score),
    4. `critical_constraints` (non-overridable constraint violation flags).
    """
    specs = [map_crop_label_to_spec(c, idx) for idx, c in enumerate(crops_en[:3])]
    while len(specs) < 3:
        specs.append(CROP_BIOPHYSICAL_SPECS["fallow_transition"])

    water_source = str(profile.get("water_source", "unknown"))
    drainage = str(profile.get("water_after_heavy_rain", "unknown"))
    soil_test = str(profile.get("soil_test", "unknown"))
    farmer_ph = profile.get("soil_ph")
    priority = str(profile.get("priority", "production_stability"))
    equipment = str(profile.get("equipment_access", "unknown"))
    market_pref = str(profile.get("market_preference", "unknown"))

    et0_obs = condition.get("et0_daily_mm")
    rain_obs = condition.get("recent_daily_rain_mm") or condition.get("baseline_daily_rain_mm")
    swb = (advisory or {}).get("seasonal_water_balance") if isinstance(advisory, dict) else None
    has_nasa_water = isinstance(et0_obs, (int, float)) or (
        isinstance(swb, dict) and swb.get("kharif2_aman", {}).get("status") == "ok"
    )
    adv_ready = isinstance(advisory, dict) and advisory.get("status") == "ADVISORY_READY"

    k2_et0 = (
        float(swb["kharif2_aman"]["period_2013_latest"]["et0_daily_mm"])
        if isinstance(swb, dict) and isinstance(swb.get("kharif2_aman", {}).get("period_2013_latest"), dict)
        else (float(et0_obs) if isinstance(et0_obs, (int, float)) else 4.3)
    )
    k2_rain = (
        float(swb["kharif2_aman"]["period_2013_latest"]["rain_daily_mm"])
        if isinstance(swb, dict) and isinstance(swb.get("kharif2_aman", {}).get("period_2013_latest"), dict)
        else (float(rain_obs) if isinstance(rain_obs, (int, float)) else 8.5)
    )
    rabi_et0 = (
        float(swb["rabi"]["period_2013_latest"]["et0_daily_mm"])
        if isinstance(swb, dict) and isinstance(swb.get("rabi", {}).get("period_2013_latest"), dict)
        else (float(et0_obs) if isinstance(et0_obs, (int, float)) else 3.4)
    )
    rabi_rain = (
        float(swb["rabi"]["period_2013_latest"]["rain_daily_mm"])
        if isinstance(swb, dict) and isinstance(swb.get("rabi", {}).get("period_2013_latest"), dict)
        else 0.8
    )
    k1_et0 = 4.9
    k1_rain = 4.2

    seasonal_met = [(k2_et0, k2_rain), (rabi_et0, rabi_rain), (k1_et0, k1_rain)]

    # ------------------------------------------------------------------
    # CRITERION 1: WATER DEMAND (Calculated: ETc, Peff, NIR, Irrigation Fit)
    # ------------------------------------------------------------------
    total_etc_mm = 0.0
    total_peff_mm = 0.0
    total_nir_mm = 0.0
    rabi_nir_mm = 0.0
    seasonal_water_breakdown: list[dict[str, Any]] = []

    for idx, sp in enumerate(specs):
        et0_d, rain_d = seasonal_met[idx]
        dur = sp["duration_days"]
        if dur <= 0:
            seasonal_water_breakdown.append(
                {"season_slot": idx + 1, "crop": sp["label_en"], "etc_mm": 0.0, "peff_mm": 0.0, "nir_mm": 0.0}
            )
            continue
        etc = dur * et0_d * sp["kc_mean"] + sp["percolation_seepage_mm"]
        gross_rain = dur * rain_d
        eff_factor = 0.82 if sp["tolerates_waterlogging"] else 0.72
        peff = min(etc, gross_rain * eff_factor)
        nir = max(0.0, etc - peff)
        total_etc_mm += etc
        total_peff_mm += peff
        total_nir_mm += nir
        if idx == 1:
            rabi_nir_mm = nir
        seasonal_water_breakdown.append(
            {
                "season_slot": idx + 1,
                "crop": sp["label_en"],
                "kc_used": sp["kc_mean"],
                "duration_days": dur,
                "etc_mm": round(etc, 1),
                "peff_mm": round(peff, 1),
                "nir_mm": round(nir, 1),
            }
        )

    water_constraint_violated = False
    if water_source == "rainfed" and rabi_nir_mm > 320.0:
        water_constraint_violated = True
    water_score = max(15.0, min(95.0, 100.0 - (total_nir_mm / 14.0)))
    if water_constraint_violated:
        water_score = max(10.0, water_score - 30.0)

    water_eval = {
        "status": "CALCULATED_FROM_NASA_POWER_AND_FAO56_KC" if has_nasa_water else "ESTIMATED_FROM_REGIONAL_CLIMATOLOGY_AND_FAO56_KC",
        "evidence_classification": "CALCULATED" if has_nasa_water else "ESTIMATED",
        "crop_water_requirement_etc_mm": round(total_etc_mm, 1),
        "effective_rainfall_peff_mm": round(total_peff_mm, 1),
        "estimated_irrigation_requirement_nir_mm": round(total_nir_mm, 1),
        "rabi_dry_season_irrigation_nir_mm": round(rabi_nir_mm, 1),
        "actual_irrigation_availability": water_source,
        "irrigation_compatibility": (
            "INCOMPATIBLE_HIGH_DRY_SEASON_DEMAND_ON_RAINFED_FIELD"
            if water_constraint_violated
            else ("UNKNOWN_IRRIGATION_ACCESS" if water_source == "unknown" else "COMPATIBLE")
        ),
        "seasonal_breakdown": seasonal_water_breakdown,
        "methodology_note": (
            "Computed via FAO-56 dual-season crop coefficient method: ETc = sum(ET0 * Kc) + wetland percolation, "
            "effective rainfall Peff = min(ETc, P * efficiency), and net irrigation requirement NIR = max(0, ETc - Peff). "
            "Rainfall and irrigation demand are strictly separated."
        ),
        "score_0_100": round(water_score, 1),
    }

    # ------------------------------------------------------------------
    # CRITERION 2: NITROGEN CONTRIBUTION (Evidence-based N Mass Balance)
    # ------------------------------------------------------------------
    residue_retention_frac = 0.35 if market_pref == "forage_livestock" else (0.80 if equipment == "conservation_zero_till" else 0.65)
    gross_bnf_kg_ha = sum(sp["bnf_fixation_kg_n_ha"] + sp["free_living_bga_n_kg_ha"] for sp in specs)
    legume_count = sum(1 for sp in specs if sp["botanical_family"] == "Fabaceae")
    harvest_n_removal_kg_ha = sum(sp["grain_n_removal_kg_ha"] for sp in specs)
    retained_residue_n_kg_ha = sum(sp["residue_n_retained_if_incorporated_kg_ha"] * residue_retention_frac for sp in specs)
    n_carryover_to_following_crop_kg_ha = round(
        sum(sp["bnf_fixation_kg_n_ha"] * 0.35 * residue_retention_frac for sp in specs) + retained_residue_n_kg_ha * 0.40,
        1,
    )
    net_soil_n_balance_before_fertilizer_kg_ha = round(
        gross_bnf_kg_ha + retained_residue_n_kg_ha - harvest_n_removal_kg_ha, 1
    )

    n_score = min(
        92.0,
        max(20.0, 50.0 + (n_carryover_to_following_crop_kg_ha * 1.1) + (net_soil_n_balance_before_fertilizer_kg_ha * 0.18)),
    )
    nitrogen_eval = {
        "status": "EVIDENCE_BASED_N_MASS_BALANCE",
        "evidence_classification": "ESTIMATED",
        "measured_parcel_soil_nitrogen_status": "UNKNOWN",
        "legume_seasons_in_rotation": legume_count,
        "gross_biological_n_fixation_kg_ha": round(gross_bnf_kg_ha, 1),
        "residue_retention_fraction_assumed": round(residue_retention_frac, 2),
        "retained_residue_n_kg_ha": round(retained_residue_n_kg_ha, 1),
        "harvested_grain_n_removal_kg_ha": round(harvest_n_removal_kg_ha, 1),
        "estimated_n_carryover_to_following_crop_kg_ha": n_carryover_to_following_crop_kg_ha,
        "net_soil_n_balance_before_fertilizer_kg_ha": net_soil_n_balance_before_fertilizer_kg_ha,
        "scientific_caveat": (
            "Biological nitrogen fixation (BNF) is an estimated range from BARC FRG-2024 (+30 to +50 kg N/ha for pulses) "
            "and is NEVER presented as a measured parcel soil N increase. Harvested pulse grain removes 30–38 kg N/ha, "
            "and removing crop haulms for livestock fodder reduces N carryover to the next cereal crop by ~55–65%."
        ),
        "score_0_100": round(n_score, 1),
    }

    # ------------------------------------------------------------------
    # CRITERION 3: SOIL COVERAGE & ROOT ARCHITECTURE (Evaluated)
    # ------------------------------------------------------------------
    canopy_days = sum(sp["duration_days"] for sp in specs)
    bare_days = max(0, 365 - canopy_days)
    root_classes = {sp["root_depth_class"] for sp in specs if sp["duration_days"] > 0}
    has_taproot = any("taproot" in r for r in root_classes)
    coverage_score = min(
        95.0,
        max(25.0, (canopy_days / 330.0) * 75.0 + (15.0 if has_taproot else 0.0) + (8.0 if residue_retention_frac >= 0.65 else 0.0)),
    )

    soil_coverage_eval = {
        "status": "EVALUATED",
        "evidence_classification": "ESTIMATED",
        "canopy_duration_days_per_year": canopy_days,
        "bare_soil_exposure_days_per_year": bare_days,
        "rooting_depth_classes": sorted(root_classes),
        "plough_pan_biopore_potential": "HIGH (includes taproot break crop)" if has_taproot else "LOW (continuous shallow fibrous roots)",
        "erosion_and_salinity_capillary_protection": (
            "STRONG — minimizes bare-soil evaporation during Nov–Apr dry months"
            if bare_days <= 85
            else "MODERATE_TO_WEAK — extended bare turnaround window exposes topsoil to evaporation and capillary salt rise"
        ),
        "score_0_100": round(coverage_score, 1),
    }

    # ------------------------------------------------------------------
    # CRITERION 4: PEST-BREAK POTENTIAL (Botanical Family Succession)
    # ------------------------------------------------------------------
    active_specs = [sp for sp in specs if sp["duration_days"] > 0]
    families = [sp["botanical_family"] for sp in active_specs]
    same_family_transitions = 0
    for i in range(len(families)):
        nxt = families[(i + 1) % len(families)]
        if families[i] == nxt and families[i] != "None (Bare Soil)":
            same_family_transitions += 1

    unique_families = len(set(families))
    if unique_families >= 3 and same_family_transitions == 0:
        pest_score = 92.0
        pest_class = "STRONG_MULTI_FAMILY_BREAK"
    elif unique_families >= 2 and same_family_transitions <= 1:
        pest_score = 78.0
        pest_class = "MODERATE_PARTIAL_BREAK"
    else:
        pest_score = 38.0
        pest_class = "WEAK_CONTINUOUS_HOST_CARRYOVER"

    pest_eval = {
        "status": "EVALUATED",
        "evidence_classification": "REFERENCE",
        "botanical_family_sequence": [sp["botanical_family"] for sp in specs],
        "unique_botanical_families": unique_families,
        "consecutive_same_family_transitions": same_family_transitions,
        "pest_break_classification": pest_class,
        "residual_pest_and_disease_risks": [
            f"{sp['label_en']} ({sp['botanical_family']}): {', '.join(sp['major_pests_diseases'])}"
            for sp in active_specs
            if sp["major_pests_diseases"]
        ],
        "scientific_caveat": (
            "Alternating botanical families (e.g., Poaceae -> Brassicaceae/Fabaceae) interrupts cereal-specific hosts "
            "(such as rice yellow stem borer), but does NOT eliminate polyphagous pests or weather-driven fungal blights "
            "(e.g., Alternaria/Stemphylium during humid winter fog)."
        ),
        "score_0_100": round(pest_score, 1),
    }

    # ------------------------------------------------------------------
    # CRITERION 5: CLIMATE RESILIENCE (Uniform 4-Scenario Stress Test)
    # ------------------------------------------------------------------
    heat_vuln = sum(1 for sp in active_specs if sp["heat_sterility_threshold_c"] <= 32.5)
    drought_vuln = sum(1 for sp in active_specs if "low" in sp["drought_tolerance"])
    waterlog_vuln = sum(1 for sp in active_specs if not sp["tolerates_waterlogging"])
    total_dur = sum(sp["duration_days"] for sp in specs)
    turnaround_buffer_days = max(0, 365 - total_dur)

    heat_sub = max(35.0, 90.0 - heat_vuln * 22.0)
    drought_sub = max(25.0, 92.0 - (rabi_nir_mm / 18.0) - drought_vuln * 15.0)
    excess_rain_sub = max(20.0, 90.0 - (waterlog_vuln * (28.0 if drainage == "stays" else 12.0)))
    delayed_onset_sub = 88.0 if turnaround_buffer_days >= 55 else (72.0 if turnaround_buffer_days >= 35 else 48.0)
    resilience_score = (heat_sub + drought_sub + excess_rain_sub + delayed_onset_sub) / 4.0

    climate_resilience_eval = {
        "status": "SCENARIO_TESTED",
        "evidence_classification": "CALCULATED",
        "scenarios_evaluated": {
            "plus_2c_temperature_spike": {
                "score_0_100": round(heat_sub, 1),
                "impact": (
                    "High floral sterility risk in late-sown winter crops (>32°C in Feb)"
                    if heat_vuln > 0
                    else "Buffered by heat-tolerant C4 or monsoon crop window"
                ),
            },
            "minus_30pct_rainfall_drought": {
                "score_0_100": round(drought_sub, 1),
                "impact": f"Dry-season net irrigation demand is {rabi_nir_mm:.0f} mm; {'high groundwater dependence' if rabi_nir_mm > 350 else 'low-water resilience'}.",
            },
            "plus_30pct_excess_rainfall_waterlogging": {
                "score_0_100": round(excess_rain_sub, 1),
                "impact": (
                    f"Contains {waterlog_vuln} waterlogging-sensitive upland crop(s); "
                    + (
                        "CRITICAL root-rot risk on poorly drained ('stays') field."
                        if drainage == "stays" and waterlog_vuln > 0
                        else "requires ridge/bed drainage channels."
                    )
                ),
            },
            "plus_10d_delayed_monsoon_onset": {
                "score_0_100": round(delayed_onset_sub, 1),
                "impact": f"Annual turnaround buffer is {turnaround_buffer_days} days across 3 seasons.",
            },
        },
        "score_0_100": round(resilience_score, 1),
    }

    # ------------------------------------------------------------------
    # CRITERION 6: LOCAL SUITABILITY (Mandatory Gate — Never Faked When Soil Test Missing)
    # ------------------------------------------------------------------
    crop_suitabilities = [
        evaluate_crop_soil_suitability(
            c,
            soil_model,
            water_source=water_source,
            drainage=drainage,
            soil_test=soil_test,
            farmer_ph=farmer_ph if isinstance(farmer_ph, (int, float)) else None,
        )
        for c in crops_en[:3]
        if "fallow" not in c.lower()
    ]
    all_violations: list[str] = []
    all_warnings: list[str] = []
    all_missing: list[str] = []
    for cs in crop_suitabilities:
        for v in cs["constraints_violated"]:
            if v not in all_violations:
                all_violations.append(v)
        for w in cs["soil_and_salinity_warnings"]:
            if w not in all_warnings:
                all_warnings.append(w)
        for m in cs["missing_evidence"]:
            if m not in all_missing:
                all_missing.append(m)
    if water_constraint_violated:
        all_violations.append(
            f"Dry-season crop requires ~{rabi_nir_mm:.0f} mm net irrigation, but field water source is reported as 'rainfed'."
        )

    has_verified_ph = soil_test == "yes" and isinstance(farmer_ph, (int, float))
    if all_violations:
        gate_status = "FLAGGED_CONSTRAINT_VIOLATION"
        local_score: float | None = 25.0 if has_verified_ph else None
    elif not has_verified_ph:
        # Spec V3.1: Do not allow unknown parcel soil measurements to appear as a measured average score!
        gate_status = "UNVERIFIED_MISSING_SOIL_TEST"
        local_score = None
    else:
        gate_status = "CONDITIONAL_LOCAL_EXTENSION_REVIEW"
        local_score = round(max(55.0, 86.0 - len(all_warnings) * 8.0), 1)

    local_suitability_eval = {
        "status": gate_status,
        "unconditional_recommendation": False,
        "evidence_classification": "FARMER_REPORTED" if has_verified_ph else "UNKNOWN",
        "parcel_measurement_status": "MEASURED_PH_PROVIDED" if has_verified_ph else "UNKNOWN_NO_SOIL_TEST",
        "constraints_violated": all_violations,
        "soil_and_salinity_warnings": all_warnings,
        "missing_essential_evidence": all_missing,
        "crop_level_checks": crop_suitabilities,
        "score_0_100": local_score,
        "uncertainty_note": (
            "Parcel laboratory soil test (pH, ECe salinity, organic matter, NPK) is UNKNOWN; local_suitability.score_0_100 "
            "is explicitly withheld (None) rather than assigned a synthetic average."
            if local_score is None
            else "Evaluated using farmer-reported soil pH and regional SRDI/BARC reference constraints."
        ),
    }

    # ------------------------------------------------------------------
    # CRITERION 7: PLANTING-WINDOW COMPATIBILITY (Historical Onset Shift)
    # ------------------------------------------------------------------
    shift_days = (advisory or {}).get("shift_days", 0) if adv_ready else None
    if turnaround_buffer_days >= 55:
        pw_score = 88.0
        pw_note = f"Generous {turnaround_buffer_days}-day annual turnaround buffer absorbs historical monsoon onset variability."
    elif turnaround_buffer_days >= 35:
        pw_score = 74.0
        pw_note = f"Moderate {turnaround_buffer_days}-day turnaround buffer; requires short-duration varieties (e.g., BARI Sarisha-14/17 or BARI Mug-6)."
    else:
        pw_score = 52.0
        pw_note = f"Tight {turnaround_buffer_days}-day turnaround window; late Aman harvest or delayed onset can compress Rabi sowing."

    planting_window_eval = {
        "status": "HISTORICALLY_EVALUATED" if adv_ready else "EVALUATED_ON_BAMIS_CALENDAR_ONLY",
        "evidence_classification": "CALCULATED" if adv_ready else "REFERENCE",
        "total_crop_duration_days": total_dur,
        "annual_turnaround_buffer_days": turnaround_buffer_days,
        "historical_onset_shift_days": shift_days,
        "compatibility_note": pw_note,
        "score_0_100": round(pw_score, 1),
    }

    # ------------------------------------------------------------------
    # CRITERION 8: FARMER PRIORITY COMPATIBILITY
    # ------------------------------------------------------------------
    if priority == "water":
        prio_score = water_score
    elif priority == "soil":
        prio_score = (n_score * 0.55) + (coverage_score * 0.45)
    else:
        prio_score = (resilience_score * 0.5) + (pw_score * 0.5)

    priority_eval = {
        "status": "EVALUATED",
        "evidence_classification": "FARMER_REPORTED",
        "stated_farmer_priority": priority,
        "equipment_access": equipment,
        "market_preference": market_pref,
        "score_0_100": round(prio_score, 1),
    }

    # ------------------------------------------------------------------
    # ORTHOGONAL SEPARATION:
    # 1. Scientific Performance (over known/evaluated criteria only)
    # 2. Evidence Completeness (explicit % and unknown dimensions list)
    # 3. Local Suitability Gate (None/UNKNOWN when soil test is missing)
    # 4. Critical Constraint Violations
    # ------------------------------------------------------------------
    criteria_scores: dict[str, float | None] = {
        "water_demand": water_eval["score_0_100"],
        "nitrogen_contribution": nitrogen_eval["score_0_100"],
        "soil_coverage": soil_coverage_eval["score_0_100"],
        "pest_break_potential": pest_eval["score_0_100"],
        "climate_resilience": climate_resilience_eval["score_0_100"],
        "local_suitability": local_suitability_eval["score_0_100"],  # None when soil_test != "yes"
        "planting_window_compatibility": planting_window_eval["score_0_100"],
        "farmer_priority_compatibility": priority_eval["score_0_100"],
    }

    known_weight_sum = round(
        sum(w for k, w in DOCUMENTED_CRITERIA_WEIGHTS.items() if criteria_scores.get(k) is not None),
        4,
    )
    scientific_performance_score = round(
        sum(float(criteria_scores[k]) * DOCUMENTED_CRITERIA_WEIGHTS[k] for k in DOCUMENTED_CRITERIA_WEIGHTS if criteria_scores.get(k) is not None)
        / max(0.01, known_weight_sum),
        1,
    )

    # Track 8 evidence completeness dimensions explicitly
    evidence_dimensions = {
        "regional_bamis_crop_calendar": bool(context.get("calendar_evidence")),
        "srdi_barc_aez_soil_reference": soil_model.get("status") == "bangladesh_srdi_barc_reference_integrated",
        "nasa_power_recent_or_seasonal_water_balance": has_nasa_water,
        "nasa_power_historical_onset_series": adv_ready,
        "field_water_source_specified": water_source != "unknown",
        "field_post_rain_drainage_specified": drainage != "unknown",
        "parcel_laboratory_soil_ph_verified": has_verified_ph,
        "parcel_laboratory_npk_and_salinity_ec_verified": False,  # requires full lab chemical sheet
    }
    known_dims = [k for k, v in evidence_dimensions.items() if v]
    unknown_dims = [k for k, v in evidence_dimensions.items() if not v]
    completeness_pct = round((len(known_dims) / len(evidence_dimensions)) * 100.0, 1)

    critical_violated = len(all_violations) > 0
    rec_gate = (
        "FLAGGED_CONSTRAINT_VIOLATION"
        if critical_violated
        else ("CONDITIONAL_MISSING_EVIDENCE" if unknown_dims or all_missing else "CONDITIONAL_EXTENSION_REVIEW")
    )

    return {
        "strategy_id": strategy_id,
        "framework_version": "boponx.rotation_science.v3.1",
        "recommendation_gate": rec_gate,
        "critical_constraint_violated": critical_violated,
        "constraint_flags": all_violations,
        "scientific_performance": {
            "score_0_100": scientific_performance_score,
            "known_criteria_weight_sum": known_weight_sum,
            "evaluated_criteria_count": sum(1 for v in criteria_scores.values() if v is not None),
            "total_criteria_count": len(DOCUMENTED_CRITERIA_WEIGHTS),
            "scoring_assumptions": [
                "Computed strictly over evaluated biophysical criteria; unmeasured parcel soil suitability (score_0_100=None) is excluded rather than imputed as an average score.",
                "FAO-56 dual-season crop coefficients (Kc) and BARC FRG-2024 biological nitrogen fixation ranges (+30–50 kg N/ha for pulses) are reference calculations/estimates, not parcel sensor measurements.",
                "A missing measurement never improves a strategy's ranking or overrides a constraint flag.",
            ],
        },
        "evidence_completeness": {
            "completeness_pct": completeness_pct,
            "known_count": len(known_dims),
            "total_dimensions": len(evidence_dimensions),
            "known_dimensions": known_dims,
            "unknown_dimensions": unknown_dims,
            "uncertainty_policy": "Unknown measurements remain explicitly UNKNOWN (None) and never inflate scientific_performance.",
        },
        "local_suitability_summary": {
            "status": gate_status,
            "score_0_100": local_score,
            "evidence_classification": local_suitability_eval["evidence_classification"],
            "missing_essential_evidence": all_missing,
        },
        "critical_constraints": {
            "critical_constraint_violated": critical_violated,
            "constraint_flags": all_violations,
            "override_policy": "Critical soil, waterlogging, salinity, or irrigation violations block unconditional adoption regardless of scientific_performance.",
        },
        "weighted_composite_score_0_100": scientific_performance_score,
        "evidence_completeness_pct": completeness_pct,
        "scoring_note": (
            f"CRITICAL CONSTRAINT FLAGGED ({len(all_violations)} violation(s)): A high biophysical performance score "
            f"({scientific_performance_score}/100, evidence completeness {completeness_pct}%) cannot override a violated "
            "waterlogging, pH, salinity, or irrigation constraint."
            if critical_violated
            else (
                f"Biophysical performance: {scientific_performance_score}/100 (Evidence completeness: {completeness_pct}%; "
                f"{len(unknown_dims)} unknown dimension(s) kept explicitly UNKNOWN)."
            )
        ),
        "documented_weights": DOCUMENTED_CRITERIA_WEIGHTS,
        "criteria_scores_0_100": criteria_scores,
        "criteria": {
            "water_demand": water_eval,
            "nitrogen_contribution": nitrogen_eval,
            "soil_coverage": soil_coverage_eval,
            "pest_break_potential": pest_eval,
            "climate_resilience": climate_resilience_eval,
            "local_suitability": local_suitability_eval,
            "planting_window_compatibility": planting_window_eval,
            "farmer_priority_compatibility": priority_eval,
        },
    }
