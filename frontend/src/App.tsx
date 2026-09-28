import { useEffect, useMemo, useState, type CSSProperties, type FormEvent } from "react";
import LocationMap from "./LocationMap";
import DecisionReport from "./DecisionReport";
import FieldIcon, { type IconName } from "./FieldIcon";
import {
  ApiError,
  apiGet,
  apiPost,
  type FarmerProfile,
  type LocalSourceRegistry,
  type LocationContext,
  type PlaceResult,
  type PlanBrief,
  type PowerBaselineWindow,
  type RecentEnvironment,
} from "./api";

type Point = { latitude: number; longitude: number };
type View = "earth" | "rotation" | "plan";
type LayerKey = "trueColor" | "rain" | "soil";

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

const cropLabels: Record<string, string> = Object.fromEntries(
  cropOptions.map(([id, label]) => [id, label]),
);

function dateMinus(days: number) {
  return new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
}

function metric(value: number | null | undefined, suffix = "") {
  if (value === null || value === undefined || !Number.isFinite(value)) return "—";
  return `${new Intl.NumberFormat("en", { maximumFractionDigits: 1 }).format(value)}${suffix}`;
}

function placeLabel(place: PlaceResult | null, point: Point | null) {
  if (place?.address.village) return place.address.village;
  if (place?.address.town) return place.address.town;
  if (place?.address.district) return place.address.district;
  if (place?.name) return place.name;
  if (point) return `${point.latitude.toFixed(3)}°, ${point.longitude.toFixed(3)}°`;
  return "No field selected";
}

function buildStrategies(
  context: LocationContext | null,
  intendedCrop: string,
  previousCrops: string[],
) {
  const names = (context?.calendar_evidence ?? []).map((item) => item.name_en);
  const unique = Array.from(new Set(names));
  const intentLabel = intendedCrop ? cropLabels[intendedCrop] ?? intendedCrop : null;
  const previousLabel = previousCrops[0] ? cropLabels[previousCrops[0]] ?? previousCrops[0] : null;
  const pool = [intentLabel, ...unique].filter((value): value is string => Boolean(value));
  const fallback = ["Local crop A", "Local crop B", "Local crop C"];
  const source = pool.length >= 3 ? pool : [...pool, ...fallback].slice(0, 3);

  return [
    {
      id: "A",
      title: "Water cautious path",
      crops: [source[0], source[1], source[2]],
      note: "Exploration path only. Check local calendar, water access and soil evidence before committing.",
    },
    {
      id: "B",
      title: "Soil recovery path",
      crops: [source[1] ?? source[0], source[2] ?? source[0], source[0]],
      note: "Sequence is not ranked until reviewed crop sequence rules are connected.",
    },
    {
      id: "C",
      title: "Farmer intent path",
      crops: [previousLabel ?? source[2], intentLabel ?? source[0], source[1] ?? source[0]],
      note: "Keeps the farmer intention visible while evidence gaps are reviewed.",
    },
  ];
}

