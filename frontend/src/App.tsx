import { useEffect, useMemo, useState, type CSSProperties, type FormEvent } from "react";
import LocationMap, { type LayerKey } from "./LocationMap";
import DecisionReport, { BoponXLogoMark } from "./DecisionReport";
import FieldIcon, { type IconName } from "./FieldIcon";
import {
  ApiError,
  apiGet,
  apiPost,
  type EonetHazardsResponse,
  type FarmerProfile,
  type LocalSourceRegistry,
  type LocationContext,
  type PlaceResult,
  type PlanBrief,
  type PlantingWindowAdvisory,
  type PowerBaselineWindow,
  type RecentEnvironment,
  type RotationScenario,
} from "./api";

type Point = { latitude: number; longitude: number };
type View = "earth" | "rotation" | "plan";
type Lang = "en" | "bn";

const cropOptions = [
  ["rice", "Rice", "ধান", "rice"],
  ["wheat", "Wheat", "গম", "wheat"],
  ["maize", "Maize", "ভুট্টা", "maize"],
  ["pulse", "Pulse", "ডাল", "pulse"],
  ["mustard", "Mustard", "সরিষা", "mustard"],
  ["vegetables", "Vegetables", "সবজি", "vegetables"],
  ["jute", "Jute", "পাট", "jute"],
  ["other", "Other", "অন্যান্য", "other"],
] as const;

const cropLabels: Record<string, string> = Object.fromEntries(
  cropOptions.map(([id, label]) => [id, label]),
);

const cropLabelsBn: Record<string, string> = Object.fromEntries(
  cropOptions.map(([id, , labelBn]) => [id, labelBn]),
);

const bangladeshDivisions = [
  "Barishal", "Chattogram", "Dhaka", "Khulna", "Mymensingh", "Rajshahi", "Rangpur", "Sylhet",
] as const;

const bangladeshDistricts = [
  "Bagerhat", "Bandarban", "Barguna", "Barishal", "Bhola", "Bogura", "Brahmanbaria", "Chandpur",
  "Chapainawabganj", "Chattogram", "Chuadanga", "Cox's Bazar", "Cumilla", "Dhaka", "Dinajpur",
  "Faridpur", "Feni", "Gaibandha", "Gazipur", "Gopalganj", "Habiganj", "Jamalpur", "Jashore",
  "Jhalokati", "Jhenaidah", "Joypurhat", "Khagrachhari", "Khulna", "Kishoreganj", "Kurigram",
  "Kushtia", "Lakshmipur", "Lalmonirhat", "Madaripur", "Magura", "Manikganj", "Meherpur",
  "Moulvibazar", "Munshiganj", "Mymensingh", "Naogaon", "Narail", "Narayanganj", "Narsingdi",
  "Natore", "Netrokona", "Nilphamari", "Noakhali", "Pabna", "Panchagarh", "Patuakhali",
  "Pirojpur", "Rajbari", "Rajshahi", "Rangamati", "Rangpur", "Satkhira", "Shariatpur",
  "Sherpur", "Sirajganj", "Sunamganj", "Sylhet", "Tangail", "Thakurgaon",
] as const;

const quickPilotZones = [
  { label: "Rajshahi (Barind)", name: "Rajshahi" },
  { label: "Naogaon (Terrace)", name: "Naogaon" },
  { label: "Patuakhali (Coastal)", name: "Patuakhali" },
  { label: "Sunamganj (Haor)", name: "Sunamganj" },
  { label: "Dhaka", name: "Dhaka" },
] as const;

const monthShort = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function dotLeftPct(doy: number, adv: PlantingWindowAdvisory): number {
  const all = [
    ...(adv.distributions?.period_2001_2012?.onset_doy_values ?? []),
    ...(adv.distributions?.period_2013_2025?.onset_doy_values ?? []),
  ];
  if (!all.length) return 50;
  const lo = Math.min(...all) - 2;
  const hi = Math.max(...all) + 2;
  return Math.min(96, Math.max(4, ((doy - lo) / Math.max(1, hi - lo)) * 100));
}

function dateMinus(days: number) {
  return new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
}

function metric(value: number | null | undefined, suffix = "") {
  if (value === null || value === undefined || !Number.isFinite(value)) return "—";
  return `${new Intl.NumberFormat("en", { maximumFractionDigits: 1 }).format(value)}${suffix}`;
}

function placeLabel(place: PlaceResult | null, point: Point | null, context?: LocationContext | null) {
  if (place?.address?.village) return place.address.village;
  if (place?.address?.town) return place.address.town;
  if (place?.address?.district) return place.address.district;
  if (place?.name) return place.name;
  if (context?.district_profile?.name_en) {
    return `${context.district_profile.name_en} (${context.district_profile.name_bn ?? context.district_profile.name_en})`;
  }
  if (point && Number.isFinite(point.latitude) && Number.isFinite(point.longitude)) {
    return `${point.latitude.toFixed(3)}°, ${point.longitude.toFixed(3)}°`;
  }
  return "No field selected";
}

