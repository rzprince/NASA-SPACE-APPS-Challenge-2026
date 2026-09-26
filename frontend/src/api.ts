export type Language = "bn" | "en";
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
  name: string;
  scope: string;
  status: string;
  source_url: string;
};

export type CalendarEvidence = {
  id: string;
  name_en: string;
  name_bn: string;
  evidence_type: string;
  region: string;
  source_name: string;
  source_url: string;
  status: string;
  meaning: string;
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

export type PowerBaseline = {
  status: "available" | "unavailable";
  provider: string;
  kind: string;
  baseline_period?: { start_year: number; end_year: number };
  coordinates?: { latitude: number; longitude: number };
  summary?: {
    calendar_month: number;
    calendar_month_key: string;
    temperature_mean_c: number | null;
    precipitation_mean_daily_mm: number | null;
  } | null;
  source_products?: string[];
  source_request_url?: string;
  limitations?: string[];
};

export type LocationContext = {
  coordinates: { latitude: number; longitude: number };
  within_bangladesh: boolean;
  nearest_supported_region: Area & {
    distance_km: number;
    note: string;
  };
  coverage: {
    environmental_context: string;
    local_agricultural_evidence: string;
    rotation_decision: string;
  };
  calendar_evidence: CalendarEvidence[];
  agricultural_sources: AgriculturalSource[];
  nasa_sources: NasaSource[];
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
    precipitation_total_mm: number | null;
  };
  source_request_url?: string;
  limitations?: string[];
  message?: string;
};

export type FarmerProfile = {
  latitude: number;
  longitude: number;
  previous_crop: string | null;
  water_source: "rainfed" | "irrigated" | "both" | "unknown";
  water_after_heavy_rain: "drains" | "stays" | "sometimes" | "unknown";
  soil_test: "yes" | "no" | "unknown";
  soil_ph: number | null;
  priority: "water" | "soil" | "production_stability";
};

export type PlanTask = { code: string; en: string; bn: string };
export type PlanMonth = {
  index: number;
  planning_month: string;
  month_name: { en: string; bn: string };
  phase: { en: string; bn: string };
  objective: { en: string; bn: string };
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
  };
  farmer_context: FarmerProfile;
  planning_window: { start: string; end: string };
  months: PlanMonth[];
  recent_environment: RecentEnvironment | null;
  historical_baseline: PowerBaseline | null;
  rotation_explorer: {
    status: string;
    message_en: string;
    message_bn: string;
  };
  evidence: {
    nasa_sources: NasaSource[];
    agricultural_sources: AgriculturalSource[];
    calendar_evidence: CalendarEvidence[];
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
