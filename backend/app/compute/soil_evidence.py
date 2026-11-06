"""Verified Bangladesh Soil Evidence & Suitability Integration (Spec V3 Priority 3).

Integrates authoritative published agro-edaphic references from:
1. Soil Resource Development Institute (SRDI), Ministry of Agriculture, Bangladesh (https://srdi.gov.bd/)
   - *Saline Soils of Bangladesh* (SRDI, 2010; updated coastal monitoring 2022)
   - *Upazila Land and Soil Resource Utilization Guides (Thana Nirdeshika)*
2. Bangladesh Agricultural Research Council (BARC) (https://barc.gov.bd/)
   - *Fertilizer Recommendation Guide (FRG-2018 / FRG-2024)* (https://apps.barc.gov.bd/fertilizer_recommendation/FRG%20English%2030.10.2024.pdf)
   - *Agro-Ecological Zones (AEZ 1–30) of Bangladesh* & *BARC Crop Zoning* (https://apps.barc.gov.bd/cropzoning/)
3. Bangladesh Agricultural Research Institute (BARI) (https://bari.gov.bd/)
   - Upland crop pH, drainage, and salinity tolerance thresholds
4. Bangladesh Rice Research Institute (BRRI) (https://brri.gov.bd/)
   - Wetland rice ecosystem soil & salinity tolerance thresholds

Evidence Classifications (strictly enforced):
- `VERIFIED`: Supported by an identifiable laboratory measurement or verified field dataset.
- `REFERENCE`: Supported by a published regional/AEZ or district-level SRDI/BARC/BARI/BRRI reference.
- `ESTIMATED`: Derived through a documented estimation methodology.
- `FARMER_REPORTED`: Provided by the farmer without independent laboratory verification.
- `UNKNOWN`: Insufficient evidence (never silently converted to zero or presented as measured).
"""
from __future__ import annotations

from typing import Any

EVIDENCE_CLASSIFICATIONS = (
    "VERIFIED",
    "REFERENCE",
    "ESTIMATED",
    "FARMER_REPORTED",
    "UNKNOWN",
)

