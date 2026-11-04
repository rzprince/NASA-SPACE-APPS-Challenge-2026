"""Bangladesh 64-district agro-ecological context, established crops, and exploratory opportunities.

Source: BoponX 64-District Agro-Ecological & Crop Opportunity Dossier (27 October 2026, bpx.pdf),
paired with official BAMIS regional hubs, BARC Crop Zoning, SRDI, and DAE references.

SCIENTIFIC BOUNDARY:
- District landform/soil descriptions, climate-analog regions, established crops, and new crop
  opportunities are preliminary district-level estimates, NOT parcel-scale prescriptions.
- Within any single district, soil texture, elevation, salinity, and drainage vary significantly
  across upazilas (>490 upazilas nationwide).
- Only specific crop pilots explicitly tagged in `online_evidence` have published trial/production
  reports; all other entries require verification with SRDI soil maps, BMD climate records,
  BARC Crop Zoning, WorldClim, and SoilGrids before field commitment.
- Any introduction of new seed or planting material requires Plant Quarantine approval and
  National Seed Board registration.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import asin, cos, radians, sin, sqrt
from typing import Any


DATASET_CAUTION_BN = (
    "সতর্কতা: মাটির ধরন, মিল থাকা এলাকা ও ফসলের তালিকা প্রাথমিক অনুমান। মিল-শতাংশ গণনা করা হয়নি "
    "এবং লাভের সংখ্যা যাচাই করা হয়নি। একই জেলার ভেতরেও উপজেলাভেদে মাটি আলাদা হতে পারে। শুধু "
    "'অনলাইন সূত্রে প্রমাণিত' লেখা ফসলগুলোর পেছনে আলাদা প্রতিবেদন আছে। বাকি সবকিছু SRDI, BMD, "
    "WorldClim ও SoilGrids ডেটা দিয়ে যাচাই করে নিতে হবে।"
)

DATASET_CAUTION_EN = (
    "Caution: District soil/landform profiles, analog regions, and crop opportunities are preliminary "
    "district-level estimates. Similarity percentages and financial returns are unverified, and soil "
    "conditions vary by upazila within the same district. Only items marked with online evidence have "
    "published reports; verify all decisions with SRDI, BMD, BARC Crop Zoning, WorldClim, and SoilGrids."
)

VERIFICATION_REQUIREMENTS: tuple[dict[str, str], ...] = (
    {
        "id": "upazila-grid-matching",
        "en": "Upazila-level matching (>490 upazilas) requires computational alignment of monthly weather (BMD / NASA POWER / WorldClim) and SRDI / SoilGrids soil properties rather than manual estimation.",
        "bn": "উপজেলা পর্যায়ে (৪৯০টির বেশি) মিল বের করতে প্রতিটি উপজেলার মাসিক আবহাওয়া ও SRDI মাটির তথ্য আর বিশ্বের গ্রিড তথ্য (WorldClim, SoilGrids) কম্পিউটারে মেলাতে হবে। হাতে লিখে এটা সঠিকভাবে সম্ভব নয়।",
    },
    {
        "id": "seed-quarantine-registration",
        "en": "Introducing new seeds or saplings requires Plant Quarantine Wing approval and National Seed Board registration.",
        "bn": "নতুন বীজ বা চারা আনতে উদ্ভিদ সংগনিরোধ অনুমোদন ও জাতীয় বীজ বোর্ডের নিবন্ধন লাগে।",
    },
    {
        "id": "photoperiod-pest-difference",
        "en": "Distant climate-analog regions may still differ in day length (photoperiod), rainfall timing, and local pest or disease pressure.",
        "bn": "দূরের এলাকার ক্ষেত্রে দিনের দৈর্ঘ্য, বৃষ্টির ধরন ও রোগ-পোকার পার্থক্য থাকতে পারে।",
    },
)

NATIONAL_IMPORT_SUBSTITUTION_CONTEXT: dict[str, Any] = {
    "edible_oil_import_share_pct": 90,
    "domestic_soybean_demand_met_pct": 7,
    "projected_pulse_deficit_2030_lakh_tonnes": 12.36,
    "summary_en": (
        "National import-substitution context: Bangladesh imports ~90% of edible oil and meets only ~7% "
        "of domestic soybean demand locally; pulse deficit may reach 12.36 lakh tonnes by 2030 (The Daily Star, USDA)."
    ),
    "summary_bn": (
        "আমদানি-নির্ভর ফসল: ভোজ্যতেলের প্রায় ৯০ শতাংশ আমদানি হয়; দেশের সয়াবিন চাহিদার মাত্র ৭ শতাংশ মেটায়; "
        "২০৩০ সালে ডালের ঘাটতি ১২.৩৬ লাখ টন হতে পারে (The Daily Star, USDA)।"
    ),
    "sources": ["The Daily Star", "USDA"],
}

ONLINE_EVIDENCE_NOTES: dict[str, dict[str, str]] = {
    "dragon-fruit-barind": {
        "id": "dragon-fruit-barind",
        "title_en": "Dragon Fruit in Naogaon–Rajshahi",
        "title_bn": "ড্রাগন ফ্রুট (নওগাঁ-রাজশাহী)",
        "detail_en": "From nearly zero in 2012 to ~100,000 tonnes/year nationally (The Daily Star, February 2026).",
        "detail_bn": "২০১২ সালে প্রায় ছিল না, এখন বছরে প্রায় এক লাখ টন (The Daily Star, ফেব্রুয়ারি ২০২৬)।",
        "source_url": "https://www.thedailystar.net/business/news/fruits-now-always-season-4105441",
    },
    "katimon-mango-rajshahi": {
        "id": "katimon-mango-rajshahi",
        "title_en": "Katimon Off-Season Mango (Rajshahi Region)",
        "title_bn": "কাতিমন আম (রাজশাহী অঞ্চল)",
        "detail_en": "Produces fruit outside the main season and fetches 3–5x regular seasonal price (The Daily Star).",
        "detail_bn": "মৌসুমের বাইরে ফলে, সাধারণ দামের তিন থেকে পাঁচ গুণ দাম পায় (The Daily Star)।",
        "source_url": "https://www.thedailystar.net/business/news/fruits-now-always-season-4105441",
    },
    "avocado-coffee-naogaon": {
        "id": "avocado-coffee-naogaon",
        "title_en": "Avocado (Sapahar, Naogaon) & Robusta Coffee (Naogaon)",
        "title_bn": "অ্যাভোকাডো (নওগাঁর সাপাহার) ও রোবাস্টা কফি (নওগাঁ)",
        "detail_en": "Early-stage demonstration cultivation under the PKSF-PACE project.",
        "detail_bn": "PKSF-PACE প্রকল্পের ডেমো চাষ, প্রাথমিক পর্যায়ে।",
        "source_url": "https://pksf.org.bd/?p=11130",
    },
    "red-mango-patuakhali": {
        "id": "red-mango-patuakhali",
        "title_en": "Exotic Red Mango Trial at BARI Lebukhali (Dumki, Patuakhali)",
        "title_bn": "বিদেশি লাল আম (মিয়াজাকি, চিয়াং মাই প্রভৃতি — পটুয়াখালী)",
        "detail_en": "Performed well in saline and waterlogged soil trials at BARI Lebukhali center, Dumki, Patuakhali (UNB; Dhaka Tribune, July 2026).",
        "detail_bn": "BARI-র লেবুখালী কেন্দ্রে (দুমকি, পটুয়াখালী) লবণাক্ত ও জলাবদ্ধ জমিতে ট্রায়ালে ভালো করেছে (UNB; Dhaka Tribune, জুলাই ২০২৬)।",
        "source_url": "https://www.dhakatribune.com/",
    },
}


@dataclass(frozen=True)
class DistrictProfile:
    id: str
    name_en: str
    name_bn: str
    division_en: str
    division_bn: str
    latitude: float
    longitude: float
    bamis_region: str
    landform_bn: str
    landform_en: str
    analog_regions_bn: str
    analog_regions_en: str
    established_crops_bn: tuple[str, ...]
    established_crops_en: tuple[str, ...]
    opportunity_crops_bn: tuple[str, ...]
    opportunity_crops_en: tuple[str, ...]
    bare_field_risk_en: str
    bare_field_risk_bn: str
    online_evidence_ids: tuple[str, ...] = ()


DIVISION_COORDINATES: dict[str, dict[str, Any]] = {
    "rangpur": {"name_en": "Rangpur Division", "name_bn": "রংপুর বিভাগ", "latitude": 25.7439, "longitude": 89.2752, "representative_district": "rangpur"},
    "rajshahi": {"name_en": "Rajshahi Division", "name_bn": "রাজশাহী বিভাগ", "latitude": 24.3745, "longitude": 88.6042, "representative_district": "rajshahi"},
    "khulna": {"name_en": "Khulna Division", "name_bn": "খুলনা বিভাগ", "latitude": 22.8456, "longitude": 89.5403, "representative_district": "khulna"},
    "barishal": {"name_en": "Barishal Division", "name_bn": "বরিশাল বিভাগ", "latitude": 22.7010, "longitude": 90.3535, "representative_district": "barishal"},
    "chattogram": {"name_en": "Chattogram Division", "name_bn": "চট্টগ্রাম বিভাগ", "latitude": 22.3569, "longitude": 91.7832, "representative_district": "chattogram"},
    "sylhet": {"name_en": "Sylhet Division", "name_bn": "সিলেট বিভাগ", "latitude": 24.8949, "longitude": 91.8687, "representative_district": "sylhet"},
    "dhaka": {"name_en": "Dhaka Division", "name_bn": "ঢাকা বিভাগ", "latitude": 23.8103, "longitude": 90.4125, "representative_district": "dhaka"},
    "mymensingh": {"name_en": "Mymensingh Division", "name_bn": "ময়মনসিংহ বিভাগ", "latitude": 24.7471, "longitude": 90.4203, "representative_district": "mymensingh"},
}


DISTRICTS: tuple[DistrictProfile, ...] = (
    # 1. Rangpur Division (8 districts)
    DistrictProfile(
        id="panchagarh", name_en="Panchagarh", name_bn="পঞ্চগড়",
        division_en="Rangpur", division_bn="রংপুর", latitude=26.3354, longitude=88.5517, bamis_region="Dinajpur",
        landform_bn="হিমালয়ের পাদদেশ, উঁচু পলিমাটি, শীতল শীত",
        landform_en="Himalayan piedmont plain, high alluvial soil, cool winter",
        analog_regions_bn="জলপাইগুড়ি, দার্জিলিং তরাই (প.ব.), ঝাপা (নেপাল)",
        analog_regions_en="Jalpaiguri, Darjeeling Terai (West Bengal), Jhapa (Nepal)",
        established_crops_bn=("চা", "আলু", "ধান"),
        established_crops_en=("Tea", "Potato", "Rice"),
        opportunity_crops_bn=("সুগন্ধি ধান", "ভুট্টা", "শীতকালীন সবজি"),
        opportunity_crops_en=("Aromatic rice", "Maize", "Winter vegetables"),
        bare_field_risk_en="Late-winter to pre-monsoon dry window (Feb–Apr) when sandy piedmont topsoil loses moisture rapidly after potato harvest.",
        bare_field_risk_bn="আলু তোলার পর ফেব্রুয়ারি–এপ্রিল শুষ্ক মৌসুমে উঁচু বেলে-পলিমাটিতে দ্রুত আর্দ্রতা কমে জমি খালি থাকার ঝুঁকি থাকে।",
    ),
    DistrictProfile(
        id="thakurgaon", name_en="Thakurgaon", name_bn="ঠাকুরগাঁও",
        division_en="Rangpur", division_bn="রংপুর", latitude=26.0337, longitude=88.4617, bamis_region="Dinajpur",
        landform_bn="পুরোনো পলিমাটি, বেলে-দোআঁশ",
        landform_en="Old alluvial floodplain, sandy loam",
        analog_regions_bn="উত্তর দিনাজপুর, কোচবিহার (প.ব.)",
        analog_regions_en="North Dinajpur, Cooch Behar (West Bengal)",
        established_crops_bn=("ধান", "আলু", "ভুট্টা"),
        established_crops_en=("Rice", "Potato", "Maize"),
        opportunity_crops_bn=("সুগন্ধি ধান", "ডাল"),
        opportunity_crops_en=("Aromatic rice", "Pulses"),
        bare_field_risk_en="Pre-monsoon Kharif-1 transition (Mar–May) on sandy-loam plots where short-duration pulses can cover bare soil.",
        bare_field_risk_bn="মার্চ–মে প্রাক-বর্ষা মৌসুমে বেলে-দোআঁশ জমি খালি না রেখে স্বল্পমেয়াদি ডাল ফসল যাচাই করা যায়।",
    ),
    DistrictProfile(
        id="dinajpur", name_en="Dinajpur", name_bn="দিনাজপুর",
        division_en="Rangpur", division_bn="রংপুর", latitude=25.6279, longitude=88.6332, bamis_region="Dinajpur",
        landform_bn="উঁচু পলিমাটি, বরেন্দ্রের উত্তর কিনারা",
        landform_en="High alluvial soil, northern edge of Barind tract",
        analog_regions_bn="দক্ষিণ দিনাজপুর, মালদা (প.ব.)",
        analog_regions_en="South Dinajpur, Malda (West Bengal)",
        established_crops_bn=("লিচু", "আম", "সুগন্ধি ধান"),
        established_crops_en=("Lychee", "Mango", "Aromatic rice"),
        opportunity_crops_bn=("ভুট্টা", "ডাল", "লিচুর নতুন জাত"),
        opportunity_crops_en=("Maize", "Pulses", "Improved lychee varieties"),
        bare_field_risk_en="Post-Aman harvest window (Nov–Dec) on higher Barind-edge plots where residual soil moisture drops quickly.",
        bare_field_risk_bn="আমন কাটার পর (নভেম্বর–ডিসেম্বর) বরেন্দ্র কিনারার উঁচু জমিতে মাটির রস দ্রুত কমে যায়।",
    ),
    DistrictProfile(
        id="nilphamari", name_en="Nilphamari", name_bn="নীলফামারী",
        division_en="Rangpur", division_bn="রংপুর", latitude=25.9318, longitude=88.8560, bamis_region="Rangpur",
        landform_bn="তিস্তা প্লাবনভূমি, বেলে-দোআঁশ",
        landform_en="Teesta floodplain, sandy loam",
        analog_regions_bn="কোচবিহার (প.ব.), ধুবড়ি (অসম)",
        analog_regions_en="Cooch Behar (West Bengal), Dhubri (Assam)",
        established_crops_bn=("আলু", "ধান", "ভুট্টা"),
        established_crops_en=("Potato", "Rice", "Maize"),
        opportunity_crops_bn=("চরে চিনাবাদাম", "ভুট্টা"),
        opportunity_crops_en=("Char-land groundnut", "Maize"),
        bare_field_risk_en="Receding floodwater window on Teesta sandy-loam and char lands (Nov–Mar) prone to wind/water erosion if left bare.",
        bare_field_risk_bn="তিস্তা অববাহিকায় পানি নামার পর (নভেম্বর–মার্চ) বেলে-দোআঁশ ও চর জমি খালি থাকলে ক্ষয় ও রসের ঘাটতি বাড়ে।",
    ),
    DistrictProfile(
        id="rangpur", name_en="Rangpur", name_bn="রংপুর",
        division_en="Rangpur", division_bn="রংপুর", latitude=25.7439, longitude=89.2752, bamis_region="Rangpur",
        landform_bn="তিস্তা প্লাবনভূমি",
        landform_en="Teesta floodplain",
        analog_regions_bn="কোচবিহার, ধুবড়ি",
        analog_regions_en="Cooch Behar (West Bengal), Dhubri (Assam)",
        established_crops_bn=("তামাক", "আলু", "ধান"),
        established_crops_en=("Tobacco", "Potato", "Rice"),
        opportunity_crops_bn=("ভুট্টা", "সবজি"),
        opportunity_crops_en=("Maize", "Vegetables"),
        bare_field_risk_en="Post-Rabi harvest transition (Apr–Jun) and nutrient depletion after intensive potato/tobacco sequences.",
        bare_field_risk_bn="রবি ফসল ও তামাক/আলুর পর (এপ্রিল–জুন) জমির জৈব পদার্থ ও পুষ্টি ঘাটতি কমাতে ফসল পর্যায় জরুরি।",
    ),
    DistrictProfile(
        id="lalmonirhat", name_en="Lalmonirhat", name_bn="লালমনিরহাট",
        division_en="Rangpur", division_bn="রংপুর", latitude=25.9165, longitude=89.4532, bamis_region="Rangpur",
        landform_bn="তিস্তা চর, বেলে মাটি",
        landform_en="Teesta river char, sandy soil",
        analog_regions_bn="ধুবড়ি, মাজুলি (অসম)",
        analog_regions_en="Dhubri, Majuli (Assam)",
        established_crops_bn=("ভুট্টা", "তামাক", "আলু"),
        established_crops_en=("Maize", "Tobacco", "Potato"),
        opportunity_crops_bn=("চিনাবাদাম", "তরমুজ"),
        opportunity_crops_en=("Groundnut", "Watermelon"),
        bare_field_risk_en="Dry-season sandy char exposure (Nov–Apr) where low water-holding capacity stresses high-water crops.",
        bare_field_risk_bn="শীত ও গ্রীষ্মের শুরুতে তিস্তার বেলে চরে পানির ধারণক্ষমতা কম থাকায় খরা-সহনশীল আচ্ছাদন ফসল দরকার।",
    ),
    DistrictProfile(
        id="kurigram", name_en="Kurigram", name_bn="কুড়িগ্রাম",
        division_en="Rangpur", division_bn="রংপুর", latitude=25.8054, longitude=89.6362, bamis_region="Rangpur",
        landform_bn="ব্রহ্মপুত্র চর, বন্যাপ্রবণ",
        landform_en="Brahmaputra river char, flood-prone",
        analog_regions_bn="মাজুলি, ধুবড়ি (অসম)",
        analog_regions_en="Majuli, Dhubri (Assam)",
        established_crops_bn=("ধান", "ভুট্টা", "পাট"),
        established_crops_en=("Rice", "Maize", "Jute"),
        opportunity_crops_bn=("চরে বাদাম", "কুমড়া", "বন্যাসহনশীল ধান"),
        opportunity_crops_en=("Char-land groundnut", "Pumpkin", "Flood-tolerant rice"),
        bare_field_risk_en="Monsoon flood submergence (Jul–Sep) followed by post-flood sand deposition on Brahmaputra chars.",
        bare_field_risk_bn="বর্ষায় ব্রহ্মপুত্রের বন্যা (জুলাই–সেপ্টেম্বর) এবং পানি নামার পর বালুচর খালি থাকার ঝুঁকি থাকে।",
    ),
    DistrictProfile(
        id="gaibandha", name_en="Gaibandha", name_bn="গাইবান্ধা",
        division_en="Rangpur", division_bn="রংপুর", latitude=25.3288, longitude=89.5281, bamis_region="Rangpur",
        landform_bn="ব্রহ্মপুত্র-যমুনা চর",
        landform_en="Brahmaputra-Jamuna river char",
        analog_regions_bn="ধুবড়ি (অসম)",
        analog_regions_en="Dhubri (Assam)",
        established_crops_bn=("ধান", "ভুট্টা", "পাট"),
        established_crops_en=("Rice", "Maize", "Jute"),
        opportunity_crops_bn=("চরে ভুট্টা", "তরমুজ"),
        opportunity_crops_en=("Char-land maize", "Watermelon"),
        bare_field_risk_en="Post-flood char emergence (Oct–Nov) and late dry season heat stress before monsoon onset.",
        bare_field_risk_bn="বন্যার পানি নামার পর (অক্টোবর–নভেম্বর) চরের জমিতে দ্রুত আচ্ছাদন ও রস সংরক্ষণ প্রয়োজন।",
    ),

    # 2. Rajshahi Division (8 districts)
    DistrictProfile(
        id="rajshahi", name_en="Rajshahi", name_bn="রাজশাহী",
        division_en="Rajshahi", division_bn="রাজশাহী", latitude=24.3745, longitude=88.6042, bamis_region="Rajshahi",
        landform_bn="গঙ্গা প্লাবনভূমি ও বরেন্দ্র, শুষ্ক শীত",
        landform_en="Ganges floodplain & Barind tract, dry winter",
        analog_regions_bn="মালদা, মুর্শিদাবাদ (প.ব.)",
        analog_regions_en="Malda, Murshidabad (West Bengal)",
        established_crops_bn=("আম", "ধান", "লিচু"),
        established_crops_en=("Mango", "Rice", "Lychee"),
        opportunity_crops_bn=("ড্রাগন ফ্রুট", "বিদেশি আম", "ডালিম"),
        opportunity_crops_en=("Dragon fruit", "Exotic mango", "Pomegranate"),
        bare_field_risk_en="Post-Aman dry Rabi/Kharif-1 window (Nov–May) in the Barind tract where low rainfall and heat stress leave non-irrigated plots bare.",
        bare_field_risk_bn="আমন ধান কাটার পর (নভেম্বর–মে) বরেন্দ্র অঞ্চলে শুষ্ক শীত ও তীব্র গরমে সেচবিহীন জমি পতিত থাকার ঝুঁকি থাকে।",
        online_evidence_ids=("dragon-fruit-barind", "katimon-mango-rajshahi"),
    ),
    DistrictProfile(
        id="naogaon", name_en="Naogaon", name_bn="নওগাঁ",
        division_en="Rajshahi", division_bn="রাজশাহী", latitude=24.7936, longitude=88.9318, bamis_region="Rajshahi",
        landform_bn="বরেন্দ্র, লালচে-বাদামি মাটি",
        landform_en="Barind tract, reddish-brown terrace soil",
        analog_regions_bn="বীরভূম, বাঁকুড়া (প.ব.)",
        analog_regions_en="Birbhum, Bankura (West Bengal)",
        established_crops_bn=("ধান", "আম", "আলু"),
        established_crops_en=("Rice", "Mango", "Potato"),
        opportunity_crops_bn=("ড্রাগন ফ্রুট", "অ্যাভোকাডো", "কফি (অনলাইন সূত্রে প্রমাণিত)", "আঙুর (পাইলট)"),
        opportunity_crops_en=("Dragon fruit", "Avocado", "Coffee (online-evidenced demo)", "Grape (pilot)"),
        bare_field_risk_en="High Barind terrace dry season (Dec–May) where continuous rice-rice depletes groundwater and leaves unirrigated terraces bare.",
        bare_field_risk_bn="উঁচু বরেন্দ্র ভূমিতে ডিসেম্বর–মে শুষ্ক মৌসুমে অতিরিক্ত সেচনির্ভর বোরোর বদলে কম পানির ফসল ও মালচিং প্রয়োজন।",
        online_evidence_ids=("dragon-fruit-barind", "avocado-coffee-naogaon"),
    ),
    DistrictProfile(
        id="natore", name_en="Natore", name_bn="নাটোর",
        division_en="Rajshahi", division_bn="রাজশাহী", latitude=24.4206, longitude=89.0006, bamis_region="Rajshahi",
        landform_bn="গঙ্গা প্লাবনভূমি, বরেন্দ্রের কিনারা",
        landform_en="Ganges floodplain, Barind margin",
        analog_regions_bn="মুর্শিদাবাদ, মালদা",
        analog_regions_en="Murshidabad, Malda (West Bengal)",
        established_crops_bn=("আম", "ধান", "সবজি"),
        established_crops_en=("Mango", "Rice", "Vegetables"),
        opportunity_crops_bn=("কাতিমন আম", "ড্রাগন ফ্রুট"),
        opportunity_crops_en=("Katimon off-season mango", "Dragon fruit"),
        bare_field_risk_en="Transition between Chalan Beel drainage recession (Nov) and pre-monsoon heat stress (Apr–May).",
        bare_field_risk_bn="বিল ও প্লাবনভূমি থেকে পানি নামার পর এবং গ্রীষ্মের খরায় জমির আর্দ্রতা ধরে রাখা গুরুত্বপূর্ণ।",
        online_evidence_ids=("katimon-mango-rajshahi",),
    ),
    DistrictProfile(
        id="chapainawabganj", name_en="Chapainawabganj", name_bn="চাঁপাইনবাবগঞ্জ",
        division_en="Rajshahi", division_bn="রাজশাহী", latitude=24.5965, longitude=88.2775, bamis_region="Rajshahi",
        landform_bn="গঙ্গা প্লাবনভূমি ও বরেন্দ্র",
        landform_en="Ganges floodplain & Barind tract",
        analog_regions_bn="মালদা (প.ব.)",
        analog_regions_en="Malda (West Bengal)",
        established_crops_bn=("আম (বিখ্যাত)", "ধান", "কলা"),
        established_crops_en=("Mango (renowned)", "Rice", "Banana"),
        opportunity_crops_bn=("কাতিমন আম", "বিদেশি আম"),
        opportunity_crops_en=("Katimon off-season mango", "Exotic mango"),
        bare_field_risk_en="Severe dry-season evaporative stress (Feb–May) in Barind uplands and inter-row bare soil in young orchards.",
        bare_field_risk_bn="ফাল্গুন–চৈত্রের তীব্র খরা ও তাপপ্রবাহে বরেন্দ্র ও নতুন বাগানের মধ্যবর্তী খালি মাটিতে রস দ্রুত শুকিয়ে যায়।",
        online_evidence_ids=("katimon-mango-rajshahi",),
    ),
    DistrictProfile(
        id="pabna", name_en="Pabna", name_bn="পাবনা",
        division_en="Rajshahi", division_bn="রাজশাহী", latitude=24.0064, longitude=89.2372, bamis_region="Rajshahi",
        landform_bn="যমুনা-পদ্মা প্লাবনভূমি",
        landform_en="Jamuna-Padma floodplain",
        analog_regions_bn="নদীয়া (প.ব.)",
        analog_regions_en="Nadia (West Bengal)",
        established_crops_bn=("ধান", "পাট", "সরিষা"),
        established_crops_en=("Rice", "Jute", "Mustard"),
        opportunity_crops_bn=("ডাল", "পেঁয়াজ"),
        opportunity_crops_en=("Pulses", "Onion"),
        bare_field_risk_en="Short turnaround window between Aman harvest, Rabi mustard/pulses, and Kharif-1 jute.",
        bare_field_risk_bn="আমন কাটার পর রবি সরিষা/ডাল ও পাটের মধ্যবর্তী সময়ে মাটির রস সংরক্ষণ জরুরি।",
    ),
    DistrictProfile(
        id="sirajganj", name_en="Sirajganj", name_bn="সিরাজগঞ্জ",
        division_en="Rajshahi", division_bn="রাজশাহী", latitude=24.4534, longitude=89.7007, bamis_region="Bogura",
        landform_bn="যমুনা চর ও প্লাবনভূমি",
        landform_en="Jamuna river char & floodplain",
        analog_regions_bn="ধুবড়ির ব্রহ্মপুত্র চর (অসম)",
        analog_regions_en="Brahmaputra char of Dhubri (Assam)",
        established_crops_bn=("ধান", "পাট", "সরিষা"),
        established_crops_en=("Rice", "Jute", "Mustard"),
        opportunity_crops_bn=("মরিচ", "ভুট্টা"),
        opportunity_crops_en=("Chili", "Maize"),
        bare_field_risk_en="Monsoon flooding on Jamuna chars (Jul–Sep) followed by rapid sand drying in late Rabi.",
        bare_field_risk_bn="বর্ষায় যমুনা চরে প্লাবন এবং পানি নামার পর বেলে চরে দ্রুত রস কমে যাওয়ার ঝুঁকি থাকে।",
    ),
    DistrictProfile(
        id="bogura", name_en="Bogura", name_bn="বগুড়া",
        division_en="Rajshahi", division_bn="রাজশাহী", latitude=24.8465, longitude=89.3773, bamis_region="Bogura",
        landform_bn="করতোয়া প্লাবনভূমি",
        landform_en="Karatoya floodplain",
        analog_regions_bn="নিম্ন অসম, কাটিহার (বিহার)",
        analog_regions_en="Lower Assam, Katihar (Bihar)",
        established_crops_bn=("ধান", "আলু", "সবজি"),
        established_crops_en=("Rice", "Potato", "Vegetables"),
        opportunity_crops_bn=("ভুট্টা", "সবজি রপ্তানি"),
        opportunity_crops_en=("Maize", "Export-grade vegetables"),
        bare_field_risk_en="Intensive potato-rice sequence leaves low organic matter and disease carryover risk if legume/pulse breaks are omitted.",
        bare_field_risk_bn="টানা আলু-ধান চাষে মাটির জৈব পদার্থ হ্রাস ও রোগবালাইয়ের ঝুঁকি থাকে; মাঝখানে ডাল বা সবজি পর্যায় উপকারী।",
    ),
    DistrictProfile(
        id="joypurhat", name_en="Joypurhat", name_bn="জয়পুরহাট",
        division_en="Rajshahi", division_bn="রাজশাহী", latitude=25.0968, longitude=89.0227, bamis_region="Bogura",
        landform_bn="বরেন্দ্রের কিনারা",
        landform_en="Barind tract margin",
        analog_regions_bn="মালদা, উত্তর দিনাজপুর",
        analog_regions_en="Malda, North Dinajpur (West Bengal)",
        established_crops_bn=("ধান", "আলু", "ভুট্টা"),
        established_crops_en=("Rice", "Potato", "Maize"),
        opportunity_crops_bn=("ভুট্টা", "ডাল"),
        opportunity_crops_en=("Maize", "Pulses"),
        bare_field_risk_en="Late-spring window (Apr–May) after potato/maize harvest when soil surface heats up before Aman transplanting.",
        bare_field_risk_bn="আলু বা ভুট্টা তোলার পর আমন রোপণের আগে (এপ্রিল–মে) জমি খালি থাকলে মাটির তাপ ও রস ঘাটতি বাড়ে।",
    ),

    # 3. Khulna Division (10 districts)
    DistrictProfile(
        id="khulna", name_en="Khulna", name_bn="খুলনা",
        division_en="Khulna", division_bn="খুলনা", latitude=22.8456, longitude=89.5403, bamis_region="Khulna",
        landform_bn="জোয়ার-ভাটার ব-দ্বীপ, লবণাক্ত",
        landform_en="Tidal delta, saline",
        analog_regions_bn="দক্ষিণ ২৪ পরগনা, মেকং ডেল্টা",
        analog_regions_en="South 24 Parganas (West Bengal), Mekong Delta",
        established_crops_bn=("চিংড়ি", "ধান"),
        established_crops_en=("Shrimp", "Rice"),
        opportunity_crops_bn=("লবণসহনশীল ধান", "ঘেরের আইলে সবজি"),
        opportunity_crops_en=("Salt-tolerant rice", "Dyke/gher-embankment vegetables"),
        bare_field_risk_en="Dry-season soil salinity peak (Jan–May) after Aman harvest leaves vast tidal polder lands bare and crusted with salt.",
        bare_field_risk_bn="আমন কাটার পর শুষ্ক মৌসুমে (জানুয়ারি–মে) লবণাক্ততা বেড়ে যাওয়ায় উপকূলীয় অনেক জমি পতিত থাকে।",
    ),
    DistrictProfile(
        id="bagerhat", name_en="Bagerhat", name_bn="বাগেরহাট",
        division_en="Khulna", division_bn="খুলনা", latitude=22.6516, longitude=89.7859, bamis_region="Khulna",
        landform_bn="জোয়ার-ভাটার ব-দ্বীপ, লবণাক্ত",
        landform_en="Tidal delta, saline",
        analog_regions_bn="দক্ষিণ ২৪ পরগনা, সক ট্রাং (ভিয়েতনাম)",
        analog_regions_en="South 24 Parganas (West Bengal), Soc Trang (Vietnam)",
        established_crops_bn=("চিংড়ি", "নারকেল", "ধান"),
        established_crops_en=("Shrimp", "Coconut", "Rice"),
        opportunity_crops_bn=("লবণসহনশীল ধান ও ফল",),
        opportunity_crops_en=("Salt-tolerant rice & fruits",),
        bare_field_risk_en="Dry-season salinity intrusion (Feb–May) and waterlogging in low polders limit dry-season crop cover.",
        bare_field_risk_bn="শুষ্ক মৌসুমে লবণাক্ততা বৃদ্ধি (ফেব্রুয়ারি–মে) এবং নিচু জমিতে জলাবদ্ধতা ফসল আচ্ছাদনে বাধা দেয়।",
    ),
    DistrictProfile(
        id="satkhira", name_en="Satkhira", name_bn="সাতক্ষীরা",
        division_en="Khulna", division_bn="খুলনা", latitude=22.7185, longitude=89.0705, bamis_region="Khulna",
        landform_bn="উপকূল, লবণাক্ত",
        landform_en="Coastal, saline",
        analog_regions_bn="সুন্দরবন-সংলগ্ন প.ব., বাক লিউ (ভিয়েতনাম)",
        analog_regions_en="Sundarbans-adjacent West Bengal, Bac Lieu (Vietnam)",
        established_crops_bn=("চিংড়ি", "ধান", "তরমুজ"),
        established_crops_en=("Shrimp", "Rice", "Watermelon"),
        opportunity_crops_bn=("লবণসহনশীল ধান", "নারকেল"),
        opportunity_crops_en=("Salt-tolerant rice", "Coconut"),
        bare_field_risk_en="High capillary salt rise on bare coastal plots during Feb–May; mulching and early residual-moisture crops are critical.",
        bare_field_risk_bn="ফেব্রুয়ারি–মে মাসে খালি জমিতে মাটির নিচ থেকে লবণ উঠে আসে; মালচিং ও লবণসহনশীল ফসল জরুরি।",
    ),
    DistrictProfile(
        id="jashore", name_en="Jashore", name_bn="যশোর",
        division_en="Khulna", division_bn="খুলনা", latitude=23.1664, longitude=89.2081, bamis_region="Jashore",
        landform_bn="নিচু পলিমাটি, নদী-প্লাবিত",
        landform_en="Low-lying alluvial, river-flooded",
        analog_regions_bn="উত্তর ২৪ পরগনা (প.ব.)",
        analog_regions_en="North 24 Parganas (West Bengal)",
        established_crops_bn=("ফুল", "সবজি", "খেজুর"),
        established_crops_en=("Flowers", "Vegetables", "Date palm"),
        opportunity_crops_bn=("ফুলের উচ্চমূল্যের জাত",),
        opportunity_crops_en=("High-value commercial flower varieties",),
        bare_field_risk_en="Waterlogged beel margins during late monsoon (Aug–Nov) and pest buildup in continuous vegetable beds.",
        bare_field_risk_bn="বর্ষার শেষে জলাবদ্ধতা এবং একই জমিতে বারবার সবজি চাষে রোগ-পোকার ঝুঁকি বাড়ে।",
    ),
    DistrictProfile(
        id="jhenaidah", name_en="Jhenaidah", name_bn="ঝিনাইদহ",
        division_en="Khulna", division_bn="খুলনা", latitude=23.5450, longitude=89.1726, bamis_region="Jashore",
        landform_bn="গঙ্গা প্লাবনভূমি, উঁচু",
        landform_en="High Ganges floodplain",
        analog_regions_bn="নদীয়া (প.ব.)",
        analog_regions_en="Nadia (West Bengal)",
        established_crops_bn=("কলা", "ডাল", "ভুট্টা"),
        established_crops_en=("Banana", "Pulses", "Maize"),
        opportunity_crops_bn=("কলা ও মসুর বাড়ানো",),
        opportunity_crops_en=("Expanding Banana & Lentil",),
        bare_field_risk_en="Pre-monsoon heat stress (Apr–May) on elevated calcareous floodplain soils.",
        bare_field_risk_bn="চৈত্র–বৈশাখের তীব্র গরমে উঁচু গঙ্গা প্লাবনভূমির মাটিতে দ্রুত রস কমে যায়।",
    ),
    DistrictProfile(
        id="magura", name_en="Magura", name_bn="মাগুরা",
        division_en="Khulna", division_bn="খুলনা", latitude=23.4873, longitude=89.4199, bamis_region="Jashore",
        landform_bn="নিচু পলিমাটি",
        landform_en="Low alluvial floodplain",
        analog_regions_bn="নদীয়া, উত্তর ২৪ পরগনা",
        analog_regions_en="Nadia, North 24 Parganas (West Bengal)",
        established_crops_bn=("ধান", "পাট", "সবজি"),
        established_crops_en=("Rice", "Jute", "Vegetables"),
        opportunity_crops_bn=("সবজি", "ফুল"),
        opportunity_crops_en=("Vegetables", "Flowers"),
        bare_field_risk_en="Short transition between Aman harvest and Rabi oilseeds/pulses (Nov) when drainage timing determines planting success.",
        bare_field_risk_bn="আমন কাটার পর রবি মৌসুমের শুরুতে পানি নিষ্কাশন দেরি হলে জমি খালি থাকার ঝুঁকি তৈরি হয়।",
    ),
    DistrictProfile(
        id="narail", name_en="Narail", name_bn="নড়াইল",
        division_en="Khulna", division_bn="খুলনা", latitude=23.1725, longitude=89.5127, bamis_region="Jashore",
        landform_bn="নিচু পলিমাটি, বিল",
        landform_en="Low alluvial soil, beel/wetland basin",
        analog_regions_bn="উত্তর ২৪ পরগনা",
        analog_regions_en="North 24 Parganas (West Bengal)",
        established_crops_bn=("ধান", "সবজি", "খেজুর"),
        established_crops_en=("Rice", "Vegetables", "Date palm"),
        opportunity_crops_bn=("মাছ-ধান", "সবজি"),
        opportunity_crops_en=("Integrated rice-fish culture", "Vegetables"),
        bare_field_risk_en="Prolonged monsoon standing water in beel basins restricts dryland Rabi crops unless raised beds or rice-fish are used.",
        bare_field_risk_bn="বিল অঞ্চলে দীর্ঘসময় পানি জমে থাকায় রবি মৌসুমে সাধারণ শুষ্ক ফসল করা কঠিন হয়।",
    ),
    DistrictProfile(
        id="kushtia", name_en="Kushtia", name_bn="কুষ্টিয়া",
        division_en="Khulna", division_bn="খুলনা", latitude=23.9013, longitude=89.1204, bamis_region="Jashore",
        landform_bn="গঙ্গা প্লাবনভূমি",
        landform_en="Ganges floodplain",
        analog_regions_bn="নদীয়া, মুর্শিদাবাদ",
        analog_regions_en="Nadia, Murshidabad (West Bengal)",
        established_crops_bn=("ধান", "আখ", "তামাক"),
        established_crops_en=("Rice", "Sugarcane", "Tobacco"),
        opportunity_crops_bn=("কলা", "মসুর"),
        opportunity_crops_en=("Banana", "Lentil"),
        bare_field_risk_en="Soil organic matter decline after tobacco/sugarcane and extreme pre-monsoon heat (Apr–May).",
        bare_field_risk_bn="তামাক ও আখ চাষের পর মাটির জৈব পদার্থ ধরে রাখতে মসুর বা ডাল জাতীয় ফসল যুক্ত করা প্রয়োজন।",
    ),
    DistrictProfile(
        id="meherpur", name_en="Meherpur", name_bn="মেহেরপুর",
        division_en="Khulna", division_bn="খুলনা", latitude=23.7622, longitude=88.6318, bamis_region="Jashore",
        landform_bn="গঙ্গা প্লাবনভূমি, উঁচু",
        landform_en="High Ganges floodplain",
        analog_regions_bn="নদীয়া",
        analog_regions_en="Nadia (West Bengal)",
        established_crops_bn=("ধান", "কলা", "ডাল"),
        established_crops_en=("Rice", "Banana", "Pulses"),
        opportunity_crops_bn=("মসুর", "ভুট্টা"),
        opportunity_crops_en=("Lentil", "Maize"),
        bare_field_risk_en="Low annual rainfall and hot dry spells (Mar–May) on high Ganges floodplain terraces.",
        bare_field_risk_bn="মার্চ–মে মাসের তীব্র গরম ও কম বৃষ্টিপাতে উঁচু জমিতে রসের ঘাটতি দেখা দেয়।",
    ),
    DistrictProfile(
        id="chuadanga", name_en="Chuadanga", name_bn="চুয়াডাঙ্গা",
        division_en="Khulna", division_bn="খুলনা", latitude=23.6402, longitude=88.8418, bamis_region="Jashore",
        landform_bn="গঙ্গা প্লাবনভূমি, উঁচু",
        landform_en="High Ganges floodplain",
        analog_regions_bn="নদীয়া",
        analog_regions_en="Nadia (West Bengal)",
        established_crops_bn=("ধান", "ভুট্টা", "তামাক"),
        established_crops_en=("Rice", "Maize", "Tobacco"),
        opportunity_crops_bn=("ভুট্টা", "মসুর", "কলা"),
        opportunity_crops_en=("Maize", "Lentil", "Banana"),
        bare_field_risk_en="Severe summer heatwave and winter cold snaps on western border high floodplain plots.",
        bare_field_risk_bn="গ্রীষ্মের তীব্র তাপপ্রবাহ ও শীতের শৈত্যপ্রবাহ—উভয় মৌসুমেই ফসলের সহনশীলতা যাচাই জরুরি।",
    ),

    # 4. Barishal Division (6 districts)
    DistrictProfile(
        id="barishal", name_en="Barishal", name_bn="বরিশাল",
        division_en="Barishal", division_bn="বরিশাল", latitude=22.7010, longitude=90.3535, bamis_region="Barishal",
        landform_bn="জোয়ার-ভাটার প্লাবনভূমি, মাঝারি লবণাক্ত",
        landform_en="Tidal floodplain, moderately saline",
        analog_regions_bn="মেকং ডেল্টা (বেন ত্রে), ইরাবতী ডেল্টা",
        analog_regions_en="Mekong Delta (Ben Tre), Irrawaddy Delta",
        established_crops_bn=("ধান", "পেয়ারা", "সুপারি"),
        established_crops_en=("Rice", "Guava", "Betel nut"),
        opportunity_crops_bn=("নারকেল", "লবণসহনশীল ফল"),
        opportunity_crops_en=("Coconut", "Salt-tolerant fruits"),
        bare_field_risk_en="Late drain-out of tidal clay soils in December delays Rabi planting, leaving fields fallow in dry months.",
        bare_field_risk_bn="ডিসেম্বরে জোয়ারের পানি দেরিতে নামার কারণে কাদামাটি ভেজা থাকে এবং রবি মৌসুমে অনেক জমি পতিত থাকে।",
    ),
    DistrictProfile(
        id="jhalokati", name_en="Jhalokati", name_bn="ঝালকাঠি",
        division_en="Barishal", division_bn="বরিশাল", latitude=22.6406, longitude=90.1987, bamis_region="Barishal",
        landform_bn="নিচু প্লাবনভূমি",
        landform_en="Low tidal floodplain",
        analog_regions_bn="বেন ত্রে (ভিয়েতনাম)",
        analog_regions_en="Ben Tre (Vietnam)",
        established_crops_bn=("পেয়ারা", "সুপারি", "ধান"),
        established_crops_en=("Guava", "Betel nut", "Rice"),
        opportunity_crops_bn=("পেয়ারা বারোমাসি", "থাই পেয়ারা"),
        opportunity_crops_en=("Year-round guava", "Thai guava"),
        bare_field_risk_en="Tidal waterlogging in monsoon and slow soil drying in early Rabi.",
        bare_field_risk_bn="বর্ষায় জোয়ারের জলাবদ্ধতা এবং শীতে মাটি দেরিতে শুকানোর ঝুঁকি থাকে।",
    ),
    DistrictProfile(
        id="pirojpur", name_en="Pirojpur", name_bn="পিরোজপুর",
        division_en="Barishal", division_bn="বরিশাল", latitude=22.5841, longitude=89.9720, bamis_region="Barishal",
        landform_bn="নিচু প্লাবনভূমি",
        landform_en="Low tidal floodplain",
        analog_regions_bn="বেন ত্রে",
        analog_regions_en="Ben Tre (Vietnam)",
        established_crops_bn=("পেয়ারা", "ধান", "সুপারি"),
        established_crops_en=("Guava", "Rice", "Betel nut"),
        opportunity_crops_bn=("থাই পেয়ারা", "নারকেল"),
        opportunity_crops_en=("Thai guava", "Coconut"),
        bare_field_risk_en="Low-lying peat and tidal basins stay waterlogged; raised-bed (sorjan) systems reduce bare-season loss.",
        bare_field_risk_bn="নিচু জমিতে জলাবদ্ধতার কারণে কান্দা বা সর্জন পদ্ধতি ছাড়া শুষ্ক মৌসুমের ফসল ঝুঁকিপূর্ণ হতে পারে।",
    ),
    DistrictProfile(
        id="patuakhali", name_en="Patuakhali", name_bn="পটুয়াখালী",
        division_en="Barishal", division_bn="বরিশাল", latitude=22.3596, longitude=90.3298, bamis_region="Barishal",
        landform_bn="উপকূল, লবণাক্ত ও জলাবদ্ধ",
        landform_en="Coastal, saline & waterlogged",
        analog_regions_bn="ইরাবতী ডেল্টা, মেকং ডেল্টা",
        analog_regions_en="Irrawaddy Delta, Mekong Delta",
        established_crops_bn=("তরমুজ", "মুগ ডাল", "ধান"),
        established_crops_en=("Watermelon", "Mungbean", "Rice"),
        opportunity_crops_bn=("বিদেশি লাল আম (BARI ট্রায়াল, অনলাইন সূত্রে)", "মাল্টা", "জাম্বুরা"),
        opportunity_crops_en=("Exotic red mango (BARI trial, online-evidenced)", "Malta", "Pomelo"),
        bare_field_risk_en="Post-Aman coastal salinity and pre-monsoon cyclone/tidal surge risk during late Rabi (Apr–May) mungbean harvest.",
        bare_field_risk_bn="আমন পরবর্তী লবণাক্ততা এবং এপ্রিল–মে মাসে মুগ ডাল তোলার সময় ঘূর্ণিঝড় বা জোয়ারের জলাবদ্ধতার ঝুঁকি থাকে।",
        online_evidence_ids=("red-mango-patuakhali",),
    ),
    DistrictProfile(
        id="barguna", name_en="Barguna", name_bn="বরগুনা",
        division_en="Barishal", division_bn="বরিশাল", latitude=22.1592, longitude=90.1255, bamis_region="Barishal",
        landform_bn="উপকূল, লবণাক্ত",
        landform_en="Coastal, saline",
        analog_regions_bn="ইরাবতী ডেল্টা",
        analog_regions_en="Irrawaddy Delta",
        established_crops_bn=("ধান", "মুগ ডাল", "নারকেল"),
        established_crops_en=("Rice", "Mungbean", "Coconut"),
        opportunity_crops_bn=("তরমুজ", "নারকেল"),
        opportunity_crops_en=("Watermelon", "Coconut"),
        bare_field_risk_en="Dry-season soil and canal salinity (Feb–May) leaves unmulched coastal fields bare after T. Aman.",
        bare_field_risk_bn="ফেব্রুয়ারি–মে মাসে খাল ও মাটির লবণাক্ততা বৃদ্ধির ফলে আমন-পরবর্তী অনেক জমি পতিত থাকে।",
    ),
    DistrictProfile(
        id="bhola", name_en="Bhola", name_bn="ভোলা",
        division_en="Barishal", division_bn="বরিশাল", latitude=22.6859, longitude=90.6482, bamis_region="Barishal",
        landform_bn="নদী-চর, লবণাক্ত",
        landform_en="Estuarine island char, saline",
        analog_regions_bn="ইরাবতী ডেল্টার চর",
        analog_regions_en="Irrawaddy Delta char islands",
        established_crops_bn=("ধান", "ডাল", "চিনাবাদাম"),
        established_crops_en=("Rice", "Pulses", "Groundnut"),
        opportunity_crops_bn=("চরে ডাল ও বাদাম",),
        opportunity_crops_en=("Char-land pulses & groundnut",),
        bare_field_risk_en="Estuarine char erosion in monsoon and coastal salinity in late Rabi.",
        bare_field_risk_bn="বর্ষায় নদীভাঙন ও জোয়ার এবং শুষ্ক মৌসুমে লবণাক্ততা চরের ফসল নির্বাচনের প্রধান বিবেচ্য।",
    ),

    # 5. Chattogram Division (11 districts)
    DistrictProfile(
        id="chattogram", name_en="Chattogram", name_bn="চট্টগ্রাম",
        division_en="Chattogram", division_bn="চট্টগ্রাম", latitude=22.3569, longitude=91.7832, bamis_region="Chattogram",
        landform_bn="পাহাড় ও উপকূল, অম্লীয় মাটি",
        landform_en="Hills & coastal plain, acidic soil",
        analog_regions_bn="রাখাইন (মিয়ানমার), মিজোরাম",
        analog_regions_en="Rakhine (Myanmar), Mizoram",
        established_crops_bn=("ধান", "সবজি", "ফল"),
        established_crops_en=("Rice", "Vegetables", "Fruits"),
        opportunity_crops_bn=("আনারস", "কাজু", "আম"),
        opportunity_crops_en=("Pineapple", "Cashew nut", "Mango"),
        bare_field_risk_en="Hillslope topsoil erosion during intense monsoon bursts (Jun–Aug) and dry-season coastal salinity.",
        bare_field_risk_bn="বর্ষায় পাহাড়ি ঢালে ভূমিধস ও মাটি ক্ষয় এবং উপকূলীয় অংশে শুষ্ক মৌসুমে লবণাক্ততার ঝুঁকি থাকে।",
    ),
    DistrictProfile(
        id="coxs-bazar", name_en="Cox's Bazar", name_bn="কক্সবাজার",
        division_en="Chattogram", division_bn="চট্টগ্রাম", latitude=21.4272, longitude=92.0058, bamis_region="Chattogram",
        landform_bn="উপকূল, বেলে মাটি",
        landform_en="Coastal plain, sandy soil",
        analog_regions_bn="রাখাইন, কেরালা উপকূল",
        analog_regions_en="Rakhine (Myanmar), Kerala Coast",
        established_crops_bn=("ধান", "তরমুজ", "সবজি"),
        established_crops_en=("Rice", "Watermelon", "Vegetables"),
        opportunity_crops_bn=("নারকেল", "কাজু", "সুপারি"),
        opportunity_crops_en=("Coconut", "Cashew nut", "Betel nut"),
        bare_field_risk_en="Rapid moisture loss and salt spray on sandy coastal plots between January and May.",
        bare_field_risk_bn="জানুয়ারি–মে মাসে উপকূলীয় বেলে মাটিতে দ্রুত রস কমে যাওয়া ও লবণাক্ত বাতাসের প্রভাব থাকে।",
    ),
    DistrictProfile(
        id="bandarban", name_en="Bandarban", name_bn="বান্দরবান",
        division_en="Chattogram", division_bn="চট্টগ্রাম", latitude=22.1953, longitude=92.2184, bamis_region="Rangamati",
        landform_bn="উঁচু পাহাড়, অম্লীয়, বেশি বৃষ্টি",
        landform_en="High hills, acidic soil, high rainfall",
        analog_regions_bn="মিজোরাম, চিন পাহাড় (মিয়ানমার)",
        analog_regions_en="Mizoram, Chin Hills (Myanmar)",
        established_crops_bn=("আদা", "হলুদ", "আনারস"),
        established_crops_en=("Ginger", "Turmeric", "Pineapple"),
        opportunity_crops_bn=("কফি (ছোট পরিসরে আছে)", "কাজু", "ড্রাগন ফ্রুট"),
        opportunity_crops_en=("Coffee (existing small-scale)", "Cashew nut", "Dragon fruit"),
        bare_field_risk_en="Severe sheet and gully erosion on bare hill slopes during heavy monsoon rain; perennial cover/agroforestry is critical.",
        bare_field_risk_bn="ভারী বর্ষায় পাহাড়ের ঢালে মাটি আলগা বা খালি থাকলে তীব্র ভূমিক্ষয় হয়; বহুবর্ষজীবী ফসল ও মালচিং জরুরি।",
    ),
    DistrictProfile(
        id="rangamati", name_en="Rangamati", name_bn="রাঙামাটি",
        division_en="Chattogram", division_bn="চট্টগ্রাম", latitude=22.7324, longitude=92.2985, bamis_region="Rangamati",
        landform_bn="পাহাড়, অম্লীয়, বেশি বৃষ্টি",
        landform_en="Hills, acidic soil, high rainfall",
        analog_regions_bn="মিজোরাম, ত্রিপুরা",
        analog_regions_en="Mizoram, Tripura",
        established_crops_bn=("আনারস", "আদা", "আম"),
        established_crops_en=("Pineapple", "Ginger", "Mango"),
        opportunity_crops_bn=("আদা-হলুদ", "কাজু", "রাবার"),
        opportunity_crops_en=("Ginger-turmeric", "Cashew nut", "Rubber"),
        bare_field_risk_en="Slope erosion during monsoon downpours and dry winter water scarcity on ridge tops (Jan–Apr).",
        bare_field_risk_bn="বর্ষায় পাহাড়ি ঢালে মাটি ক্ষয় এবং শুষ্ক মৌসুমে (জানুয়ারি–এপ্রিল) পাহাড়ের চূড়ায় পানির সংকট দেখা দেয়।",
    ),
    DistrictProfile(
        id="khagrachhari", name_en="Khagrachhari", name_bn="খাগড়াছড়ি",
        division_en="Chattogram", division_bn="চট্টগ্রাম", latitude=23.1193, longitude=91.9847, bamis_region="Rangamati",
        landform_bn="পাহাড়, অম্লীয়",
        landform_en="Hills, acidic soil",
        analog_regions_bn="ত্রিপুরা",
        analog_regions_en="Tripura",
        established_crops_bn=("আনারস", "কলা", "রাবার"),
        established_crops_en=("Pineapple", "Banana", "Rubber"),
        opportunity_crops_bn=("আদা", "হলুদ", "কাজু"),
        opportunity_crops_en=("Ginger", "Turmeric", "Cashew nut"),
        bare_field_risk_en="Acidic hill soil nutrient leaching and erosion when root/rhizome crops are harvested across the slope.",
        bare_field_risk_bn="পাহাড়ের ঢালে কন্দজাত ফসল তোলার সময় মাটি ক্ষয় ও অম্লীয় মাটিতে পুষ্টি ধুয়ে যাওয়ার ঝুঁকি থাকে।",
    ),
    DistrictProfile(
        id="feni", name_en="Feni", name_bn="ফেনী",
        division_en="Chattogram", division_bn="চট্টগ্রাম", latitude=23.0159, longitude=91.3976, bamis_region="Chattogram",
        landform_bn="নিচু প্লাবনভূমি, উপকূলের কিনারা",
        landform_en="Low floodplain, coastal margin",
        analog_regions_bn="ত্রিপুরার সমভূমি",
        analog_regions_en="Tripura plains",
        established_crops_bn=("ধান", "সবজি", "আম"),
        established_crops_en=("Rice", "Vegetables", "Mango"),
        opportunity_crops_bn=("সবজি", "ডাল"),
        opportunity_crops_en=("Vegetables", "Pulses"),
        bare_field_risk_en="Flash-flood waterlogging from upstream rivers (Muhuri/Feni) and late-autumn drainage delays.",
        bare_field_risk_bn="উজানের ঢল ও আকস্মিক বন্যায় জলাবদ্ধতা এবং আমন পরবর্তী পানি নামতে দেরি হওয়ার ঝুঁকি থাকে।",
    ),
    DistrictProfile(
        id="noakhali", name_en="Noakhali", name_bn="নোয়াখালী",
        division_en="Chattogram", division_bn="চট্টগ্রাম", latitude=22.8696, longitude=91.0994, bamis_region="Chattogram",
        landform_bn="মেঘনা মোহনা, লবণাক্ত চর",
        landform_en="Meghna estuary, saline char",
        analog_regions_bn="মেকং ডেল্টার মোহনা",
        analog_regions_en="Mekong Delta estuary",
        established_crops_bn=("ধান", "সুপারি", "সবজি"),
        established_crops_en=("Rice", "Betel nut", "Vegetables"),
        opportunity_crops_bn=("সয়াবিন", "ডাল", "সবজি"),
        opportunity_crops_en=("Soybean", "Pulses", "Vegetables"),
        bare_field_risk_en="Dry-season salinity rise on young Meghna chars (Jan–May) where nitrogen-fixing soybean/pulses protect bare soil.",
        bare_field_risk_bn="জানুয়ারি–মে মাসে মেঘনা মোহনার লবণাক্ত চরে জমি খালি না রেখে সয়াবিন বা ডাল চাষ মাটির নাইট্রোজেন ও ঢাকনা বজায় রাখে।",
    ),
    DistrictProfile(
        id="lakshmipur", name_en="Lakshmipur", name_bn="লক্ষ্মীপুর",
        division_en="Chattogram", division_bn="চট্টগ্রাম", latitude=22.9447, longitude=90.8282, bamis_region="Cumilla",
        landform_bn="মেঘনা মোহনা, নিচু",
        landform_en="Meghna estuary, low-lying",
        analog_regions_bn="মেকং ডেল্টার মোহনা",
        analog_regions_en="Mekong Delta estuary",
        established_crops_bn=("ধান", "সুপারি", "নারকেল"),
        established_crops_en=("Rice", "Betel nut", "Coconut"),
        opportunity_crops_bn=("সয়াবিন", "ডাল"),
        opportunity_crops_en=("Soybean", "Pulses"),
        bare_field_risk_en="Post-Aman recession window (Dec–Jan) and late-spring storm rain during Rabi soybean/pulse harvest.",
        bare_field_risk_bn="আমন পরবর্তী জোয়ারের পানি নামার সময় এবং বৈশাখে সয়াবিন/ডাল তোলার সময় অতিবৃষ্টির ঝুঁকি থাকে।",
    ),
    DistrictProfile(
        id="cumilla", name_en="Cumilla", name_bn="কুমিল্লা",
        division_en="Chattogram", division_bn="চট্টগ্রাম", latitude=23.4607, longitude=91.1809, bamis_region="Cumilla",
        landform_bn="পুরোনো পলিমাটি, মাঝারি উঁচু",
        landform_en="Old Meghna estuarine floodplain, medium high land",
        analog_regions_bn="ত্রিপুরার সমভূমি",
        analog_regions_en="Tripura plains",
        established_crops_bn=("ধান", "সবজি", "কলা"),
        established_crops_en=("Rice", "Vegetables", "Banana"),
        opportunity_crops_bn=("সবজি", "কলা"),
        opportunity_crops_en=("Vegetables", "Banana"),
        bare_field_risk_en="High cropping intensity (3 crops/yr) risks micronutrient depletion and pest carryover without vegetable/legume rotation.",
        bare_field_risk_bn="বছরে তিন ফসলি জমিতে একটানা চাষের ফলে মাটির অনুখাদ্য ঘাটতি ও রোগবালাই কমাতে ফসল পর্যায় জরুরি।",
    ),
    DistrictProfile(
        id="chandpur", name_en="Chandpur", name_bn="চাঁদপুর",
        division_en="Chattogram", division_bn="চট্টগ্রাম", latitude=23.2332, longitude=90.6713, bamis_region="Cumilla",
        landform_bn="মেঘনা-ডাকাতিয়া প্লাবনভূমি",
        landform_en="Meghna-Dakatiya floodplain",
        analog_regions_bn="ত্রিপুরা সমভূমি, লাল নদীর ব-দ্বীপ",
        analog_regions_en="Tripura plains, Red River Delta",
        established_crops_bn=("ধান", "সবজি", "ইলিশ-সংলগ্ন কৃষি"),
        established_crops_en=("Rice", "Vegetables", "Riverine agriculture"),
        opportunity_crops_bn=("সবজি", "ডাল"),
        opportunity_crops_en=("Vegetables", "Pulses"),
        bare_field_risk_en="Seasonal flooding and drainage congestion in low floodplain pockets outside irrigation polders.",
        bare_field_risk_bn="বর্ষায় প্লাবন এবং নিচু জমিতে পানি নিষ্কাশন বিলম্বিত হলে রবি আবাদ পিছিয়ে যায়।",
    ),
    DistrictProfile(
        id="brahmanbaria", name_en="Brahmanbaria", name_bn="ব্রাহ্মণবাড়িয়া",
        division_en="Chattogram", division_bn="চট্টগ্রাম", latitude=23.9571, longitude=91.1119, bamis_region="Cumilla",
        landform_bn="প্লাবনভূমি, হাওরের কিনারা",
        landform_en="Floodplain, haor basin margin",
        analog_regions_bn="ত্রিপুরা সমভূমি",
        analog_regions_en="Tripura plains",
        established_crops_bn=("ধান", "সবজি"),
        established_crops_en=("Rice", "Vegetables"),
        opportunity_crops_bn=("সবজি", "কলা"),
        opportunity_crops_en=("Vegetables", "Banana"),
        bare_field_risk_en="Monsoon submergence on haor-margin lowlands leaves fields unavailable for upland Kharif crops.",
        bare_field_risk_bn="হাওর-সংলগ্ন নিচু জমিতে বর্ষার দীর্ঘ জলাবদ্ধতা এবং পানি নামার পর দ্রুত রবি প্রস্তুতির চ্যালেঞ্জ থাকে।",
    ),

    # 6. Sylhet Division (4 districts)
    DistrictProfile(
        id="sylhet", name_en="Sylhet", name_bn="সিলেট",
        division_en="Sylhet", division_bn="সিলেট", latitude=24.8949, longitude=91.8687, bamis_region="Sylhet",
        landform_bn="টিলা ও উপত্যকা, অম্লীয়, অতি বেশি বৃষ্টি",
        landform_en="Tillah hills & valleys, acidic soil, very high rainfall",
        analog_regions_bn="কাছাড় (বরাক উপত্যকা), মেঘালয়ের পাদদেশ",
        analog_regions_en="Cachar (Barak Valley), Meghalaya foothills",
        established_crops_bn=("চা", "ধান", "আনারস"),
        established_crops_en=("Tea", "Rice", "Pineapple"),
        opportunity_crops_bn=("লেবু", "আগর", "রাবার"),
        opportunity_crops_en=("Citrus/Lemon", "Agarwood", "Rubber"),
        bare_field_risk_en="Flash floods in May–Jul coupled with Paradoxical Rabi fallow (Nov–Feb) where acidic basin clays crust when dry.",
        bare_field_risk_bn="অতিবৃষ্টি ও পাহাড়ি ঢলের পাশাপাশি শীতকালে (নভেম্বর–ফেব্রুয়ারি) অম্লীয় মাটি শক্ত হয়ে অনেক জমি পতিত থাকে।",
    ),
    DistrictProfile(
        id="moulvibazar", name_en="Moulvibazar", name_bn="মৌলভীবাজার",
        division_en="Sylhet", division_bn="সিলেট", latitude=24.4829, longitude=91.7774, bamis_region="Sylhet",
        landform_bn="টিলা, অম্লীয়, বেশি বৃষ্টি",
        landform_en="Tillah hills, acidic soil, high rainfall",
        analog_regions_bn="কাছাড়, উজান অসম",
        analog_regions_en="Cachar, Upper Assam",
        established_crops_bn=("চা", "লেবু", "আনারস"),
        established_crops_en=("Tea", "Citrus/Lemon", "Pineapple"),
        opportunity_crops_bn=("রাবার", "আগর", "লেবু"),
        opportunity_crops_en=("Rubber", "Agarwood", "Citrus/Lemon"),
        bare_field_risk_en="Acidic tillah slope erosion in heavy monsoon rain and dry-season moisture deficit on unshaded hillocks.",
        bare_field_risk_bn="বর্ষায় টিলার অম্লীয় মাটি ক্ষয় এবং শীতকালে টিলার উপরিভাগে রসের ঘাটতি দেখা দেয়।",
    ),
    DistrictProfile(
        id="habiganj", name_en="Habiganj", name_bn="হবিগঞ্জ",
        division_en="Sylhet", division_bn="সিলেট", latitude=24.3749, longitude=91.4155, bamis_region="Sylhet",
        landform_bn="টিলা ও হাওর",
        landform_en="Tillah hills & haor wetland",
        analog_regions_bn="কাছাড়, টনলে সাপ (কম্বোডিয়া)",
        analog_regions_en="Cachar, Tonle Sap (Cambodia)",
        established_crops_bn=("চা", "ধান"),
        established_crops_en=("Tea", "Rice"),
        opportunity_crops_bn=("লেবু", "মাছ-ধান মিশ্র চাষ"),
        opportunity_crops_en=("Citrus/Lemon", "Integrated rice-fish culture"),
        bare_field_risk_en="Dual risk: early flash flood in haor basins (Apr–May) during Boro ripening and acidic runoff on southern tillahs.",
        bare_field_risk_bn="বৈশাখে বোরো পাকার সময় হাওরে আগাম পাহাড়ি ঢল এবং টিলা অঞ্চলে অম্লীয় মাটির ক্ষয় প্রধান ঝুঁকি।",
    ),
    DistrictProfile(
        id="sunamganj", name_en="Sunamganj", name_bn="সুনামগঞ্জ",
        division_en="Sylhet", division_bn="সিলেট", latitude=25.0658, longitude=91.3950, bamis_region="Sylhet",
        landform_bn="গভীর হাওর, ভারী কাদামাটি",
        landform_en="Deep haor basin, heavy clay soil",
        analog_regions_bn="টনলে সাপ (কম্বোডিয়া), মেকং ডেল্টার উজান",
        analog_regions_en="Tonle Sap (Cambodia), Upper Mekong Delta",
        established_crops_bn=("বোরো ধান", "মাছ"),
        established_crops_en=("Boro rice", "Fish"),
        opportunity_crops_bn=("বন্যাসহনশীল ও ভাসমান ধান", "মাছ-ধান মিশ্র চাষ"),
        opportunity_crops_en=("Submergence-tolerant & floating rice", "Integrated rice-fish culture"),
        bare_field_risk_en="Single-crop Boro dependence with 6-month deep submergence (May–Oct) and high flash-flood vulnerability in April.",
        bare_field_risk_bn="এপ্রিল মাসে আগাম পাহাড়ি ঢলে বোরো ডুবে যাওয়ার ঝুঁকি এবং বছরের বাকি ৬ মাস গভীর জলাবদ্ধতা থাকে।",
    ),

    # 7. Dhaka Division (13 districts)
    DistrictProfile(
        id="dhaka", name_en="Dhaka", name_bn="ঢাকা",
        division_en="Dhaka", division_bn="ঢাকা", latitude=23.8103, longitude=90.4125, bamis_region="Dhaka",
        landform_bn="উঁচু ও নিচু পলিমাটি",
        landform_en="High & low alluvial floodplain",
        analog_regions_bn="লাল নদীর ব-দ্বীপ (ভিয়েতনাম)",
        analog_regions_en="Red River Delta (Vietnam)",
        established_crops_bn=("সবজি", "ধান", "পাট"),
        established_crops_en=("Vegetables", "Rice", "Jute"),
        opportunity_crops_bn=("উচ্চমূল্যের সবজি",),
        opportunity_crops_en=("High-value peri-urban vegetables",),
        bare_field_risk_en="Monsoon drainage congestion in low pockets and pest/disease pressure in continuous peri-urban vegetable plots.",
        bare_field_risk_bn="নিচু জমিতে বর্ষার জলাবদ্ধতা এবং একই জমিতে টানা সবজি চাষে মাটিবাহিত রোগবালাইয়ের ঝুঁকি থাকে।",
    ),
    DistrictProfile(
        id="gazipur", name_en="Gazipur", name_bn="গাজীপুর",
        division_en="Dhaka", division_bn="ঢাকা", latitude=24.0023, longitude=90.4264, bamis_region="Dhaka",
        landform_bn="ভাওয়াল গড়, লালচে অম্লীয় মাটি",
        landform_en="Bhawal Garh terrace, reddish acidic soil",
        analog_regions_bn="অসমের পুরোনো টেরেস, প.ব.-র ল্যাটেরাইট",
        analog_regions_en="Old Assam terraces, West Bengal lateritic belt",
        established_crops_bn=("আনারস", "কলা", "পেঁপে"),
        established_crops_en=("Pineapple", "Banana", "Papaya"),
        opportunity_crops_bn=("থাই পেয়ারা", "কলা"),
        opportunity_crops_en=("Thai guava", "Banana"),
        bare_field_risk_en="Acidic red terrace soil crusting and moisture stress during dry winter/spring (Jan–Apr) without organic mulch.",
        bare_field_risk_bn="ভাওয়াল গড়ের লালচে অম্লীয় মাটিতে শীত ও গ্রীষ্মে জৈব আবরণ না থাকলে মাটি শক্ত হয়ে রস কমে যায়।",
    ),
    DistrictProfile(
        id="narayanganj", name_en="Narayanganj", name_bn="নারায়ণগঞ্জ",
        division_en="Dhaka", division_bn="ঢাকা", latitude=23.6238, longitude=90.5000, bamis_region="Dhaka",
        landform_bn="নিচু প্লাবনভূমি",
        landform_en="Low floodplain",
        analog_regions_bn="লাল নদীর ব-দ্বীপ",
        analog_regions_en="Red River Delta",
        established_crops_bn=("সবজি", "ধান", "পাট"),
        established_crops_en=("Vegetables", "Rice", "Jute"),
        opportunity_crops_bn=("সবজি",),
        opportunity_crops_en=("Vegetables",),
        bare_field_risk_en="Seasonal inundation in low floodplains and soil quality concerns requiring verified lab soil testing.",
        bare_field_risk_bn="নিচু প্লাবনভূমিতে বর্ষার জলাবদ্ধতা এবং মাটির গুণাগুণ জানতে পরীক্ষাগার ভিত্তিক মাটি পরীক্ষা জরুরি।",
    ),
    DistrictProfile(
        id="munshiganj", name_en="Munshiganj", name_bn="মুন্সিগঞ্জ",
        division_en="Dhaka", division_bn="ঢাকা", latitude=23.5422, longitude=90.5305, bamis_region="Dhaka",
        landform_bn="পদ্মা প্লাবনভূমি",
        landform_en="Padma floodplain",
        analog_regions_bn="লাল নদীর ব-দ্বীপ",
        analog_regions_en="Red River Delta",
        established_crops_bn=("আলু (বিখ্যাত)", "সবজি"),
        established_crops_en=("Potato (renowned)", "Vegetables"),
        opportunity_crops_bn=("আলুর উন্নত জাত", "সবজি"),
        opportunity_crops_en=("Improved potato varieties", "Vegetables"),
        bare_field_risk_en="Late monsoon flood recession (Nov) threatens timely potato planting; continuous potato increases blight/soil disease risk.",
        bare_field_risk_bn="নভেম্বরে বন্যার পানি দেরিতে নামলে আলু রোপণ ব্যাহত হয় এবং টানা আলু চাষে নাবী ধসা ও মাটির রোগ বাড়ে।",
    ),
    DistrictProfile(
        id="narsingdi", name_en="Narsingdi", name_bn="নরসিংদী",
        division_en="Dhaka", division_bn="ঢাকা", latitude=23.9229, longitude=90.7177, bamis_region="Dhaka",
        landform_bn="পুরোনো পলিমাটি, কিছু উঁচু",
        landform_en="Old Brahmaputra alluvial soil, partly elevated",
        analog_regions_bn="ত্রিপুরার সমভূমি",
        analog_regions_en="Tripura plains",
        established_crops_bn=("ধান", "সবজি", "কলা"),
        established_crops_en=("Rice", "Vegetables", "Banana"),
        opportunity_crops_bn=("সবজি", "পেঁপে"),
        opportunity_crops_en=("Vegetables", "Papaya"),
        bare_field_risk_en="Pest and wilt carryover in intensive banana/vegetable uplands when non-host rotation breaks are skipped.",
        bare_field_risk_bn="একই জমিতে টানা কলা ও সবজি চাষে পানামা বা উইল্ট রোগের ঝুঁকি কমাতে ফসল পর্যায় আবশ্যক।",
    ),
    DistrictProfile(
        id="manikganj", name_en="Manikganj", name_bn="মানিকগঞ্জ",
        division_en="Dhaka", division_bn="ঢাকা", latitude=23.8617, longitude=90.0003, bamis_region="Dhaka",
        landform_bn="যমুনা-ধলেশ্বরী প্লাবনভূমি",
        landform_en="Jamuna-Dhaleshwari floodplain",
        analog_regions_bn="নদীয়া",
        analog_regions_en="Nadia (West Bengal)",
        established_crops_bn=("ধান", "পাট", "সরিষা"),
        established_crops_en=("Rice", "Jute", "Mustard"),
        opportunity_crops_bn=("ভুট্টা", "সবজি"),
        opportunity_crops_en=("Maize", "Vegetables"),
        bare_field_risk_en="Monsoon flooding (Jul–Sep) followed by tight post-flood mustard/maize establishment window.",
        bare_field_risk_bn="বর্ষার পানি নামার পর পরই সরিষা বা ভুট্টা বুনতে দেরি হলে মাটির রস কমে যায়।",
    ),
    DistrictProfile(
        id="tangail", name_en="Tangail", name_bn="টাঙ্গাইল",
        division_en="Dhaka", division_bn="ঢাকা", latitude=24.2513, longitude=89.9167, bamis_region="Dhaka",
        landform_bn="মধুপুর গড়, লালচে অম্লীয়; প্লাবনভূমি",
        landform_en="Madhupur Garh terrace (reddish acidic) & floodplain",
        analog_regions_bn="অসমের টেরেস, প.ব.-র ল্যাটেরাইট",
        analog_regions_en="Assam terraces, West Bengal lateritic belt",
        established_crops_bn=("আনারস", "কলা", "পাট"),
        established_crops_en=("Pineapple", "Banana", "Jute"),
        opportunity_crops_bn=("পেঁপে", "কলা", "ডাল"),
        opportunity_crops_en=("Papaya", "Banana", "Pulses"),
        bare_field_risk_en="Sharp contrast within the district: acidic moisture-stressed Madhupur terrace vs. flood-prone Jamuna chars.",
        bare_field_risk_bn="একই জেলায় মধুপুর গড়ের অম্লীয় উঁচু মাটি এবং যমুনা তীরের প্লাবনভূমি—উপজেলাভেদে মাটি ও ঝুঁকি সম্পূর্ণ ভিন্ন।",
    ),
    DistrictProfile(
        id="kishoreganj", name_en="Kishoreganj", name_bn="কিশোরগঞ্জ",
        division_en="Dhaka", division_bn="ঢাকা", latitude=24.4449, longitude=90.7766, bamis_region="Mymensingh",
        landform_bn="হাওর ও নিচু প্লাবনভূমি",
        landform_en="Haor basin & low floodplain",
        analog_regions_bn="টনলে সাপ",
        analog_regions_en="Tonle Sap (Cambodia)",
        established_crops_bn=("বোরো ধান", "মাছ"),
        established_crops_en=("Boro rice", "Fish"),
        opportunity_crops_bn=("ভাসমান ধান", "মাছ-ধান মিশ্র চাষ"),
        opportunity_crops_en=("Floating rice", "Integrated rice-fish culture"),
        bare_field_risk_en="Eastern haor upazilas stay submerged Jun–Oct and face April flash-flood risk during Boro harvest.",
        bare_field_risk_bn="হাওর অঞ্চলে বর্ষায় দীর্ঘ জলাবদ্ধতা এবং এপ্রিল মাসে বোরো কাটার সময় আগাম বন্যার ঝুঁকি থাকে।",
    ),
    DistrictProfile(
        id="faridpur", name_en="Faridpur", name_bn="ফরিদপুর",
        division_en="Dhaka", division_bn="ঢাকা", latitude=23.6071, longitude=89.8429, bamis_region="Faridpur",
        landform_bn="গঙ্গা প্লাবনভূমি, বিল",
        landform_en="Ganges floodplain, beel wetland",
        analog_regions_bn="নদীয়া, চাও ফ্রায়া সমভূমি",
        analog_regions_en="Nadia (West Bengal), Chao Phraya plain",
        established_crops_bn=("পাট", "সবজি", "ধান"),
        established_crops_en=("Jute", "Vegetables", "Rice"),
        opportunity_crops_bn=("সবজি", "ডাল"),
        opportunity_crops_en=("Vegetables", "Pulses"),
        bare_field_risk_en="Post-jute and post-Aman transitions where pulse crops (lentil/mungbean) help restore nitrogen and cover soil.",
        bare_field_risk_bn="পাট ও আমন পরবর্তী সময়ে ডাল ফসল যুক্ত করলে মাটির নাইট্রোজেন ও জৈব গুণাগুণ বজায় থাকে।",
    ),
    DistrictProfile(
        id="rajbari", name_en="Rajbari", name_bn="রাজবাড়ী",
        division_en="Dhaka", division_bn="ঢাকা", latitude=23.7574, longitude=89.6445, bamis_region="Faridpur",
        landform_bn="গঙ্গা-পদ্মা প্লাবনভূমি",
        landform_en="Ganges-Padma floodplain",
        analog_regions_bn="নদীয়া",
        analog_regions_en="Nadia (West Bengal)",
        established_crops_bn=("ধান", "পাট", "সরিষা"),
        established_crops_en=("Rice", "Jute", "Mustard"),
        opportunity_crops_bn=("ডাল", "সরিষা", "তরমুজ"),
        opportunity_crops_en=("Pulses", "Mustard", "Watermelon"),
        bare_field_risk_en="Padma char and floodplain recession window (Nov) followed by dry spring winds.",
        bare_field_risk_bn="পদ্মা তীরবর্তী প্লাবনভূমি ও চরে পানি নামার পর দ্রুত সরিষা বা ডাল বপন না করলে মাটির রস শুকিয়ে যায়।",
    ),
    DistrictProfile(
        id="gopalganj", name_en="Gopalganj", name_bn="গোপালগঞ্জ",
        division_en="Dhaka", division_bn="ঢাকা", latitude=23.0051, longitude=89.8266, bamis_region="Faridpur",
        landform_bn="নিচু বিল, কাদামাটি",
        landform_en="Low beel basin, heavy clay soil",
        analog_regions_bn="উত্তর ২৪ পরগনা",
        analog_regions_en="North 24 Parganas (West Bengal)",
        established_crops_bn=("ধান", "পাট"),
        established_crops_en=("Rice", "Jute"),
        opportunity_crops_bn=("মাছ-ধান", "সবজি"),
        opportunity_crops_en=("Integrated rice-fish culture", "Vegetables"),
        bare_field_risk_en="Deep peat/clay beel waterlogging limits dryland rotation unless floating beds (dhap) or rice-fish are used.",
        bare_field_risk_bn="গভীর বিল ও ভারী কাদামাটিতে দীর্ঘ জলাবদ্ধতা থাকায় ভাসমান ধাপ বা মাছ-ধান পদ্ধতি কার্যকর।",
    ),
    DistrictProfile(
        id="madaripur", name_en="Madaripur", name_bn="মাদারীপুর",
        division_en="Dhaka", division_bn="ঢাকা", latitude=23.1641, longitude=90.1897, bamis_region="Faridpur",
        landform_bn="পদ্মা প্লাবনভূমি, নিচু",
        landform_en="Padma floodplain, low-lying",
        analog_regions_bn="নদীয়া, লাল নদীর ব-দ্বীপ",
        analog_regions_en="Nadia (West Bengal), Red River Delta",
        established_crops_bn=("ধান", "পাট", "সবজি"),
        established_crops_en=("Rice", "Jute", "Vegetables"),
        opportunity_crops_bn=("সবজি", "ডাল"),
        opportunity_crops_en=("Vegetables", "Pulses"),
        bare_field_risk_en="Seasonal flood recession timing in November governs whether Rabi pulses/mustard can establish before Boro.",
        bare_field_risk_bn="নভেম্বরে বন্যার পানি নামার সময়ের ওপর রবি ডাল ও সবজি চাষের সাফল্য নির্ভর করে।",
    ),
    DistrictProfile(
        id="shariatpur", name_en="Shariatpur", name_bn="শরীয়তপুর",
        division_en="Dhaka", division_bn="ঢাকা", latitude=23.2423, longitude=90.4348, bamis_region="Faridpur",
        landform_bn="পদ্মা-মেঘনা প্লাবনভূমি",
        landform_en="Padma-Meghna floodplain",
        analog_regions_bn="লাল নদীর ব-দ্বীপ",
        analog_regions_en="Red River Delta",
        established_crops_bn=("ধান", "পাট", "সবজি"),
        established_crops_en=("Rice", "Jute", "Vegetables"),
        opportunity_crops_bn=("সবজি", "ডাল"),
        opportunity_crops_en=("Vegetables", "Pulses"),
        bare_field_risk_en="Riverbank erosion and char emergence windows along the Padma-Meghna confluence.",
        bare_field_risk_bn="পদ্মা-মেঘনা অববাহিকায় বর্ষার প্লাবন এবং পানি নামার পর চরের মাটিতে রস সংরক্ষণ প্রধান বিষয়।",
    ),

    # 8. Mymensingh Division (4 districts)
    DistrictProfile(
        id="mymensingh", name_en="Mymensingh", name_bn="ময়মনসিংহ",
        division_en="Mymensingh", division_bn="ময়মনসিংহ", latitude=24.7471, longitude=90.4203, bamis_region="Mymensingh",
        landform_bn="ব্রহ্মপুত্র পুরোনো প্লাবনভূমি, উত্তরে মধুপুর ঘেঁষা",
        landform_en="Old Brahmaputra floodplain, bordering Madhupur tract in north",
        analog_regions_bn="গারো পাহাড়ের পাদদেশ (মেঘালয়)",
        analog_regions_en="Garo Hills piedmont (Meghalaya)",
        established_crops_bn=("ধান", "সবজি", "কলা"),
        established_crops_en=("Rice", "Vegetables", "Banana"),
        opportunity_crops_bn=("ভুট্টা", "সরিষা", "সবজি"),
        opportunity_crops_en=("Maize", "Mustard", "Vegetables"),
        bare_field_risk_en="Short fallow gap between T. Aman and Boro (Nov–Jan) where short-duration mustard can break rice monoculture.",
        bare_field_risk_bn="আমন ও বোরো ধানের মধ্যবর্তী সময়ে (নভেম্বর–জানুয়ারি) জমি পতিত না রেখে স্বল্পমেয়াদি সরিষা চাষ যাচাই করা যায়।",
    ),
    DistrictProfile(
        id="jamalpur", name_en="Jamalpur", name_bn="জামালপুর",
        division_en="Mymensingh", division_bn="ময়মনসিংহ", latitude=24.9375, longitude=89.9378, bamis_region="Mymensingh",
        landform_bn="যমুনা ও ব্রহ্মপুত্র চর, বেলে",
        landform_en="Jamuna & Brahmaputra river char, sandy soil",
        analog_regions_bn="ধুবড়ি (অসম)",
        analog_regions_en="Dhubri (Assam)",
        established_crops_bn=("ধান", "পাট", "সরিষা"),
        established_crops_en=("Rice", "Jute", "Mustard"),
        opportunity_crops_bn=("ভুট্টা", "চিনাবাদাম"),
        opportunity_crops_en=("Maize", "Groundnut"),
        bare_field_risk_en="Monsoon char flooding followed by dry sandy soil exposure from December to April.",
        bare_field_risk_bn="বর্ষায় চরের প্লাবন এবং শীতে বেলে মাটিতে দ্রুত রস কমে যাওয়ার ঝুঁকি থাকে।",
    ),
    DistrictProfile(
        id="netrokona", name_en="Netrokona", name_bn="নেত্রকোনা",
        division_en="Mymensingh", division_bn="ময়মনসিংহ", latitude=24.8710, longitude=90.7279, bamis_region="Mymensingh",
        landform_bn="হাওর ও গারো পাহাড়ের পাদদেশ",
        landform_en="Haor basin & Garo Hills piedmont",
        analog_regions_bn="টনলে সাপ, মেঘালয়",
        analog_regions_en="Tonle Sap (Cambodia), Meghalaya",
        established_crops_bn=("বোরো ধান", "মাছ"),
        established_crops_en=("Boro rice", "Fish"),
        opportunity_crops_bn=("ভাসমান ধান", "মাছ-ধান"),
        opportunity_crops_en=("Floating rice", "Integrated rice-fish culture"),
        bare_field_risk_en="Flash-flood hazard from Meghalaya hills in April–May and prolonged monsoon waterlogging in eastern haors.",
        bare_field_risk_bn="এপ্রিল–মে মাসে গারো পাহাড়ের ঢলে আগাম বন্যা এবং হাওরাঞ্চলে দীর্ঘ জলাবদ্ধতার ঝুঁকি থাকে।",
    ),
    DistrictProfile(
        id="sherpur", name_en="Sherpur", name_bn="শেরপুর",
        division_en="Mymensingh", division_bn="ময়মনসিংহ", latitude=25.0205, longitude=90.0153, bamis_region="Mymensingh",
        landform_bn="গারো পাহাড়ের পাদদেশ, অম্লীয় মাটি",
        landform_en="Garo Hills piedmont, acidic soil",
        analog_regions_bn="মেঘালয়ের পাদদেশ",
        analog_regions_en="Meghalaya foothills",
        established_crops_bn=("ধান", "কলা", "সরিষা"),
        established_crops_en=("Rice", "Banana", "Mustard"),
        opportunity_crops_bn=("ভুট্টা", "কলা", "আনারস"),
        opportunity_crops_en=("Maize", "Banana", "Pineapple"),
        bare_field_risk_en="Hill-piedmont flash floods and acidic soil nutrient leaching during heavy monsoon rains.",
        bare_field_risk_bn="পাহাড়ি ঢল ও অতিবৃষ্টিতে অম্লীয় মাটির পুষ্টি ধুয়ে যাওয়া এবং শীতকালে উঁচু জমিতে সেচের সংকট থাকে।",
    ),
)

_DISTRICT_BY_ID: dict[str, DistrictProfile] = {d.id: d for d in DISTRICTS}
_DISTRICT_BY_NAME: dict[str, DistrictProfile] = {}
for _d in DISTRICTS:
    _DISTRICT_BY_NAME[_d.name_en.lower()] = _d
    _DISTRICT_BY_NAME[_d.id.lower()] = _d
    _DISTRICT_BY_NAME[_d.name_bn] = _d
    _DISTRICT_BY_NAME[_d.name_en.lower().replace("'", "")] = _d


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0088
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * radius * asin(sqrt(a))


def serialize_district(district: DistrictProfile, *, distance_km: float | None = None) -> dict[str, Any]:
    payload = asdict(district)
    payload["established_crops_bn"] = list(district.established_crops_bn)
    payload["established_crops_en"] = list(district.established_crops_en)
    payload["opportunity_crops_bn"] = list(district.opportunity_crops_bn)
    payload["opportunity_crops_en"] = list(district.opportunity_crops_en)
    payload["online_evidence"] = [
        ONLINE_EVIDENCE_NOTES[eid]
        for eid in district.online_evidence_ids
        if eid in ONLINE_EVIDENCE_NOTES
    ]
    if distance_km is not None:
        payload["distance_km"] = round(distance_km, 1)
    payload["verification_status"] = "preliminary_district_profile_requires_srdi_barc_check"
    payload["caution_bn"] = DATASET_CAUTION_BN
    payload["caution_en"] = DATASET_CAUTION_EN
    payload["verification_requirements"] = list(VERIFICATION_REQUIREMENTS)
    payload["national_import_context"] = NATIONAL_IMPORT_SUBSTITUTION_CONTEXT
    return payload


def nearest_bangladesh_district(lat: float, lon: float) -> tuple[DistrictProfile, float]:
    district = min(DISTRICTS, key=lambda item: _distance_km(lat, lon, item.latitude, item.longitude))
    return district, _distance_km(lat, lon, district.latitude, district.longitude)


def lookup_bangladesh_area(query: str) -> dict[str, Any] | None:
    """Resolve any Bangladesh division or district name deterministically without external network dependence."""
    raw_lower = query.strip().lower()
    explicit_division = "division" in raw_lower or "বিভাগ" in raw_lower
    clean = raw_lower
    for suffix in (", bangladesh", " district", " division", " zila", " জেলা", " বিভাগ"):
        if clean.endswith(suffix):
            clean = clean[: -len(suffix)].strip()
    if explicit_division and clean in DIVISION_COORDINATES:
        div = DIVISION_COORDINATES[clean]
        rep = _DISTRICT_BY_ID[div["representative_district"]]
        return {
            "kind": "division",
            "id": clean,
            "name_en": div["name_en"],
            "name_bn": div["name_bn"],
            "division_en": rep.division_en,
            "division_bn": rep.division_bn,
            "latitude": div["latitude"],
            "longitude": div["longitude"],
            "district_profile": serialize_district(rep, distance_km=0.0),
        }
    if clean in _DISTRICT_BY_NAME:
        d = _DISTRICT_BY_NAME[clean]
        return {
            "kind": "district",
            "id": d.id,
            "name_en": d.name_en,
            "name_bn": d.name_bn,
            "division_en": d.division_en,
            "division_bn": d.division_bn,
            "latitude": d.latitude,
            "longitude": d.longitude,
            "district_profile": serialize_district(d, distance_km=0.0),
        }
    if clean in DIVISION_COORDINATES:
        div = DIVISION_COORDINATES[clean]
        rep = _DISTRICT_BY_ID[div["representative_district"]]
        return {
            "kind": "division",
            "id": clean,
            "name_en": div["name_en"],
            "name_bn": div["name_bn"],
            "division_en": rep.division_en,
            "division_bn": rep.division_bn,
            "latitude": div["latitude"],
            "longitude": div["longitude"],
            "district_profile": serialize_district(rep, distance_km=0.0),
        }
    return None


def list_bangladesh_districts(division: str | None = None) -> list[dict[str, Any]]:
    items = DISTRICTS
    if division:
        div_clean = division.strip().lower()
        items = tuple(
            d for d in DISTRICTS
            if d.division_en.lower() == div_clean or d.division_bn == division.strip()
        )
    return [serialize_district(d) for d in items]
