export type Status = "idle" | "loading" | "ready" | "unavailable";

export type Area = {
  id: string;
  name_en: string;
  name_bn: string;
  latitude: number;
  longitude: number;
  evidence_region: string;
};

export type NasaSource = {
  id: string;
  name: string;
  role: string;
  kind: string;
  status: string;
  latency_note: string;
  resolution_note: string;
  source_url: string;
  advisory?: string;
};

export type AgriculturalSource = {
  id?: string;
  name: string;
  organization?: string;
  scope: string;
  kind?: string;
  status: string;
  source_url: string;
  note?: string;
};

export type LocalSourceRegistry = {
  country_code: string | null;
  country_name?: string | null;
  official_sources: AgriculturalSource[];
  government_discovery: AgriculturalSource;
  global_sources: AgriculturalSource[];
  coverage: "verified_country_adapter" | "global_reference_only";
  warning: string;
};

export type CalendarEvidence = {
  id: string;
  name_en: string;
  name_bn: string;
  season_code?: string;
  window_en?: string;
  window_bn?: string;
  months?: number[];
  water_need_class?: string;
  water_need_note_en?: string;
  water_need_note_bn?: string;
  soil_role_en?: string;
  soil_role_bn?: string;
  evidence_type: string;
  region: string;
  source_name: string;
  source_url: string;
  status: string;
  meaning: string;
};

export type OnlineEvidenceReport = {
  id: string;
  title_en: string;
  title_bn: string;
  detail_en: string;
  detail_bn: string;
  source_url: string;
};

export type VerificationRequirement = {
  id: string;
  en: string;
  bn: string;
};

export type DistrictProfile = {
  id: string;
  name_en: string;
  name_bn: string;
  division_en: string;
  division_bn: string;
  latitude: number;
  longitude: number;
  bamis_region: string;
  landform_bn: string;
  landform_en: string;
  analog_regions_bn: string;
  analog_regions_en: string;
  established_crops_bn: string[];
  established_crops_en: string[];
  opportunity_crops_bn: string[];
  opportunity_crops_en: string[];
  bare_field_risk_en: string;
  bare_field_risk_bn: string;
  online_evidence_ids?: string[];
  online_evidence?: OnlineEvidenceReport[];
  distance_km?: number;
  verification_status: string;
  caution_bn: string;
  caution_en: string;
  verification_requirements?: VerificationRequirement[];
  national_import_context?: {
    edible_oil_import_share_pct: number;
    domestic_soybean_demand_met_pct: number;
    projected_pulse_deficit_2030_lakh_tonnes: number;
    summary_en: string;
    summary_bn: string;
    sources: string[];
  };
};

export type MultiResolutionLayer = {
  layer: string;
  spatial_scale: string;
  temporal_scale: string;
  role: string;
};

export type MultiResolutionHarmonization = {
  method: string;
  summary_en: string;
  summary_bn: string;
  layers: MultiResolutionLayer[];
};

export type ScientificGlossaryItem = {
  term_id: string;
  term_en: string;
  term_bn: string;
  explanation_en: string;
  explanation_bn: string;
};

export type FunctionalCropRole = {
  role_id: string;
  title_en: string;
  title_bn: string;
  examples_en: string;
  examples_bn: string;
  benefit_en?: string;
  benefit_bn?: string;
  mechanism_en?: string;
  mechanism_bn?: string;
  nasa_link_en?: string;
  nasa_link_bn?: string;
};

export type SiModelingMethod = {
  method_id: string;
  title_en?: string;
  title_bn?: string;
  name_en?: string;
  name_bn?: string;
  detail_en: string;
  detail_bn: string;
};

export type EonetEvent = {
  id: string;
  title: string;
  category_id?: string;
  category_title?: string;
  categories?: string[];
  date: string | null;
  latitude: number;
  longitude: number;
  distance_km: number;
  within_alert_radius?: boolean;
  source_url: string;
};

export type EonetHazardsResponse = {
  status: "available" | "unavailable";
  provider: string;
  coordinates: { latitude: number; longitude: number };
  radius_km?: number;
  search_radius_km?: number;
  active_count?: number;
  regional_events_count?: number;
  nearby_events?: EonetEvent[];
  regional_events?: EonetEvent[];
  nearest_global_events?: EonetEvent[];
  events?: EonetEvent[];
  source_request_url: string;
  limitations?: string[];
};