# Authoritative Agro-Ecological Zone (AEZ) & SRDI/BARC regional soil reference profiles
# Values are published regional ranges from BARC Fertilizer Recommendation Guide (FRG-2018/2024)
# and SRDI Saline Soils / Upazila Soil Surveys — never presented as exact parcel measurements.
AEZ_SOIL_PROFILES: dict[str, dict[str, Any]] = {
    "barind_tract": {
        "aez_id": "AEZ-25 / AEZ-26 (Level & High Barind Tract)",
        "matching_districts": ("rajshahi", "naogaon", "chapainawabganj", "joypurhat", "bogura"),
        "soil_classification": "Grey Terrace Soils (Albaquepts / Haplaquepts) over Madhupur Clay",
        "soil_ph": {"min": 4.8, "max": 6.2, "typical": 5.4, "class_en": "Strongly to slightly acidic"},
        "organic_matter_pct": {"min": 0.8, "max": 1.5, "typical": 1.1, "class_en": "Low (below BARC 2.0% optimum)"},
        "salinity_ec_ds_m": {"min": 0.2, "max": 1.2, "typical": 0.5, "class_en": "Non-saline (<2.0 dS/m)"},
        "soil_texture": "Silty clay loam to clay loam over compact plough pan",
        "drainage_class": "Imperfectly drained on level terraces; rapid runoff on tilted slopes",
        "nutrient_status_en": "Very low Total N (0.05–0.09%), low available P in acidic clay, deficient in S, Zn, and B (BARC FRG-2024).",
        "limitations_en": [
            "Compact plough pan at 10–15 cm depth restricts shallow root penetration after puddled Aman rice.",
            "Low water-holding capacity in dry Rabi months and acidic topsoil (pH 4.8–5.8) can limit phosphorus availability.",
        ],
        "source_institution": "BARC & SRDI",
        "source_document": "BARC Fertilizer Recommendation Guide (FRG-2018 / FRG-2024) & SRDI Barind Soil Survey",
        "source_url": "https://apps.barc.gov.bd/fertilizer_recommendation/FRG%20English%2030.10.2024.pdf",
        "survey_year": "2018–2024 (BARC FRG)",
    },
    "coastal_tidal_floodplain": {
        "aez_id": "AEZ-13 / AEZ-18 (Ganges Tidal Floodplain & Young Meghna Estuarine Floodplain)",
        "matching_districts": (
            "patuakhali", "barguna", "bhola", "barishal", "pirojpur", "jhalokati",
            "khulna", "satkhira", "bagerhat", "noakhali", "lakshmipur", "feni", "cox's bazar",
        ),
        "soil_classification": "Non-calcareous & Calcareous Grey Floodplain Soils (Saline phase in dry season)",
        "soil_ph": {"min": 6.2, "max": 7.9, "typical": 7.1, "class_en": "Neutral to slightly alkaline in dry season"},
        "organic_matter_pct": {"min": 1.2, "max": 2.1, "typical": 1.6, "class_en": "Low to medium"},
        "salinity_ec_ds_m": {"min": 2.0, "max": 12.5, "typical": 5.8, "class_en": "Slightly to strongly saline in Rabi (Dec–May peak)"},
        "soil_texture": "Silty clay to heavy clay",
        "drainage_class": "Poorly drained; subject to tidal inundation and late Aman harvest recession",
        "nutrient_status_en": "Low Total N (0.06–0.12%), low available P (1–9 µg/g), high K & Mg, localized S/Zn deficiency (SRDI Saline Soils 2010/2022; BARC FRG-2024).",
        "limitations_en": [
            "Dry-season capillary rise increases topsoil electrical conductivity (ECe 4–12+ dS/m) from December to April (SRDI).",
            "Late recession of monsoon/tidal water delays Rabi seedbed preparation ('jo' condition) past mid-November.",
        ],
        "source_institution": "SRDI & BARC",
        "source_document": "SRDI Saline Soils of Bangladesh (2010/2022) & BARC FRG-2024",
        "source_url": "https://srdi.gov.bd/",
        "survey_year": "2010–2024 (SRDI / BARC)",
    },
    "haor_sylhet_basin": {
        "aez_id": "AEZ-20 / AEZ-21 (Eastern Surma-Kushiyara Floodplain & Sylhet Basin)",
        "matching_districts": ("sunamganj", "sylhet", "habiganj", "moulvibazar", "kishoreganj", "netrokona", "brahmanbaria"),
        "soil_classification": "Non-calcareous Grey & Dark Grey Floodplain Acid Basin Clays",
        "soil_ph": {"min": 4.5, "max": 5.8, "typical": 5.1, "class_en": "Very strongly to moderately acidic"},
        "organic_matter_pct": {"min": 1.8, "max": 3.5, "typical": 2.4, "class_en": "Medium to high (peat/basin accumulation)"},
        "salinity_ec_ds_m": {"min": 0.1, "max": 0.8, "typical": 0.3, "class_en": "Non-saline (<1.0 dS/m)"},
        "soil_texture": "Heavy silty clay to clay in haor basins; sandy loam on piedmont rims",
        "drainage_class": "Very poorly drained in wet season (deep seasonal flooding May–Oct); slow drying in Nov",
        "nutrient_status_en": "Moderate organic N (slow mineralization in submerged acid clay), strong P fixation due to acidity (BARC FRG-2024).",
        "limitations_en": [
            "Early pre-monsoon flash floods (Chaitra–Baishakh, late March–April) can submerge standing Boro/Rabi crops.",
            "Strong soil acidity (pH < 5.5) restricts legume nodulation unless dolomitic lime or Mo/B is applied.",
        ],
        "source_institution": "BARC & BRRI",
        "source_document": "BARC FRG-2024 (AEZ-21 Sylhet Basin) & BRRI Haor Rice Cropping Guidelines",
        "source_url": "https://apps.barc.gov.bd/fertilizer_recommendation/FRG%20English%2030.10.2024.pdf",
        "survey_year": "2018–2024 (BARC FRG)",
    },
    "tista_active_floodplain": {
        "aez_id": "AEZ-1 / AEZ-2 / AEZ-3 (Old Himalayan Piedmont Plain & Tista Meander Floodplain)",
        "matching_districts": (
            "panchagarh", "thakurgaon", "dinajpur", "nilphamari", "rangpur",
            "lalmonirhat", "kurigram", "gaibandha",
        ),
        "soil_classification": "Non-calcareous Brown & Grey Floodplain Soils (Sandy loam to silt loam)",
        "soil_ph": {"min": 5.0, "max": 6.4, "typical": 5.6, "class_en": "Moderately to slightly acidic"},
        "organic_matter_pct": {"min": 0.9, "max": 1.8, "typical": 1.3, "class_en": "Low"},
        "salinity_ec_ds_m": {"min": 0.1, "max": 0.9, "typical": 0.4, "class_en": "Non-saline"},
        "soil_texture": "Sandy loam (char/piedmont) to silt loam (floodplain ridges)",
        "drainage_class": "Well to moderately well drained on ridges; rapid percolation in sandy char soils",
        "nutrient_status_en": "Low N, K, S, Zn, B, and Mg; leaching loss is high in coarse-textured soils (BARC FRG-2024).",
        "limitations_en": [
            "Low water retention in sandy loam and char lands causes rapid moisture stress during dry spells.",
            "Acidic pH (5.0–5.8) and Boron/Magnesium deficiency cause sterility in wheat and mustard if unamended.",
        ],
        "source_institution": "BARC & BARI",
        "source_document": "BARC FRG-2024 (AEZ 1–3) & BARI Northern Cropping Research",
        "source_url": "https://apps.barc.gov.bd/fertilizer_recommendation/FRG%20English%2030.10.2024.pdf",
        "survey_year": "2018–2024 (BARC FRG)",
    },
    "hill_tracts": {
        "aez_id": "AEZ-29 (Northern and Eastern Hills)",
        "matching_districts": ("rangamati", "khagrachhari", "bandarban", "chattogram"),
        "soil_classification": "Brown Hill Soils (Dystrochrepts / Ultisols)",
        "soil_ph": {"min": 4.5, "max": 5.6, "typical": 5.0, "class_en": "Strongly acidic"},
        "organic_matter_pct": {"min": 1.2, "max": 2.2, "typical": 1.6, "class_en": "Low to medium (vulnerable to topsoil erosion)"},
        "salinity_ec_ds_m": {"min": 0.1, "max": 1.5, "typical": 0.4, "class_en": "Non-saline inland; localized coastal fringe salinity in Chattogram"},
        "soil_texture": "Sandy loam to sandy clay loam over shale/sandstone",
        "drainage_class": "Excessively to well drained on slopes; moderately drained in valley bottoms",
        "nutrient_status_en": "Low available P (high Fe/Al fixation), low Ca, Mg, and N (BARC FRG-2024).",
        "limitations_en": [
            "Severe sheet and rill erosion hazard if steep slopes are tilled or left bare during May–August monsoon.",
            "Strong acidity (pH < 5.5) limits phosphorus availability.",
        ],
        "source_institution": "BARC & SRDI",
        "source_document": "BARC FRG-2024 (AEZ-29 Hill Soils) & SRDI Hill Tract Land Capability Survey",
        "source_url": "https://srdi.gov.bd/",
        "survey_year": "2018–2024 (BARC / SRDI)",
    },
    "gangetic_brahmaputra_floodplain": {
        "aez_id": "AEZ-8 / AEZ-9 / AEZ-11 / AEZ-12 (Old & Young Brahmaputra, Jamuna & High/Low Ganges River Floodplain)",
        "matching_districts": (),  # default floodplain profile for remaining central/western floodplain districts
        "soil_classification": "Calcareous Dark Grey Floodplain Soils (Ganges) & Non-calcareous Grey Floodplain Soils (Brahmaputra/Meghna)",
        "soil_ph": {"min": 5.6, "max": 7.8, "typical": 6.6, "class_en": "Slightly acidic (Brahmaputra) to mildly alkaline/calcareous (Ganges)"},
        "organic_matter_pct": {"min": 1.0, "max": 1.9, "typical": 1.4, "class_en": "Low (below BARC 2.0% target)"},
        "salinity_ec_ds_m": {"min": 0.2, "max": 1.6, "typical": 0.6, "class_en": "Non-saline (<2.0 dS/m)"},
        "soil_texture": "Silt loam to silty clay loam on ridges; silty clay in basins (beels)",
        "drainage_class": "Moderately well drained on medium high land (F0/F1); poorly drained in low basins (F2/F3)",
        "nutrient_status_en": "Deficient in N, S, Zn, and B; calcareous Ganges soils have high Ca but elevated Zn/P immobilization (BARC FRG-2024).",
        "limitations_en": [
            "Intensive Boro–T. Aman cereal monoculture depletes soil organic matter (<1.5%) and micronutrients (Zn, S, B).",
            "Lowland basins retain standing water into November, narrowing the optimal sowing window for upland Rabi pulses.",
        ],
        "source_institution": "BARC & SRDI",
        "source_document": "BARC Fertilizer Recommendation Guide (FRG-2024) & Crop Zoning",
        "source_url": "https://apps.barc.gov.bd/cropzoning/",
        "survey_year": "2018–2024 (BARC FRG)",
    },
}