export default function App() {
  const [view, setView] = useState<View>("earth");
  const [point, setPoint] = useState<Point | null>(null);
  const [place, setPlace] = useState<PlaceResult | null>(null);
  const [search, setSearch] = useState("");
  const [searchResults, setSearchResults] = useState<PlaceResult[]>([]);
  const [searchBusy, setSearchBusy] = useState(false);
  const [gpsBusy, setGpsBusy] = useState(false);
  const [context, setContext] = useState<LocationContext | null>(null);
  const [localSources, setLocalSources] = useState<LocalSourceRegistry | null>(null);
  const [recent, setRecent] = useState<RecentEnvironment | null>(null);
  const [baselineWindow, setBaselineWindow] = useState<PowerBaselineWindow | null>(null);
  const [dataBusy, setDataBusy] = useState(false);
  const [activeLayer, setActiveLayer] = useState<LayerKey | null>("trueColor");
  const [error, setError] = useState("");

  const [previousCrops, setPreviousCrops] = useState<string[]>([]);
  const [intendedCrop, setIntendedCrop] = useState("");
  const [waterSource, setWaterSource] = useState<FarmerProfile["water_source"]>("unknown");
  const [drainage, setDrainage] = useState<FarmerProfile["water_after_heavy_rain"]>("unknown");
  const [soilTest, setSoilTest] = useState<FarmerProfile["soil_test"]>("unknown");
  const [soilPh, setSoilPh] = useState("");
  const [priority, setPriority] = useState<FarmerProfile["priority"]>("production_stability");
  const [startMonth, setStartMonth] = useState(() => new Date().getMonth() + 1);
  const [startYear, setStartYear] = useState(() => Math.max(2026, new Date().getFullYear()));
  const [plan, setPlan] = useState<PlanBrief | null>(null);
  const [planBusy, setPlanBusy] = useState(false);

  const mapDate = useMemo(() => dateMinus(2), []);
  const strategies = useMemo(
    () => buildStrategies(context, intendedCrop, previousCrops),
    [context, intendedCrop, previousCrops],
  );

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
    ]).then(async ([contextResult, recentResult, baselineResult, placeResult]) => {
      if (controller.signal.aborted) return;

      if (contextResult.status === "fulfilled") setContext(contextResult.value);
      else setContext(null);

      if (recentResult.status === "fulfilled") setRecent(recentResult.value);
      else setRecent(null);

      if (baselineResult.status === "fulfilled") setBaselineWindow(baselineResult.value);
      else setBaselineWindow(null);

      const resolvedPlace = placeResult.status === "fulfilled" ? placeResult.value.place : null;
      setPlace(resolvedPlace);

      const countryCode = resolvedPlace?.address.country_code;
      if (countryCode) {
        try {
          const registry = await apiGet<LocalSourceRegistry>(
            `/api/v1/local-sources?country_code=${encodeURIComponent(countryCode)}`,
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

  const recentSummary = recent?.status === "available" ? recent.summary : undefined;
  const firstBaseline = baselineWindow?.status === "available" ? baselineWindow.summaries?.[0] : undefined;
  const recentDailyRain =
    recentSummary?.precipitation_total_mm != null && recentSummary.precipitation_valid_days
      ? recentSummary.precipitation_total_mm / recentSummary.precipitation_valid_days
      : null;
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

  const readiness = Math.min(
    100,
    (point ? 20 : 0) +
      (recent?.status === "available" ? 20 : 0) +
      (baselineWindow?.status === "available" ? 15 : 0) +
      (place?.address.country_code ? 10 : 0) +
      (localSources?.official_sources.length ? 10 : 0) +
      (previousCrops.length ? 10 : 0) +
      (intendedCrop ? 10 : 0) +
      (waterSource !== "unknown" && drainage !== "unknown" ? 5 : 0),
  );

  function choosePoint(next: Point, selected: PlaceResult | null = null) {
    if (!Number.isFinite(next.latitude) || !Number.isFinite(next.longitude)) return;
    setPoint({
      latitude: Number(next.latitude.toFixed(5)),
      longitude: Number(next.longitude.toFixed(5)),
    });
    if (selected) setPlace(selected);
  }

  function locateMe() {
    setError("");
    if (!navigator.geolocation) {
      setError("Location access is unavailable in this browser. Search for a place or tap the globe.");
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
      () => {
        setGpsBusy(false);
        setError("Location permission was not granted. Search for a place or tap the globe.");
      },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 },
    );
  }

  function toggleHistory(crop: string) {
    setPreviousCrops((current) => {
      if (current.includes(crop)) return current.filter((item) => item !== crop);
      if (current.length >= 4) return current;
      return [...current, crop];
    });
  }

  async function runDecisionEngine(event?: FormEvent) {
    event?.preventDefault();
    if (!point) {
      setError("Select a field on Earth before running the decision engine.");
      setView("earth");
      return;
    }

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
    };

    setPlanBusy(true);
    setError("");
    try {
      const payload = await apiPost<PlanBrief>("/api/v1/plans/preview", {
        farm,
        start_year: startYear,
        start_month: startMonth,
        include_recent_power: false,
        include_climate_baseline: false,
        recent_environment: recent,
        baseline_window: baselineWindow,
      });
      setPlan(payload);
      setView("plan");
    } catch (runError) {
      setError(runError instanceof ApiError ? runError.message : "Decision engine failed.");
    } finally {
      setPlanBusy(false);
    }
  }

  return (
    <div className="mission-app">
      <header className="mission-topbar">
        <div className="mission-brand">
          <span className="brand-orbit"><i /><b /></span>
          <div>
            <strong>BoponX</strong>
            <small>EARTH.exe | Field Shift Intelligence</small>
          </div>
        </div>

        <nav className="mission-nav">
          <button className={view === "earth" ? "active" : ""} onClick={() => setView("earth")}>
            <span>01</span> Earth Twin
          </button>
          <button className={view === "rotation" ? "active" : ""} onClick={() => setView("rotation")}>
            <span>02</span> Rotation Lab
          </button>
          <button className={view === "plan" ? "active" : ""} onClick={() => setView("plan")}>
            <span>03</span> Field Plan
          </button>
        </nav>

        <div className="mission-status">
          <span className={dataBusy ? "pulse loading" : "pulse"} />
          {point ? placeLabel(place, point) : "Awaiting field"}
        </div>
      </header>

      {view === "earth" && (
        <main className="earth-command">
          <aside className="control-rail left-rail">
            <div className="rail-title">
              <span>FIELD CONTROL</span>
              <strong>Choose one field on Earth</strong>
            </div>

            <button className="locate-command" onClick={locateMe} disabled={gpsBusy}>
              <FieldIcon name="stability" />
              <span>
                <strong>{gpsBusy ? "Locating…" : "Use current location"}</strong>
                <small>Browser permission only</small>
              </span>
            </button>

            <div className="global-search">
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search any village, district, city or country"
              />
              <span>{searchBusy ? "…" : "⌕"}</span>
              {searchResults.length > 0 && (
                <div className="search-results">
                  {searchResults.slice(0, 6).map((result, index) => (
                    <button
                      key={`${result.latitude}-${result.longitude}-${index}`}
                      onClick={() => {
                        choosePoint({ latitude: result.latitude, longitude: result.longitude }, result);
                        setSearch("");
                        setSearchResults([]);
                      }}
                    >
                      <strong>{result.name}</strong>
                      <small>
                        {[result.address.district, result.address.division, result.address.country]
                          .filter(Boolean)
                          .join(" · ")}
                      </small>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <section className="selected-field-card">
              <span className="micro-label">SELECTED FIELD</span>
              <h2>{placeLabel(place, point)}</h2>
              <p>{place?.address.country ?? "Select a point anywhere on Earth"}</p>
              {point && <code>{point.latitude.toFixed(5)} / {point.longitude.toFixed(5)}</code>}
            </section>

            <section className="local-mesh">
              <div className="rail-section-head">
                <span>LOCAL DATA MESH</span>
                <b>{localSources?.coverage === "verified_country_adapter" ? "VERIFIED" : "GLOBAL FALLBACK"}</b>
              </div>
              {(localSources?.official_sources ?? []).map((source) => (
                <a key={source.id ?? source.name} href={source.source_url} target="_blank" rel="noreferrer">
                  <strong>{source.name}</strong>
                  <small>{source.scope}</small>
                </a>
              ))}
              {localSources?.official_sources.length === 0 && (
                <div className="source-gap">
                  <strong>No verified national adapter is connected yet.</strong>
                  <p>NASA analysis still works globally. Local crop advice stays constrained until a reviewed source is connected.</p>
                </div>
              )}
              {(localSources?.global_sources ?? []).map((source) => (
                <a className="global-source" key={source.id ?? source.name} href={source.source_url} target="_blank" rel="noreferrer">
                  <strong>{source.name}</strong>
                  <small>International crop calendar reference</small>
                </a>
              ))}
            </section>
          </aside>

          <section className="globe-center">
            <LocationMap
              point={point}
              onPick={(next) => choosePoint(next)}
              mapDate={mapDate}
              activeLayer={activeLayer}
              onLayerChange={setActiveLayer}
            />

            <div className="fusion-strip">
              <div>
                <span>RAIN ANOMALY</span>
                <strong>{rainAnomaly == null ? "—" : `${rainAnomaly >= 0 ? "+" : ""}${rainAnomaly.toFixed(0)}%`}</strong>
                <small>recent POWER vs climatology</small>
              </div>
              <div>
                <span>HEAT SHIFT</span>
                <strong>{tempDelta == null ? "—" : `${tempDelta >= 0 ? "+" : ""}${tempDelta.toFixed(1)}°C`}</strong>
                <small>recent mean vs monthly baseline</small>
              </div>
              <div>
                <span>SOIL MOISTURE</span>
                <strong>SMAP</strong>
                <small>spatial layer | 9 km context</small>
              </div>
              <div>
                <span>DECISION READINESS</span>
                <strong>{readiness}%</strong>
                <small>evidence completeness, not suitability</small>
              </div>
            </div>
          </section>

          <aside className="control-rail right-rail">
            <div className="rail-title">
              <span>NASA FUSION ENGINE</span>
              <strong>One field. One evidence stack.</strong>
            </div>

            <div className="earth-pulse">
              <div className="pulse-ring" style={{ "--score": readiness } as CSSProperties}>
                <span>{readiness}</span>
                <small>READY</small>
              </div>
              <div className="pulse-copy">
                <strong>{dataBusy ? "Resolving Earth signals…" : "Earth Pulse"}</strong>
                <small>NASA data are fused once here, then reused by the decision engine.</small>
              </div>
            </div>

            <div className="signal-grid">
              <article>
                <span>PRECIPITATION</span>
                <strong>{metric(recentSummary?.precipitation_total_mm, " mm")}</strong>
                <small>NASA POWER recent period</small>
              </article>
              <article>
                <span>MEAN TEMP</span>
                <strong>{metric(recentSummary?.temperature_mean_c, "°C")}</strong>
                <small>NASA POWER</small>
              </article>
              <article>
                <span>MAX TEMP</span>
                <strong>{metric(recentSummary?.temperature_max_mean_c, "°C")}</strong>
                <small>period mean of daily max</small>
              </article>
              <article>
                <span>HUMIDITY</span>
                <strong>{metric(recentSummary?.relative_humidity_mean_pct, "%")}</strong>
                <small>2 m relative humidity</small>
              </article>
              <article>
                <span>WIND</span>
                <strong>{metric(recentSummary?.wind_speed_mean_m_s, " m/s")}</strong>
                <small>2 m wind speed</small>
              </article>
              <article>
                <span>BASELINE RAIN</span>
                <strong>{metric(firstBaseline?.precipitation_mean_daily_mm, " mm/d")}</strong>
                <small>POWER 2001 to 2020</small>
              </article>
            </div>

            <div className="source-stack">
              <div><i className="green" /><span>GPM IMERG V07B</span><small>near real time rain layer</small></div>
              <div><i className="blue" /><span>SMAP SPL3SMP E V6</span><small>surface soil moisture</small></div>
              <div><i className="amber" /><span>NASA POWER</span><small>agroclimate + baseline</small></div>
              <div><i className="white" /><span>NASA GIBS</span><small>spatial evidence delivery</small></div>
            </div>

            <button className="next-command" onClick={() => setView("rotation")}>
              Open Rotation Lab <b>→</b>
            </button>

            {error && <div className="command-error">{error}</div>}
          </aside>
        </main>
      )}

      {view === "rotation" && (
        <main className="rotation-lab">
          <aside className="profile-panel">
            <div className="rail-title">
              <span>FARMER INPUT</span>
              <strong>Only ask what the farmer knows.</strong>
            </div>

            <label className="profile-group">
              <span>RECENT CROPS</span>
              <div className="crop-mini-grid">
                {cropOptions.map(([id, label, icon]) => (
                  <button
                    type="button"
                    className={previousCrops.includes(id) ? "active" : ""}
                    key={id}
                    onClick={() => toggleHistory(id)}
                  >
                    <FieldIcon name={icon as IconName} />
                    {label}
                    {previousCrops.includes(id) && <b>{previousCrops.indexOf(id) + 1}</b>}
                  </button>
                ))}
              </div>
            </label>

            <label className="profile-group">
              <span>WHAT DO YOU WANT TO GROW NOW?</span>
              <select value={intendedCrop} onChange={(event) => setIntendedCrop(event.target.value)}>
                <option value="">Not decided</option>
                {cropOptions.map(([id, label]) => <option key={id} value={id}>{label}</option>)}
              </select>
            </label>

            <div className="two-control">
              <label>
                <span>WATER SOURCE</span>
                <select value={waterSource} onChange={(event) => setWaterSource(event.target.value as FarmerProfile["water_source"])}>
                  <option value="unknown">Not sure</option>
                  <option value="rainfed">Mostly rain</option>
                  <option value="irrigated">Mostly irrigation</option>
                  <option value="both">Rain and irrigation</option>
                </select>
              </label>
              <label>
                <span>AFTER HEAVY RAIN</span>
                <select value={drainage} onChange={(event) => setDrainage(event.target.value as FarmerProfile["water_after_heavy_rain"])}>
                  <option value="unknown">Not sure</option>
                  <option value="drains">Drains quickly</option>
                  <option value="stays">Water stays</option>
                  <option value="sometimes">Changes</option>
                </select>
              </label>
            </div>

            <div className="two-control">
              <label>
                <span>SOIL TEST</span>
                <select value={soilTest} onChange={(event) => setSoilTest(event.target.value as FarmerProfile["soil_test"])}>
                  <option value="unknown">Not sure</option>
                  <option value="no">No report</option>
                  <option value="yes">Yes</option>
                </select>
              </label>
              {soilTest === "yes" && (
                <label>
                  <span>pH FROM REPORT</span>
                  <input type="number" min="0" max="14" step="0.1" value={soilPh} onChange={(event) => setSoilPh(event.target.value)} />
                </label>
              )}
            </div>

            <label className="profile-group">
              <span>PRIMARY PRIORITY</span>
              <div className="priority-toggle">
                {[
                  ["water", "Water"],
                  ["soil", "Soil"],
                  ["production_stability", "Stability"],
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

            <div className="two-control">
              <label>
                <span>START MONTH</span>
                <select value={startMonth} onChange={(event) => setStartMonth(Number(event.target.value))}>
                  {Array.from({ length: 12 }, (_, index) => index + 1).map((month) => (
                    <option value={month} key={month}>{String(month).padStart(2, "0")}</option>
                  ))}
                </select>
              </label>
              <label>
                <span>YEAR</span>
                <select value={startYear} onChange={(event) => setStartYear(Number(event.target.value))}>
                  {Array.from({ length: 10 }, (_, index) => 2026 + index).map((year) => (
                    <option value={year} key={year}>{year}</option>
                  ))}
                </select>
              </label>
            </div>

            <button className="run-engine" onClick={() => runDecisionEngine()} disabled={planBusy}>
              <span>{planBusy ? "RUNNING…" : "RUN DECISION ENGINE"}</span><b>→</b>
            </button>
          </aside>

          <section className="strategy-stage">
            <div className="strategy-heading">
              <div>
                <span>ROTATION SANDBOX</span>
                <h1>Explore futures before choosing one.</h1>
              </div>
              <p>
                BoponX does not repeat the raw NASA cards here. It carries forward the Earth Pulse as decision context and shows only what changes the rotation discussion.
              </p>
            </div>

            <div className="strategy-context-row">
              <div><span>FIELD</span><strong>{placeLabel(place, point)}</strong></div>
              <div><span>RAIN SIGNAL</span><strong>{rainAnomaly == null ? "pending" : rainAnomaly > 30 ? "wetter" : rainAnomaly < -30 ? "drier" : "near baseline"}</strong></div>
              <div><span>LOCAL SOURCES</span><strong>{localSources?.official_sources.length ?? 0} verified</strong></div>
              <div><span>FARMER INTENT</span><strong>{intendedCrop ? cropLabels[intendedCrop] : "not decided"}</strong></div>
            </div>

            <div className="strategy-cards">
              {strategies.map((strategy) => (
                <article key={strategy.id}>
                  <header>
                    <span>PATH {strategy.id}</span>
                    <strong>{strategy.title}</strong>
                  </header>
                  <div className="season-flow">
                    {strategy.crops.map((crop, index) => (
                      <div key={`${crop}-${index}`}>
                        <small>SEASON {index + 1}</small>
                        <strong>{crop}</strong>
                        {index < 2 && <i>→</i>}
                      </div>
                    ))}
                  </div>
                  <footer>
                    <p>{strategy.note}</p>
                    <span>{context?.calendar_evidence.length ?? 0} local crop calendar records available</span>
                  </footer>
                </article>
              ))}
            </div>

            <div className="evidence-gate">
              <div className="gate-icon">!</div>
              <div>
                <strong>Evidence gate</strong>
                <p>
                  These are exploration paths, not agronomic rankings. A winning decision engine should refuse to invent crop suitability when reviewed local crop requirements, soil constraints or sequence rules are missing.
                </p>
              </div>
              <button onClick={() => runDecisionEngine()} disabled={planBusy}>Generate evidence based field plan</button>
            </div>
          </section>
        </main>
      )}

      {view === "plan" && (
        <main className="plan-workspace">
          {!plan ? (
            <div className="empty-plan">
              <span>03 | FIELD PLAN</span>
              <h1>Turn Earth evidence into actions a farmer can use.</h1>
              <p>
                The printed card is designed to stand alone. It does not depend on clickable links. Source names remain traceable for advisers and judges.
              </p>
              <button onClick={() => setView("rotation")}>Complete farmer context →</button>
            </div>
          ) : (
            <DecisionReport brief={plan} placeName={placeLabel(place, point)} />
          )}
        </main>
      )}
    </div>
  );
}
