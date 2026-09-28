import { useEffect, useMemo, useState, type FormEvent } from "react";
import WorldGlobe from "./WorldGlobe";
import LocationMap from "./LocationMap";
import DecisionReport from "./DecisionReport";
import FieldIcon, { type IconName } from "./FieldIcon";
import {
  ApiError,
  apiGet,
  apiPost,
  type FarmerProfile,
  type LocationContext,
  type NasaSource,
  type PlaceResult,
  type PlanBrief,
  type PowerBaseline,
  type PowerBaselineWindow,
  type RecentEnvironment,
  type Status,
  type Workspace,
} from "./api";

type Point = { latitude: number; longitude: number };

const cropOptions = [
  ["rice", "Rice", "rice"],
  ["wheat", "Wheat", "wheat"],
  ["maize", "Maize", "maize"],
  ["pulse", "Pulse", "pulse"],
  ["mustard", "Mustard", "mustard"],
  ["vegetables", "Vegetables", "vegetables"],
  ["jute", "Jute", "jute"],
  ["other", "Other", "other"],
] as const;

const priorities = [
  ["water", "Use water carefully", "water"],
  ["soil", "Protect the soil", "soil"],
  ["production_stability", "Keep production stable", "stability"],
] as const;

function dateMinus(days: number) {
  return new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
}

function formatMetric(value: number | null | undefined, suffix = "") {
  if (value === null || value === undefined || !Number.isFinite(value)) return "Unavailable";
  return `${new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 }).format(value)}${suffix}`;
}

function shortPlace(place: PlaceResult | null, context: LocationContext | null) {
  if (place?.name) return place.name.split(",")[0];
  if (context?.country?.name) return context.country.name;
  return "No field selected";
}

function integrationLabel(value: string) {
  if (value.includes("ready")) return "READY";
  if (value.includes("pending")) return "ADAPTER";
  if (value.includes("gated")) return "QA GATE";
  return "SOURCE";
}

function statusLabel(status: Status) {
  if (status === "loading") return "SYNCING";
  if (status === "ready") return "ONLINE";
  if (status === "unavailable") return "UNAVAILABLE";
  return "STANDBY";
}

function validPoint(point: Point) {
  return (
    Number.isFinite(point.latitude) &&
    Number.isFinite(point.longitude) &&
    point.latitude >= -90 &&
    point.latitude <= 90 &&
    point.longitude >= -180 &&
    point.longitude <= 180
  );
}

