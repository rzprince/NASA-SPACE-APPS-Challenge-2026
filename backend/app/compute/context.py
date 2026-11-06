"""Global Earth-observation context with Bangladesh 64-district & regional deep local evidence.

NASA environmental coverage is global. Local agronomic evidence is deliberately
separate: Bangladesh has a reviewed regional calendar index plus a 64-district
agro-ecological profile dataset (with explicit SRDI/BMD/BARC verification caveats),
while other countries use the verified source registry and FAO reference layer
until a country adapter is added.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from math import asin, cos, radians, sin, sqrt
from typing import Any

from backend.app.compute.agronomy import calendar_evidence_for_region
from backend.app.compute.bangladesh_districts import (
    nearest_bangladesh_district,
    serialize_district,
)
from backend.app.compute.soil_evidence import build_soil_evidence_model
from backend.app.services.imerg_check import get_imerg_crosscheck_status
from backend.app.services.provenance import build_centralized_provenance_registry

BANGLADESH_BOUNDS = {"south": 20.5, "north": 26.75, "west": 88.0, "east": 92.8}


@dataclass(frozen=True)
class Area:
    id: str
    name_en: str
    name_bn: str
    latitude: float
    longitude: float
    evidence_region: str


AREAS = (
    Area("dhaka", "Dhaka region", "ঢাকা অঞ্চল", 23.8103, 90.4125, "Dhaka"),
    Area("mymensingh", "Mymensingh region", "ময়মনসিংহ অঞ্চল", 24.7471, 90.4203, "Mymensingh"),
    Area("cumilla", "Cumilla region", "কুমিল্লা অঞ্চল", 23.4607, 91.1809, "Cumilla"),
    Area("chattogram", "Chattogram region", "চট্টগ্রাম অঞ্চল", 22.3569, 91.7832, "Chattogram"),
    Area("sylhet", "Sylhet region", "সিলেট অঞ্চল", 24.8949, 91.8687, "Sylhet"),
    Area("rangpur", "Rangpur region", "রংপুর অঞ্চল", 25.7439, 89.2752, "Rangpur"),
    Area("dinajpur", "Dinajpur region", "দিনাজপুর অঞ্চল", 25.6279, 88.6332, "Dinajpur"),
    Area("bogura", "Bogura region", "বগুড়া অঞ্চল", 24.8465, 89.3773, "Bogura"),
    Area("rajshahi", "Rajshahi region", "রাজশাহী অঞ্চল", 24.3745, 88.6042, "Rajshahi"),
    Area("jashore", "Jashore region", "যশোর অঞ্চল", 23.1664, 89.2081, "Jashore"),
    Area("faridpur", "Faridpur region", "ফরিদপুর অঞ্চল", 23.6071, 89.8429, "Faridpur"),
    Area("khulna", "Khulna region", "খুলনা অঞ্চল", 22.8456, 89.5403, "Khulna"),
    Area("barishal", "Barishal region", "বরিশাল অঞ্চল", 22.7010, 90.3535, "Barishal"),
    Area("rangamati", "Rangamati region", "রাঙামাটি অঞ্চল", 22.7324, 92.2985, "Rangamati"),
)

NASA_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "id": "gpm-imerg-early-v07b",
        "name": "GPM IMERG Early V07B",
        "role": "recent_precipitation",
        "kind": "near_real_time_earth_observation",
        "status": "global_map_layer_ready",
        "latency_note": "NASA documents about 4 hour minimum latency. This is not a forecast.",
        "resolution_note": "0.1 degree, about 10 km.",
        "source_url": "https://gpm.nasa.gov/data/directory",
    },
    {
        "id": "smap-spl3smp-e-v6",
        "name": "SMAP SPL3SMP_E Version 6 & POWER Root-Zone Wetness",
        "role": "surface_and_root_zone_soil_moisture",
        "kind": "earth_observation",
        "status": "global_map_layer_ready_numeric_adapter_gated",
        "latency_note": "Daily surface (0–5 cm) & root-zone (0–100 cm) physical wetness context. Never measures pH or NPK.",
        "resolution_note": "9 km EASE-Grid (SMAP) + 0.5°×0.625° (POWER GWETTOP/GWETROOT).",
        "source_url": "https://nsidc.org/data/spl3smp_e/versions/6",
        "advisory": "SMAP Standard and NRT products experienced a geolocation issue from 14 May to 28 July 2026. Affected dates require QA awareness.",
    },
    {
        "id": "nasa-power-daily",
        "name": "NASA POWER Daily Agroclimatology",
        "role": "recent_agroclimate",
        "kind": "analysis_ready_gridded_context",
        "status": "global_point_query_ready",
        "latency_note": "Daily data (T2M, T2M_MAX, T2M_MIN, T2MDEW, PRECTOTCORR, RH2M, WS2M, ALLSKY_SFC_SW_DWN, GWETTOP, GWETROOT).",
        "resolution_note": "Source grid context (0.5° × 0.625°), not a parcel sensor.",
        "source_url": "https://power.larc.nasa.gov/docs/services/api/temporal/daily/",
    },
    {
        "id": "nasa-power-climatology",
        "name": "NASA POWER Climatology",
        "role": "historical_baseline",
        "kind": "historical_climate_context",
        "status": "global_point_query_ready",
        "latency_note": "Historical baseline only (2001–2020).",
        "resolution_note": "Source grid context, not a field measurement.",
        "source_url": "https://power.larc.nasa.gov/docs/services/api/temporal/climatology/",
    },
    {
        "id": "nasa-gibs",
        "name": "NASA GIBS / Worldview (MODIS, SRTM, IMERG, SMAP)",
        "role": "spatial_visualization",
        "kind": "earth_observation_visualization",
        "status": "global_layers_ready",
        "latency_note": "Supports multi-date time scrubbing across seasonal layers.",
        "resolution_note": "Resolution follows each source product (MODIS 250 m–1 km, SRTM 30 m–90 m, IMERG 0.1°, SMAP 9 km).",
        "source_url": "https://worldview.earthdata.nasa.gov/",
    },
    {
        "id": "nasa-eonet-v3",
        "name": "NASA EONET v3 Natural Event Tracker",
        "role": "real_time_natural_hazards",
        "kind": "near_real_time_hazard_feed",
        "status": "global_live_feed_ready",
        "latency_note": "Tracks active cyclones/storms, floods, droughts, wildfires, and landslides.",
        "resolution_note": "Event-based point/polygon coordinates with distance to selected farm.",
        "source_url": "https://eonet.gsfc.nasa.gov/docs/v3",
    },
)

MULTI_RESOLUTION_HARMONIZATION: dict[str, Any] = {
    "method": "coordinate_anchored_multi_scale_evidence_stack",
    "summary_en": (
        "BoponX aligns multi-resolution NASA grids (0.5°×0.625° POWER agroclimate & GWETTOP/GWETROOT wetness, "
        "0.1° ~10 km GPM IMERG rainfall, 9 km SMAP surface soil moisture, 250 m–1 km MODIS GIBS NDVI & LST, "
        "SRTM elevation/drainage, and live NASA EONET hazard events) to the selected field coordinate, "
        "keeping satellite grids distinct from district/upazila agronomy and parcel soil tests."
    ),
    "summary_bn": (
        "BoponX বিভিন্ন রেজোলিউশনের নাসা ডেটা (০.৫°×০.৬২৫° POWER আবহাওয়া ও মাটির আর্দ্রতা, ~১০ কিমি GPM IMERG বৃষ্টিপাত, "
        "৯ কিমি SMAP, ২৫০ মিটার MODIS NDVI, SRTM ভূমির উচ্চতা এবং লাইভ EONET দুর্যোগ সতর্কতা) নির্বাচিত জমির স্থানাঙ্কে সমন্বয় করে, "
        "তবে স্যাটেলাইট গ্রিডকে কখনোই মাঠের মাটি পরীক্ষার বিকল্প হিসেবে ধরে না।"
    ),
    "layers": [
        {"layer": "NASA POWER Daily & Climatology", "spatial_scale": "0.5° × 0.625° (~50 km)", "temporal_scale": "Live 2026 Daily (14d) & Multi-Year Climatology", "role": "Active: Temp, rain, solar, dew/frost, GWETTOP (0–5cm) & GWETROOT (0–100cm)"},
        {"layer": "GPM IMERG Early V07B", "spatial_scale": "0.1° (~10 km)", "temporal_scale": "Near-real-time (~4h latency)", "role": "Active: Spatial precipitation distribution & extreme rain context"},
        {"layer": "SMAP SPL3SMP_E V6", "spatial_scale": "9 km EASE-Grid", "temporal_scale": "Daily multi-date", "role": "Active: Top-5 cm regional soil moisture context (not pH/nutrients)"},
        {"layer": "MODIS Terra / Landsat Reflectance & NDVI", "spatial_scale": "30 m – 1 km", "temporal_scale": "Daily / 8-day composite", "role": "Active GIBS visual layer & bare-field / canopy NDVI stress detection"},
        {"layer": "SRTM Elevation & MODIS LST / ECOSTRESS", "spatial_scale": "30 m–90 m (SRTM) / 1 km (LST)", "temporal_scale": "Static DEM & Daily thermal", "role": "Active GIBS layers: Topographic drainage/erosion & daytime surface heat"},
        {"layer": "NASA EONET v3 Live Hazards", "spatial_scale": "Regional Event Radius", "temporal_scale": "Real-Time Open Feed", "role": "Active: Tracks live cyclones, floods, droughts & landslides near the farm"},
        {"layer": "Local Agronomy & Lab Soil Report", "spatial_scale": "64 Districts / >490 Upazilas / Parcel", "temporal_scale": "Seasonal & Lab-report dated", "role": "Active: BAMIS calendars, 64-district landform/analog profile & farmer lab soil pH"},
    ],
}

SCIENTIFIC_GLOSSARY: tuple[dict[str, str], ...] = (
    {
        "term_id": "evapotranspiration",
        "term_en": "Evapotranspiration & Evaporative Stress (ET₀ / ECOSTRESS)",
        "term_bn": "বাষ্পীভবন ও প্রস্বদন চাপ (Evapotranspiration / ET₀)",
        "explanation_en": "Combined water lost from soil evaporation and crop leaf transpiration. High temperature and wind increase evaporative demand, stressing shallow-rooted crops if soil moisture is low.",
        "explanation_bn": "মাটি থেকে বাষ্পীভবন এবং গাছের পাতা থেকে প্রস্বদনের মাধ্যমে পানির সম্মিলিত ক্ষয়। তাপমাত্রা ও বাতাস বাড়লে পানির চাহিদা বাড়ে।",
    },
    {
        "term_id": "soil_moisture_anomaly",
        "term_en": "Topsoil (GWETTOP 0–5cm) vs. Root-Zone (GWETROOT 0–100cm) & SMAP",
        "term_bn": "উপরিভাগের (০–৫ সেমি) বনাম শিকড় অঞ্চলের (০–১০০ সেমি) মাটির আর্দ্রতা",
        "explanation_en": "Topsoil wetness (0–5 cm) governs seed germination ('jo' condition), while root-zone wetness (0–100 cm) sustains deep-rooted legumes and trees during dry spells. Neither measures soil pH or NPK.",
        "explanation_bn": "উপরিভাগের আর্দ্রতা (০–৫ সেমি) বীজ গজানোর ('জো' অবস্থা) জন্য জরুরি, আর গভীর শিকড় অঞ্চলের আর্দ্রতা (০–১০০ সেমি) খরায় গভীর মূলী ফসলকে বাঁচিয়ে রাখে।",
    },
    {
        "term_id": "vegetation_index_ndvi",
        "term_en": "Vegetation Stress & Bare-Field Windows (NDVI / MODIS / Landsat)",
        "term_bn": "উদ্ভিদ সূচক ও পতিত জমির সময়কাল (NDVI / Bare Window)",
        "explanation_en": "Satellite reflectance indicators show when fields are bare between harvest and planting (increasing erosion and salinity capillary rise) or when standing crops face mid-season stress.",
        "explanation_bn": "ফসল কাটা ও পরবর্তী বপনের মাঝে জমি কখন খালি থাকে (যখন ক্ষয় ও লবণাক্ততা বাড়ে) বা ফসলের চাপের সময় নির্দেশ করে।",
    },
    {
        "term_id": "heat_frost_risk",
        "term_en": "Heat Shift, Dew-Point Fog & Frost Vulnerability (T2M_MAX / T2MDEW)",
        "term_bn": "তাপপ্রবাহ, কুয়াশা/ব্লাইট ও শৈত্যপ্রবাহের ঝুঁকি",
        "explanation_en": "Extreme max temperatures (≥35°C) cause floral sterility, while narrow air-to-dewpoint spread (T2M − T2MDEW ≤ 2.5°C) with low solar radiation triggers winter fog and fungal blights.",
        "explanation_bn": "অতিরিক্ত তাপমাত্রা (≥৩৫°C) পরাগায়ন ব্যাহত করে, আর শীতকালে কুয়াশা ও শিশিরবিন্দুর পার্থক্য কমে গেলে আলু, সরিষা ও ডালের ব্লাইট রোগের ঝুঁকি বাড়ে।",
    },
    {
        "term_id": "water_balance",
        "term_en": "Water-Balance, SRTM Drainage & Long-Term Storage (P − ET₀ / GRACE-FO)",
        "term_bn": "জমির পানির ভারসাম্য, ভূমির ঢাল ও ভূগর্ভস্থ পানি",
        "explanation_en": "Combines regional rainfall minus evapotranspiration (P − ET₀) with topographic drainage and farmer observations to flag waterlogging vs. groundwater depletion risk.",
        "explanation_bn": "বৃষ্টিপাত ও বাষ্পীভবনের পার্থক্য (P − ET₀), ভূমির ঢাল এবং কৃষকের নিষ্কাশন পর্যবেক্ষণ মিলিয়ে জলাবদ্ধতা বা খরার ঝুঁকি নির্ণয়।",
    },
)

FUNCTIONAL_CROP_ROLES: tuple[dict[str, str], ...] = (
    {
        "role_id": "nitrogen_fixing",
        "title_en": "Nitrogen-Fixing Crops (Pulses / Legumes)",
        "title_bn": "নাইট্রোজেন সংবন্ধনকারী ফসল (ডাল জাতীয় ফসল)",
        "examples_en": "Lentil (মসুর), Mungbean / Green Gram (মুগ), Chickpea (ছোলা), Blackgram, Soybean (সয়াবিন)",
        "examples_bn": "মসুর, মুগ ডাল, ছোলা, মাসকলাই, সয়াবিন, চিনাবাদাম",
        "benefit_en": "Form symbiotic Rhizobium root nodules that fix +30 to +60 kg atmospheric N/ha, reducing synthetic urea need for the next cereal crop by 25–30% while breaking cereal pest cycles.",
        "benefit_bn": "শিকড়ের রাইজোবিয়াম গুটির মাধ্যমে বাতাস থেকে হেক্টরে ৩০–৬০ কেজি নাইট্রোজেন মাটিতে যুক্ত করে, পরবর্তী ফসলে ইউরিয়া খরচ ২৫–৩০% কমায় এবং রোগ-পোকার চক্র ভাঙে।",
    },
    {
        "role_id": "cover_crops",
        "title_en": "Short-Duration Cover & Bridge Crops",
        "title_bn": "স্বল্পমেয়াদি আচ্ছাদন ও অন্তর্বর্তী ফসল (Cover Crops)",
        "examples_en": "Short-duration Mustard (সরিষা, 75–80d), Mungbean, Dhaincha (Sesbania green manure), Cowpea",
        "examples_bn": "স্বল্পমেয়াদি সরিষা (৭৫–৮০ দিন), মুগ ডাল, ধইঞ্চা (সবুজ সার), ফেলন",
        "benefit_en": "Protects bare soil between main harvests (Nov–Jan or Mar–May), cutting topsoil evaporation, sheet erosion, weed growth, and dry-season capillary salt rise in coastal plots.",
        "benefit_bn": "দুই প্রধান ফসলের মাঝের খালি সময়ে মাটি ঢেকে রাখে; ফলে মাটির রস উড়ে যাওয়া, ভূমিক্ষয়, আগাছা এবং উপকূলীয় জমিতে লবণ ওঠা রোধ হয়।",
    },
    {
        "role_id": "deep_rooting",
        "title_en": "Deep-Rooting & Plough-Pan Breaking Crops",
        "title_bn": "গভীর মূলী ও মাটির শক্ত স্তর (প্লাউ প্যান) ভাঙার ফসল",
        "examples_en": "Jute (পাট), Pigeonpea / Arhar (অড়হর), Maize, Sunflower, Mustard taproots",
        "examples_bn": "পাট, অড়হর, ভুট্টা, সূর্যমুখী, সরিষা",
        "benefit_en": "Taproots penetrate compacted subsoil plough pans created by repeated puddled rice, creating biopores that improve rainfall infiltration and access deeper moisture (GWETROOT).",
        "benefit_bn": "টানা ধান চাষের ফলে মাটির নিচে যে শক্ত স্তর (প্লাউ প্যান) তৈরি হয় তা ভেদ করে মাটির পানি শোষণ ক্ষমতা বাড়ায় এবং গভীর স্তরের আর্দ্রতা (GWETROOT) ব্যবহার করে।",
    },
    {
        "role_id": "drought_saline_tolerant",
        "title_en": "Drought-, Heat- & Saline-Tolerant Crops",
        "title_bn": "খরা, তাপ ও লবণাক্ততা সহনশীল ফসল",
        "examples_en": "Millet / Sorghum, Chickpea, Barley, Dragon Fruit (Barind); Salt-tolerant Rice, Soybean, Watermelon, BARI Red Mango (Coastal)",
        "examples_bn": "ছোলা, যব, ভুট্টা, ড্রাগন ফ্রুট (বরেন্দ্র); লবণসহনশীল ধান, সয়াবিন, তরমুজ (উপকূল)",
        "benefit_en": "Maintain physiological yield stability when NASA POWER shows negative water balance (P − ET₀ < 0), low root-zone moisture, or high evaporative stress.",
        "benefit_bn": "যখন নাসা তথ্যে পানির ঘাটতি (P − ET₀ < 0), খরা বা উপকূলীয় লবণাক্ততা দেখা যায়, তখন কম পানিতে স্থিতিশীল ফলন ও বাড়তি আয় নিশ্চিত করে।",
    },
)

SI_MODELING_METHODS: tuple[dict[str, str], ...] = (
    {
        "method_id": "climatological_anomaly_z",
        "title_en": "1. Climatological Baseline Anomaly & Stress Thresholding",
        "title_bn": "১. ঐতিহাসিক জলবায়ু বিচ্যুতি ও তাপ/বৃষ্টি সীমা বিশ্লেষণ",
        "detail_en": "Compares lag-safe 14-day NASA POWER observations against the 20-year (2001–2020) monthly distribution to flag >30% rainfall departures, heat spikes (≥35°C), frost risk (≤8°C), and narrow dewpoint spreads (fog/blight risk).",
        "detail_bn": "সাম্প্রতিক ১৪ দিনের নাসা তথ্যের সাথে ২০ বছরের (২০০১–২০২০) মাসিক গড়ের তুলনা করে ±৩০% বৃষ্টিপাত বিচ্যুতি, তাপপ্রবাহ (≥৩৫°C), শৈত্যপ্রবাহ ও কুয়াশাজনিত ব্লাইট ঝুঁকি শনাক্ত করে।",
    },
    {
        "method_id": "fao56_water_balance",
        "title_en": "2. Physical Agro-Hydrological Water-Balance Fusion (P − ET₀ & GWET)",
        "title_bn": "২. ফাও-৫৬ (FAO-56) পানির ভারসাম্য ও শিকড় অঞ্চলের আর্দ্রতা মডেল",
        "detail_en": "Combines FAO-56 Hargreaves-Samani Reference Evapotranspiration (ET₀), Vapor Pressure Deficit (VPD), topsoil wetness (GWETTOP 0–5cm), and root-zone wetness (GWETROOT 0–100cm) with farmer-reported drainage.",
        "detail_bn": "বাষ্পীভবন চাহিদা (ET₀), বায়ুর শুষ্কতা (VPD), উপরিভাগ (০–৫ সেমি) ও শিকড় অঞ্চলের (০–১০০ সেমি) আর্দ্রতার সাথে কৃষকের দেওয়া নিষ্কাশন তথ্যের সমন্বয় ঘটায়।",
    },
    {
        "method_id": "evidence_gated_decision_tree",
        "title_en": "3. Fail-Closed Deterministic Rule Gate & Uncertainty Handling",
        "title_bn": "৩. অনিশ্চয়তা ব্যবস্থাপনা ও প্রমাণ-নির্ভর সিদ্ধান্ত গেট (Fail-Closed Gate)",
        "detail_en": "Rather than using a black-box neural network that hallucinates parcel soil chemistry, BoponX explicitly separates regional satellite certainty from parcel unknowns (soil pH, NPK, upazila micro-topography) and requires human extension sign-off.",
        "detail_bn": "কাল্পনিক এআই অনুমানের বদলে BoponX উপগ্রহ তথ্যের সীমা ও মাঠের অজানা বিষয়গুলো (যেমন মাটির pH, সার বা উপজেলার সূক্ষ্ম পার্থক্য) আলাদা রাখে এবং কৃষি কর্মকর্তার যাচাই নিশ্চিত করে।",
    },
)


def in_bangladesh(lat: float, lon: float) -> bool:
    return (
        BANGLADESH_BOUNDS["south"] <= lat <= BANGLADESH_BOUNDS["north"]
        and BANGLADESH_BOUNDS["west"] <= lon <= BANGLADESH_BOUNDS["east"]
    )


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0088
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * radius * asin(sqrt(a))


def nearest_area(lat: float, lon: float) -> tuple[Area, float]:
    area = min(AREAS, key=lambda item: _distance_km(lat, lon, item.latitude, item.longitude))
    return area, _distance_km(lat, lon, area.latitude, area.longitude)


def list_areas() -> list[dict[str, Any]]:
    return [asdict(area) for area in AREAS]


def build_context(lat: float, lon: float) -> dict[str, Any]:
    inside = in_bangladesh(lat, lon)
    if inside:
        area, distance = nearest_area(lat, lon)
        district, district_distance = nearest_bangladesh_district(lat, lon)
        district_payload = serialize_district(district, distance_km=district_distance)
        region = {
            **asdict(area),
            "distance_km": round(distance, 1),
            "note": "Nearest Bangladesh agricultural evidence hub, not an administrative boundary lookup.",
        }
        calendars = calendar_evidence_for_region(area.evidence_region)
        agricultural_sources = [
            {
                "name": "Bangladesh Agro Meteorological Information Service",
                "scope": f"{area.evidence_region} crop weather calendars and agromet information",
                "status": "official_calendar_index_connected",
                "source_url": "https://www.bamis.gov.bd/",
            },
            {
                "name": "Bangladesh Agricultural Research Council crop zoning",
                "scope": f"Upazila level agro edaphic and agro climatic crop suitability and zoning reference ({district.name_en} District)",
                "status": "official_reference",
                "source_url": "https://apps.barc.gov.bd/cropzoning/",
            },
            {
                "name": "Soil Resource Development Institute (SRDI)",
                "scope": f"Upazila soil fertility, salinity, and land-type verification required for {district.name_en} ({district.landform_en})",
                "status": "official_reference",
                "source_url": "https://srdi.gov.bd/",
            },
            {
                "name": "Agriculture Information Service",
                "scope": "Government crop production technology, seasonal agriculture guidance, market information and farmer information services",
                "status": "official_reference",
                "source_url": "https://ais.gov.bd/",
            },
            {
                "name": "Department of Agricultural Extension",
                "scope": "Government extension service and local farmer support",
                "status": "official_reference",
                "source_url": "https://dae.gov.bd/",
            },
            {
                "name": "FAO Crop Calendar",
                "scope": "Country and agroecological zone crop calendar reference",
                "status": "global_reference",
                "source_url": "https://cropcalendar.apps.fao.org/",
            },
        ]
        local_status = "bangladesh_deep_adapter"
    else:
        district_payload = None
        region = {
            "id": "global-field",
            "name_en": "Global field",
            "name_bn": "বৈশ্বিক মাঠ",
            "latitude": lat,
            "longitude": lon,
            "evidence_region": "Country adapter",
            "distance_km": 0.0,
            "note": "NASA context is global. Country-specific agricultural evidence is resolved separately from the verified source registry.",
        }
        calendars = []
        agricultural_sources = [
            {
                "name": "FAO Crop Calendar",
                "scope": "Country and agroecological-zone crop calendar reference",
                "status": "global_reference",
                "source_url": "https://cropcalendar.apps.fao.org/",
            }
        ]
        local_status = "country_adapter_required"

    return {
        "status": "available",
        "data_origin": "static_verified_registry",
        "retrieved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lag_days": 0,
        "coordinates": {"latitude": round(lat, 5), "longitude": round(lon, 5)},
        "within_bangladesh": inside,
        "global_environmental_coverage": True,
        "nearest_supported_region": region,
        "district_profile": district_payload,
        "coverage": {
            "environmental_context": "global_nasa_coverage",
            "local_agricultural_evidence": local_status,
            "rotation_decision": "evidence_bounded_exploration",
        },
        "calendar_evidence": calendars,
        "agricultural_sources": agricultural_sources,
        "nasa_sources": [dict(source) for source in NASA_SOURCES],
        "imerg_crosscheck": get_imerg_crosscheck_status(lat, lon),
        "soil_evidence": build_soil_evidence_model(district_payload),
        "nasa_provenance": build_centralized_provenance_registry(
            lat, lon, imerg_status=get_imerg_crosscheck_status(lat, lon)
        ),
        "multi_resolution_harmonization": MULTI_RESOLUTION_HARMONIZATION,
        "scientific_glossary": list(SCIENTIFIC_GLOSSARY),
        "functional_crop_roles": list(FUNCTIONAL_CROP_ROLES),
        "si_modeling_methods": list(SI_MODELING_METHODS),
        "privacy": {
            "coordinates_persisted": False,
            "note": "Coordinates are used for the current session unless the user explicitly saves them.",
        },
    }
