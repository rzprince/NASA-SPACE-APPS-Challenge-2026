/** Versioned, deliberately small BoponX API contract. */
export type Status = "loading" | "ready" | "unavailable";

export type Location = {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  location_note: string;
};

export type ClimateDay = {
  date: string;
  T2M: number | null;
  PRECTOTCORR: number | null;
};

export type Coverage = { valid_days: number; expected_days: number; fraction: number };

export type ClimateSnapshot = {
  schema_version: "power-pilot/v1";
  location_id: string;
  period: { start: string; end: string; time_standard: string };
  variables: Record<string, { provider_unit: string; description: string | null }>;
  summary: {
    temperature_mean_valid_days: number;
    precipitation_total_full_period: number | null;
    precipitation_sum_valid_days: number;
    coverage: Record<string, Coverage>;
  };
  daily: ClimateDay[];
  evidence: {
    provider: string;
    source_request_url: string;
    raw_sha256: string;
    snapshot_id: string;
    ingestion_origin: string;
    data_kind: string;
    source_products: string[];
  };
};

export type FarmProfile = {
  location_id: "rajshahi-pilot";
  previous_crop: string | null;
  soil_ph: number | null;
  soil_texture: "sandy" | "loamy" | "clayey" | "unknown";
  irrigation_mode: "none" | "limited" | "reliable" | "unknown";
  priorities: ("water" | "soil" | "production_stability")[];
};

export type FarmValidation = {
  status: string;
  profile: FarmProfile;
  missing_inputs: string[];
  warnings: string[];
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