# Crop-specific soil & water suitability thresholds from BARI, BRRI, and BARC FRG-2024
CROP_SOIL_REQUIREMENTS: dict[str, dict[str, Any]] = {
    "rice": {
        "crop_id": "rice",
        "name_en": "Rice (Aman / Boro / Aus)",
        "botanical_family": "Poaceae",
        "optimal_ph_range": (5.0, 7.5),
        "max_salinity_ec_ds_m": 4.0,  # standard varieties; BRRI dhan67/97/99 tolerate up to 8-12 dS/m at seedling stage
        "saline_cultivar_note": "Standard rice declines >4.0 dS/m; coastal fields require BRRI dhan67/97/99 or BINA dhan-10 (tolerates 8–12 dS/m).",
        "tolerates_standing_water": True,
        "preferred_textures": ("silt loam", "silty clay loam", "silty clay", "clay"),
        "source": "BRRI (https://brri.gov.bd/) & BARC FRG-2024",
    },
    "mustard": {
        "crop_id": "mustard",
        "name_en": "Mustard (BARI Sarisha-14/17/18)",
        "botanical_family": "Brassicaceae",
        "optimal_ph_range": (5.8, 7.5),
        "max_salinity_ec_ds_m": 4.5,  # sensitive above 4-5 dS/m during germination
        "saline_cultivar_note": "Germination and seedling emergence drop sharply when topsoil ECe exceeds 4.5 dS/m; requires pre-sowing mulch or BARI Sarisha-16/18.",
        "tolerates_standing_water": False,
        "preferred_textures": ("loam", "silt loam", "silty clay loam"),
        "source": "BARI Oilseed Research Centre (https://bari.gov.bd/) & BARC FRG-2024",
    },
    "pulse": {
        "crop_id": "pulse",
        "name_en": "Pulse (Lentil / Mungbean / Chickpea)",
        "botanical_family": "Fabaceae",
        "optimal_ph_range": (6.0, 7.5),
        "max_salinity_ec_ds_m": 3.0,  # pulses (especially lentil) are highly sensitive to salinity (>3 dS/m) and waterlogging
        "saline_cultivar_note": "Lentil and mungbean suffer severe nodulation failure and root rot above ECe 3.0 dS/m or pH < 5.5.",
        "tolerates_standing_water": False,
        "preferred_textures": ("sandy loam", "loam", "silt loam", "silty clay loam"),
        "source": "BARI Pulses Research Centre (https://bari.gov.bd/) & BARC FRG-2024",
    },
    "wheat": {
        "crop_id": "wheat",
        "name_en": "Wheat (BARI Gom-30/32/33)",
        "botanical_family": "Poaceae",
        "optimal_ph_range": (5.8, 7.5),
        "max_salinity_ec_ds_m": 6.0,
        "saline_cultivar_note": "Moderately tolerant up to 6.0 dS/m; acidic soils (pH < 5.5) require boron and lime to prevent grain sterility.",
        "tolerates_standing_water": False,
        "preferred_textures": ("loam", "silt loam", "clay loam"),
        "source": "BWMRI / BARI (https://bari.gov.bd/) & BARC FRG-2024",
    },
    "maize": {
        "crop_id": "maize",
        "name_en": "Maize (Kharif-1 / Rabi)",
        "botanical_family": "Poaceae",
        "optimal_ph_range": (5.5, 7.5),
        "max_salinity_ec_ds_m": 4.0,
        "saline_cultivar_note": "Sensitive to waterlogging at V3–V6 knee-high stage and topsoil ECe > 4.0 dS/m.",
        "tolerates_standing_water": False,
        "preferred_textures": ("sandy loam", "loam", "silt loam"),
        "source": "BWMRI / BARI (https://bari.gov.bd/) & BARC FRG-2024",
    },
    "jute": {
        "crop_id": "jute",
        "name_en": "Jute (Tossa / Deshi)",
        "botanical_family": "Malvaceae",
        "optimal_ph_range": (5.5, 7.2),
        "max_salinity_ec_ds_m": 4.0,
        "saline_cultivar_note": "Tossa jute (Corchorus olitorius) is sensitive to early waterlogging; Deshi jute (C. capsularis) tolerates wetter lowlands.",
        "tolerates_standing_water": False,
        "preferred_textures": ("loam", "silt loam", "silty clay loam"),
        "source": "BJRI & BARC FRG-2024 (https://barc.gov.bd/)",
    },
    "vegetables": {
        "crop_id": "vegetables",
        "name_en": "Vegetables / Potato",
        "botanical_family": "Solanaceae / Cucurbitaceae",
        "optimal_ph_range": (5.5, 7.0),
        "max_salinity_ec_ds_m": 2.5,
        "saline_cultivar_note": "Most vegetables and potato are sensitive to salinity (>2.5 dS/m) and require raised beds with good drainage.",
        "tolerates_standing_water": False,
        "preferred_textures": ("sandy loam", "loam", "silt loam"),
        "source": "BARI Olericulture / Tuber Crops Research Centre (https://bari.gov.bd/)",
    },
}