export type PlantingWindowAdvisory = {
  status: string;
  district?: {
    id: string;
    name_en: string;
    name_bn: string;
    division_en: string;
    division_bn: string;
    landform_en: string;
    landform_bn: string;
  };
  crop?: {
    id: string;
    name_en: string;
    name_bn: string;
    action_word_en: string;
    action_word_bn: string;
    gdd_base_temp_c: number;
    gdd_target_c_days: number;
  };
  shift_days?: number;
  baseline_window?: { en: string; bn: string };
  recommended_window?: { en: string; bn: string };
  advisory_sentence?: { en: string; bn: string };
  sms_advisory?: {
    en: string;
    bn: string;
    char_count_en: number;
    char_count_bn: number;
    max_chars: number;
  };
  distributions?: {
    period_2001_2012?: {
      label: string;
      onset_doy_values?: number[];
      mean_onset_doy?: number;
      mean_onset_label_en?: string;
      mean_onset_label_bn?: string;
    };
    period_2013_2025?: {
      label: string;
      onset_doy_values?: number[];
      mean_onset_doy?: number;
      mean_onset_label_en?: string;
      mean_onset_label_bn?: string;
    };
  };
  mann_whitney_test?: {
    u_statistic: number;
    z_score: number;
    p_value: number;
    significant_at_0_05: boolean;
  };
  gdd_summary?: {
    base_temp_c: number;
    period_2001_2012_seasonal_gdd: number;
    period_2013_2025_seasonal_gdd: number;
    gdd_delta_c_days: number;
    note_en: string;
    note_bn: string;
  };
  sensitivity_check?: {
    window_days: number;
    dry_spell_max_days: number;
    thresholds?: Array<{
      key: string;
      threshold_mm: number;
      mean_onset_2001_2012_day: number;
      mean_onset_2013_2025_day: number;
      shift_days: number;
    }>;
    max_shift_variation_days: number;
    is_stable: boolean;
    stability_note_en: string;
    stability_note_bn: string;
  };
  assumptions?: {
    onset_definition_en: string;
    onset_definition_bn: string;
    window_days: number;
    threshold_mm: number;
    dry_spell_max_days: number;
    gdd_base_temp_c: number;
    statistical_test: string;
  };
};

export type RotationScenario = {
  id: string;
  kind: string;
  title_en: string;
  title_bn: string;
  crops_en: string[];
  crops_bn: string[];
  why_suggested_en: string;
  why_suggested_bn: string;
  supporting_evidence: string[];
  potential_benefits: string[];
  information_gaps: string[];
  local_review_risks: string[];
  water_demand_badge?: string;
  nitrogen_badge?: string;
  pest_break_badge?: string;
};

export type PlaceResult = {
  display_name: string | null;
  name: string | null;
  latitude: number;
  longitude: number;
  type: string | null;
  category: string | null;
  address: {
    village: string | null;
    town: string | null;
    upazila: string | null;
    district: string | null;
    division: string | null;
    country: string | null;
    country_code: string;
  };
  provider: string;
};

export type PowerBaselineSummary = {
  calendar_month: number;
  calendar_month_key?: string;
  temperature_mean_c: number | null;
  temperature_max_mean_c?: number | null;
  temperature_min_mean_c?: number | null;
  precipitation_mean_daily_mm: number | null;
  relative_humidity_mean_pct?: number | null;
  wind_speed_mean_m_s?: number | null;
  et0_mean_daily_mm?: number | null;
  water_balance_daily_mm?: number | null;
  surface_soil_wetness_pct?: number | null;
  root_zone_soil_wetness_pct?: number | null;
  solar_radiation_mean?: number | null;
};

export type PowerBaselineWindow = {
  status: "available" | "unavailable";
  provider: string;
  kind: string;
  baseline_period?: { start_year: number; end_year: number };
  coordinates?: { latitude: number; longitude: number };
  summaries: PowerBaselineSummary[];
  source_products?: string[];
  source_request_url?: string;
  limitations?: string[];
};

export type LocationContext = {
  coordinates: { latitude: number; longitude: number };
  within_bangladesh: boolean;
  global_environmental_coverage: boolean;
  nearest_supported_region: Area & {
    distance_km: number;
    note: string;
  };
  district_profile?: DistrictProfile | null;
  coverage: {
    environmental_context: string;
    local_agricultural_evidence: string;
    rotation_decision: string;
  };
  calendar_evidence: CalendarEvidence[];
  agricultural_sources: AgriculturalSource[];
  nasa_sources: NasaSource[];
  multi_resolution_harmonization?: MultiResolutionHarmonization;
  scientific_glossary?: ScientificGlossaryItem[];
  functional_crop_roles?: FunctionalCropRole[];
  si_modeling_methods?: SiModelingMethod[];
  privacy: {
    coordinates_persisted: boolean;
    note: string;
  };
};

export type RecentEnvironment = {
  status: "available" | "unavailable";
  mode?: string;
  provider: string;
  source_products?: string[];
  period?: { start: string; end: string; time_standard: string };
  coordinates?: { latitude: number; longitude: number };
  summary?: {
    days_requested: number;
    temperature_valid_days: number;
    precipitation_valid_days: number;
    temperature_mean_c: number | null;
    temperature_max_mean_c?: number | null;
    temperature_min_mean_c?: number | null;
    precipitation_total_mm: number | null;
    precipitation_mean_daily_mm?: number | null;
    relative_humidity_mean_pct?: number | null;
    wind_speed_mean_m_s?: number | null;
    et0_mean_daily_mm?: number | null;
    water_balance_daily_mm?: number | null;
    water_balance_period_mm?: number | null;
    vpd_mean_kpa?: number | null;
    surface_soil_wetness_pct?: number | null;
    root_zone_soil_wetness_pct?: number | null;
    solar_radiation_mean?: number | null;
    dew_point_mean_c?: number | null;
    heat_stress_days?: number;
    cold_stress_days?: number;
    frost_risk_days?: number;
    fog_blight_risk_days?: number;
    heavy_rain_days?: number;
    dry_days?: number;
  };
  source_request_url?: string;
  limitations?: string[];
  message?: string;
};

