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
  agricultural_relevance?: "agricultural_impact" | "low_agricultural_relevance";
  affects_field_operations?: boolean;
  source_url: string;
};

export type EonetHazardsResponse = {
  status: "available" | "unavailable";
  data_origin?: string;
  retrieved_at?: string;
  lag_days?: number;
  provider: string;
  coordinates: { latitude: number; longitude: number };
  radius_km?: number;
  search_radius_km?: number;
  active_count?: number;
  regional_events_count?: number;
  agricultural_alert_count?: number;
  nearby_events?: EonetEvent[];
  regional_events?: EonetEvent[];
  agricultural_events?: EonetEvent[];
  nearest_global_events?: EonetEvent[];
  events?: EonetEvent[];
  source_request_url: string;
  limitations?: string[];
  note?: string;
};

export type SeasonalWaterBalanceSeason = {
  season: string;
  label_en: string;
  label_bn: string;
  status: string;
  period_2001_2012?: {
    n_years: number;
    rain_daily_mm: number;
    et0_daily_mm: number;
    water_balance_daily_mm: number;
    water_balance_total_mm: number;
  };
  period_2013_latest?: {
    n_years: number;
    rain_daily_mm: number;
    et0_daily_mm: number;
    water_balance_daily_mm: number;
    water_balance_total_mm: number;
  };
  shift_daily_mm?: number;
  ci_95_daily_mm?: { low: number; high: number };
};

export type PlantingWindowAdvisory = {
  status: string;
  data_origin?: string;
  advisory_kind?: string;
  message?: string;
  data_through?: string;
  retrieved_at?: string;
  lag_days?: number;
  shared_with?: string[];
  grid_cell?: {
    id: string;
    center_latitude: number;
    center_longitude: number;
    resolution_deg: { latitude: number; longitude: number };
  };
  shift?: {
    estimate_days: number;
    estimator?: string;
    mean_difference_days?: number;
    reliable: boolean;
    applied_shift_days: number;
    window_adjustment_applies_to_crop?: boolean;
    ci_95_days?: { low: number; high: number; n_boot?: number; seed?: number };
  };
  trend?: {
    sen_slope_days_per_decade?: number | null;
    years_used?: number;
    mann_kendall?: { s: number; z: number; p_value: number; significant_at_0_05: boolean } | null;
  };
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
    max_chars_en?: number;
    max_chars_bn?: number;
    encoding_en?: string;
    encoding_bn?: string;
    segments_en?: number;
    segments_bn?: number;
  };
  distributions?: {
    period_2001_2012?: {
      label: string;
      years?: number[];
      onset_doy_values?: number[];
      mean_onset_doy?: number;
      mean_onset_label_en?: string;
      mean_onset_label_bn?: string;
    };
    period_2013_2025?: {
      label: string;
      years?: number[];
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
    period_2001_2012_seasonal_gdd: number | null;
    period_2013_2025_seasonal_gdd: number | null;
    gdd_delta_c_days: number | null;
    days_to_target_2001_2012?: number | null;
    days_to_target_2013_latest?: number | null;
    note_en: string;
    note_bn: string;
  };
  seasonal_water_balance?: {
    method: string;
    kharif2_aman?: SeasonalWaterBalanceSeason;
    rabi?: SeasonalWaterBalanceSeason;
  };
  sensitivity_check?: {
    window_days: number;
    dry_spell_max_days: number;
    thresholds?: Array<{
      key: string;
      threshold_mm: number;
      mean_early_doy?: number;
      mean_late_doy?: number;
      shift_days: number | null;
    }>;
    grid?: Array<{
      key: string;
      threshold_mm: number;
      window_days: number;
      dry_spell_max_days: number;
      search_start: string;
      shift_days: number | null;
    }>;
    grid_shift_range_days?: [number, number] | null;
    grid_sign_consistent?: boolean;
    max_shift_variation_days: number | null;
    is_stable: boolean;
    stability_note_en: string;
    stability_note_bn: string;
  };
  yearly_evidence?: Array<{
    year: number;
    onset_date: string;
    onset_doy: number;
    window_rain_mm: number;
    max_day_in_next_7_mm: number;
  }>;
  how_computed?: { en: string; bn: string };
  evidence_types?: Record<string, string>;
  limitations?: string[];
  assumptions?: {
    onset_definition_en: string;
    onset_definition_bn: string;
    window_days: number;
    threshold_mm: number;
    dry_spell_max_days: number;
    gdd_base_temp_c: number;
    statistical_test: string;
    transplanting_follows_onset?: string;
  };
};