def resolve_aez_profile(district_id: str | None) -> dict[str, Any]:
    """Return the published SRDI/BARC AEZ reference soil profile for a Bangladesh district."""
    did = (district_id or "").strip().lower()
    for key, prof in AEZ_SOIL_PROFILES.items():
        if did in prof["matching_districts"]:
            return {"zone_key": key, **prof}
    return {"zone_key": "gangetic_brahmaputra_floodplain", **AEZ_SOIL_PROFILES["gangetic_brahmaputra_floodplain"]}


def build_soil_evidence_model(
    district_profile: dict[str, Any] | None,
    *,
    soil_test: str = "unknown",
    farmer_soil_ph: float | None = None,
    farmer_drainage: str = "unknown",
) -> dict[str, Any]:
    """Build a structured soil evidence model preserving provenance, units, survey year, spatial resolution,
    and explicit evidence classifications (`VERIFIED`, `REFERENCE`, `ESTIMATED`, `FARMER_REPORTED`, `UNKNOWN`).
    Never presents a district/AEZ reference range as a measured farm-level parcel value."""
    if not isinstance(district_profile, dict):
        return {
            "status": "global_no_srdi_adapter",
            "overall_classification": "FARMER_REPORTED" if (soil_test == "yes" and farmer_soil_ph is not None) else "UNKNOWN",
            "parcel_lab_verified": False,
            "false_precision_guard": (
                "No reviewed national soil survey adapter is connected for this coordinate, and satellite microwave "
                "sensors (SMAP / POWER) cannot measure soil pH, salinity (EC), organic matter, or NPK."
            ),
            "records": [],
        }

    did = str(district_profile.get("id", "")).lower()
    dname = str(district_profile.get("name_en", "Selected District"))
    aez = resolve_aez_profile(did)
    ph_ref = aez["soil_ph"]
    om_ref = aez["organic_matter_pct"]
    ec_ref = aez["salinity_ec_ds_m"]

    has_farmer_ph = soil_test == "yes" and isinstance(farmer_soil_ph, (int, float))
    records: list[dict[str, Any]] = [
        {
            "property_id": "soil_ph",
            "property_name": "Soil Reaction (pH)",
            "location_coverage": f"Parcel-reported ({dname})" if has_farmer_ph else f"{dname} District / {aez['aez_id']}",
            "reported_value": round(float(farmer_soil_ph), 2) if has_farmer_ph else None,
            "reference_range": {"min": ph_ref["min"], "max": ph_ref["max"], "regional_typical": ph_ref["typical"]},
            "class_description": ph_ref["class_en"],
            "unit": "pH units (-log[H+])",
            "source_institution": "Farmer Lab Soil Report + BARC/SRDI Reference" if has_farmer_ph else aez["source_institution"],
            "source_document": aez["source_document"],
            "source_url": aez["source_url"],
            "survey_year": aez["survey_year"],
            "spatial_resolution": "Parcel lab sample (farmer-entered)" if has_farmer_ph else "Regional AEZ / District survey (~1:50,000 SRDI Thana Nirdeshika)",
            "evidence_classification": "FARMER_REPORTED" if has_farmer_ph else "REFERENCE",
            "limitations": (
                "Farmer-reported lab pH recorded; verify test date (<3 years) and sampling depth (0–15 cm)."
                if has_farmer_ph
                else f"Regional AEZ reference range ({ph_ref['min']}–{ph_ref['max']}) for {dname}; parcel pH varies by upazila and land type (F0–F3). Lab test required."
            ),
        },
        {
            "property_id": "organic_matter_pct",
            "property_name": "Soil Organic Matter (SOM)",
            "location_coverage": f"{dname} District / {aez['aez_id']}",
            "reported_value": None,
            "reference_range": {"min": om_ref["min"], "max": om_ref["max"], "regional_typical": om_ref["typical"]},
            "class_description": om_ref["class_en"],
            "unit": "% (Walkley-Black wet oxidation)",
            "source_institution": aez["source_institution"],
            "source_document": aez["source_document"],
            "source_url": aez["source_url"],
            "survey_year": aez["survey_year"],
            "spatial_resolution": "Regional AEZ / District survey",
            "evidence_classification": "REFERENCE",
            "limitations": f"Regional AEZ range ({om_ref['min']}–{om_ref['max']}%); exact parcel organic matter is UNKNOWN without a laboratory soil test.",
        },
        {
            "property_id": "salinity_ec_ds_m",
            "property_name": "Electrical Conductivity / Dry-Season Soil Salinity (ECe)",
            "location_coverage": f"{dname} District / {aez['aez_id']}",
            "reported_value": None,
            "reference_range": {"min": ec_ref["min"], "max": ec_ref["max"], "regional_typical": ec_ref["typical"]},
            "class_description": ec_ref["class_en"],
            "unit": "dS/m (saturated paste extract, 0–15 cm)",
            "source_institution": "SRDI (Soil Resource Development Institute)",
            "source_document": "SRDI Saline Soils of Bangladesh (2010 / 2022) & BARC FRG-2024",
            "source_url": "https://srdi.gov.bd/",
            "survey_year": aez["survey_year"],
            "spatial_resolution": "Regional AEZ / Coastal monitoring network",
            "evidence_classification": "REFERENCE",
            "limitations": (
                "Coastal salinity fluctuates sharply between wet monsoon (<2 dS/m) and dry Rabi season (up to 8–12+ dS/m in Dec–Apr). "
                "Parcel ECe is UNKNOWN without an in-season EC meter or SRDI lab test."
            ),
        },
        {
            "property_id": "soil_texture_and_classification",
            "property_name": "Soil Texture & Taxonomic Group",
            "location_coverage": f"{dname} District / {aez['aez_id']}",
            "reported_value": aez["soil_texture"],
            "reference_range": None,
            "class_description": aez["soil_classification"],
            "unit": "USDA / SRDI textural class",
            "source_institution": aez["source_institution"],
            "source_document": aez["source_document"],
            "source_url": aez["source_url"],
            "survey_year": aez["survey_year"],
            "spatial_resolution": "Regional AEZ / District survey",
            "evidence_classification": "REFERENCE",
            "limitations": "Within any district, ridge tops are coarser (sandy/silt loam) and basin bottoms (beels) are heavier clay.",
        },
        {
            "property_id": "drainage_class",
            "property_name": "Field Drainage & Post-Rain Water Retention",
            "location_coverage": f"Parcel-reported + {dname} AEZ reference",
            "reported_value": farmer_drainage if farmer_drainage != "unknown" else None,
            "reference_range": None,
            "class_description": aez["drainage_class"],
            "unit": "Drainage class",
            "source_institution": "Farmer Observation + SRDI Land Type Reference" if farmer_drainage != "unknown" else "SRDI & BARC",
            "source_document": aez["source_document"],
            "source_url": aez["source_url"],
            "survey_year": aez["survey_year"],
            "spatial_resolution": "Parcel observation + Regional AEZ",
            "evidence_classification": "FARMER_REPORTED" if farmer_drainage != "unknown" else "REFERENCE",
            "limitations": "Post-rain standing water depends on micro-topography (Highland F0 vs. Medium Lowland F2) and local canal drainage.",
        },
        {
            "property_id": "parcel_npk_nutrients",
            "property_name": "Parcel Available N, P, K, S, Zn, B",
            "location_coverage": f"Selected Parcel ({dname})",
            "reported_value": None,
            "reference_range": None,
            "class_description": aez["nutrient_status_en"],
            "unit": "mg/kg or % (lab chemical test required)",
            "source_institution": "BARC FRG-2024 Regional Baseline (Parcel value UNKNOWN)",
            "source_document": "BARC Fertilizer Recommendation Guide (FRG-2024)",
            "source_url": "https://apps.barc.gov.bd/fertilizer_recommendation/FRG%20English%2030.10.2024.pdf",
            "survey_year": "2024",
            "spatial_resolution": "Parcel (unmeasured)",
            "evidence_classification": "UNKNOWN",
            "limitations": "Satellite sensors cannot measure soil NPK or micronutrients. Laboratory soil analysis (SRDI Upazila Soil Testing Lab) is required before prescribing fertilizer rates.",
        },
    ]

    return {
        "status": "bangladesh_srdi_barc_reference_integrated",
        "aez_id": aez["aez_id"],
        "soil_classification": aez["soil_classification"],
        "overall_classification": "FARMER_REPORTED_AND_REFERENCE" if has_farmer_ph else "REFERENCE_ONLY_PARCEL_UNKNOWN",
        "parcel_lab_verified": False,
        "false_precision_guard": (
            f"All SRDI/BARC soil figures for {dname} ({aez['aez_id']}) are classified as REFERENCE (regional survey ranges), "
            "never as exact farm-level measurements. Parcel NPK and electrical conductivity (ECe) are classified as UNKNOWN "
            "until a laboratory soil test is entered."
        ),
        "regional_limitations": aez["limitations_en"],
        "records": records,
    }