export type FarmerProfile = {
  latitude: number;
  longitude: number;
  previous_crop: string | null;
  previous_crops: string[];
  intended_crop: string | null;
  water_source: "rainfed" | "irrigated" | "both" | "unknown";
  water_after_heavy_rain: "drains" | "stays" | "sometimes" | "unknown";
  soil_test: "yes" | "no" | "unknown";
  soil_ph: number | null;
  priority: "water" | "soil" | "production_stability";
  equipment_access?: "manual_traditional" | "power_tiller_machinery" | "conservation_zero_till" | "unknown";
  market_preference?: "household_subsistence" | "local_cash_market" | "high_value_commercial" | "forage_livestock" | "unknown";
};

export type PlanTask = {
  code: string;
  en: string;
  bn: string;
  category?: string;
  reason?: string;
  reason_bn?: string;
  evidence?: string;
};

export type PlanMonth = {
  index: number;
  planning_month: string;
  month_name: { en: string; bn: string };
  phase: { en: string; bn: string };
  objective: { en: string; bn: string };
  context?: {
    region?: string;
    baseline?: PowerBaselineSummary | null;
    recent_rain_signal?: string;
    farmer_priority?: string;
    intended_crop?: string | null;
  };
  tasks: PlanTask[];
};

export type PlanBrief = {
  status: string;
  location: {
    coordinates: { latitude: number; longitude: number };
    region_id: string;
    region_name_en: string;
    region_name_bn: string;
    distance_to_reference_km: number;
    district_profile?: DistrictProfile | null;
  };
  farmer_context: FarmerProfile;
  planning_window: { start: string; end: string };
  conditions?: {
    rain_signal: string;
    temperature_signal: string;
    recent_daily_rain_mm: number | null;
    baseline_daily_rain_mm: number | null;
    recent_temperature_c: number | null;
    baseline_temperature_c: number | null;
    surface_soil_wetness_pct?: number | null;
    root_zone_soil_wetness_pct?: number | null;
    frost_risk_days?: number | null;
    fog_blight_risk_days?: number | null;
  };
  decision_advice?: {
    status: string;
    verdict: string;
    reasons: string[];
    better_next_step: string;
    intended_crop: string | null;
    intended_crop_label: string | null;
    regional_calendar_match: boolean;
    regional_options_to_investigate: Array<{
      id?: string;
      name?: string;
      source_url?: string;
      note: string;
    }>;
    boundary: string;
  };
  months: PlanMonth[];
  recent_environment: RecentEnvironment | null;
  historical_baseline?: unknown;
  historical_baseline_window?: PowerBaselineWindow | null;
  rotation_explorer: {
    status: string;
    message_en: string;
    message_bn: string;
    bare_field_window?: { en: string; bn: string };
    vulnerability_summary?: { en: string; bn: string };
    scenarios?: RotationScenario[];
  };
  evidence: {
    nasa_sources: NasaSource[];
    agricultural_sources: AgriculturalSource[];
    calendar_evidence: CalendarEvidence[];
    multi_resolution_harmonization?: MultiResolutionHarmonization;
    scientific_glossary?: ScientificGlossaryItem[];
    functional_crop_roles?: FunctionalCropRole[];
    si_modeling_methods?: SiModelingMethod[];
  };
  limitations: { en: string; bn: string };
};

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const apiBase = (import.meta.env.VITE_BOPONX_API_BASE_URL ?? "").replace(/\/$/, "");

export async function apiGet<T>(path: string, signal?: AbortSignal): Promise<T> {
  return apiRequest<T>(path, { signal });
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  return apiRequest<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

async function apiRequest<T>(path: string, init: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${apiBase}${path}`, init);
  } catch {
    throw new ApiError(0, "NETWORK_UNAVAILABLE", "Cannot connect to the BoponX API.");
  }

  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    throw new ApiError(response.status, "INVALID_RESPONSE", "The API returned an unreadable response.");
  }

  if (!response.ok) {
    const detail =
      typeof payload === "object" && payload !== null && "detail" in payload
        ? (payload as { detail: unknown }).detail
        : undefined;
    if (typeof detail === "object" && detail !== null && "code" in detail) {
      const error = detail as { code: string; message?: string };
      throw new ApiError(response.status, error.code, error.message ?? "Request was not accepted.");
    }
    throw new ApiError(response.status, "REQUEST_FAILED", "Request was not accepted.");
  }

  return payload as T;
}