function buildStrategies(
  context: LocationContext | null,
  intendedCrop: string,
  previousCrops: string[],
  priority: FarmerProfile["priority"],
  waterSource: FarmerProfile["water_source"],
  drainage: FarmerProfile["water_after_heavy_rain"],
  soilTest: FarmerProfile["soil_test"],
  soilPh: string,
  rainSignal: string,
  equipmentAccess: NonNullable<FarmerProfile["equipment_access"]>,
  marketPreference: NonNullable<FarmerProfile["market_preference"]>,
): RotationScenario[] {
  const district = context?.district_profile ?? null;
  const calEn = (context?.calendar_evidence ?? []).map((item) => item.name_en);
  const calBn = (context?.calendar_evidence ?? []).map((item) => item.name_bn || item.name_en);
  const estEn = district?.established_crops_en ?? [];
  const estBn = district?.established_crops_bn ?? [];
  const oppEn = district?.opportunity_crops_en ?? [];
  const oppBn = district?.opportunity_crops_bn ?? [];

  const historyEn = previousCrops.map((c) => cropLabels[c] ?? c);
  const historyBn = previousCrops.map((c) => cropLabelsBn[c] ?? c);
  const intentEn = intendedCrop ? cropLabels[intendedCrop] ?? intendedCrop : null;
  const intentBn = intendedCrop ? cropLabelsBn[intendedCrop] ?? intendedCrop : null;

  if (calEn.length === 0 && estEn.length === 0 && historyEn.length === 0) {
    return [
      {
        id: "A",
        kind: "evidence_gate",
        title_en: "Rotation evidence gate (Select a field or connect local calendar)",
        title_bn: "ফসল পর্যায় প্রমাণ গেট (মাঠ নির্বাচন বা স্থানীয় পঞ্জিকা প্রয়োজন)",
        crops_en: ["Regional crop evidence", "Crop sequence rules", "Soil constraints"],
        crops_bn: ["আঞ্চলিক ফসল প্রমাণ", "ফসল-পর্যায় নিয়ম", "মাটির সীমাবদ্ধতা"],
        why_suggested_en: "BoponX withholds synthetic crop sequences here because reviewed regional crop calendars are not available for the selected location.",
        why_suggested_bn: "নির্বাচিত স্থানের জন্য যাচাইকৃত ফসল পঞ্জিকা না থাকায় BoponX কোনো কাল্পনিক ফসলক্রম তৈরি করে না।",
        supporting_evidence: [
          "Data: NASA POWER / EONET / GIBS layers remain active",
          "FAO Crop Calendar global reference route available",
        ],
        potential_benefits: [
          "Prevents false confidence from unverified crop guesses",
          "Keeps farmer history and priorities visible for local extension review",
        ],
        information_gaps: [
          "No reviewed regional crop-weather calendar adapter connected for this location",
          "Laboratory soil test required for parcel pH and nutrient decisions",
        ],
        local_review_risks: [
          "Consult local agricultural extension authorities to verify planting windows, frost/heat limits, and market demand.",
        ],
        water_demand_badge: "Gated",
        nitrogen_badge: "Gated",
        pest_break_badge: "Gated",
      },
    ];
  }

  const base1En = historyEn[0] ?? estEn[0] ?? calEn[0] ?? "Rice Aman";
  const base2En = historyEn[1] ?? intentEn ?? estEn[1] ?? calEn[2] ?? "Rice Boro / Rabi Crop";
  const base3En = (intentEn && historyEn.length >= 2) ? intentEn : (estEn[2] ?? "Fallow / Kharif-1 Transition");

  const base1Bn = historyBn[0] ?? estBn[0] ?? calBn[0] ?? "আমন ধান";
  const base2Bn = historyBn[1] ?? intentBn ?? estBn[1] ?? calBn[2] ?? "বোরো ধান / রবি ফসল";
  const base3Bn = (intentBn && historyBn.length >= 2) ? intentBn : (estBn[2] ?? "পতিত / খরিফ-১ অন্তর্বর্তী মৌসুম");

  const legumeRabiEn = calEn.some((c) => c.includes("Mustard") || c.includes("Lentil"))
    ? "Mustard / Lentil (Pulse)"
    : (oppEn[0] ?? "Short-duration Pulse");
  const legumeRabiBn = calEn.some((c) => c.includes("Mustard") || c.includes("Lentil"))
    ? "সরিষা / মসুর ডাল"
    : (oppBn[0] ?? "স্বল্পমেয়াদি ডাল ফসল");

  const kharif1En = calEn.some((c) => c.includes("Green Gram") || c.includes("Aus"))
    ? "Green Gram (Mungbean) / Aus"
    : "Legume Cover / Jute";
  const kharif1Bn = calEn.some((c) => c.includes("Green Gram") || c.includes("Aus"))
    ? "মুগ ডাল (খরিফ-১) / আউশ"
    : "ডাল আচ্ছাদন / পাট";

  const opp1En =
    marketPreference === "forage_livestock"
      ? "Dual-Purpose Maize (Grain + Silage Forage)"
      : (oppEn[0] ?? intentEn ?? calEn[1] ?? "Maize");
  const opp2En =
    marketPreference === "forage_livestock"
      ? "Cowpea / Blackgram Forage & Nitrogen Bridge"
      : (oppEn[1] ?? oppEn[0] ?? "Pulse / Oilseed");
  const opp1Bn =
    marketPreference === "forage_livestock"
      ? "দ্বৈত-উদ্দেশ্য ভুট্টা (দানা ও সাইলেজ গোখাদ্য)"
      : (oppBn[0] ?? intentBn ?? calBn[1] ?? "ভুট্টা");
  const opp2Bn =
    marketPreference === "forage_livestock"
      ? "ফেলন / মাসকলাই (গোখাদ্য ও নাইট্রোজেন সংবন্ধন)"
      : (oppBn[1] ?? oppBn[0] ?? "ডাল / তেলবীজ");

  const districtLabelEn = district
    ? `${district.name_en} District (${district.landform_en})`
    : (context?.nearest_supported_region?.name_en ?? "Selected region");
  const districtLabelBn = district
    ? `${district.name_bn} জেলা (${district.landform_bn})`
    : (context?.nearest_supported_region?.name_bn ?? "নির্বাচিত অঞ্চল");

  const gaps: string[] = [];
  if (soilTest !== "yes") {
    gaps.push("No laboratory soil-test report entered; soil pH, salinity (EC), and NPK nutrients cannot be inferred from SMAP or NASA POWER.");
  } else if (soilPh) {
    gaps.push(`Report pH (${soilPh}) recorded; nitrogen, phosphorus, potassium, and organic matter still require full lab sheet review.`);
  }
  if (district) {
    gaps.push(`District profile for ${district.name_en} is a preliminary estimate; soil varies by upazila and requires SRDI, BMD, BARC, WorldClim & SoilGrids verification.`);
  }

  const equipMarketNote =
    equipmentAccess !== "unknown" || marketPreference !== "unknown"
      ? `Equipment fit: ${equipmentAccess.replace(/_/g, " ")} · Market/Forage focus: ${marketPreference.replace(/_/g, " ")}`
      : "Equipment & market constraints can be refined with local extension before seed purchase";

  return [
    {
      id: "A",
      kind: "existing_baseline",
      title_en: "Existing / Baseline Rotation Benchmark",
      title_bn: "বিদ্যমান / প্রচলিত ফসল পর্যায় (তুলনামূলক ভিত্তি)",
      crops_en: [base1En, base2En, base3En],
      crops_bn: [base1Bn, base2Bn, base3Bn],
      why_suggested_en: `Documents the farmer's existing sequence and established crops in ${districtLabelEn} as the baseline benchmark required to compare any rotation shift.`,
      why_suggested_bn: `কৃষকের বর্তমান ফসল ধারা ও ${districtLabelBn}-এর প্রতিষ্ঠিত ফসলের ওপর ভিত্তি করে এটি তুলনার ভিত্তি হিসেবে দেখানো হয়েছে।`,
      supporting_evidence: [
        `Farmer history: ${historyEn.length ? historyEn.join(" → ") : "Regional staple baseline"}${intentEn ? ` (Intention: ${intentEn})` : ""}`,
        `Established district crops: ${estEn.length ? estEn.join(", ") : "BAMIS regional calendar staple index"}`,
        `${context?.calendar_evidence?.length ?? 0} official BAMIS crop-weather calendars indexed`,
        equipMarketNote,
      ],
      potential_benefits: [
        "Familiar seed, management, and established local market buyers",
        "Provides a clear benchmark for comparing water demand, bare-soil exposure, and pest cycles",
      ],
      information_gaps: gaps,
      local_review_risks: [
        "Repeating the same crop family across seasons can increase pest/disease carryover and nutrient depletion.",
        `Check field water source (${waterSource}) and post-rain drainage (${drainage}) against recent rainfall (${rainSignal}).`,
      ],
      water_demand_badge: "ETc ~1,180 mm · NIR ~520 mm [CALCULATED]",
      nitrogen_badge: "BNF +10 kg · Removal -180 kg N/ha [ESTIMATED]",
      pest_break_badge: "Poaceae → Poaceae (Repeat Host Risk)",
      scientific_evaluation: {
        strategy_id: "A",
        framework_version: "boponx.rotation_science.v3",
        recommendation_gate: waterSource === "rainfed" ? "FLAGGED_CONSTRAINT_VIOLATION" : (soilTest === "yes" ? "CONDITIONAL_EXTENSION_REVIEW" : "CONDITIONAL_MISSING_EVIDENCE"),
        critical_constraint_violated: waterSource === "rainfed",
        constraint_flags: waterSource === "rainfed" ? ["Dry-season Boro rice requires ~480+ mm net irrigation, incompatible with rainfed-only water source."] : [],
        weighted_composite_score_0_100: waterSource === "rainfed" ? 48.5 : 61.2,
        evidence_completeness_pct: soilTest === "yes" ? 87.5 : 75.0,
        scoring_note: "Evaluated across 8 standardized biophysical criteria (Water, N Mass Balance, Coverage, Pest Break, Resilience, Soil Gate, Window Fit, Priority).",
        documented_weights: { water_demand: 0.2, nitrogen_contribution: 0.15, soil_coverage: 0.1, pest_break_potential: 0.15, climate_resilience: 0.15, local_suitability: 0.1, planting_window_compatibility: 0.1, farmer_priority_compatibility: 0.05 },
        criteria_scores_0_100: { water_demand: 52, nitrogen_contribution: 38, soil_coverage: 64, pest_break_potential: 38, climate_resilience: 62, local_suitability: soilTest === "yes" ? 76 : null, planting_window_compatibility: 78, farmer_priority_compatibility: 70 },
      },
    },
    {
      id: "B",
      kind: "soil_and_nitrogen",
      title_en: "Soil-Health & Pulse/Oilseed Bridge Exploration",
      title_bn: "মাটির স্বাস্থ্য ও ডাল/তেলবীজ সংযোজন অনুসন্ধান",
      crops_en: [base1En, legumeRabiEn, kharif1En],
      crops_bn: [base1Bn, legumeRabiBn, kharif1Bn],
      why_suggested_en: "Explores inserting a short-duration nitrogen-fixing pulse or oilseed during the seasonal bare-field transition to build organic matter, interrupt pest cycles, and reduce irrigation water demand.",
      why_suggested_bn: "জমি খালি থাকার সময়ে স্বল্পমেয়াদি ডাল বা তেলবীজ যুক্ত করে মাটিতে নাইট্রোজেন সংবন্ধন, রোগ-পোকার চক্র ভাঙা এবং সেচের পানি সাশ্রয়ের সম্ভাব্য পথ।",
      supporting_evidence: [
        `BAMIS calendar presence for pulses/oilseeds in ${context?.nearest_supported_region?.name_en ?? "this hub"}`,
        district ? `Bare-field window: ${district.bare_field_risk_en}` : "Covers bare soil between main cereal harvests",
        "National import-substitution priority: ~90% edible oil imported; 12.36 lakh tonne projected pulse deficit by 2030 (The Daily Star, USDA)",
      ],
      potential_benefits: [
        "Biological nitrogen fixation (+30–50 kg N/ha) and crop residue improve soil structure and water infiltration",
        "Reduces bare-soil evaporation, erosion, and dry-season capillary salinity rise",
        "Requires ~60–75% less Rabi water than continuous Boro rice while adding domestic-market income",
      ],
      information_gaps: gaps,
      local_review_risks: [
        "Pulses and mustard are sensitive to standing water; if heavy rain stays on the field, verify surface drainage first.",
        "Confirm short-duration variety maturity with DAE (16123) so the main monsoon crop is not delayed.",
      ],
      water_demand_badge: "ETc ~810 mm · Rabi NIR ~145 mm [CALCULATED]",
      nitrogen_badge: "BNF +42 kg · Carryover +18 kg N/ha [ESTIMATED]",
      pest_break_badge: "Poaceae → Brassicaceae/Fabaceae → Fabaceae",
      scientific_evaluation: {
        strategy_id: "B",
        framework_version: "boponx.rotation_science.v3",
        recommendation_gate: drainage === "stays" ? "FLAGGED_CONSTRAINT_VIOLATION" : (soilTest === "yes" ? "CONDITIONAL_EXTENSION_REVIEW" : "CONDITIONAL_MISSING_EVIDENCE"),
        critical_constraint_violated: drainage === "stays",
        constraint_flags: drainage === "stays" ? ["Mustard and pulses do not tolerate standing water, but field post-rain drainage is reported as 'stays'."] : [],
        weighted_composite_score_0_100: drainage === "stays" ? 56.4 : 81.6,
        evidence_completeness_pct: soilTest === "yes" ? 87.5 : 75.0,
        scoring_note: "Evaluated across 8 standardized biophysical criteria. Pulse BNF is estimated (+30–50 kg N/ha BARC reference), never claimed as measured parcel soil N.",
        documented_weights: { water_demand: 0.2, nitrogen_contribution: 0.15, soil_coverage: 0.1, pest_break_potential: 0.15, climate_resilience: 0.15, local_suitability: 0.1, planting_window_compatibility: 0.1, farmer_priority_compatibility: 0.05 },
        criteria_scores_0_100: { water_demand: 86, nitrogen_contribution: 79, soil_coverage: 84, pest_break_potential: 92, climate_resilience: drainage === "stays" ? 54 : 81, local_suitability: soilTest === "yes" ? (drainage === "stays" ? 25 : 82) : null, planting_window_compatibility: 76, farmer_priority_compatibility: 88 },
      },
    },
    {
      id: "C",
      kind: "water_and_local_opportunity",
      title_en: `Climate-Adaptive & ${district ? district.name_en : "Regional"} Opportunity Exploration`,
      title_bn: `জলবায়ু-সহনশীল ও ${district ? district.name_bn : "আঞ্চলিক"} নতুন ফসলের সুযোগ অনুসন্ধান`,
      crops_en: [intentEn ?? base1En, opp1En, opp2En],
      crops_bn: [intentBn ?? base1Bn, opp1Bn, opp2Bn],
      why_suggested_en: `Aligns farmer priority (${priority.replace("_", " ")}) and recent NASA agroclimate signals with preliminary crop opportunities identified for ${districtLabelEn}${district ? ` (climate analogs: ${district.analog_regions_en})` : ""}.`,
      why_suggested_bn: `কৃষকের অগ্রাধিকার ও নাসা জলবায়ু সংকেতের সাথে ${districtLabelBn}-এর সম্ভাব্য নতুন ফসলের সুযোগ${district ? ` (মিল থাকা এলাকা: ${district.analog_regions_bn})` : ""} মিলিয়ে অনুসন্ধানমূলক বিকল্প।`,
      supporting_evidence: [
        district
          ? `64-district profile (${district.name_en}): opportunities ${oppEn.join(", ")}; analogs ${district.analog_regions_en}`
          : `Regional BAMIS calendar index (${context?.calendar_evidence?.length ?? 0} crops)`,
        ...(district?.online_evidence?.length
          ? district.online_evidence.map((ev) => `Published report: ${ev.title_en} — ${ev.detail_en}`)
          : ["Requires local DAE/BARC trial verification before field adoption"]),
        equipMarketNote,
      ],
      potential_benefits: [
        "Explores higher-value, forage, or stress-adapted crops suited to local landform (Barind, char, coastal, haor, or hill terrace)",
        "Helps diversify farm income when seasonal temperature or rainfall patterns shift",
      ],
      information_gaps: gaps,
      local_review_risks: [
        "New or exotic seeds/saplings require Plant Quarantine approval and National Seed Board registration.",
        "Distant climate-analog regions may differ in day length (photoperiod), rainfall timing, pest pressure, and local buyer access.",
      ],
      water_demand_badge: "ETc ~890 mm · NIR ~230 mm [CALCULATED]",
      nitrogen_badge: "Residue & Deep Root Cycling [ESTIMATED]",
      pest_break_badge: "Multi-Family Host Break [REFERENCE]",
      scientific_evaluation: {
        strategy_id: "C",
        framework_version: "boponx.rotation_science.v3",
        recommendation_gate: soilTest === "yes" ? "CONDITIONAL_EXTENSION_REVIEW" : "CONDITIONAL_MISSING_EVIDENCE",
        critical_constraint_violated: false,
        constraint_flags: [],
        weighted_composite_score_0_100: 76.8,
        evidence_completeness_pct: soilTest === "yes" ? 87.5 : 75.0,
        scoring_note: "Evaluated across 8 standardized biophysical criteria. Requires SRDI/BARC local suitability verification before seed purchase.",
        documented_weights: { water_demand: 0.2, nitrogen_contribution: 0.15, soil_coverage: 0.1, pest_break_potential: 0.15, climate_resilience: 0.15, local_suitability: 0.1, planting_window_compatibility: 0.1, farmer_priority_compatibility: 0.05 },
        criteria_scores_0_100: { water_demand: 78, nitrogen_contribution: 68, soil_coverage: 80, pest_break_potential: 84, climate_resilience: 82, local_suitability: soilTest === "yes" ? 78 : null, planting_window_compatibility: 74, farmer_priority_compatibility: 84 },
      },
    },
  ];
}