export type SoilEvidenceRecord = {
  property_id: string;
  property_name: string;
  location_coverage: string;
  reported_value: number | string | null;
  reference_range?: { min: number; max: number; regional_typical: number } | null;
  class_description: string;
  unit: string;
  source_institution: string;
  source_document: string;
  source_url: string;
  survey_year: string;
  spatial_resolution: string;
  evidence_classification: "VERIFIED" | "REFERENCE" | "ESTIMATED" | "FARMER_REPORTED" | "UNKNOWN";
  limitations: string;
};

export type SoilEvidenceModel = {
  status: string;
  aez_id?: string;
  soil_classification?: string;
  overall_classification: string;
  parcel_lab_verified: boolean;
  false_precision_guard: string;
  regional_limitations?: string[];
  records: SoilEvidenceRecord[];
};

export type StrategyScientificEvaluation = {
  strategy_id: string;
  framework_version: string;
  recommendation_gate: string;
  critical_constraint_violated: boolean;
  constraint_flags: string[];
  weighted_composite_score_0_100: number;
  scoring_note: string;
  documented_weights: Record<string, number>;
  evidence_completeness_pct?: number;
  scientific_performance?: {
    score_0_100: number;
    known_criteria_weight_sum: number;
    evaluated_criteria_count: number;
    total_criteria_count: number;
    scoring_assumptions: string[];
  };
  evidence_completeness?: {
    completeness_pct: number;
    known_count: number;
    total_dimensions: number;
    known_dimensions: string[];
    unknown_dimensions: string[];
  };
  criteria_scores_0_100: Record<string, number | null>;
  criteria?: {
    water_demand?: {
      crop_water_requirement_etc_mm: number;
      effective_rainfall_peff_mm: number;
      estimated_irrigation_requirement_nir_mm: number;
      rabi_dry_season_irrigation_nir_mm: number;
      actual_irrigation_availability: string;
      irrigation_compatibility: string;
      evidence_classification: string;
      score_0_100: number;
    };
    nitrogen_contribution?: {
      gross_biological_n_fixation_kg_ha: number;
      harvested_grain_n_removal_kg_ha: number;
      estimated_n_carryover_to_following_crop_kg_ha: number;
      net_soil_n_balance_before_fertilizer_kg_ha: number;
      measured_parcel_soil_nitrogen_status: string;
      evidence_classification: string;
      score_0_100: number;
    };
    soil_coverage?: {
      canopy_duration_days_per_year: number;
      bare_soil_exposure_days_per_year: number;
      plough_pan_biopore_potential: string;
      score_0_100: number;
    };
    pest_break_potential?: {
      botanical_family_sequence: string[];
      pest_break_classification: string;
      score_0_100: number;
    };
    local_suitability?: {
      status: string;
      evidence_classification: string;
      constraints_violated: string[];
      missing_essential_evidence: string[];
      score_0_100: number;
    };
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
  scientific_evaluation?: StrategyScientificEvaluation;
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
  data_origin?: string;
  retrieved_at?: string;
  lag_days?: number;
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
  status?: string;
  data_origin?: string;
  retrieved_at?: string;
  lag_days?: number;
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
  imerg_crosscheck?: {
    status: string;
    numerical_validation_status?: string;
    mode: string;
    provider: string;
    why_unavailable?: string;
    note?: string;
    paired_days?: number;
    bias_mm_per_day?: number | null;
    mae_mm_per_day?: number | null;
    rmse_mm_per_day?: number | null;
    pearson_r?: number | null;
  };
  soil_evidence?: SoilEvidenceModel;
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
  data_origin?: string;
  retrieved_at?: string;
  lag_days?: number;
  data_through?: string;
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

export type EvidenceLabel =
  | "observed_nasa"
  | "derived_from_nasa"
  | "official_local_reference"
  | "rule_based"
  | "preliminary_estimate";

export type TaskDateRange = {
  start: string;
  end: string;
  days_en: string;
  days_bn: string;
  en: string;
  bn: string;
};

export type PlanTask = {
  code: string;
  date_range?: TaskDateRange;
  en: string;
  bn: string;
  category?: string;
  reason?: string;
  reason_bn?: string;
  source?: string;
  evidence_label?: EvidenceLabel;
  evidence?: string;
  needs_native_bn_review?: boolean;
};

export type PlanMonth = {
  index: number;
  planning_month: string;
  day_span?: { en: string; bn: string };
  date_range?: TaskDateRange;
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

export type WatchListItem = {
  id: string;
  signal: string;
  evidence_label: EvidenceLabel;
  en: string;
  bn: string;
};

export type PlanBrief = {
  status: string;
  data_status?: "AVAILABLE" | "UNAVAILABLE";
  data_through?: string | null;
  planner_header?: {
    district_en: string;
    district_bn: string;
    crop_id: string;
    crop_en: string;
    crop_bn: string;
    plan_start_date: string;
    plan_end_date: string;
    data_through: string | null;
    data_through_label_en: string;
    data_through_label_bn: string;
    language_options: string[];
  };
  window_guidance?: {
    bamis_baseline_window: {
      en: string;
      bn: string;
      evidence_label: EvidenceLabel;
      source: string;
    };
    shift_reliable: boolean;
    shifted_window: {
      en: string;
      bn: string;
      applied_shift_days: number;
      evidence_label: EvidenceLabel;
    } | null;
    note_en: string;
    note_bn: string;
  };
  watch_list?: WatchListItem[];
  location: {
    coordinates: { latitude: number; longitude: number };
    region_id: string;
    region_name_en: string;
    region_name_bn: string;
    distance_to_reference_km: number;
    district_profile?: DistrictProfile | null;
  };
  farmer_context: FarmerProfile;
  planning_window: { start: string; end: string; start_date?: string; end_date?: string };
  conditions?: {
    rain_signal: string;
    temperature_signal: string;
    recent_daily_rain_mm: number | null;
    baseline_daily_rain_mm: number | null;
    recent_temperature_c: number | null;
    baseline_temperature_c: number | null;
    et0_daily_mm?: number | null;
    water_balance_daily_mm?: number | null;
    surface_soil_wetness_pct?: number | null;
    root_zone_soil_wetness_pct?: number | null;
    frost_risk_days?: number | null;
    fog_blight_risk_days?: number | null;
  };
  decision_advice?: {
    status: string;
    verdict: string;
    verdict_bn?: string;
    reasons: string[];
    reasons_bn?: string[];
    better_next_step: string;
    better_next_step_bn?: string;
    intended_crop: string | null;
    intended_crop_label: string | null;
    intended_crop_label_bn?: string | null;
    regional_calendar_match: boolean;
    regional_options_to_investigate: Array<{
      id?: string;
      name?: string;
      source_url?: string;
      note: string;
    }>;
    boundary: string;
    boundary_bn?: string;
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
  footer?: {
    verify_en: string;
    verify_bn: string;
    limitations_en: string;
    limitations_bn: string;
    provenance_en: string;
    provenance_bn: string;
  };
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