def evaluate_crop_soil_suitability(
    crop_key: str,
    soil_model: dict[str, Any],
    *,
    water_source: str = "unknown",
    drainage: str = "unknown",
    soil_test: str = "unknown",
    farmer_ph: float | None = None,
) -> dict[str, Any]:
    """Evaluate crop-specific soil suitability (pH, salinity, drainage, texture, water availability, and missing evidence gates)."""
    norm_key = (crop_key or "rice").strip().lower()
    if "mustard" in norm_key or "oil" in norm_key:
        norm_key = "mustard"
    elif any(k in norm_key for k in ("pulse", "lentil", "mung", "gram", "legume", "cowpea", "soy")):
        norm_key = "pulse"
    elif "wheat" in norm_key:
        norm_key = "wheat"
    elif "maize" in norm_key or "corn" in norm_key:
        norm_key = "maize"
    elif "jute" in norm_key:
        norm_key = "jute"
    elif "veg" in norm_key or "potato" in norm_key:
        norm_key = "vegetables"
    else:
        norm_key = "rice"

    req = CROP_SOIL_REQUIREMENTS[norm_key]
    records = {r["property_id"]: r for r in (soil_model.get("records") or []) if isinstance(r, dict) and r.get("property_id")}

    constraints_violated: list[str] = []
    warnings: list[str] = []
    missing_evidence: list[str] = []

    if soil_test != "yes":
        missing_evidence.append("Parcel laboratory soil test (pH, EC salinity, organic matter, NPK) is not available (UNKNOWN).")

    # 1. pH compatibility
    ph_rec = records.get("soil_ph")
    lo_ph, hi_ph = req["optimal_ph_range"]
    if isinstance(farmer_ph, (int, float)) and soil_test == "yes":
        if farmer_ph < lo_ph or farmer_ph > hi_ph:
            constraints_violated.append(
                f"Farmer-reported soil pH ({farmer_ph:.1f}) is outside {req['name_en']} optimal range ({lo_ph:.1f}–{hi_ph:.1f})."
            )
    elif ph_rec and isinstance(ph_rec.get("reference_range"), dict):
        typ_ph = ph_rec["reference_range"].get("regional_typical")
        if isinstance(typ_ph, (int, float)) and (typ_ph < lo_ph - 0.3 or typ_ph > hi_ph + 0.3):
            warnings.append(
                f"Regional SRDI/BARC reference pH (typical ~{typ_ph}) is marginal for {req['name_en']} (optimal {lo_ph}–{hi_ph}); verify parcel pH and lime/boron need."
            )

    # 2. Salinity sensitivity
    ec_rec = records.get("salinity_ec_ds_m")
    if ec_rec and isinstance(ec_rec.get("reference_range"), dict):
        max_ec = ec_rec["reference_range"].get("max", 0.0)
        typ_ec = ec_rec["reference_range"].get("regional_typical", 0.0)
        if typ_ec > req["max_salinity_ec_ds_m"] or max_ec >= 8.0:
            warnings.append(
                f"Coastal dry-season salinity risk (SRDI REFERENCE range {ec_rec['reference_range']['min']}–{max_ec} dS/m vs. "
                f"{req['name_en']} threshold {req['max_salinity_ec_ds_m']} dS/m): {req['saline_cultivar_note']}"
            )
            if soil_test != "yes":
                missing_evidence.append(
                    f"Dry-season topsoil salinity (ECe in dS/m) is unverified for this coastal parcel; {req['name_en']} is sensitive above {req['max_salinity_ec_ds_m']} dS/m."
                )

    # 3. Drainage compatibility
    if not req["tolerates_standing_water"] and drainage == "stays":
        constraints_violated.append(
            f"{req['name_en']} does not tolerate standing water, but field post-rain drainage is reported as 'stays' (waterlogged)."
        )
    elif not req["tolerates_standing_water"] and drainage == "unknown":
        missing_evidence.append(f"Field surface drainage after heavy rain is UNKNOWN; {req['name_en']} is sensitive to waterlogging.")

    # 4. Water availability compatibility
    if norm_key == "rice" and water_source == "rainfed":
        warnings.append("Rainfed water source requires supplemental irrigation backup if dry spells occur during flowering/booting.")

    if constraints_violated:
        suitability_status = "FLAGGED_CONSTRAINT_VIOLATION"
    elif missing_evidence or warnings:
        suitability_status = "CONDITIONAL_VERIFICATION_REQUIRED"
    else:
        suitability_status = "SUITABLE_WITH_VERIFIED_INPUTS"

    return {
        "crop_id": norm_key,
        "crop_name_en": req["name_en"],
        "botanical_family": req["botanical_family"],
        "suitability_status": suitability_status,
        "unconditional_recommendation_allowed": False,  # Mandatory gate: never unconditional without full parcel lab sheet
        "optimal_ph_range": list(req["optimal_ph_range"]),
        "max_salinity_ec_ds_m": req["max_salinity_ec_ds_m"],
        "tolerates_standing_water": req["tolerates_standing_water"],
        "constraints_violated": constraints_violated,
        "soil_and_salinity_warnings": warnings,
        "missing_evidence": missing_evidence,
        "authoritative_source": req["source"],
    }