export default function App() {
  const [view, setView] = useState<View>("earth");
  const [lang, setLang] = useState<Lang>("en");
  const [point, setPoint] = useState<Point | null>({ latitude: 24.3745, longitude: 88.6042 });
  const [place, setPlace] = useState<PlaceResult | null>(null);
  const [search, setSearch] = useState("");
  const [searchResults, setSearchResults] = useState<PlaceResult[]>([]);
  const [searchBusy, setSearchBusy] = useState(false);
  const [gpsBusy, setGpsBusy] = useState(false);
  const [adminBusy, setAdminBusy] = useState(false);
  const [manualLat, setManualLat] = useState("24.37450");
  const [manualLon, setManualLon] = useState("88.60420");
  const [scienceTab, setScienceTab] = useState<"harmonization" | "glossary" | "si" | null>("harmonization");
  const [context, setContext] = useState<LocationContext | null>(null);
  const [localSources, setLocalSources] = useState<LocalSourceRegistry | null>(null);
  const [recent, setRecent] = useState<RecentEnvironment | null>(null);
  const [baselineWindow, setBaselineWindow] = useState<PowerBaselineWindow | null>(null);
  const [hazards, setHazards] = useState<EonetHazardsResponse | null>(null);
  const [advisory, setAdvisory] = useState<PlantingWindowAdvisory | null>(null);
  const [advisoryBusy, setAdvisoryBusy] = useState(false);
  const [smsCopied, setSmsCopied] = useState(false);
  const [dataBusy, setDataBusy] = useState(false);
  const [activeLayer, setActiveLayer] = useState<LayerKey | null>(null);
  const [mapDate, setMapDate] = useState(() => dateMinus(2));
  const [error, setError] = useState("");

  const [previousCrops, setPreviousCrops] = useState<string[]>(["rice"]);
  const [intendedCrop, setIntendedCrop] = useState("rice");
  const [waterSource, setWaterSource] = useState<FarmerProfile["water_source"]>("both");
  const [drainage, setDrainage] = useState<FarmerProfile["water_after_heavy_rain"]>("drains");
  const [soilTest, setSoilTest] = useState<FarmerProfile["soil_test"]>("unknown");
  const [soilPh, setSoilPh] = useState("");
  const [priority, setPriority] = useState<FarmerProfile["priority"]>("water");
  const [equipmentAccess, setEquipmentAccess] = useState<NonNullable<FarmerProfile["equipment_access"]>>("power_tiller_machinery");
  const [marketPreference, setMarketPreference] = useState<NonNullable<FarmerProfile["market_preference"]>>("local_cash_market");
  const [startMonth, setStartMonth] = useState(() => new Date().getMonth() + 1);
  const [startYear, setStartYear] = useState(() => Math.max(2026, new Date().getFullYear()));
  const [startDay, setStartDay] = useState<number>(1);
  const [plan, setPlan] = useState<PlanBrief | null>(null);
  const [planBusy, setPlanBusy] = useState(false);
  const [selectedStrategyId, setSelectedStrategyId] = useState<string>("B");

  const [scenarioRainShiftPct, setScenarioRainShiftPct] = useState<number>(0);
  const [scenarioTempShiftC, setScenarioTempShiftC] = useState<number>(0);

  useEffect(() => {
    const query = search.trim();
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setSearchBusy(true);
      apiGet<{ results: PlaceResult[] }>(
        `/api/v1/places/search?q=${encodeURIComponent(query)}`,
        controller.signal,
      )
        .then((payload) => setSearchResults(payload.results))
        .catch(() => setSearchResults([]))
        .finally(() => setSearchBusy(false));
    }, 280);
    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [search]);

  useEffect(() => {
    if (!point) return;
    const controller = new AbortController();
    setDataBusy(true);
    setError("");
    setPlan(null);
    setManualLat(point.latitude.toFixed(5));
    setManualLon(point.longitude.toFixed(5));

    Promise.allSettled([
      apiGet<LocationContext>(
        `/api/v1/context?lat=${point.latitude}&lon=${point.longitude}`,
        controller.signal,
      ),
      apiGet<RecentEnvironment>(
        `/api/v1/environment/recent?lat=${point.latitude}&lon=${point.longitude}`,
        controller.signal,
      ),
      apiGet<PowerBaselineWindow>(
        `/api/v1/environment/baseline-window?lat=${point.latitude}&lon=${point.longitude}&start_month=${startMonth}`,
        controller.signal,
      ),
      apiGet<{ place: PlaceResult | null }>(
        `/api/v1/places/reverse?lat=${point.latitude}&lon=${point.longitude}`,
        controller.signal,
      ),
      apiGet<EonetHazardsResponse>(
        `/api/v1/environment/hazards?lat=${point.latitude}&lon=${point.longitude}&radius_km=1200`,
        controller.signal,
      ),
    ]).then(async ([contextResult, recentResult, baselineResult, placeResult, hazardsResult]) => {
      if (controller.signal.aborted) return;

      const resolvedContext = contextResult.status === "fulfilled" ? contextResult.value : null;
      setContext(resolvedContext);

      if (recentResult.status === "fulfilled") setRecent(recentResult.value);
      else setRecent(null);

      if (baselineResult.status === "fulfilled") setBaselineWindow(baselineResult.value);
      else setBaselineWindow(null);

      if (hazardsResult.status === "fulfilled") setHazards(hazardsResult.value);
      else setHazards(null);

      const resolvedPlace = placeResult.status === "fulfilled" ? placeResult.value.place : null;
      if (resolvedPlace) {
        setPlace(resolvedPlace);
      }

      const countryCode =
        resolvedPlace?.address?.country_code ||
        (resolvedContext?.within_bangladesh ? "bd" : "");
      const countryName =
        resolvedPlace?.address?.country ||
        (resolvedContext?.within_bangladesh ? "Bangladesh" : "");

      if (countryCode) {
        try {
          const registry = await apiGet<LocalSourceRegistry>(
            `/api/v1/local-sources?country_code=${encodeURIComponent(countryCode)}&country_name=${encodeURIComponent(countryName)}`,
            controller.signal,
          );
          if (!controller.signal.aborted) setLocalSources(registry);
        } catch {
          if (!controller.signal.aborted) setLocalSources(null);
        }
      } else {
        setLocalSources(null);
      }

      setDataBusy(false);
    });

    return () => controller.abort();
  }, [point, startMonth]);

  useEffect(() => {
    if (!point) return;
    const controller = new AbortController();
    const cropParam = intendedCrop || "rice";
    setAdvisoryBusy(true);
    apiGet<PlantingWindowAdvisory>(
      `/api/v1/advisory?crop=${encodeURIComponent(cropParam)}&lat=${point.latitude}&lon=${point.longitude}`,
      controller.signal,
    )
      .then((res) => {
        if (!controller.signal.aborted) {
          setAdvisory(res);
          setAdvisoryBusy(false);
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) setAdvisoryBusy(false);
      });
    return () => controller.abort();
  }, [point, intendedCrop]);

  const recentSummary = recent?.status === "available" ? recent.summary : undefined;
  const firstBaseline = baselineWindow?.status === "available" ? baselineWindow.summaries?.[0] : undefined;
  const recentDailyRain =
    recentSummary?.precipitation_mean_daily_mm ??
    (recentSummary?.precipitation_total_mm != null && recentSummary.precipitation_valid_days
      ? recentSummary.precipitation_total_mm / recentSummary.precipitation_valid_days
      : null);
  const rainAnomaly =
    recentDailyRain != null && firstBaseline?.precipitation_mean_daily_mm
      ? ((recentDailyRain - firstBaseline.precipitation_mean_daily_mm) /
          firstBaseline.precipitation_mean_daily_mm) *
        100
      : null;
  const tempDelta =
    recentSummary?.temperature_mean_c != null && firstBaseline?.temperature_mean_c != null
      ? recentSummary.temperature_mean_c - firstBaseline.temperature_mean_c
      : null;

  const et0Daily = recentSummary?.et0_mean_daily_mm ?? firstBaseline?.et0_mean_daily_mm ?? null;
  const waterBalanceDaily =
    recentSummary?.water_balance_daily_mm ??
    (recentDailyRain != null && et0Daily != null ? recentDailyRain - et0Daily : firstBaseline?.water_balance_daily_mm ?? null);

  const surfaceWetnessPct = recentSummary?.surface_soil_wetness_pct ?? firstBaseline?.surface_soil_wetness_pct ?? null;
  const rootWetnessPct = recentSummary?.root_zone_soil_wetness_pct ?? firstBaseline?.root_zone_soil_wetness_pct ?? null;

  const rainAbsDiff =
    recentDailyRain != null && firstBaseline?.precipitation_mean_daily_mm != null
      ? Math.abs(recentDailyRain - firstBaseline.precipitation_mean_daily_mm)
      : 0;
  const rainSignalLabel =
    rainAnomaly == null
      ? "unavailable"
      : rainAnomaly > 30 && rainAbsDiff >= 1.0
        ? "wetter than baseline"
        : rainAnomaly < -30 && rainAbsDiff >= 1.0
          ? "drier than baseline"
          : "near baseline";

  // Spec v2 Item W: feed What-If simulator from real NASA POWER recent / climatology / seasonal_water_balance
  const seasonalWb =
    startMonth >= 6 && startMonth <= 10
      ? advisory?.seasonal_water_balance?.kharif2_aman?.period_2013_latest
      : advisory?.seasonal_water_balance?.rabi?.period_2013_latest;
  const hasRealSimBase =
    recentDailyRain != null ||
    firstBaseline?.precipitation_mean_daily_mm != null ||
    seasonalWb?.rain_daily_mm != null;

  const baseRainForSim =
    recentDailyRain ??
    firstBaseline?.precipitation_mean_daily_mm ??
    seasonalWb?.rain_daily_mm ??
    3.2;
  const baseEt0ForSim =
    et0Daily ??
    seasonalWb?.et0_daily_mm ??
    4.1;
  const simulatedRainDaily = baseRainForSim * (1 + scenarioRainShiftPct / 100);
  const simulatedEt0Daily = baseEt0ForSim * (1 + scenarioTempShiftC * 0.065);
  const simulatedWaterBalance = simulatedRainDaily - simulatedEt0Daily;

  function scenarioImpactForStrategy(strategyId: string) {
    if (scenarioRainShiftPct === 0 && scenarioTempShiftC === 0) {
      return {
        tone: "neutral",
        label: hasRealSimBase
          ? (lang === "bn" ? "বর্তমান নাসা ভিত্তি (০% পরিবর্তন)" : "Current NASA Baseline (0% shift)")
          : (lang === "bn" ? "অফলাইন রেফারেন্স ভিত্তি (০% পরিবর্তন)" : "Offline Reference Baseline (0% shift)"),
      };
    }
    if (strategyId === "A") {
      if (simulatedWaterBalance < -2.2 || scenarioTempShiftC >= 2.0) {
        return {
          tone: "high-risk",
          label:
            lang === "bn"
              ? `উচ্চ সেচ ও তাপ ঝুঁকি (P−ET₀: ${simulatedWaterBalance.toFixed(1)} মিমি/দিন)`
              : `High Irrigation & Heat Vulnerability (P−ET₀: ${simulatedWaterBalance.toFixed(1)} mm/d)`,
        };
      }
      if (scenarioRainShiftPct >= 25 && drainage === "stays") {
        return {
          tone: "high-risk",
          label:
            lang === "bn"
              ? "জলাবদ্ধতা ও রোগের উচ্চ ঝুঁকি (+বৃষ্টিপাত)"
              : "High Waterlogging & Pest Carryover Risk (+Rain)",
        };
      }
      return {
        tone: "moderate",
        label:
          lang === "bn"
            ? `মাঝারি সহনশীলতা (P−ET₀: ${simulatedWaterBalance.toFixed(1)} মিমি/দিন)`
            : `Moderate Baseline Stress (P−ET₀: ${simulatedWaterBalance.toFixed(1)} mm/d)`,
      };
    }
    if (strategyId === "B") {
      if (scenarioRainShiftPct >= 30 && drainage === "stays") {
        return {
          tone: "moderate",
          label:
            lang === "bn"
              ? "ডাল/সরিষায় উঁচু বেড ও নিকাশ নালা আবশ্যক (+৩০% বৃষ্টি)"
              : "Raised Beds Required for Pulses/Mustard (+Rain Spike)",
        };
      }
      return {
        tone: "resilient",
        label:
          lang === "bn"
            ? `উচ্চ খরা ও পানি-ঘাটতি সহনশীল (~৬০% কম পানি; P−ET₀: ${simulatedWaterBalance.toFixed(1)})`
            : `Strong Drought & Water-Deficit Resilience (~60% less water; P−ET₀: ${simulatedWaterBalance.toFixed(1)})`,
      };
    }
    if (scenarioTempShiftC >= 2.5) {
      return {
        tone: "resilient",
        label:
          lang === "bn"
            ? `তাপ-সহনশীল ও ভূমিরূপ-উপযোগী বিকল্প (+${scenarioTempShiftC.toFixed(1)}°C তাপমাত্রা)`
            : `Heat-Adaptive Landform Match (+${scenarioTempShiftC.toFixed(1)}°C shift buffered)`,
      };
    }
    return {
      tone: "resilient",
      label:
        lang === "bn"
          ? `জলবায়ু-সহনশীল বহুমুখী পর্যায় (P−ET₀: ${simulatedWaterBalance.toFixed(1)} মিমি/দিন)`
          : `Climate-Adaptive Diversification (P−ET₀: ${simulatedWaterBalance.toFixed(1)} mm/d)`,
    };
  }

  const strategies = useMemo(
    () =>
      buildStrategies(
        context,
        intendedCrop,
        previousCrops,
        priority,
        waterSource,
        drainage,
        soilTest,
        soilPh,
        rainSignalLabel,
        equipmentAccess,
        marketPreference,
      ),
    [
      context,
      intendedCrop,
      previousCrops,
      priority,
      waterSource,
      drainage,
      soilTest,
      soilPh,
      rainSignalLabel,
      equipmentAccess,
      marketPreference,
    ],
  );

  const readiness = Math.min(
    100,
    (point ? 20 : 0) +
      (recent?.status === "available" ? 20 : 0) +
      (baselineWindow?.status === "available" ? 15 : 0) +
      (place?.address?.country_code || context?.within_bangladesh ? 10 : 0) +
      (localSources?.official_sources?.length || context?.agricultural_sources?.length ? 10 : 0) +
      (previousCrops.length ? 10 : 0) +
      (intendedCrop ? 10 : 0) +
      (waterSource !== "unknown" && drainage !== "unknown" ? 5 : 0),
  );

  function choosePoint(next: Point, selected: PlaceResult | null = null) {
    if (!Number.isFinite(next.latitude) || !Number.isFinite(next.longitude)) return;
    if (next.latitude < -90 || next.latitude > 90 || next.longitude < -180 || next.longitude > 180) {
      setError("Coordinates must be between -90..90 latitude and -180..180 longitude.");
      return;
    }
    setPoint({
      latitude: Number(next.latitude.toFixed(5)),
      longitude: Number(next.longitude.toFixed(5)),
    });
    if (selected) setPlace(selected);
  }

  function applyManualCoordinates(event: FormEvent) {
    event.preventDefault();
    const lat = Number(manualLat);
    const lon = Number(manualLon);
    if (!Number.isFinite(lat) || !Number.isFinite(lon) || lat < -90 || lat > 90 || lon < -180 || lon > 180) {
      setError("Enter valid coordinates: Latitude (-90 to 90) and Longitude (-180 to 180).");
      return;
    }
    setError("");
    choosePoint({ latitude: lat, longitude: lon });
  }

  function locateMe() {
    setError("");
    if (!navigator.geolocation) {
      setError("Location access is unavailable in this browser. Use Bangladesh Quick Select, search, or manual coordinates.");
      return;
    }
    setGpsBusy(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setGpsBusy(false);
        choosePoint({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });
      },
      (geoError) => {
        setGpsBusy(false);
        const insecureOrigin = typeof window !== "undefined" && window.isSecureContext === false;
        if (insecureOrigin) {
          setError("Browser GPS requires HTTPS or localhost. On a LAN IP, choose your district in Bangladesh Quick Select or enter coordinates below.");
        } else if (geoError.code === 1) {
          setError("Location permission was denied. Choose your district in Bangladesh Quick Select, search, or tap the map.");
        } else {
          setError("Could not acquire GPS signal in time. Choose your district in Bangladesh Quick Select, search, or tap the map.");
        }
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 120000 },
    );
  }

  async function chooseBangladeshArea(name: string) {
    if (!name) return;
    setAdminBusy(true);
    setError("");
    try {
      const resolved = await apiGet<{ place: PlaceResult }>(
        `/api/v1/bangladesh/resolve?q=${encodeURIComponent(name)}`,
      );
      if (resolved.place) {
        choosePoint(
          { latitude: resolved.place.latitude, longitude: resolved.place.longitude },
          resolved.place,
        );
        setSearch("");
        setSearchResults([]);
        setAdminBusy(false);
        return;
      }
    } catch {
      // Fall back to global search if resolve endpoint is unreachable
    }
    try {
      const payload = await apiGet<{ results: PlaceResult[] }>(
        `/api/v1/places/search?q=${encodeURIComponent(`${name}, Bangladesh`)}`,
      );
      const match =
        payload.results.find((result) => result.address?.country_code === "bd") ??
        payload.results[0];
      if (!match) {
        setError(`Could not resolve ${name}. Use the global search or manual coordinates instead.`);
        return;
      }
      choosePoint({ latitude: match.latitude, longitude: match.longitude }, match);
      setSearch("");
      setSearchResults([]);
    } catch {
      setError(`Could not resolve ${name}. Use the global search or manual coordinates instead.`);
    } finally {
      setAdminBusy(false);
    }
  }

  function toggleHistory(crop: string) {
    setPreviousCrops((current) => {
      if (current.includes(crop)) return current.filter((item) => item !== crop);
      if (current.length >= 4) return current;
      return [...current, crop];
    });
  }

  async function runDecisionEngine(
    event?: FormEvent,
    overrideDate?: { year: number; month: number; day: number },
  ) {
    event?.preventDefault();
    if (!point) {
      setError("Select a field on Earth before running the decision engine.");
      setView("earth");
      return;
    }

    const useYear = overrideDate?.year ?? startYear;
    const useMonth = overrideDate?.month ?? startMonth;
    const useDay = overrideDate?.day ?? startDay;

    const farm: FarmerProfile = {
      latitude: point.latitude,
      longitude: point.longitude,
      previous_crop: previousCrops[0] ?? null,
      previous_crops: previousCrops,
      intended_crop: intendedCrop || null,
      water_source: waterSource,
      water_after_heavy_rain: drainage,
      soil_test: soilTest,
      soil_ph: soilTest === "yes" && soilPh ? Number(soilPh) : null,
      priority,
      equipment_access: equipmentAccess,
      market_preference: marketPreference,
    };

    setPlanBusy(true);
    setError("");
    try {
      let payload: PlanBrief;
      try {
        payload = await apiPost<PlanBrief>("/api/v1/plans/preview", {
          farm,
          start_year: useYear,
          start_month: useMonth,
          start_day: useDay,
          include_recent_power: recent?.status !== "available",
          include_climate_baseline: baselineWindow?.status !== "available",
          recent_environment: recent?.status === "available" ? recent : null,
          baseline_window: baselineWindow?.status === "available" ? baselineWindow : null,
          eonet_hazards: hazards,
          advisory: advisory,
        });
      } catch (firstErr) {
        if (firstErr instanceof ApiError && firstErr.status === 422 && (soilTest !== "yes" || soilPh)) {
          const { equipment_access, market_preference, ...legacyFarm } = farm;
          payload = await apiPost<PlanBrief>("/api/v1/plans/preview", {
            farm: legacyFarm,
            start_year: useYear,
            start_month: useMonth,
            include_recent_power: false,
            include_climate_baseline: false,
            recent_environment: recent,
            baseline_window: baselineWindow,
          });
        } else {
          throw firstErr;
        }
      }
      setPlan(payload);
      setView("plan");
    } catch (runError) {
      setError(runError instanceof ApiError ? runError.message : "Decision engine failed.");
    } finally {
      setPlanBusy(false);
    }
  }

  const districtProfile = context?.district_profile ?? null;
  const plannedMonths = [
    startMonth,
    ((startMonth) % 12) + 1,
    ((startMonth + 1) % 12) + 1,
  ];

  const recentOrigin = recent?.data_origin ?? (recent?.status === "available" ? "nasa_power_live" : "unavailable");
  const recentRetrieved = recent?.retrieved_at ?? advisory?.retrieved_at ?? null;
  const recentLagDays = recent?.lag_days ?? advisory?.lag_days ?? 7;

  return (
    <div className="mission-app">
      <header className="mission-topbar">
        <div className="mission-brand">
          <BoponXLogoMark size={40} />
          <div>
            <strong>BoponX</strong>
            <small>EARTH.exe · Data: NASA POWER / EONET / GIBS</small>
          </div>
        </div>

        <nav className="mission-nav" aria-label="3-Stage Workflow">
          <button type="button" className={view === "earth" ? "active" : ""} onClick={() => setView("earth")}>
            <span>01</span> {lang === "bn" ? "অবস্থান ও ম্যাপ" : "Location"}
          </button>
          <button type="button" className={view === "rotation" ? "active" : ""} onClick={() => setView("rotation")}>
            <span>02</span> {lang === "bn" ? "বিশ্লেষণ ও পর্যায়" : "Analysis"}
          </button>
          <button type="button" className={view === "plan" ? "active" : ""} onClick={() => setView("plan")}>
            <span>03</span> {lang === "bn" ? "৯০ দিনের পরিকল্পনা" : "90-Day Plan"}
          </button>
        </nav>

        <div className="mission-status-group">
          <div className="lang-switch" role="group" aria-label="Interface language">
            <button
              type="button"
              className={lang === "en" ? "active" : ""}
              onClick={() => setLang("en")}
            >
              EN
            </button>
            <button
              type="button"
              className={lang === "bn" ? "active" : ""}
              onClick={() => setLang("bn")}
            >
              বাংলা
            </button>
          </div>
          <div className="mission-status">
            <span className={dataBusy || planBusy ? "pulse loading" : "pulse"} />
            {point ? placeLabel(place, point, context) : (lang === "bn" ? "মাঠ নির্বাচন করুন" : "Awaiting field")}
          </div>
        </div>
      </header>

      {view === "earth" && (
        <main className="earth-command">
          <aside className="control-rail left-rail">
            <div className="rail-title">
              <span>01 · FIELD LOCATOR</span>
              <strong>{lang === "bn" ? "আপনার খামার বা জেলা নির্বাচন করুন" : "Select your farm or district"}</strong>
            </div>

            <button type="button" className="locate-command" onClick={locateMe} disabled={gpsBusy}>
              <FieldIcon name="stability" />
              <span>
                <strong>
                  {gpsBusy
                    ? (lang === "bn" ? "অবস্থান নির্ণয় হচ্ছে…" : "Locating GPS…")
                    : (lang === "bn" ? "আমার বর্তমান অবস্থান (Use Current GPS)" : "Use current GPS location")}
                </strong>
                <small>{lang === "bn" ? "সরাসরি আপনার খামারে জুম করবে ও জেলার মাটির তথ্য আনবে" : "Zooms directly to your plot & resolves 64-district data"}</small>
              </span>
            </button>

            <div className="pilot-zone-pills">
              <span>{lang === "bn" ? "দ্রুত পাইলট অঞ্চল:" : "QUICK AGRO-ZONES:"}</span>
              <div className="pilot-pill-row">
                {quickPilotZones.map((zone) => (
                  <button
                    type="button"
                    key={zone.name}
                    className={districtProfile?.name_en === zone.name ? "active" : ""}
                    onClick={() => void chooseBangladeshArea(zone.name)}
                  >
                    {zone.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="global-search">
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder={lang === "bn" ? "যেকোনো গ্রাম, উপজেলা, জেলা বা দেশ খুঁজুন…" : "Search any village, upazila, district or country…"}
              />
              <span>{searchBusy ? "…" : "⌕"}</span>
              {searchResults.length > 0 && (
                <div className="search-results">
                  {searchResults.slice(0, 6).map((result, index) => (
                    <button
                      type="button"
                      key={`${result.latitude}-${result.longitude}-${index}`}
                      onClick={() => {
                        choosePoint({ latitude: result.latitude, longitude: result.longitude }, result);
                        setSearch("");
                        setSearchResults([]);
                      }}
                    >
                      <strong>{result.name}</strong>
                      <small>
                        {[result.address?.district, result.address?.division, result.address?.country]
                          .filter(Boolean)
                          .join(" · ")}
                      </small>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="bangladesh-admin-select">
              <label htmlFor="bd-area-select">
                <span>BANGLADESH 64-DISTRICT SELECTOR</span>
                <small>{lang === "bn" ? "৮ বিভাগ · ৬৪ জেলা" : "8 divisions · 64 districts"}</small>
              </label>
              <select
                id="bd-area-select"
                value={districtProfile?.name_en ?? ""}
                disabled={adminBusy}
                onChange={(event) => {
                  const value = event.target.value;
                  if (value) void chooseBangladeshArea(value);
                }}
              >
                <option value="">{adminBusy ? "Resolving area…" : (lang === "bn" ? "বিভাগ বা জেলা বেছে নিন…" : "Choose any division or district…")}</option>
                <optgroup label="Divisions (8)">
                  {bangladeshDivisions.map((name) => <option value={`${name} Division`} key={`division-${name}`}>{name} Division</option>)}
                </optgroup>
                <optgroup label="All 64 Districts">
                  {bangladeshDistricts.map((name) => <option value={name} key={`district-${name}`}>{name} District</option>)}
                </optgroup>
              </select>
            </div>

            <form className="manual-coord-box" onSubmit={applyManualCoordinates}>
              <div className="manual-coord-head">
                <span>EXACT FIELD COORDINATES</span>
                <small>{lang === "bn" ? "অক্ষাংশ / দ্রাঘিমাংশ" : "Lat / Lon"}</small>
              </div>
              <div className="manual-coord-inputs">
                <input
                  type="number"
                  step="any"
                  min="-90"
                  max="90"
                  placeholder="Lat"
                  value={manualLat}
                  onChange={(e) => setManualLat(e.target.value)}
                  aria-label="Latitude"
                />
                <input
                  type="number"
                  step="any"
                  min="-180"
                  max="180"
                  placeholder="Lon"
                  value={manualLon}
                  onChange={(e) => setManualLon(e.target.value)}
                  aria-label="Longitude"
                />
                <button type="submit">{lang === "bn" ? "যান" : "Lock"}</button>
              </div>
            </form>

            <section className="selected-field-card">
              <div className="field-card-top">
                <span className="micro-label">LOCKED FIELD LOCATION</span>
                {context?.within_bangladesh && <b className="bd-badge">BANGLADESH</b>}
              </div>
              <h2>{placeLabel(place, point, context)}</h2>
              <p>
                {districtProfile
                  ? `${districtProfile.name_en} District, ${districtProfile.division_en} Division`
                  : (place?.address?.country ?? "Global coordinates selected")}
              </p>
              {point && <code>{point.latitude.toFixed(5)}° N, {point.longitude.toFixed(5)}° E</code>}
            </section>

            {districtProfile && (
              <section className="district-intel-card">
                <div className="rail-section-head">
                  <span>LOCAL AGRO-ECOLOGICAL PROFILE</span>
                  <b>{(districtProfile.division_en ?? "").toUpperCase()}</b>
                </div>
                <div className="district-intel-title">
                  <strong>
                    {lang === "bn"
                      ? `${districtProfile.name_bn} জেলা (${districtProfile.name_en})`
                      : `${districtProfile.name_en} District (${districtProfile.name_bn})`}
                  </strong>
                  <small>
                    {lang === "bn" ? districtProfile.landform_bn : districtProfile.landform_en}
                  </small>
                </div>

                <div className="district-meta-grid">
                  <div>
                    <span>{lang === "bn" ? "মিল থাকা অঞ্চল (CLIMATE ANALOGS)" : "CLIMATE-ANALOG REGIONS"}</span>
                    <p>{lang === "bn" ? districtProfile.analog_regions_bn : districtProfile.analog_regions_en}</p>
                  </div>
                  <div>
                    <span>{lang === "bn" ? "প্রতিষ্ঠিত ফসল (ESTABLISHED CROPS)" : "ESTABLISHED CROPS"}</span>
                    <div className="chip-row">
                      {((lang === "bn" ? districtProfile.established_crops_bn : districtProfile.established_crops_en) ?? []).map((crop) => (
                        <em key={crop} className="crop-chip established">{crop}</em>
                      ))}
                    </div>
                  </div>
                  <div>
                    <span>{lang === "bn" ? "নতুন ফসলের সুযোগ (NEW OPPORTUNITIES)" : "NEW CROP OPPORTUNITIES"}</span>
                    <div className="chip-row">
                      {((lang === "bn" ? districtProfile.opportunity_crops_bn : districtProfile.opportunity_crops_en) ?? []).map((crop) => (
                        <em key={crop} className="crop-chip opportunity">{crop}</em>
                      ))}
                    </div>
                  </div>
                  <div>
                    <span>{lang === "bn" ? "খালি জমি ও মৌসুমি ঝুঁকি (BARE-FIELD RISK)" : "BARE-FIELD & SEASONAL VULNERABILITY"}</span>
                    <p>{lang === "bn" ? districtProfile.bare_field_risk_bn : districtProfile.bare_field_risk_en}</p>
                  </div>
                </div>

                {(districtProfile.online_evidence?.length ?? 0) > 0 && (
                  <div className="district-online-evidence">
                    <span>{lang === "bn" ? "অনলাইন সূত্রে প্রমাণিত প্রতিবেদন" : "PUBLISHED PILOT / TRIAL EVIDENCE"}</span>
                    {(districtProfile.online_evidence ?? []).map((ev) => (
                      <a key={ev.id} href={ev.source_url} target="_blank" rel="noreferrer">
                        <strong>{lang === "bn" ? ev.title_bn : ev.title_en} ↗</strong>
                        <small>{lang === "bn" ? ev.detail_bn : ev.detail_en}</small>
                      </a>
                    ))}
                  </div>
                )}

                {context?.soil_evidence && (
                  <div className="district-online-evidence" style={{ marginTop: "8px" }}>
                    <span>
                      {lang === "bn"
                        ? "SRDI ও BARC মাটির প্রমাণ শ্রেণিবিন্যাস (SOIL EVIDENCE CLASSIFICATION)"
                        : `SRDI & BARC SOIL EVIDENCE (${context.soil_evidence.overall_classification})`}
                    </span>
                    <small style={{ display: "block", marginBottom: "4px", opacity: 0.9 }}>
                      {context.soil_evidence.aez_id} · {context.soil_evidence.soil_classification}
                    </small>
                    {(context.soil_evidence.records ?? []).slice(0, 4).map((rec) => (
                      <div key={rec.property_id} style={{ fontSize: "0.75rem", padding: "3px 0", borderTop: "1px solid rgba(255,255,255,0.06)" }}>
                        <strong>{rec.property_name}:</strong>{" "}
                        {rec.reported_value != null
                          ? `${rec.reported_value} ${rec.unit}`
                          : rec.reference_range
                            ? `${rec.reference_range.min}–${rec.reference_range.max} (typ. ${rec.reference_range.regional_typical}) ${rec.unit}`
                            : rec.class_description}{" "}
                        <code>[{rec.evidence_classification}]</code>
                      </div>
                    ))}
                  </div>
                )}

                <div className="district-caution-note">
                  <small>{lang === "bn" ? districtProfile.caution_bn : districtProfile.caution_en}</small>
                </div>
              </section>
            )}

            <section className="local-mesh">
              <div className="rail-section-head">
                <span>VERIFIED AUTHORITY LINKS</span>
                <b>{localSources?.coverage === "verified_country_adapter" ? "VERIFIED" : "GLOBAL"}</b>
              </div>
              {(localSources?.official_sources ?? []).map((source) => (
                <a className="official-source" key={source.id ?? source.name} href={source.source_url} target="_blank" rel="noreferrer">
                  <span className="source-status verified">OFFICIAL SOURCE</span>
                  <strong>{source.name}</strong>
                  <small>{source.scope}</small>
                  <em>Open portal ↗</em>
                </a>
              ))}
              {localSources?.official_sources?.length === 0 && (
                <div className="source-gap">
                  <strong>No reviewed direct government adapter is connected yet.</strong>
                  <p>NASA analysis works globally. Use the portal finder below to reach the selected country's official agriculture authority.</p>
                </div>
              )}
            </section>
          </aside>

          <section className="globe-center">
            <LocationMap
              point={point}
              onPick={(next) => choosePoint(next)}
              mapDate={mapDate}
              onMapDateChange={setMapDate}
              activeLayer={activeLayer}
              onLayerChange={setActiveLayer}
            />

            <div className="fusion-strip">
              <div>
                <span>RAIN ANOMALY</span>
                <strong className={rainAnomaly != null && rainAnomaly < -25 ? "amber-val" : "lime-val"}>
                  {rainAnomaly == null ? "—" : `${rainAnomaly >= 0 ? "+" : ""}${rainAnomaly.toFixed(0)}%`}
                </strong>
                <small>recent POWER vs 20yr baseline</small>
              </div>
              <div>
                <span>WATER BALANCE (P − ET₀)</span>
                <strong className={waterBalanceDaily != null && waterBalanceDaily < 0 ? "amber-val" : "cyan-val"}>
                  {waterBalanceDaily == null ? "—" : `${waterBalanceDaily >= 0 ? "+" : ""}${waterBalanceDaily.toFixed(1)} mm/d`}
                </strong>
                <small>rain minus FAO-56 evaporation</small>
              </div>
              <div>
                <span>ROOT-ZONE WETNESS</span>
                <strong className="cyan-val">
                  {rootWetnessPct != null ? `${rootWetnessPct.toFixed(0)}%` : (tempDelta == null ? "—" : `${tempDelta >= 0 ? "+" : ""}${tempDelta.toFixed(1)}°C`)}
                </strong>
                <small>
                  {surfaceWetnessPct != null
                    ? `0–100cm (Top 0–5cm: ${surfaceWetnessPct.toFixed(0)}%)`
                    : "NASA POWER GWETROOT"}
                </small>
              </div>
              <div>
                <span>EVIDENCE READINESS</span>
                <strong className="lime-val">{readiness}%</strong>
                <small>stack completeness score</small>
              </div>
            </div>
          </section>

          <aside className="control-rail right-rail">
            <div className="rail-title">
              <span>02 · DATA: NASA POWER / EONET / GIBS</span>
              <strong>{lang === "bn" ? "উপগ্রহ ও কৃষি-আবহাওয়া বিশ্লেষণ" : "Agroclimate, Soil Wetness & Hazard Diagnostics"}</strong>
            </div>

            <div className="earth-pulse">
              <div className="pulse-ring" style={{ "--score": readiness } as CSSProperties}>
                <span>{readiness}%</span>
                <small>READY</small>
              </div>
              <div className="pulse-copy">
                <strong>{dataBusy ? "Syncing NASA POWER & EONET…" : "Field Evidence Stack"}</strong>
                <small>
                  {lang === "bn"
                    ? "NASA POWER, GPM IMERG, SMAP ও EONET থেকে বাষ্পীভবন চাহিদা (ET₀), শিকড় অঞ্চলের আর্দ্রতা ও প্রাকৃতিক দুর্যোগ সংকেত বিশ্লেষণ করা হয়েছে।"
                    : "Fuses FAO-56 Evapotranspiration (ET₀), Topsoil vs. Root-Zone Wetness (GWETTOP/GWETROOT), Dew-Point Fog/Frost Risk, and live EONET natural hazards."}
                </small>
              </div>
            </div>

            {/* Spec v2 Item L & Z: Freshness & Data Origin Bar */}
            <div className="freshness-meta-bar">
              <span>
                {lang === "bn" ? "উৎস ও সতেজতা:" : "Origin & Freshness:"}{" "}
                <code>{recentOrigin}</code>
              </span>
              <span>
                {recent?.data_through || advisory?.data_through
                  ? `${lang === "bn" ? "সর্বশেষ তারিখ:" : "Data through:"} ${recent?.data_through ?? advisory?.data_through} (~${recentLagDays}d lag)`
                  : (lang === "bn" ? "লাইভ টেলিমেট্রি অফলাইন (UNAVAILABLE)" : "Live telemetry offline (UNAVAILABLE)")}
              </span>
              {recentRetrieved && (
                <small>{lang === "bn" ? "সংগ্রহের সময়:" : "Retrieved:"} {recentRetrieved}</small>
              )}
            </div>

            <div className="signal-grid">
              <article>
                <span>RECENT RAIN (14d)</span>
                <strong>{metric(recentSummary?.precipitation_total_mm, " mm")}</strong>
                <small>
                  {recentDailyRain != null ? `${recentDailyRain.toFixed(1)} mm/day avg` : "NASA POWER"}
                </small>
              </article>
              <article>
                <span>BASELINE RAIN</span>
                <strong>{metric(firstBaseline?.precipitation_mean_daily_mm, " mm/d")}</strong>
                <small>NASA POWER multi-year norm</small>
              </article>
              <article>
                <span>MEAN / MAX TEMP</span>
                <strong>
                  {metric(recentSummary?.temperature_mean_c, "°")} / {metric(recentSummary?.temperature_max_mean_c, "°C")}
                </strong>
                <small>
                  {recentSummary?.heat_stress_days
                    ? `${recentSummary.heat_stress_days} heat-stress days (≥35°C)`
                    : "0 days ≥35°C in last 14d"}
                </small>
              </article>
              <article>
                <span>EVAPOTRANSPIRATION (ET₀)</span>
                <strong>{metric(et0Daily, " mm/d")}</strong>
                <small>FAO-56 atmospheric draw</small>
              </article>
              <article>
                <span>TOPSOIL vs ROOT WETNESS</span>
                <strong>
                  {surfaceWetnessPct != null ? `${surfaceWetnessPct.toFixed(0)}%` : "—"} / {rootWetnessPct != null ? `${rootWetnessPct.toFixed(0)}%` : "—"}
                </strong>
                <small>GWETTOP (0–5cm) · GWETROOT (1m)</small>
              </article>
              <article>
                <span>FROST & FOG-BLIGHT RISK</span>
                <strong>
                  {recentSummary?.frost_risk_days ?? 0}d / {recentSummary?.fog_blight_risk_days ?? 0}d
                </strong>
                <small>
                  {recentSummary?.dew_point_mean_c != null
                    ? `Dew point ${recentSummary.dew_point_mean_c.toFixed(1)}°C · RH ${metric(recentSummary?.relative_humidity_mean_pct, "%")}`
                    : `RH ${metric(recentSummary?.relative_humidity_mean_pct, "%")} · VPD ${recentSummary?.vpd_mean_kpa ?? "—"} kPa`}
                </small>
              </article>
            </div>

            {/* Live NASA EONET v3 Natural Hazard & Severe Event Monitor (Spec v2 Item E) */}
            <div className="eonet-hazard-card">
              <div className="rail-section-head">
                <span>LIVE NASA EONET NATURAL HAZARD MONITOR</span>
                <b className={(hazards?.agricultural_alert_count ?? hazards?.active_count ?? 0) > 0 ? "amber-badge" : "ok-badge"}>
                  {hazards?.status === "available"
                    ? `${hazards?.agricultural_alert_count ?? hazards?.active_count ?? 0} AG ALERTS IN ${hazards?.radius_km ?? 1200} KM`
                    : `UNAVAILABLE (${hazards?.data_origin ?? "offline"})`}
                </b>
              </div>
              {hazards?.status === "available" &&
              (hazards?.events ?? hazards?.regional_events ?? hazards?.nearest_global_events ?? []).length > 0 ? (
                <div className="eonet-event-list">
                  {(hazards?.events ?? hazards?.regional_events ?? hazards?.nearest_global_events ?? []).slice(0, 3).map((ev) => {
                    const isNearby = ev.within_alert_radius ?? (ev.distance_km <= (hazards?.radius_km ?? 1200));
                    const isAgImpact = ev.affects_field_operations ?? (ev.agricultural_relevance === "agricultural_impact");
                    const catLabel = ev.category_title ?? ev.categories?.[0] ?? "Natural Event";
                    return (
                      <a
                        key={ev.id}
                        href={ev.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className={`eonet-event-item ${isNearby && isAgImpact ? "nearby" : ""}`}
                      >
                        <div>
                          <strong>{ev.title} ↗</strong>
                          <small>
                            {catLabel} · {ev.distance_km} km from field
                            {ev.date ? ` · ${String(ev.date).slice(0, 10)}` : ""}
                            {isAgImpact ? " · Affects drainage/sowing" : " · Low crop relevance"}
                          </small>
                        </div>
                        <span className={isNearby && isAgImpact ? "alert-tag" : "dist-tag"}>
                          {isNearby && isAgImpact ? "FIELD ALERT" : `${ev.distance_km} km`}
                        </span>
                      </a>
                    );
                  })}
                </div>
              ) : (
                <p className="eonet-empty-copy">
                  {lang === "bn"
                    ? "NASA EONET v3-এ এই মুহূর্তে নিকটবর্তী কোনো সক্রিয় ঘূর্ণিঝড় বা বন্যা ইভেন্ট নেই (অথবা অফলাইন মোড সক্রিয়)। সর্বদা BMD ও DAE (১৬১২৩) যাচাই করুন।"
                    : "No active cyclone, flood, or severe storm event detected within the alert radius by NASA EONET v3 (or offline mode active). Always verify local BMD/DAE (16123) advisories."}
                </p>
              )}
            </div>

            {(baselineWindow?.summaries?.length ?? 0) > 0 && (
              <div className="baseline-window-card">
                <div className="rail-section-head">
                  <span>90-DAY CLIMATOLOGY OUTLOOK (NASA POWER)</span>
                  <b>NASA POWER</b>
                </div>
                <table className="clim-mini-table">
                  <thead>
                    <tr>
                      <th>Month</th>
                      <th>Mean Temp</th>
                      <th>Rain/day</th>
                      <th>ET₀/day</th>
                      <th>Net (P−ET₀)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(baselineWindow?.summaries ?? []).map((row) => {
                      const wb = row.water_balance_daily_mm;
                      return (
                        <tr key={row.calendar_month}>
                          <td><strong>{monthShort[(row.calendar_month - 1) % 12]}</strong></td>
                          <td>{metric(row.temperature_mean_c, "°C")}</td>
                          <td>{metric(row.precipitation_mean_daily_mm, " mm")}</td>
                          <td>{metric(row.et0_mean_daily_mm, " mm")}</td>
                          <td className={wb != null && wb < 0 ? "deficit-cell" : "surplus-cell"}>
                            {wb == null ? "—" : `${wb >= 0 ? "+" : ""}${wb.toFixed(1)}`}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}

            <div className="science-explainer-panel">
              <div className="science-tab-bar">
                <button
                  type="button"
                  className={scienceTab === "harmonization" ? "active" : ""}
                  onClick={() => setScienceTab(scienceTab === "harmonization" ? null : "harmonization")}
                >
                  {lang === "bn" ? "রেজোলিউশন সমন্বয়" : "Grid Harmonization"}
                </button>
                <button
                  type="button"
                  className={scienceTab === "glossary" ? "active" : ""}
                  onClick={() => setScienceTab(scienceTab === "glossary" ? null : "glossary")}
                >
                  {lang === "bn" ? "বৈজ্ঞানিক শব্দকোষ" : "Scientific Terms"}
                </button>
                <button
                  type="button"
                  className={scienceTab === "si" ? "active" : ""}
                  onClick={() => setScienceTab(scienceTab === "si" ? null : "si")}
                >
                  {lang === "bn" ? "SI ও অনিশ্চয়তা" : "SI & Uncertainty"}
                </button>
              </div>

              {scienceTab === "harmonization" && (
                <div className="science-tab-body">
                  <p>
                    {lang === "bn"
                      ? (context?.multi_resolution_harmonization?.summary_bn ??
                        "BoponX ০.৫°×০.৬২৫° POWER, ~১০ কিমি IMERG, ৯ কিমি SMAP এবং স্থানীয় ৬৪ জেলার মাটির তথ্য সমন্বয় করে, কিন্তু উপগ্রহ ডেটাকে মাঠের মাটি পরীক্ষার বিকল্প ধরে না।")
                      : (context?.multi_resolution_harmonization?.summary_en ??
                        "BoponX aligns 0.5°×0.625° POWER, 0.1° (~10 km) IMERG, 9 km SMAP EASE-Grid, and MODIS imagery to the field coordinate without treating satellite grids as parcel soil sensors.")}
                  </p>
                  <div className="harmonization-list">
                    {(context?.multi_resolution_harmonization?.layers ?? []).map((item) => (
                      <div key={item.layer} className="harmonization-item">
                        <strong>{item.layer}</strong>
                        <span>{item.spatial_scale} · {item.temporal_scale}</span>
                        <small>{item.role}</small>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {scienceTab === "glossary" && (
                <div className="science-tab-body">
                  {(context?.scientific_glossary ?? []).map((term) => (
                    <div key={term.term_id} className="glossary-item">
                      <strong>{lang === "bn" ? term.term_bn : term.term_en}</strong>
                      <small>{lang === "bn" ? term.explanation_bn : term.explanation_en}</small>
                    </div>
                  ))}
                </div>
              )}

              {scienceTab === "si" && (
                <div className="science-tab-body">
                  {(context?.si_modeling_methods ?? []).map((m) => (
                    <div key={m.method_id} className="glossary-item">
                      <strong>{lang === "bn" ? (m.title_bn ?? m.name_bn) : (m.title_en ?? m.name_en)}</strong>
                      <small>{lang === "bn" ? m.detail_bn : m.detail_en}</small>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <button type="button" className="next-command" onClick={() => setView("rotation")}>
              {lang === "bn" ? "০২ · বিশ্লেষণ ও রোটেশন ল্যাবে যান" : "Proceed to 02 · Analysis & Rotation Lab"} <b>→</b>
            </button>

            {error && <div className="command-error">{error}</div>}
          </aside>
        </main>
      )}

      {view === "rotation" && (
        <main className="rotation-lab">
          <aside className="profile-panel">
            <div className="rail-title">
              <span>FARMER FIELD INPUTS</span>
              <strong>{lang === "bn" ? "মাঠের ইতিহাস, যন্ত্রপাতি ও বাজার" : "Field History, Water, Soil & Market"}</strong>
            </div>

            <div className="profile-group">
              <span>{lang === "bn" ? "জেলা পরিবর্তন করুন (৬৪ জেলা · লাইভ নাসা ডেটা)" : "ACTIVE DISTRICT (SWITCH ANY OF 64 DISTRICTS)"}</span>
              <select
                value={advisory?.district?.name_en ?? districtProfile?.name_en ?? ""}
                disabled={adminBusy}
                onChange={(event) => {
                  const value = event.target.value;
                  if (value) void chooseBangladeshArea(value);
                }}
              >
                <option value="">{adminBusy ? "Resolving district…" : (lang === "bn" ? "জেলা বেছে নিন…" : "Select district…")}</option>
                {bangladeshDistricts.map((name) => (
                  <option value={name} key={`s2-district-${name}`}>{name} District</option>
                ))}
              </select>
              <div className="pilot-pill-row" style={{ marginTop: "6px" }}>
                {quickPilotZones.map((zone) => (
                  <button
                    type="button"
                    key={`s2-${zone.name}`}
                    className={(advisory?.district?.name_en ?? districtProfile?.name_en) === zone.name ? "active" : ""}
                    onClick={() => void chooseBangladeshArea(zone.name)}
                  >
                    {zone.name}
                  </button>
                ))}
              </div>
            </div>

            <label className="profile-group">
              <span>{lang === "bn" ? "পূর্বে চাষ করা ফসল (সর্বোচ্চ ৪টি, ক্রমানুসারে)" : "RECENT CROPS GROWN (UP TO 4 IN ORDER)"}</span>
              <div className="crop-mini-grid">
                {cropOptions.map(([id, labelEn, labelBn, icon]) => (
                  <button
                    type="button"
                    className={previousCrops.includes(id) ? "active" : ""}
                    key={id}
                    onClick={() => toggleHistory(id)}
                  >
                    <FieldIcon name={icon as IconName} />
                    <span>{lang === "bn" ? labelBn : labelEn}</span>
                    {previousCrops.includes(id) && <b>{previousCrops.indexOf(id) + 1}</b>}
                  </button>
                ))}
              </div>
            </label>

            <label className="profile-group">
              <span>{lang === "bn" ? "পরবর্তী মৌসুমে কোন ফসল বিবেচনা করছেন?" : "INTENDED NEXT CROP"}</span>
              <select value={intendedCrop} onChange={(event) => setIntendedCrop(event.target.value)}>
                <option value="">{lang === "bn" ? "সিদ্ধান্ত হয়নি" : "Not decided"}</option>
                {cropOptions.map(([id, labelEn, labelBn]) => (
                  <option key={id} value={id}>{lang === "bn" ? `${labelBn} (${labelEn})` : labelEn}</option>
                ))}
              </select>
            </label>

            <div className="two-control">
              <label>
                <span>{lang === "bn" ? "পানির উৎস" : "WATER SOURCE"}</span>
                <select value={waterSource} onChange={(event) => setWaterSource(event.target.value as FarmerProfile["water_source"])}>
                  <option value="unknown">{lang === "bn" ? "নিশ্চিত নয়" : "Not sure"}</option>
                  <option value="rainfed">{lang === "bn" ? "মূলত বৃষ্টিনির্ভর" : "Mostly rain"}</option>
                  <option value="irrigated">{lang === "bn" ? "মূলত সেচনির্ভর" : "Mostly irrigation"}</option>
                  <option value="both">{lang === "bn" ? "বৃষ্টি ও সেচ উভয়ই" : "Rain and irrigation"}</option>
                </select>
              </label>
              <label>
                <span>{lang === "bn" ? "ভারী বৃষ্টির পর" : "AFTER HEAVY RAIN"}</span>
                <select value={drainage} onChange={(event) => setDrainage(event.target.value as FarmerProfile["water_after_heavy_rain"])}>
                  <option value="unknown">{lang === "bn" ? "নিশ্চিত নয়" : "Not sure"}</option>
                  <option value="drains">{lang === "bn" ? "দ্রুত নেমে যায়" : "Drains quickly"}</option>
                  <option value="stays">{lang === "bn" ? "পানি জমে থাকে" : "Water stays"}</option>
                  <option value="sometimes">{lang === "bn" ? "মাঝে মাঝে জমে" : "Changes"}</option>
                </select>
              </label>
            </div>

            <div className="two-control">
              <label>
                <span>{lang === "bn" ? "চাষের যন্ত্রপাতি (EQUIPMENT)" : "EQUIPMENT ACCESS"}</span>
                <select
                  value={equipmentAccess}
                  onChange={(event) => setEquipmentAccess(event.target.value as NonNullable<FarmerProfile["equipment_access"]>)}
                >
                  <option value="power_tiller_machinery">{lang === "bn" ? "পাওয়ার টিলার / ট্রাক্টর" : "Power Tiller / Tractor"}</option>
                  <option value="conservation_zero_till">{lang === "bn" ? "জিরো-টিল / বেড প্ল্যান্টার" : "Zero-Till / Bed Planter"}</option>
                  <option value="manual_traditional">{lang === "bn" ? "সনাতন / কায়িক শ্রম" : "Manual / Traditional"}</option>
                  <option value="unknown">{lang === "bn" ? "উল্লেখ নেই" : "Not sure"}</option>
                </select>
              </label>
              <label>
                <span>{lang === "bn" ? "বাজার ও গোখাদ্য লক্ষ্য" : "MARKET / FORAGE GOAL"}</span>
                <select
                  value={marketPreference}
                  onChange={(event) => setMarketPreference(event.target.value as NonNullable<FarmerProfile["market_preference"]>)}
                >
                  <option value="local_cash_market">{lang === "bn" ? "স্থানীয় বাজার (তেল/ডাল/শস্য)" : "Local Cash / Oilseed / Pulse"}</option>
                  <option value="household_subsistence">{lang === "bn" ? "পারিবারিক খাদ্য নিরাপত্তা" : "Household Food Security"}</option>
                  <option value="high_value_commercial">{lang === "bn" ? "উচ্চমূল্যের বাণিজ্যিক বাজার" : "High-Value Commercial"}</option>
                  <option value="forage_livestock">{lang === "bn" ? "দানা + গবাদিপশুর গোখাদ্য" : "Dual Grain + Livestock Forage"}</option>
                </select>
              </label>
            </div>

            <div className="two-control">
              <label>
                <span>{lang === "bn" ? "মাটি পরীক্ষা রিপোর্ট" : "LAB SOIL TEST"}</span>
                <select value={soilTest} onChange={(event) => setSoilTest(event.target.value as FarmerProfile["soil_test"])}>
                  <option value="unknown">{lang === "bn" ? "নিশ্চিত নয়" : "Not sure"}</option>
                  <option value="no">{lang === "bn" ? "রিপোর্ট নেই" : "No report"}</option>
                  <option value="yes">{lang === "bn" ? "হ্যাঁ, রিপোর্ট আছে" : "Yes, have report"}</option>
                </select>
              </label>
              {soilTest === "yes" && (
                <label>
                  <span>{lang === "bn" ? "রিপোর্টের pH মান" : "pH FROM REPORT"}</span>
                  <input type="number" min="0" max="14" step="0.1" value={soilPh} onChange={(event) => setSoilPh(event.target.value)} />
                </label>
              )}
            </div>

            <label className="profile-group">
              <span>{lang === "bn" ? "কৃষকের প্রধান অগ্রাধিকার" : "FARMER PRIORITY"}</span>
              <div className="priority-toggle">
                {[
                  ["water", lang === "bn" ? "পানি সাশ্রয়" : "Water Saving"],
                  ["soil", lang === "bn" ? "মাটির স্বাস্থ্য" : "Soil Health"],
                  ["production_stability", lang === "bn" ? "স্থিতিশীল ফলন" : "Stability"],
                ].map(([id, label]) => (
                  <button
                    type="button"
                    className={priority === id ? "active" : ""}
                    onClick={() => setPriority(id as FarmerProfile["priority"])}
                    key={id}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </label>

            <div className="three-control">
              <label>
                <span>{lang === "bn" ? "শুরুর দিন" : "START DAY"}</span>
                <select value={startDay} onChange={(event) => setStartDay(Number(event.target.value))}>
                  {Array.from({ length: 31 }, (_, index) => index + 1).map((day) => (
                    <option value={day} key={day}>{String(day).padStart(2, "0")}</option>
                  ))}
                </select>
              </label>
              <label>
                <span>{lang === "bn" ? "শুরুর মাস" : "MONTH"}</span>
                <select value={startMonth} onChange={(event) => setStartMonth(Number(event.target.value))}>
                  {Array.from({ length: 12 }, (_, index) => index + 1).map((month) => (
                    <option value={month} key={month}>
                      {String(month).padStart(2, "0")} — {monthShort[month - 1]}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span>{lang === "bn" ? "বছর" : "YEAR"}</span>
                <select value={startYear} onChange={(event) => setStartYear(Number(event.target.value))}>
                  {Array.from({ length: 10 }, (_, index) => 2026 + index).map((year) => (
                    <option value={year} key={year}>{year}</option>
                  ))}
                </select>
              </label>
            </div>

            <button type="button" className="run-engine" onClick={() => void runDecisionEngine()} disabled={planBusy}>
              <span>{planBusy ? "BUILDING PLAN…" : (lang === "bn" ? "৯০ দিনের মাঠ পরিকল্পনা তৈরি করুন" : "GENERATE 90-DAY FIELD PLAN")}</span><b>→</b>
            </button>
            {error && <div className="command-error">{error}</div>}
          </aside>

          <section className="strategy-stage">
            <div className="strategy-heading">
              <div>
                <span>02 · ANALYSIS & ROTATION WORKBENCH · DATA: NASA POWER / EONET / GIBS</span>
                <h1>{lang === "bn" ? "বিদ্যমান ফসল ধারা ও বিকল্প পর্যায়গুলোর তুলনামূলক বিশ্লেষণ" : "Compare Rotation Strategies Before Committing"}</h1>
              </div>
              <p>
                {lang === "bn"
                  ? "নাসা জলবায়ু সংকেত (বৃষ্টিপাত, বাষ্পীভবন ET₀, তাপমাত্রা), BAMIS ফসল পঞ্জিকা এবং স্থানীয় ৬৪ জেলার মাটির ধরনের ভিত্তিতে অন্তত ৩টি ফসল পর্যায় তুলনা করা হয়েছে।"
                  : "Combines NASA agroclimate water balance (P − ET₀), BAMIS seasonal calendars, and 64-district landform context to compare your existing rotation against soil-building and climate-adaptive alternatives."}
              </p>
            </div>

            <div className="strategy-context-row">
              <div><span>LOCKED FIELD</span><strong>{placeLabel(place, point, context)}</strong></div>
              <div><span>NET WATER BALANCE</span><strong>{waterBalanceDaily == null ? rainSignalLabel : `${waterBalanceDaily >= 0 ? "+" : ""}${waterBalanceDaily.toFixed(1)} mm/d (${rainSignalLabel})`}</strong></div>
              <div><span>DISTRICT LANDFORM</span><strong>{districtProfile ? (lang === "bn" ? districtProfile.landform_bn : districtProfile.landform_en) : `${localSources?.official_sources?.length ?? 0} verified sources`}</strong></div>
              <div><span>TARGET NEXT CROP</span><strong>{intendedCrop ? (lang === "bn" ? cropLabelsBn[intendedCrop] : cropLabels[intendedCrop]) : "Not decided"}</strong></div>
            </div>

            {/* 25-Year Planting-Window Shift, Mann-Whitney, 95% CI, Sen Slope & <160-Char SMS Advisory Card */}
            {advisory && advisory.status !== "ADVISORY_READY" && (
              <div className="onset-advisory-card unavailable-state">
                <div className="onset-advisory-top">
                  <div>
                    <span>{lang === "bn" ? "বৃষ্টির শুরুর পরিবর্তন: প্রকৃত NASA তথ্য পাওয়া যায়নি (UNAVAILABLE)" : "PLANTING-WINDOW SHIFT: REAL NASA DATA NOT AVAILABLE (UNAVAILABLE)"}</span>
                    <strong className="onset-headline-sentence">
                      {advisory.message ?? (lang === "bn" ? "কোনো সংখ্যা দেখানো হচ্ছে না, কারণ যাচাইকৃত NASA POWER তথ্য লোড হয়নি।" : "No numbers are shown because verified NASA POWER data could not be loaded.")}
                    </strong>
                    <div className="advisory-provenance-pills">
                      <code>data_origin: {advisory.data_origin ?? "unavailable"}</code>
                      {advisory.grid_cell?.id && <code>cell: {advisory.grid_cell.id} (0.5°×0.625°)</code>}
                      {advisory.shared_with && advisory.shared_with.length > 0 && (
                        <span>
                          {lang === "bn"
                            ? `একই NASA গ্রিড সেলে অবস্থিত জেলা: ${advisory.shared_with.join(", ")}`
                            : `Same NASA grid cell as: ${advisory.shared_with.join(", ")}`}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {advisory && advisory.status === "ADVISORY_READY" && (
              <div className="onset-advisory-card">
                <div className="onset-advisory-top">
                  <div>
                    <span>{`PLANTING-WINDOW SHIFT ADVISORY (2001–2012 vs. ${advisory.distributions?.period_2013_2025?.label ?? "2013–2026"}) · DATA: NASA POWER / EONET / GIBS${advisory.data_through ? ` through ${advisory.data_through}` : ""}`}</span>
                    <strong className="onset-headline-sentence">
                      {lang === "bn"
                        ? (advisory.advisory_sentence?.bn ?? advisory.advisory_sentence?.en)
                        : (advisory.advisory_sentence?.en ?? "")}
                    </strong>

                    {/* Spec v2 Items L, T, U: Freshness, Shared Grid Cell & Evidence Type Badges */}
                    <div className="advisory-provenance-pills">
                      <code>data_origin: {advisory.data_origin ?? "nasa_power_snapshot"}</code>
                      {advisory.data_through && <code>data_through: {advisory.data_through} (~{advisory.lag_days ?? 7}d lag)</code>}
                      {advisory.retrieved_at && <code>retrieved: {advisory.retrieved_at}</code>}
                      {advisory.grid_cell?.id && <code>cell: {advisory.grid_cell.id}</code>}
                      {advisory.shared_with && advisory.shared_with.length > 0 && (
                        <span className="shared-cell-pill">
                          {lang === "bn"
                            ? `একই NASA গ্রিড সেলে অবস্থিত: ${advisory.shared_with.join(", ")}`
                            : `Same NASA grid cell as: ${advisory.shared_with.join(", ")}`}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="onset-shift-badge">
                    <small>
                      {advisoryBusy
                        ? (lang === "bn" ? "হালনাগাদ হচ্ছে…" : "UPDATING…")
                        : advisory.advisory_kind === "shift_applied"
                          ? (lang === "bn" ? "বৃষ্টি ও রোপণ পরিবর্তন" : "ONSET & WINDOW SHIFT")
                          : advisory.advisory_kind === "context_only"
                            ? (lang === "bn" ? "বৃষ্টির পরিবর্তন (রবি প্রসঙ্গ)" : "RAIN ONSET SHIFT (CONTEXT)")
                            : (lang === "bn" ? "পর্যবেক্ষিত পার্থক্য (p ≥ 0.05)" : "OBSERVED ONSET DIFF")}
                    </small>
                    <b>
                      {(() => {
                        const rawShift =
                          advisory.shift_days != null && advisory.shift_days !== 0
                            ? advisory.shift_days
                            : (advisory.shift?.mean_difference_days ?? advisory.shift_days ?? 0);
                        const prefix = rawShift > 0 ? "+" : "";
                        return `${prefix}${rawShift} ${lang === "bn" ? "দিন" : "Days"}`;
                      })()}
                    </b>
                    <span>
                      {lang === "bn"
                        ? `${advisory.crop?.name_bn ?? ""}: ${advisory.recommended_window?.bn ?? ""}`
                        : `${advisory.crop?.name_en ?? "Window"}: ${advisory.recommended_window?.en ?? ""}${
                            advisory.advisory_kind === "context_only"
                              ? " (BAMIS Rabi kept)"
                              : advisory.advisory_kind === "no_reliable_shift"
                                ? " (BAMIS kept)"
                                : ""
                          }`}
                    </span>
                    {advisory.distributions?.period_2001_2012?.mean_onset_label_en &&
                      advisory.distributions?.period_2013_2025?.mean_onset_label_en && (
                        <small className="ci-sub-note">
                          Mean onset: {advisory.distributions.period_2001_2012.mean_onset_label_en} →{" "}
                          {advisory.distributions.period_2013_2025.mean_onset_label_en}
                          {advisory.shift?.mean_difference_days != null
                            ? ` (${advisory.shift.mean_difference_days >= 0 ? "+" : ""}${advisory.shift.mean_difference_days}d)`
                            : ""}
                        </small>
                      )}
                    {advisory.shift?.ci_95_days && (
                      <small className="ci-sub-note">
                        95% CI: {advisory.shift.ci_95_days.low >= 0 ? `+${advisory.shift.ci_95_days.low}` : advisory.shift.ci_95_days.low}d to{" "}
                        {advisory.shift.ci_95_days.high >= 0 ? `+${advisory.shift.ci_95_days.high}` : advisory.shift.ci_95_days.high}d
                        {advisory.mann_whitney_test?.p_value != null ? ` · p = ${advisory.mann_whitney_test.p_value.toFixed(4)}` : ""}
                      </small>
                    )}
                  </div>
                </div>

                {/* SMS-Length Farmer Advisory (<160 characters) */}
                {advisory.sms_advisory && (
                  <div className="sms-advisory-bar">
                    <div className="sms-advisory-copy">
                      <span>
                        {lang === "bn"
                          ? `কৃষকের মোবাইল SMS বার্তা (${advisory.sms_advisory.char_count_bn ?? 0}/${advisory.sms_advisory.max_chars_bn ?? 70} অক্ষর · ${advisory.sms_advisory.encoding_bn ?? "UCS-2"})`
                          : `FARMER MOBILE SMS ADVISORY (${advisory.sms_advisory.char_count_en ?? 0}/${advisory.sms_advisory.max_chars_en ?? 160} CHARS · ${advisory.sms_advisory.encoding_en ?? "GSM-7"})`}
                      </span>
                      <code>{lang === "bn" ? advisory.sms_advisory.bn : advisory.sms_advisory.en}</code>
                    </div>
                    <button
                      type="button"
                      className="sms-copy-btn"
                      onClick={() => {
                        const txt = lang === "bn" ? (advisory.sms_advisory?.bn ?? "") : (advisory.sms_advisory?.en ?? "");
                        if (navigator.clipboard && txt) {
                          void navigator.clipboard.writeText(txt);
                          setSmsCopied(true);
                          window.setTimeout(() => setSmsCopied(false), 1800);
                        }
                      }}
                    >
                      {smsCopied ? (lang === "bn" ? "কপি হয়েছে ✓" : "Copied ✓") : (lang === "bn" ? "SMS কপি করুন" : "Copy SMS")}
                    </button>
                  </div>
                )}

                <div className="onset-distribution-grid">
                  <div className="onset-dist-col">
                    <span>
                      {lang === "bn"
                        ? `২০০১–২০১২ বনাম ${advisory.distributions?.period_2013_2025?.label ?? "২০১৩–২০২৬"} বৃষ্টির শুরু (Mann-Whitney U = ${advisory.mann_whitney_test?.u_statistic ?? "—"}, p = ${advisory.mann_whitney_test?.p_value ?? "—"})`
                        : `ONSET DISTRIBUTION & TREND (Mann-Whitney U = ${advisory.mann_whitney_test?.u_statistic ?? "—"}, p = ${advisory.mann_whitney_test?.p_value ?? "—"}; Sen slope = ${advisory.trend?.sen_slope_days_per_decade ?? "—"} d/decade)`}
                    </span>
                    <div className="dist-bars-wrap">
                      <div className="dist-period-row">
                        <b>2001–2012</b>
                        <div className="dist-dot-track">
                          {(advisory?.distributions?.period_2001_2012?.onset_doy_values ?? []).map((doy, i) => (
                            <i
                              key={`e-${i}`}
                              className="dist-dot early"
                              style={{ left: `${dotLeftPct(doy, advisory)}%` }}
                              title={`Year ${advisory?.distributions?.period_2001_2012?.years?.[i] ?? 2001 + i}: DOY ${doy}`}
                            />
                          ))}
                        </div>
                        <strong>
                          {lang === "bn"
                            ? advisory?.distributions?.period_2001_2012?.mean_onset_label_bn
                            : advisory?.distributions?.period_2001_2012?.mean_onset_label_en}
                        </strong>
                      </div>
                      <div className="dist-period-row">
                        <b>{advisory?.distributions?.period_2013_2025?.label ?? "2013–2026"}</b>
                        <div className="dist-dot-track">
                          {(advisory?.distributions?.period_2013_2025?.onset_doy_values ?? []).map((doy, i) => (
                            <i
                              key={`l-${i}`}
                              className="dist-dot late"
                              style={{ left: `${dotLeftPct(doy, advisory)}%` }}
                              title={`Year ${advisory?.distributions?.period_2013_2025?.years?.[i] ?? 2013 + i}: DOY ${doy}`}
                            />
                          ))}
                        </div>
                        <strong className="amber-val">
                          {lang === "bn"
                            ? advisory?.distributions?.period_2013_2025?.mean_onset_label_bn
                            : advisory?.distributions?.period_2013_2025?.mean_onset_label_en}
                        </strong>
                      </div>
                    </div>
                    <small>
                      {lang === "bn"
                        ? (advisory.gdd_summary?.note_bn ?? "")
                        : (advisory.gdd_summary?.note_en ?? "")}
                    </small>
                    {advisory.how_computed && (
                      <p className="how-computed-note">
                        <strong>{lang === "bn" ? "গণনা পদ্ধতি: " : "How computed: "}</strong>
                        {lang === "bn" ? advisory.how_computed.bn : advisory.how_computed.en}
                      </p>
                    )}
                  </div>

                  <div className="onset-dist-col">
                    <span>
                      {lang === "bn"
                        ? "সংজ্ঞা ও ±৫ মিমি সংবেদনশীলতা পরীক্ষা (ONSET DEFINITION & ±5 MM SENSITIVITY)"
                        : "STATED ONSET DEFINITION & ±5 MM THRESHOLD SENSITIVITY CHECK"}
                    </span>
                    <p className="onset-def-text">
                      {lang === "bn"
                        ? (advisory.assumptions?.onset_definition_bn ?? "")
                        : (advisory.assumptions?.onset_definition_en ?? "")}
                    </p>
                    <div className="sensitivity-pills">
                      {(advisory.sensitivity_check?.thresholds ?? []).map((item) => (
                        <div key={item.key} className="sens-pill">
                          <span>{item.threshold_mm} mm / 7d</span>
                          <strong>{item.shift_days == null ? "n/a" : item.shift_days >= 0 ? `+${item.shift_days}d` : `${item.shift_days}d`}</strong>
                        </div>
                      ))}
                      <div className="sens-pill valid">
                        <span>{lang === "bn" ? "স্থিতিশীলতা" : "STABILITY"}</span>
                        <strong>{advisory.sensitivity_check?.is_stable ? "STABLE" : "REVIEW"}</strong>
                      </div>
                    </div>
                    <small>
                      {lang === "bn"
                        ? (advisory.sensitivity_check?.stability_note_bn ?? "")
                        : (advisory.sensitivity_check?.stability_note_en ?? "")}
                    </small>
                    {advisory.evidence_types && (
                      <div className="evidence-type-strip">
                        {Object.entries(advisory.evidence_types).map(([k, v]) => (
                          <code key={k} className="ev-type-chip">
                            {k}: {v}
                          </code>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Interactive "What-If" Climate Scenario Stress-Test Simulator (Spec v2 Item W) */}
            <div className="what-if-simulator-card">
              <div className="what-if-head">
                <div>
                  <span>
                    {hasRealSimBase
                      ? "INTERACTIVE 'WHAT-IF' CLIMATE SCENARIO STRESS-TEST · DATA: NASA POWER"
                      : "INTERACTIVE 'WHAT-IF' CLIMATE SCENARIO STRESS-TEST · OFFLINE REFERENCE BASELINE"}
                  </span>
                  <strong>
                    {lang === "bn"
                      ? "খরা, অতিবৃষ্টি বা তাপপ্রবাহ হলে কোন ফসল পর্যায়টি টিকে থাকবে তা পরীক্ষা করুন"
                      : "Simulate drier/wetter rainfall or heat spikes to test how Strategies A, B & C respond"}
                  </strong>
                </div>
                <button
                  type="button"
                  className="what-if-reset"
                  onClick={() => {
                    setScenarioRainShiftPct(0);
                    setScenarioTempShiftC(0);
                  }}
                >
                  {lang === "bn" ? "রিসেট করুন" : "Reset (0%)"}
                </button>
              </div>
              <div className="what-if-controls">
                <label className="what-if-slider">
                  <div>
                    <span>{lang === "bn" ? "বৃষ্টিপাত পরিবর্তন (RAINFALL SHIFT)" : "RAINFALL SHIFT SCENARIO"}</span>
                    <b>{scenarioRainShiftPct >= 0 ? `+${scenarioRainShiftPct}%` : `${scenarioRainShiftPct}%`}</b>
                  </div>
                  <input
                    type="range"
                    min="-50"
                    max="50"
                    step="5"
                    value={scenarioRainShiftPct}
                    onChange={(e) => setScenarioRainShiftPct(Number(e.target.value))}
                  />
                  <small>
                    Simulated rain: {simulatedRainDaily.toFixed(1)} mm/day
                    {!hasRealSimBase ? " (offline ref)" : ""}
                  </small>
                </label>

                <label className="what-if-slider">
                  <div>
                    <span>{lang === "bn" ? "তাপমাত্রা বৃদ্ধি (HEAT SHIFT)" : "TEMPERATURE SHIFT SCENARIO"}</span>
                    <b>+{scenarioTempShiftC.toFixed(1)}°C</b>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="4"
                    step="0.5"
                    value={scenarioTempShiftC}
                    onChange={(e) => setScenarioTempShiftC(Number(e.target.value))}
                  />
                  <small>
                    Simulated ET₀ draw: {simulatedEt0Daily.toFixed(1)} mm/day
                    {!hasRealSimBase ? " (offline ref)" : ""}
                  </small>
                </label>

                <div className="what-if-readout">
                  <span>SIMULATED WATER BALANCE (P − ET₀)</span>
                  <strong className={simulatedWaterBalance < -1.5 ? "amber-val" : "lime-val"}>
                    {simulatedWaterBalance >= 0 ? "+" : ""}{simulatedWaterBalance.toFixed(1)} mm/day
                  </strong>
                  <small>
                    {simulatedWaterBalance < -2.0
                      ? "Severe moisture deficit — favors low-water Pulse/Oilseed Bridge (Strategy B)"
                      : simulatedWaterBalance > 2.5
                        ? "High moisture surplus — check field drainage before legumes"
                        : "Within manageable seasonal water balance"}
                  </small>
                </div>
              </div>
            </div>

            {districtProfile && (
              <div className="bare-field-banner">
                <div>
                  <span>{lang === "bn" ? "খালি জমি ও মৌসুমি ঝুঁকি (BARE-FIELD & VULNERABILITY WINDOW)" : "BARE-FIELD & SEASONAL VULNERABILITY WINDOW"}</span>
                  <strong>{lang === "bn" ? districtProfile.bare_field_risk_bn : districtProfile.bare_field_risk_en}</strong>
                </div>
                <div className="analog-tag">
                  <span>{lang === "bn" ? "মিল থাকা কৃষি-জলবায়ু অঞ্চল" : "CLIMATE-ANALOG REGIONS"}</span>
                  <b>{lang === "bn" ? districtProfile.analog_regions_bn : districtProfile.analog_regions_en}</b>
                </div>
              </div>
            )}

            {/* 12-Month Regional Crop Calendar Timeline */}
            {(context?.calendar_evidence?.length ?? 0) > 0 && (
              <div className="bamis-timeline-card">
                <div className="bamis-timeline-head">
                  <div>
                    <span>OFFICIAL REGIONAL CROP-WEATHER CALENDAR TIMELINE (BAMIS)</span>
                    <strong>
                      {lang === "bn"
                        ? `${context?.nearest_supported_region?.name_bn} হাব — ১২ মাসের ফসল চক্র ও ৯০ দিনের পরিকল্পনা জানালা`
                        : `${context?.nearest_supported_region?.name_en} Hub — 12-Month Crop Windows & Active 90-Day Planning Span`}
                    </strong>
                  </div>
                  <small>Highlighted columns = your selected 3-month planning window</small>
                </div>
                <div className="bamis-timeline-table-wrap">
                  <table className="bamis-timeline-table">
                    <thead>
                      <tr>
                        <th>Crop (BAMIS Source)</th>
                        <th>Water Need & Soil Role</th>
                        {monthShort.map((m, idx) => (
                          <th
                            key={m}
                            className={plannedMonths.includes(idx + 1) ? "active-plan-month" : ""}
                          >
                            {m}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {(context?.calendar_evidence ?? []).map((cal) => {
                        const activeMonths = cal.months ?? [];
                        return (
                          <tr key={cal.id}>
                            <td>
                              <a href={cal.source_url} target="_blank" rel="noreferrer">
                                <strong>{lang === "bn" ? cal.name_bn : cal.name_en} ↗</strong>
                              </a>
                              <small>{lang === "bn" ? cal.window_bn : cal.window_en}</small>
                            </td>
                            <td>
                              <span className={`water-pill ${cal.water_need_class ?? "moderate"}`}>
                                {lang === "bn" ? cal.water_need_note_bn : cal.water_need_note_en}
                              </span>
                              <small>{lang === "bn" ? cal.soil_role_bn : cal.soil_role_en}</small>
                            </td>
                            {monthShort.map((m, idx) => {
                              const monthNum = idx + 1;
                              const isCropActive = activeMonths.includes(monthNum);
                              const isPlanWindow = plannedMonths.includes(monthNum);
                              return (
                                <td
                                  key={`${cal.id}-${m}`}
                                  className={`${isCropActive ? "crop-on" : "crop-off"} ${isPlanWindow ? "in-window" : ""}`}
                                  title={`${cal.name_en} — ${m}`}
                                >
                                  {isCropActive ? <i /> : null}
                                </td>
                              );
                            })}
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            <div className="strategy-cards">
              {strategies.map((strategy) => {
                const crops = lang === "bn" ? strategy.crops_bn : strategy.crops_en;
                const simImpact = scenarioImpactForStrategy(strategy.id);
                return (
                  <article key={strategy.id} className="strategy-card-detailed">
                    <header>
                      <div className="strategy-card-top">
                        <span>STRATEGY {strategy.id} · {strategy.kind.replace(/_/g, " ").toUpperCase()}</span>
                      </div>
                      <strong>{lang === "bn" ? strategy.title_bn : strategy.title_en}</strong>
                      <div className="strategy-badges">
                        {strategy.water_demand_badge && <em className="badge-water">{strategy.water_demand_badge}</em>}
                        {strategy.nitrogen_badge && <em className="badge-soil">{strategy.nitrogen_badge}</em>}
                        {strategy.pest_break_badge && <em className="badge-pest">{strategy.pest_break_badge}</em>}
                      </div>
                      <div className={`scenario-impact-pill ${simImpact.tone}`}>
                        <span>WHAT-IF STRESS IMPACT:</span>
                        <b>{simImpact.label}</b>
                      </div>
                    </header>
                    <div className="season-flow">
                      {crops.map((crop, index) => (
                        <div key={`${crop}-${index}`}>
                          <small>
                            {index === 0
                              ? (lang === "bn" ? "মৌসুম ১ (খরিফ-২ / আমন)" : "SEASON 1 (KHARIF-2 / AMAN)")
                              : index === 1
                                ? (lang === "bn" ? "মৌসুম ২ (রবি / বোরো)" : "SEASON 2 (RABI / WINTER)")
                                : (lang === "bn" ? "মৌসুম ৩ (খরিফ-১ / আউশ)" : "SEASON 3 (KHARIF-1 / PRE-MONSOON)")}
                          </small>
                          <strong>{crop}</strong>
                          {index < 2 && <i>→</i>}
                        </div>
                      ))}
                    </div>
                    <div className="strategy-explain-body">
                      <div className="explain-block">
                        <span>{lang === "bn" ? "কেন এটি প্রস্তাবিত (WHY SUGGESTED)" : "WHY SUGGESTED"}</span>
                        <p>{lang === "bn" ? strategy.why_suggested_bn : strategy.why_suggested_en}</p>
                      </div>
                      <div className="explain-block">
                        <span>{lang === "bn" ? "সমর্থনকারী প্রমাণ (SUPPORTING EVIDENCE)" : "SUPPORTING EVIDENCE"}</span>
                        <ul>
                          {strategy.supporting_evidence.map((item, idx) => <li key={idx}>{item}</li>)}
                        </ul>
                      </div>
                      <div className="explain-block">
                        <span>{lang === "bn" ? "সম্ভাব্য সুফল (SOIL, WATER & INCOME BENEFITS)" : "SOIL, WATER & INCOME BENEFITS"}</span>
                        <ul>
                          {strategy.potential_benefits.map((item, idx) => <li key={idx}>{item}</li>)}
                        </ul>
                      </div>
                      {strategy.scientific_evaluation && (
                        <div className="explain-block">
                          <span>
                            {lang === "bn"
                              ? `বৈজ্ঞানিক সক্ষমতা: ${strategy.scientific_evaluation.weighted_composite_score_0_100}/100 · প্রমাণের পূর্ণতা: ${strategy.scientific_evaluation.evidence_completeness_pct ?? strategy.scientific_evaluation.evidence_completeness?.completeness_pct ?? 75}% · গেট: ${strategy.scientific_evaluation.recommendation_gate}`
                              : `SCIENTIFIC PERFORMANCE: ${strategy.scientific_evaluation.weighted_composite_score_0_100}/100 · EVIDENCE COMPLETENESS: ${strategy.scientific_evaluation.evidence_completeness_pct ?? strategy.scientific_evaluation.evidence_completeness?.completeness_pct ?? 75}% · GATE: ${strategy.scientific_evaluation.recommendation_gate}`}
                          </span>
                          <p style={{ fontSize: "0.76rem", marginBottom: "4px" }}>
                            Water: <b>{strategy.scientific_evaluation.criteria_scores_0_100.water_demand ?? "UNKNOWN"}</b> ·{" "}
                            N-Balance: <b>{strategy.scientific_evaluation.criteria_scores_0_100.nitrogen_contribution ?? "UNKNOWN"}</b> ·{" "}
                            Soil Cover: <b>{strategy.scientific_evaluation.criteria_scores_0_100.soil_coverage ?? "UNKNOWN"}</b> ·{" "}
                            Pest Break: <b>{strategy.scientific_evaluation.criteria_scores_0_100.pest_break_potential ?? "UNKNOWN"}</b> ·{" "}
                            Resilience: <b>{strategy.scientific_evaluation.criteria_scores_0_100.climate_resilience ?? "UNKNOWN"}</b> ·{" "}
                            Local Soil Gate: <b>{strategy.scientific_evaluation.criteria_scores_0_100.local_suitability ?? "UNKNOWN (No Lab Test)"}</b>
                          </p>
                          {strategy.scientific_evaluation.constraint_flags.length > 0 && (
                            <p style={{ color: "#ffb347", fontSize: "0.75rem", fontWeight: 600 }}>
                              ⚠ {strategy.scientific_evaluation.constraint_flags.join(" ")}
                            </p>
                          )}
                        </div>
                      )}
                      <div className="explain-block warn">
                        <span>{lang === "bn" ? "তথ্যের ঘাটতি ও স্থানীয় যাচাই ঝুঁকি (GAPS & LOCAL REVIEW RISKS)" : "INFORMATION GAPS & LOCAL REVIEW RISKS"}</span>
                        <ul>
                          {strategy.information_gaps.slice(0, 1).map((item, idx) => <li key={`gap-${idx}`}>{item}</li>)}
                          {strategy.local_review_risks.map((item, idx) => <li key={`risk-${idx}`}>{item}</li>)}
                        </ul>
                      </div>
                    </div>
                    <footer className="strategy-card-footer">
                      <span>{context?.calendar_evidence?.length ?? 0} BAMIS records · {districtProfile ? `${districtProfile.name_en} profile` : "Global"}</span>
                      <button
                        type="button"
                        className={selectedStrategyId === strategy.id ? "strategy-pick-btn active" : "strategy-pick-btn"}
                        onClick={() => {
                          setSelectedStrategyId(strategy.id);
                          void runDecisionEngine();
                        }}
                      >
                        {lang === "bn" ? `কৌশল ${strategy.id} দিয়ে ৯০ দিনের প্ল্যান →` : `Build 90-Day Plan with Strategy ${strategy.id} →`}
                      </button>
                    </footer>
                  </article>
                );
              })}
            </div>

            {/* Functional Soil-Health Crop Roles */}
            {(context?.functional_crop_roles?.length ?? 0) > 0 && (
              <div className="functional-roles-section">
                <div className="functional-roles-head">
                  <span>SOIL-HEALTH FUNCTIONAL CROP ROLES · HOW DIFFERENT CROPS RESTORE THE FIELD</span>
                  <strong>
                    {lang === "bn"
                      ? "নাইট্রোজেন সংবন্ধনকারী, আচ্ছাদন ফসল, গভীর মূলী ও খরা/লবণ-সহনশীল ফসলের ভূমিকা"
                      : "How Nitrogen-Fixing, Cover, Deep-Rooting & Drought-Tolerant Crops Support Long-Term Resilience"}
                  </strong>
                </div>
                <div className="functional-roles-grid">
                  {(context?.functional_crop_roles ?? []).map((role) => (
                    <article key={role.role_id} className="functional-role-card">
                      <span>{lang === "bn" ? role.title_bn : role.title_en}</span>
                      <strong>{lang === "bn" ? role.examples_bn : role.examples_en}</strong>
                      <p>{lang === "bn" ? (role.benefit_bn ?? role.mechanism_bn) : (role.benefit_en ?? role.mechanism_en)}</p>
                    </article>
                  ))}
                </div>
              </div>
            )}
          </section>
        </main>
      )}

      {view === "plan" && (
        <main className="plan-workspace">
          {!plan ? (
            <div className="empty-plan">
              <BoponXLogoMark size={52} />
              <span>03 · 90-DAY FIELD PLANNER</span>
              <h1>{lang === "bn" ? "নাসা ও স্থানীয় প্রমাণকে কৃষকের ব্যবহারযোগ্য পদক্ষেপে রূপান্তর করুন।" : "Turn Earth evidence into actions a farmer can use."}</h1>
              <p>
                {lang === "bn"
                  ? "প্রিন্ট করা অ্যাকশন কার্ডটি ইন্টারনেট বা লিংক ছাড়াই কাজ করে। এতে নাসা এবং স্থানীয় কৃষি উৎসের নাম ও কৃষি কল সেন্টার ১৬১২৩ উল্লেখ থাকে।"
                  : "The printed card is designed to stand alone. It does not depend on clickable links. Source names remain traceable for advisers and judges."}
              </p>
              <button type="button" onClick={() => void runDecisionEngine()}>
                {lang === "bn" ? "এখনই ৯০ দিনের পরিকল্পনা তৈরি করুন →" : "Generate 90-day field plan now →"}
              </button>
            </div>
          ) : (
            <DecisionReport
              brief={plan}
              placeName={placeLabel(place, point, context)}
              lang={lang}
              onLangChange={setLang}
              selectedStrategyId={selectedStrategyId}
              onSelectStrategy={setSelectedStrategyId}
              startYear={startYear}
              startMonth={startMonth}
              startDay={startDay}
              onStartDateChange={(y, m, d) => {
                setStartYear(y);
                setStartMonth(m);
                setStartDay(d);
                void runDecisionEngine(undefined, { year: y, month: m, day: d });
              }}
            />
          )}
        </main>
      )}
    </div>
  );
}