export default function App() {
  const [workspace, setWorkspace] = useState<Workspace>("earth");
  const [point, setPoint] = useState<Point | null>(null);
  const [selectedPlace, setSelectedPlace] = useState<PlaceResult | null>(null);
  const [context, setContext] = useState<LocationContext | null>(null);
  const [contextStatus, setContextStatus] = useState<Status>("idle");
  const [recent, setRecent] = useState<RecentEnvironment | null>(null);
  const [recentStatus, setRecentStatus] = useState<Status>("idle");
  const [baseline, setBaseline] = useState<PowerBaseline | null>(null);
  const [baselineWindow, setBaselineWindow] = useState<PowerBaselineWindow | null>(null);
  const [baselineStatus, setBaselineStatus] = useState<Status>("idle");
  const [nasaCatalog, setNasaCatalog] = useState<NasaSource[]>([]);
  const [search, setSearch] = useState("");
  const [searchStatus, setSearchStatus] = useState<Status>("idle");
  const [placeResults, setPlaceResults] = useState<PlaceResult[]>([]);
  const [locationError, setLocationError] = useState("");
  const [gpsBusy, setGpsBusy] = useState(false);

  const [previousCrops, setPreviousCrops] = useState<string[]>([]);
  const [intendedCrop, setIntendedCrop] = useState("");
  const [waterSource, setWaterSource] = useState<FarmerProfile["water_source"]>("unknown");
  const [waterAfterRain, setWaterAfterRain] = useState<FarmerProfile["water_after_heavy_rain"]>("unknown");
  const [soilTest, setSoilTest] = useState<FarmerProfile["soil_test"]>("unknown");
  const [soilPh, setSoilPh] = useState("");
  const [priority, setPriority] = useState<FarmerProfile["priority"]>("production_stability");
  const [startMonth, setStartMonth] = useState(() => new Date().getMonth() + 1);
  const [startYear, setStartYear] = useState(() => Math.max(2026, new Date().getFullYear()));
  const [plan, setPlan] = useState<PlanBrief | null>(null);
  const [planBusy, setPlanBusy] = useState(false);
  const [planError, setPlanError] = useState("");

  const mapDate = useMemo(() => dateMinus(2), []);
  const locationName = shortPlace(selectedPlace, context);

  useEffect(() => {
    apiGet<{ sources: NasaSource[] }>("/api/v1/nasa/catalog")
      .then((payload) => setNasaCatalog(payload.sources))
      .catch(() => setNasaCatalog([]));
  }, []);

  useEffect(() => {
    const query = search.trim();
    if (query.length < 2) {
      setPlaceResults([]);
      setSearchStatus("idle");
      return;
    }

    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setSearchStatus("loading");
      apiGet<{ results: PlaceResult[] }>(
        `/api/v1/places/search?q=${encodeURIComponent(query)}`,
        controller.signal,
      )
        .then((payload) => {
          setPlaceResults(payload.results ?? []);
          setSearchStatus("ready");
        })
        .catch(() => {
          if (!controller.signal.aborted) {
            setPlaceResults([]);
            setSearchStatus("unavailable");
          }
        });
    }, 280);

    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [search]);

  useEffect(() => {
    if (!point) {
      setContext(null);
      setRecent(null);
      setBaseline(null);
      setBaselineWindow(null);
      setContextStatus("idle");
      setRecentStatus("idle");
      setBaselineStatus("idle");
      return;
    }

    const controller = new AbortController();
    setContextStatus("loading");
    setRecentStatus("loading");
    setLocationError("");
    setPlan(null);

    const load = async () => {
      let place: PlaceResult | null = selectedPlace;
      try {
        const reverse = await apiGet<{ place: PlaceResult | null }>(
          `/api/v1/places/reverse?lat=${point.latitude}&lon=${point.longitude}`,
          controller.signal,
        );
        if (reverse.place) {
          place = reverse.place;
          setSelectedPlace(reverse.place);
        }
      } catch {
        // Coordinates remain usable even when reverse geocoding is unavailable.
      }

      const countryCode = place?.address.country_code || "";
      const countryName = place?.address.country || "";
      const contextQuery =
        `/api/v1/context?lat=${point.latitude}&lon=${point.longitude}` +
        (countryCode ? `&country_code=${encodeURIComponent(countryCode)}` : "") +
        (countryName ? `&country_name=${encodeURIComponent(countryName)}` : "");

      const [contextResult, recentResult] = await Promise.allSettled([
        apiGet<LocationContext>(contextQuery, controller.signal),
        apiGet<RecentEnvironment>(
          `/api/v1/environment/recent?lat=${point.latitude}&lon=${point.longitude}`,
          controller.signal,
        ),
      ]);

      if (controller.signal.aborted) return;

      if (contextResult.status === "fulfilled") {
        setContext(contextResult.value);
        setContextStatus("ready");
      } else {
        setContext(null);
        setContextStatus("unavailable");
        setLocationError("The country context could not be resolved. NASA coordinate queries can still be retried.");
      }

      if (recentResult.status === "fulfilled") {
        setRecent(recentResult.value);
        setRecentStatus(recentResult.value.status === "available" ? "ready" : "unavailable");
      } else {
        setRecent(null);
        setRecentStatus("unavailable");
      }
    };

    void load();
    return () => controller.abort();
  }, [point]);

  useEffect(() => {
    if (!point) return;
    const controller = new AbortController();
    setBaselineStatus("loading");

    apiGet<PowerBaselineWindow>(
      `/api/v1/environment/baseline-window?lat=${point.latitude}&lon=${point.longitude}&start_month=${startMonth}`,
      controller.signal,
    )
      .then((payload) => {
        setBaselineWindow(payload);
        const first = payload.summaries?.[0] ?? null;
        setBaseline({
          status: payload.status,
          provider: payload.provider,
          product: payload.product,
          kind: "historical_climatology",
          baseline_period: payload.baseline_period,
          coordinates: payload.coordinates,
          summary: first,
          source_products: payload.source_products,
          source_request_url: payload.source_request_url,
          limitations: payload.limitations,
        });
        setBaselineStatus(payload.status === "available" ? "ready" : "unavailable");
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setBaseline(null);
          setBaselineWindow(null);
          setBaselineStatus("unavailable");
        }
      });

    return () => controller.abort();
  }, [point, startMonth]);

  function setFieldPoint(next: Point, place: PlaceResult | null = null) {
    if (!validPoint(next)) {
      setLocationError("That coordinate could not be used.");
      return;
    }
    setSelectedPlace(place);
    setPoint({
      latitude: Number(next.latitude.toFixed(5)),
      longitude: Number(next.longitude.toFixed(5)),
    });
    setLocationError("");
  }

  function choosePlace(place: PlaceResult) {
    setSearch("");
    setPlaceResults([]);
    setFieldPoint({ latitude: place.latitude, longitude: place.longitude }, place);
  }

  function useMyLocation() {
    if (!navigator.geolocation) {
      setLocationError("Location access is not available in this browser. Use global search or select the Earth.");
      return;
    }
    setGpsBusy(true);
    setLocationError("");
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setGpsBusy(false);
        setFieldPoint({ latitude: position.coords.latitude, longitude: position.coords.longitude });
      },
      () => {
        setGpsBusy(false);
        setLocationError("Location permission was not granted. Global search and the 3D Earth remain available.");
      },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 },
    );
  }

  function togglePreviousCrop(value: string) {
    setPreviousCrops((current) => {
      if (current.includes(value)) return current.filter((crop) => crop !== value);
      if (current.length >= 4) return current;
      return [...current, value];
    });
  }

  async function generatePlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!point) {
      setPlanError("Select the field on Earth before building the decision brief.");
      setWorkspace("earth");
      return;
    }

    const profile: FarmerProfile = {
      latitude: point.latitude,
      longitude: point.longitude,
      previous_crop: previousCrops[0] ?? null,
      previous_crops: previousCrops,
      intended_crop: intendedCrop || null,
      water_source: waterSource,
      water_after_heavy_rain: waterAfterRain,
      soil_test: soilTest,
      soil_ph: soilTest === "yes" && soilPh.trim() ? Number(soilPh) : null,
      priority,
      country_code: context?.country.code ?? selectedPlace?.address.country_code ?? null,
      country_name: context?.country.name ?? selectedPlace?.address.country ?? null,
      place_name: selectedPlace?.display_name ?? locationName,
    };

    setPlanBusy(true);
    setPlanError("");
    try {
      await apiPost("/api/v1/farms/validate", profile);
      const payload = await apiPost<PlanBrief>("/api/v1/plans/preview", {
        farm: profile,
        start_year: startYear,
        start_month: startMonth,
        include_recent_power: false,
        include_climate_baseline: false,
        recent_environment: recent,
        baseline_environment: baseline,
        baseline_window: baselineWindow,
      });
      if (!payload || !Array.isArray(payload.months) || payload.months.length !== 3) {
        throw new ApiError(500, "INVALID_PLAN_RESPONSE", "The decision brief was incomplete.");
      }
      setPlan(payload);
      setWorkspace("brief");
    } catch (error) {
      setPlanError(error instanceof ApiError ? error.message : "The decision brief could not be generated.");
    } finally {
      setPlanBusy(false);
    }
  }

  const summary = recent?.summary;
  const localCoverage = context?.coverage.local_agricultural_evidence ?? "waiting_for_field";
  const localSources = context?.agricultural_sources ?? [];
  const calendars = context?.calendar_evidence ?? [];
  const directSources = nasaCatalog.filter((source) => source.integration.includes("ready"));
  const adapterSources = nasaCatalog.filter((source) => source.integration.includes("pending") || source.integration.includes("gated"));

  return (
    <div className="os-app">
      <header className="os-topbar">
        <button type="button" className="os-brand" onClick={() => setWorkspace("earth")}>
          <span className="os-logo"><i /><i /><i /></span>
          <span>
            <strong>BoponX</strong>
            <small>EARTH INTELLIGENCE</small>
          </span>
        </button>

        <nav className="os-nav" aria-label="BoponX workspaces">
          {[
            ["earth", "Earth", "01"],
            ["intelligence", "Field Intelligence", "02"],
            ["rotation", "Rotation Lab", "03"],
            ["brief", "Farmer Brief", "04"],
          ].map(([id, label, number]) => (
            <button
              type="button"
              key={id}
              className={workspace === id ? "active" : ""}
              onClick={() => setWorkspace(id as Workspace)}
              disabled={id === "brief" && !plan}
            >
              <span>{number}</span>
              {label}
            </button>
          ))}
        </nav>

        <div className="os-statusbar">
          <span className={point ? "os-dot live" : "os-dot"} />
          <div>
            <small>{point ? "FIELD LOCK" : "NO FIELD"}</small>
            <strong>{locationName}</strong>
          </div>
        </div>
      </header>

      {workspace === "earth" && (
        <main className="earth-workspace">
          <aside className="earth-left-panel">
            <div className="panel-eyebrow"><span>01</span> FIELD ACQUISITION</div>
            <h1>Choose one field on Earth.</h1>
            <p className="panel-lead">
              Search a place, use your location, or click the 3D Earth. One coordinate becomes the anchor for every NASA query and every local evidence adapter.
            </p>

            <button type="button" className="gps-command" onClick={useMyLocation} disabled={gpsBusy}>
              <span className="gps-target"><i /><i /></span>
              <span>
                <strong>{gpsBusy ? "Locating field" : "Use my location"}</strong>
                <small>Browser permission required</small>
              </span>
              <b>⌖</b>
            </button>

            <div className="global-search">
              <span>⌕</span>
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search any village, city, or country"
                aria-label="Global place search"
              />
              {search && <button type="button" onClick={() => setSearch("")}>×</button>}
            </div>

            {search && (
              <div className="global-results">
                {searchStatus === "loading" && <div className="result-loading">Searching the world</div>}
                {searchStatus === "ready" && placeResults.length === 0 && <div className="result-empty">No place found</div>}
                {placeResults.slice(0, 6).map((place, index) => (
                  <button
                    type="button"
                    key={`${place.latitude}-${place.longitude}-${index}`}
                    onClick={() => choosePlace(place)}
                  >
                    <i>⌖</i>
                    <span>
                      <strong>{place.name ?? "Selected place"}</strong>
                      <small>
                        {[place.address.district, place.address.division, place.address.country]
                          .filter(Boolean)
                          .join(" · ")}
                      </small>
                    </span>
                  </button>
                ))}
              </div>
            )}

            {locationError && <div className="os-warning">{locationError}</div>}

            <div className="field-lock-card">
              <div className="lock-card-head">
                <span><i className={point ? "live" : ""} />{point ? "FIELD LOCKED" : "WAITING"}</span>
                <small>{statusLabel(contextStatus)}</small>
              </div>
              <strong>{locationName}</strong>
              {point ? (
                <>
                  <p>{point.latitude.toFixed(5)}° · {point.longitude.toFixed(5)}°</p>
                  <div className="lock-meta">
                    <span>{context?.country.name ?? selectedPlace?.address.country ?? "Resolving country"}</span>
                    <span>{localCoverage.replaceAll("_", " ")}</span>
                  </div>
                </>
              ) : (
                <p>No coordinates selected</p>
              )}
            </div>

            <button
              type="button"
              className="workspace-next"
              disabled={!point}
              onClick={() => setWorkspace("intelligence")}
            >
              Open Field Intelligence <span>→</span>
            </button>
          </aside>

          <section className="globe-command">
            <div className="globe-hud top-left">
              <span>GLOBAL FIELD SELECTOR</span>
              <strong>DRAG TO ROTATE · CLICK TO SELECT</strong>
            </div>
            <WorldGlobe point={point} onPick={(next) => setFieldPoint(next)} />
            <div className="globe-crosshair" aria-hidden="true"><i /><i /></div>
            <div className="globe-coordinate">
              <span>FIELD COORDINATE</span>
              <strong>{point ? `${point.latitude.toFixed(3)}°, ${point.longitude.toFixed(3)}°` : "CLICK EARTH"}</strong>
            </div>
            <div className="globe-legend">
              <span><i className="green" />NASA GLOBAL CONTEXT</span>
              <span><i className="cyan" />FIELD TARGET</span>
              <span><i className="amber" />LOCAL ADAPTER</span>
            </div>
          </section>

          <aside className="earth-right-panel">
            <div className="panel-eyebrow"><span>NASA</span> EVIDENCE BUS</div>
            <div className="evidence-bus-head">
              <strong>{nasaCatalog.length || 7} SOURCES</strong>
              <small>one decision pipeline</small>
            </div>

            <div className="evidence-bus">
              {(nasaCatalog.length ? nasaCatalog : []).map((source, index) => (
                <div className="bus-source" key={source.id}>
                  <span className="bus-index">{String(index + 1).padStart(2, "0")}</span>
                  <div>
                    <strong>{source.mission}</strong>
                    <p>{source.role.replaceAll("_", " ")}</p>
                  </div>
                  <b className={source.integration.includes("ready") ? "ready" : "adapter"}>
                    {integrationLabel(source.integration)}
                  </b>
                </div>
              ))}
            </div>

            <div className="fusion-note">
              <span>RULE 01</span>
              <p>Each NASA source has one job. BoponX never turns a map layer into a soil test or a forecast.</p>
            </div>
          </aside>
        </main>
      )}

      {workspace === "intelligence" && (
        <main className="intel-workspace">
          <div className="workspace-titlebar">
            <div>
              <span className="workspace-code">02 / FIELD INTELLIGENCE</span>
              <h1>{locationName}</h1>
            </div>
            <div className="workspace-title-status">
              <span><i className={recentStatus === "ready" ? "live" : ""} />POWER {statusLabel(recentStatus)}</span>
              <span><i className={baselineStatus === "ready" ? "live" : ""} />BASELINE {statusLabel(baselineStatus)}</span>
              <span><i className={contextStatus === "ready" ? "live" : ""} />LOCAL {statusLabel(contextStatus)}</span>
            </div>
          </div>

          <div className="intel-grid">
            <section className="intel-map-panel">
              <LocationMap point={point} onPick={(next) => setFieldPoint(next)} mapDate={mapDate} />
            </section>

            <aside className="signal-console">
              <div className="console-head">
                <div>
                  <span>NASA POWER</span>
                  <strong>AGROCLIMATE TELEMETRY</strong>
                </div>
                <small>{recent?.period ? `${recent.period.start} → ${recent.period.end}` : "WAITING FOR DATA"}</small>
              </div>

              <div className="telemetry-grid">
                <div className="telemetry primary">
                  <span>AIR TEMP</span>
                  <strong>{formatMetric(summary?.temperature_mean_c, "°C")}</strong>
                  <small>2 m mean</small>
                </div>
                <div className="telemetry">
                  <span>RAIN</span>
                  <strong>{formatMetric(summary?.precipitation_total_mm, " mm")}</strong>
                  <small>recent period</small>
                </div>
                <div className="telemetry">
                  <span>HUMIDITY</span>
                  <strong>{formatMetric(summary?.relative_humidity_mean_pct, "%")}</strong>
                  <small>2 m mean</small>
                </div>
                <div className="telemetry">
                  <span>WIND</span>
                  <strong>{formatMetric(summary?.wind_speed_2m_mean_ms, " m/s")}</strong>
                  <small>2 m mean</small>
                </div>
                <div className="telemetry">
                  <span>SOLAR</span>
                  <strong>{formatMetric(summary?.solar_radiation_mean_kwh_m2_day, " kWh/m²")}</strong>
                  <small>daily mean</small>
                </div>
                <div className="telemetry">
                  <span>MAX / MIN</span>
                  <strong>
                    {formatMetric(summary?.temperature_max_mean_c, "°")} / {formatMetric(summary?.temperature_min_mean_c, "°")}
                  </strong>
                  <small>period means</small>
                </div>
              </div>

              <div className="baseline-strip">
                <div>
                  <span>HISTORICAL REFERENCE</span>
                  <strong>{baseline?.baseline_period ? `${baseline.baseline_period.start_year}–${baseline.baseline_period.end_year}` : "Unavailable"}</strong>
                </div>
                <div>
                  <span>MONTH TEMP</span>
                  <strong>{formatMetric(baseline?.summary?.temperature_mean_c, "°C")}</strong>
                </div>
                <div>
                  <span>MONTH RAIN</span>
                  <strong>{formatMetric(baseline?.summary?.precipitation_mean_daily_mm, " mm/day")}</strong>
                </div>
              </div>

              <div className="observation-matrix">
                <div className="matrix-head">
                  <strong>OBSERVATION MATRIX</strong>
                  <small>what each layer contributes</small>
                </div>
                {directSources.slice(0, 5).map((source) => (
                  <div className="matrix-row" key={source.id}>
                    <span className="matrix-mission">{source.mission}</span>
                    <span>{source.decision_use}</span>
                    <b>{source.spatial}</b>
                  </div>
                ))}
              </div>
            </aside>

            <section className="local-adapter-panel">
              <div className="adapter-head">
                <div>
                  <span>LOCAL EVIDENCE ADAPTER</span>
                  <strong>{context?.country.name ?? "Select a field"}</strong>
                </div>
                <b className={localCoverage === "official_sources_indexed" ? "coverage-ready" : "coverage-gap"}>
                  {localCoverage === "official_sources_indexed" ? "VERIFIED SOURCES" : "ADAPTER GAP"}
                </b>
              </div>

              {localSources.length ? (
                <div className="local-source-row">
                  {localSources.map((source) => (
                    <a key={source.name} href={source.source_url} target="_blank" rel="noreferrer">
                      <span>{source.agency}</span>
                      <strong>{source.name}</strong>
                      <small>{source.kind.replaceAll("_", " ")}</small>
                    </a>
                  ))}
                </div>
              ) : (
                <div className="local-gap-message">
                  <strong>NASA coverage is available. A verified local agriculture adapter is not onboarded for this country yet.</strong>
                  <p>BoponX leaves the local layer empty instead of inventing government guidance.</p>
                </div>
              )}

              {calendars.length > 0 && (
                <div className="calendar-rail">
                  <span>REGIONAL CROP CALENDARS</span>
                  {calendars.slice(0, 8).map((crop) => <b key={crop.id}>{crop.name_en}</b>)}
                </div>
              )}
            </section>

            <section className="highres-panel">
              <div className="adapter-head">
                <div>
                  <span>HIGH RESOLUTION CHANNELS</span>
                  <strong>FIELD SCALE PATH</strong>
                </div>
                <small>truthful adapter state</small>
              </div>
              <div className="highres-grid">
                {adapterSources.map((source) => (
                  <article key={source.id}>
                    <span>{source.mission}</span>
                    <strong>{source.product}</strong>
                    <p>{source.decision_use}</p>
                    <div>
                      <b>{source.spatial}</b>
                      <small>{integrationLabel(source.integration)}</small>
                    </div>
                  </article>
                ))}
              </div>
            </section>
          </div>

          <button className="floating-next" type="button" disabled={!point} onClick={() => setWorkspace("rotation")}>
            Build decision scenario <span>→</span>
          </button>
        </main>
      )}

      {workspace === "rotation" && (
        <main className="rotation-workspace">
          <div className="workspace-titlebar">
            <div>
              <span className="workspace-code">03 / ROTATION LAB</span>
              <h1>Turn evidence into a field decision.</h1>
            </div>
            <div className="field-context-chip">
              <span>{locationName}</span>
              <strong>{context?.country.name ?? "No country"}</strong>
            </div>
          </div>

          <form className="scenario-grid" onSubmit={generatePlan}>
            <section className="scenario-column crop-history-column">
              <div className="scenario-heading">
                <span>01</span>
                <div><strong>Field memory</strong><small>Recent crops, newest first</small></div>
              </div>
              <div className="crop-console">
                {cropOptions.map(([value, label, icon]) => (
                  <button
                    type="button"
                    key={value}
                    className={previousCrops.includes(value) ? "scenario-crop active" : "scenario-crop"}
                    onClick={() => togglePreviousCrop(value)}
                  >
                    <FieldIcon name={icon as IconName} />
                    <span>{label}</span>
                    {previousCrops.includes(value) && <b>{previousCrops.indexOf(value) + 1}</b>}
                  </button>
                ))}
              </div>
              <button type="button" className="unknown-command" onClick={() => setPreviousCrops([])}>
                <FieldIcon name="unknown" /> Clear or not sure
              </button>

              <div className="scenario-heading intention-head">
                <span>02</span>
                <div><strong>Farmer intention</strong><small>What is being considered now</small></div>
              </div>
              <div className="crop-console intention">
                {cropOptions.map(([value, label, icon]) => (
                  <button
                    type="button"
                    key={value}
                    className={intendedCrop === value ? "scenario-crop active" : "scenario-crop"}
                    onClick={() => setIntendedCrop(intendedCrop === value ? "" : value)}
                  >
                    <FieldIcon name={icon as IconName} />
                    <span>{label}</span>
                  </button>
                ))}
              </div>
            </section>

            <section className="scenario-column constraint-column">
              <div className="scenario-heading">
                <span>03</span>
                <div><strong>Field constraints</strong><small>Only things the farmer can know</small></div>
              </div>

              <ScenarioChoice
                title="How does the field get water?"
                value={waterSource}
                options={[
                  ["rainfed", "Mostly rain", "rain"],
                  ["irrigated", "Mostly irrigation", "irrigation"],
                  ["both", "Rain and irrigation", "both"],
                  ["unknown", "Not sure", "unknown"],
                ]}
                onChange={(value) => setWaterSource(value as FarmerProfile["water_source"])}
              />

              <ScenarioChoice
                title="What happens after heavy rain?"
                value={waterAfterRain}
                options={[
                  ["drains", "Drains quickly", "drainage"],
                  ["stays", "Water stays", "standingWater"],
                  ["sometimes", "Changes by event", "mixed"],
                  ["unknown", "Not sure", "unknown"],
                ]}
                onChange={(value) => setWaterAfterRain(value as FarmerProfile["water_after_heavy_rain"])}
              />

              <div className="constraint-group">
                <span className="constraint-label">Soil test report</span>
                <div className="three-way">
                  {[
                    ["yes", "Yes"],
                    ["no", "No"],
                    ["unknown", "Not sure"],
                  ].map(([value, label]) => (
                    <button
                      type="button"
                      key={value}
                      className={soilTest === value ? "active" : ""}
                      onClick={() => setSoilTest(value as FarmerProfile["soil_test"])}
                    >
                      {label}
                    </button>
                  ))}
                </div>
                {soilTest === "yes" && (
                  <label className="ph-console">
                    <span>pH from report <small>optional</small></span>
                    <input
                      type="number"
                      min="0"
                      max="14"
                      step="0.1"
                      value={soilPh}
                      onChange={(event) => setSoilPh(event.target.value)}
                      placeholder="6.5"
                    />
                  </label>
                )}
              </div>
            </section>

            <section className="scenario-column mission-column">
              <div className="scenario-heading">
                <span>04</span>
                <div><strong>Mission objective</strong><small>What matters most now</small></div>
              </div>

              <div className="priority-console">
                {priorities.map(([value, label, icon]) => (
                  <button
                    type="button"
                    key={value}
                    className={priority === value ? "active" : ""}
                    onClick={() => setPriority(value as FarmerProfile["priority"])}
                  >
                    <FieldIcon name={icon as IconName} />
                    <span>{label}</span>
                  </button>
                ))}
              </div>

              <div className="planning-window-console">
                <span>90 DAY WINDOW</span>
                <div>
                  <select value={startMonth} onChange={(event) => setStartMonth(Number(event.target.value))}>
                    {Array.from({ length: 12 }, (_, index) => index + 1).map((month) => (
                      <option value={month} key={month}>{new Date(2026, month - 1, 1).toLocaleString("en", { month: "long" })}</option>
                    ))}
                  </select>
                  <select value={startYear} onChange={(event) => setStartYear(Number(event.target.value))}>
                    {Array.from({ length: 10 }, (_, index) => 2026 + index).map((year) => (
                      <option value={year} key={year}>{year}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="readiness-console">
                <div className="readiness-title">
                  <span>DECISION INPUTS</span>
                  <strong>{point ? "FIELD READY" : "FIELD REQUIRED"}</strong>
                </div>
                <ReadinessRow label="NASA agroclimate" ready={recentStatus === "ready"} />
                <ReadinessRow label="Monthly baseline" ready={baselineStatus === "ready"} />
                <ReadinessRow label="Local official sources" ready={localCoverage === "official_sources_indexed"} optional />
                <ReadinessRow label="Farmer intention" ready={Boolean(intendedCrop)} optional />
                <p>Missing sources stay visible as unknown. They are never replaced with sample values.</p>
              </div>

              {planError && <div className="os-warning">{planError}</div>}

              <button type="submit" className="generate-command" disabled={!point || planBusy}>
                <span>
                  <small>DETERMINISTIC EVIDENCE ENGINE</small>
                  <strong>{planBusy ? "Building scenario" : "Generate farmer brief"}</strong>
                </span>
                <b>→</b>
              </button>
            </section>
          </form>
        </main>
      )}

      {workspace === "brief" && (
        <main className="brief-workspace">
          {plan ? (
            <DecisionReport
              brief={plan}
              localSources={localSources}
              onBack={() => setWorkspace("rotation")}
              onEarth={() => setWorkspace("earth")}
            />
          ) : (
            <div className="empty-brief">
              <span>04 / FARMER BRIEF</span>
              <h1>No brief has been generated yet.</h1>
              <button type="button" onClick={() => setWorkspace("rotation")}>Open Rotation Lab</button>
            </div>
          )}
        </main>
      )}

      <footer className="os-footer">
        <span>EARTH.exe · BoponX</span>
        <span>NASA data + verified local evidence + farmer context</span>
        <span>Independent project · no NASA endorsement</span>
      </footer>
    </div>
  );
}

function ScenarioChoice({
  title,
  value,
  options,
  onChange,
}: {
  title: string;
  value: string;
  options: Array<[string, string, string]>;
  onChange: (value: string) => void;
}) {
  return (
    <div className="constraint-group">
      <span className="constraint-label">{title}</span>
      <div className="constraint-options">
        {options.map(([id, label, icon]) => (
          <button type="button" key={id} className={value === id ? "active" : ""} onClick={() => onChange(id)}>
            <FieldIcon name={icon as IconName} />
            <span>{label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

function ReadinessRow({ label, ready, optional = false }: { label: string; ready: boolean; optional?: boolean }) {
  return (
    <div className="readiness-row">
      <i className={ready ? "ready" : optional ? "optional" : ""} />
      <span>{label}</span>
      <b>{ready ? "READY" : optional ? "OPTIONAL" : "WAITING"}</b>
    </div>
  );
}
