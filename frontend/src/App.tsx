import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import EarthScene from "./EarthScene";
import LocationMap from "./LocationMap";
import DecisionReport from "./DecisionReport";
import FieldIcon, { type IconName } from "./FieldIcon";
import {
  ApiError,
  apiGet,
  apiPost,
  type Area,
  type FarmerProfile,
  type LocationContext,
  type PlaceResult,
  type PlanBrief,
  type PowerBaseline,
  type RecentEnvironment,
  type Status,
} from "./api";

type Point = { latitude: number; longitude: number };

const HERO_IMAGE =
  "https://assets.science.nasa.gov/dynamicimage/assets/science/esd/eo/images/imagerecords/148000/148203/baniachong_oli_202176.jpg";

const STORY_IMAGE =
  "https://assets.science.nasa.gov/dynamicimage/assets/science/esd/eo/images/imagerecords/148000/148203/baniachong10_oli_202176.jpg";

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
  const value = new Date(Date.now() - days * 86400000);
  return value.toISOString().slice(0, 10);
}

function formatMetric(value: number | null | undefined, suffix: string) {
  if (value === null || value === undefined) return "Not available";
  return `${new Intl.NumberFormat("en-BD", { maximumFractionDigits: 1 }).format(value)}${suffix}`;
}

function locationName(place: PlaceResult | null, context: LocationContext | null) {
  if (place?.name) return place.name;
  if (context) return context.nearest_supported_region.name_en;
  return "Selected field";
}

function statusCopy(status: Status) {
  if (status === "loading") return "Loading";
  if (status === "ready") return "Connected";
  if (status === "unavailable") return "Unavailable";
  return "Waiting";
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
  const [areas, setAreas] = useState<Area[]>([]);
  const [search, setSearch] = useState("");
  const [placeResults, setPlaceResults] = useState<PlaceResult[]>([]);
  const [placeSearchStatus, setPlaceSearchStatus] = useState<Status>("idle");
  const [selectedPlace, setSelectedPlace] = useState<PlaceResult | null>(null);
  const [point, setPoint] = useState<Point | null>(null);
  const [context, setContext] = useState<LocationContext | null>(null);
  const [contextStatus, setContextStatus] = useState<Status>("idle");
  const [recent, setRecent] = useState<RecentEnvironment | null>(null);
  const [recentStatus, setRecentStatus] = useState<Status>("idle");
  const [baseline, setBaseline] = useState<PowerBaseline | null>(null);
  const [baselineStatus, setBaselineStatus] = useState<Status>("idle");
  const [locationError, setLocationError] = useState("");
  const [gpsBusy, setGpsBusy] = useState(false);
  const [plan, setPlan] = useState<PlanBrief | null>(null);
  const [planBusy, setPlanBusy] = useState(false);
  const [planError, setPlanError] = useState("");
  const [previousCrop, setPreviousCrop] = useState("");
  const [waterSource, setWaterSource] = useState<FarmerProfile["water_source"]>("unknown");
  const [waterAfterRain, setWaterAfterRain] = useState<FarmerProfile["water_after_heavy_rain"]>("unknown");
  const [soilTest, setSoilTest] = useState<FarmerProfile["soil_test"]>("unknown");
  const [soilPh, setSoilPh] = useState("");
  const [priority, setPriority] = useState<FarmerProfile["priority"]>("production_stability");
  const [startMonth, setStartMonth] = useState(() => new Date().getMonth() + 1);
  const [startYear, setStartYear] = useState(() => Math.max(2026, new Date().getFullYear()));
  const [navSolid, setNavSolid] = useState(false);
  const didAutoLocate = useRef(false);

  const mapDate = useMemo(() => dateMinus(2), []);
  const currentLocationName = locationName(selectedPlace, context);

  useEffect(() => {
    apiGet<{ areas: Area[] }>("/api/v1/areas")
      .then((payload) => setAreas(payload.areas))
      .catch(() => setAreas([]));
  }, []);

  useEffect(() => {
    const onScroll = () => setNavSolid(window.scrollY > 28);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    if (didAutoLocate.current || !navigator.permissions || !navigator.geolocation) return;
    didAutoLocate.current = true;
    navigator.permissions
      .query({ name: "geolocation" })
      .then((permission) => {
        if (permission.state !== "granted") return;
        navigator.geolocation.getCurrentPosition(
          (position) => {
            setPoint({
              latitude: Number(position.coords.latitude.toFixed(5)),
              longitude: Number(position.coords.longitude.toFixed(5)),
            });
          },
          () => undefined,
          { enableHighAccuracy: false, timeout: 7000, maximumAge: 300000 },
        );
      })
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    const query = search.trim();
    if (query.length < 2) {
      setPlaceResults([]);
      setPlaceSearchStatus("idle");
      return;
    }

    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setPlaceSearchStatus("loading");
      apiGet<{ results: PlaceResult[] }>(
        `/api/v1/places/search?q=${encodeURIComponent(query)}`,
        controller.signal,
      )
        .then((payload) => {
          setPlaceResults(payload.results);
          setPlaceSearchStatus("ready");
        })
        .catch(() => {
          if (!controller.signal.aborted) {
            setPlaceResults([]);
            setPlaceSearchStatus("unavailable");
          }
        });
    }, 300);

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

    apiGet<LocationContext>(
      `/api/v1/context?lat=${point.latitude}&lon=${point.longitude}`,
      controller.signal,
    )
      .then((payload) => {
        setContext(payload);
        setContextStatus("ready");
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setContextStatus("unavailable");
        setLocationError(error instanceof ApiError ? error.message : "Location context could not be loaded.");
      });

    apiGet<RecentEnvironment>(
      `/api/v1/environment/recent?lat=${point.latitude}&lon=${point.longitude}`,
      controller.signal,
    )
      .then((payload) => {
        setRecent(payload);
        setRecentStatus(payload.status === "available" ? "ready" : "unavailable");
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setRecent(null);
          setRecentStatus("unavailable");
        }
      });

    apiGet<{ place: PlaceResult | null }>(
      `/api/v1/places/reverse?lat=${point.latitude}&lon=${point.longitude}`,
      controller.signal,
    )
      .then((payload) => {
        if (payload.place) setSelectedPlace(payload.place);
      })
      .catch(() => undefined);

    return () => controller.abort();
  }, [point]);

  useEffect(() => {
    if (!point) return;

    const controller = new AbortController();
    setBaselineStatus("loading");

    apiGet<PowerBaseline>(
      `/api/v1/environment/baseline?lat=${point.latitude}&lon=${point.longitude}&month=${startMonth}`,
      controller.signal,
    )
      .then((payload) => {
        setBaseline(payload);
        setBaselineStatus(payload.status === "available" ? "ready" : "unavailable");
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setBaseline(null);
          setBaselineStatus("unavailable");
        }
      });

    return () => controller.abort();
  }, [point, startMonth]);

  const filteredAreas = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return areas;
    return areas.filter(
      (area) =>
        area.name_en.toLowerCase().includes(query) ||
        area.evidence_region.toLowerCase().includes(query),
    );
  }, [areas, search]);

  const recentRain = recent?.status === "available" ? recent.summary?.precipitation_total_mm : null;
  const recentTemp = recent?.status === "available" ? recent.summary?.temperature_mean_c : null;
  const baselineRain = baseline?.status === "available" ? baseline.summary?.precipitation_mean_daily_mm : null;
  const baselineTemp = baseline?.status === "available" ? baseline.summary?.temperature_mean_c : null;

  function scrollToLocation() {
    document.getElementById("field-locator")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function setFieldPoint(nextPoint: Point, place: PlaceResult | null = null) {
    if (!validPoint(nextPoint)) {
      setLocationError("That location could not be read. Please choose another point on the map.");
      return;
    }
    setLocationError("");
    setSelectedPlace(place);
    setPoint({
      latitude: Number(nextPoint.latitude.toFixed(5)),
      longitude: Number(nextPoint.longitude.toFixed(5)),
    });
  }

  function chooseArea(area: Area) {
    setFieldPoint({ latitude: area.latitude, longitude: area.longitude });
    setSearch("");
    setPlaceResults([]);
  }

  function choosePlace(place: PlaceResult) {
    setFieldPoint({ latitude: place.latitude, longitude: place.longitude }, place);
    setSearch("");
    setPlaceResults([]);
  }

  function useMyLocation() {
    setLocationError("");

    if (!navigator.geolocation) {
      setLocationError("This browser does not provide location access. Search for a place or choose a point on the map.");
      return;
    }

    setGpsBusy(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setGpsBusy(false);
        setFieldPoint({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });
        window.setTimeout(scrollToLocation, 100);
      },
      () => {
        setGpsBusy(false);
        setLocationError("Location permission was not granted. Search for a place or choose a point on the map instead.");
      },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 },
    );
  }

  async function generatePlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!point) {
      setPlanError("Choose your field location first. You can use location access, search for a place, or choose a point on the map.");
      scrollToLocation();
      return;
    }

    const profile: FarmerProfile = {
      latitude: point.latitude,
      longitude: point.longitude,
      previous_crop: previousCrop || null,
      water_source: waterSource,
      water_after_heavy_rain: waterAfterRain,
      soil_test: soilTest,
      soil_ph: soilTest === "yes" && soilPh.trim() ? Number(soilPh) : null,
      priority,
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
      });

      if (!payload || !Array.isArray(payload.months) || payload.months.length !== 3) {
        throw new ApiError(500, "INVALID_PLAN_RESPONSE", "The field brief response was incomplete. Please try again.");
      }

      const completeBrief: PlanBrief = {
        ...payload,
        recent_environment: recent,
        historical_baseline: baseline,
      };

      setPlan(completeBrief);
      window.requestAnimationFrame(() => {
        window.requestAnimationFrame(() => {
          document.getElementById("field-brief")?.scrollIntoView({ behavior: "smooth", block: "start" });
        });
      });
    } catch (error) {
      setPlanError(error instanceof ApiError ? error.message : "The field brief could not be generated.");
    } finally {
      setPlanBusy(false);
    }
  }

  return (
    <div className="bx-app">
      <header className={navSolid ? "bx-nav solid" : "bx-nav"}>
        <a className="bx-brand" href="#top" aria-label="BoponX home">
          <span className="bx-brand-mark"><i /><i /><i /></span>
          <span className="bx-brand-type">
            <strong>BoponX</strong>
            <small>From Space to Soil</small>
          </span>
        </a>

        <nav className="bx-links" aria-label="Primary">
          <a href="#field-locator">Field</a>
          <a href="#earth-signals">NASA evidence</a>
          <a href="#farm-story">Farm story</a>
          <a href="#field-brief">Plan</a>
        </nav>

        <button type="button" className="locate-mini" onClick={useMyLocation}>
          <span>⌖</span>
          Locate my field
        </button>
      </header>

      <main id="top">
        <section className="cinematic-hero">
          <div className="hero-photo" aria-hidden="true">
            <img src={HERO_IMAGE} alt="" />
            <div className="hero-photo-overlay" />
          </div>

          <EarthScene className="hero-earth" />
          <div className="hero-grid" aria-hidden="true" />
          <div className="hero-scan" aria-hidden="true" />

          <div className="hero-content">
            <div className="hero-kicker">
              <span className="live-dot" />
              <span>NASA Space Apps 2026 | Field Shift</span>
            </div>

            <h1>
              <span>Your field.</span>
              <span className="hero-accent">Earth evidence.</span>
              <span>A clearer next move.</span>
            </h1>

            <p className="hero-lead">
              BoponX starts with the farmer's real location. It loads only the NASA and local evidence that matters for that place, then turns it into a practical seasonal decision workflow.
            </p>

            <div className="hero-actions">
              <button type="button" className="hero-primary" onClick={useMyLocation}>
                <span className="hero-primary-icon">⌖</span>
                <span>
                  <strong>{gpsBusy ? "Finding your field…" : "Use my location"}</strong>
                  <small>Location permission is requested only when needed</small>
                </span>
                <b>→</b>
              </button>

              <button type="button" className="hero-secondary" onClick={scrollToLocation}>
                Search or choose on map
              </button>
            </div>

            <div className="hero-source-line">
              <span>GPM IMERG</span><i />
              <span>SMAP</span><i />
              <span>NASA POWER</span><i />
              <span>BAMIS</span><i />
              <span>BARC</span>
            </div>
          </div>

          <div className="hero-data-stack" aria-hidden="true">
            <div className="floating-data-card data-card-a">
              <span>PRECIPITATION</span>
              <strong>IMERG</strong>
              <small>V07B | near real time</small>
            </div>
            <div className="floating-data-card data-card-b">
              <span>SOIL MOISTURE</span>
              <strong>SMAP</strong>
              <small>9 km | regional context</small>
            </div>
            <div className="floating-data-card data-card-c">
              <span>CLIMATE</span>
              <strong>POWER</strong>
              <small>recent data | baseline</small>
            </div>
          </div>

          <div className="hero-credit">NASA and USGS Landsat image | Baniachong, Bangladesh</div>
        </section>

        <section className="source-marquee" aria-label="Data sources">
          <div className="source-track">
            {["NASA GPM IMERG Early V07B", "NASA GIBS", "SMAP SPL3SMP E V6", "NASA POWER", "BAMIS", "BARC", "Farmer observations"].map((item) => (
              <span key={item}><i />{item}</span>
            ))}
          </div>
        </section>

        <section className="field-locator bx-section" id="field-locator">
          <div className="section-heading" data-reveal>
            <div className="section-index">01</div>
            <div>
              <p className="section-kicker">Start from one real place</p>
              <h2>Show us where the field is.</h2>
            </div>
            <p className="section-copy">
              The selected point controls the map, NASA queries, climate baseline and local agricultural evidence. A farmer sees information for the chosen area, not a national data dump.
            </p>
          </div>

          <div className="location-command" data-reveal>
            <div className="location-search-panel">
              <div className="location-mode-title">
                <span className="mini-index">A</span>
                <div>
                  <strong>Detect, search, or choose on the map</strong>
                  <small>The farmer chooses the field. NASA supplies the environmental context.</small>
                </div>
              </div>

              <button type="button" className="detect-button" onClick={useMyLocation} disabled={gpsBusy}>
                <span className="detect-radar"><i /><i /></span>
                <span>
                  <strong>{gpsBusy ? "Finding your location…" : "Detect my current location"}</strong>
                  <small>Uses browser location access after permission</small>
                </span>
                <b>⌖</b>
              </button>

              <label className="place-search-box">
                <span className="search-symbol">⌕</span>
                <input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Search village, upazila, district, or city"
                  aria-label="Search a Bangladesh place"
                />
                {search && <button type="button" onClick={() => setSearch("")}>×</button>}
              </label>

              {search && (
                <div className="place-suggestions">
                  {placeSearchStatus === "loading" && (
                    <div className="searching-row"><span className="spinner" />Searching Bangladesh…</div>
                  )}

                  {placeResults.slice(0, 6).map((place, index) => (
                    <button
                      type="button"
                      key={`${place.latitude}-${place.longitude}-${index}`}
                      onClick={() => choosePlace(place)}
                    >
                      <span className="suggestion-pin">⌖</span>
                      <span>
                        <strong>{place.name ?? place.address.village ?? place.address.town ?? "Selected place"}</strong>
                        <small>
                          {[place.address.village, place.address.upazila, place.address.district, place.address.division]
                            .filter(Boolean)
                            .join(" | ")}
                        </small>
                      </span>
                    </button>
                  ))}

                  {placeResults.length === 0 && placeSearchStatus !== "loading" && filteredAreas.slice(0, 6).map((area) => (
                    <button type="button" key={area.id} onClick={() => chooseArea(area)}>
                      <span className="suggestion-pin">◎</span>
                      <span>
                        <strong>{area.name_en}</strong>
                        <small>Regional evidence hub</small>
                      </span>
                    </button>
                  ))}
                </div>
              )}

              <div className="privacy-note">
                <span>◌</span>
                <p>
                  <strong>Your field location stays temporary.</strong>
                  {" "}BoponX does not save exact coordinates by default.
                </p>
              </div>

              {locationError && <div className="error-banner">{locationError}</div>}
            </div>

            <div className="location-map-panel">
              <LocationMap
                point={point}
                onPick={(value) => setFieldPoint(value)}
                mapDate={mapDate}
              />

              <div className={point ? "field-lock active" : "field-lock"}>
                <div className="field-lock-head">
                  <span className="field-lock-status"><i />{point ? "FIELD SELECTED" : "WAITING FOR FIELD"}</span>
                  <span>{contextStatus !== "idle" && statusCopy(contextStatus)}</span>
                </div>

                <strong>{point ? currentLocationName : "Choose a field point"}</strong>

                {point && (
                  <>
                    <p>{point.latitude.toFixed(5)}° N | {point.longitude.toFixed(5)}° E</p>
                    {selectedPlace && (
                      <small>
                        {[selectedPlace.address.village, selectedPlace.address.upazila, selectedPlace.address.district, selectedPlace.address.division]
                          .filter(Boolean)
                          .join(" | ")}
                      </small>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        </section>

        <section className="earth-signals bx-section dark-section" id="earth-signals">
          <div className="signal-orbit" aria-hidden="true"><i /><i /><i /></div>

          <div className="section-heading light" data-reveal>
            <div className="section-index">02</div>
            <div>
              <p className="section-kicker">Earth intelligence filtered by place</p>
              <h2>{point ? currentLocationName : "Choose a field to load the evidence."}</h2>
            </div>
            <p className="section-copy">
              Each source has one job. Recent rainfall, regional soil moisture, recent climate and historical baseline stay separate so the farmer can see what each signal really means.
            </p>
          </div>

          <div className="signal-stage" data-reveal>
            <article className="signal-card signal-rain">
              <div className="signal-card-top">
                <span className="source-badge live"><i />Near real time</span>
                <span className="signal-number">01</span>
              </div>
              <div className="signal-visual rain-visual">
                <span className="rain-column r1" /><span className="rain-column r2" /><span className="rain-column r3" /><span className="rain-column r4" />
                <div className="rain-radar"><i /><i /><i /></div>
              </div>
              <h3>GPM IMERG Early</h3>
              <p>Recent precipitation evidence around the selected field.</p>
              <dl>
                <div><dt>Map date</dt><dd>{mapDate}</dd></div>
                <div><dt>Resolution</dt><dd>0.1° | about 10 km</dd></div>
                <div><dt>Minimum latency</dt><dd>about 4 hours</dd></div>
              </dl>
            </article>

            <article className="signal-card signal-power">
              <div className="signal-card-top">
                <span className={`source-badge ${recentStatus}`}><i />{statusCopy(recentStatus)}</span>
                <span className="signal-number">02</span>
              </div>
              <div className="signal-metric">
                <strong>{formatMetric(recentTemp, "°C")}</strong>
                <span>Recent period mean</span>
              </div>
              <div className="signal-metric secondary">
                <strong>{formatMetric(recentRain, " mm")}</strong>
                <span>Complete period rainfall</span>
              </div>
              <h3>NASA POWER</h3>
              <p>
                {recent?.period
                  ? `${recent.period.start} to ${recent.period.end} | ${recent.period.time_standard}`
                  : "Select a field to request recent regional climate context."}
              </p>
            </article>

            <article className="signal-card signal-baseline">
              <div className="signal-card-top">
                <span className={`source-badge ${baselineStatus}`}><i />{statusCopy(baselineStatus)}</span>
                <span className="signal-number">03</span>
              </div>
              <div className="baseline-rings" aria-hidden="true"><i /><i /><i /></div>
              <div className="signal-metric">
                <strong>{formatMetric(baselineTemp, "°C")}</strong>
                <span>Planning month climate mean</span>
              </div>
              <div className="signal-metric secondary">
                <strong>{formatMetric(baselineRain, " mm per day")}</strong>
                <span>Climatological daily rain</span>
              </div>
              <h3>POWER 2001 to 2020</h3>
              <p>Historical reference for the selected planning month. This is context, not a forecast.</p>
            </article>

            <article className="signal-card signal-soil">
              <div className="signal-card-top">
                <span className="source-badge review"><i />Quality review</span>
                <span className="signal-number">04</span>
              </div>
              <div className="soil-cube" aria-hidden="true">
                <span className="soil-face top" /><span className="soil-face left" /><span className="soil-face right" />
                <i className="soil-wave w1" /><i className="soil-wave w2" /><i className="soil-wave w3" />
              </div>
              <h3>SMAP SPL3SMP E V6</h3>
              <p>Regional surface soil moisture context. Numeric use stays behind quality checks until the authenticated adapter is complete.</p>
              <dl>
                <div><dt>Resolution</dt><dd>9 km | daily</dd></div>
                <div><dt>Never treated as</dt><dd>soil pH</dd></div>
              </dl>
            </article>
          </div>

          <div className="data-quality-banner" data-reveal>
            <span className="quality-icon">!</span>
            <div>
              <strong>2026 SMAP quality note</strong>
              <p>NSIDC reported a geolocation issue affecting Standard and NRT products from 14 May to 28 July 2026. BoponX keeps those dates behind a quality check.</p>
            </div>
          </div>
        </section>

        <section className="nasa-story bx-section">
          <div className="nasa-story-media" data-reveal>
            <img
              src={STORY_IMAGE}
              alt="NASA Landsat view of Baniachong, Bangladesh, surrounded by agricultural fields"
            />
            <div className="image-coordinate">24.50° N | 91.35° E</div>
            <div className="image-caption">
              <span>NASA and USGS Landsat</span>
              <strong>Baniachong, Bangladesh</strong>
            </div>
          </div>

          <div className="nasa-story-copy" data-reveal>
            <p className="section-kicker">A real Bangladesh example</p>
            <h2>Earth data should support a decision, not decorate a dashboard.</h2>
            <p>
              NASA Earth Observatory documented the use of Landsat and other satellite information around Baniachong to support irrigation research. BoponX follows the same principle by connecting Earth observations to a farmer's next decision.
            </p>
            <a href="https://science.nasa.gov/earth/earth-observatory/fine-tuning-irrigation-in-asia-148203/" target="_blank" rel="noreferrer">
              Read the NASA Earth Observatory story ↗
            </a>
          </div>
        </section>

        <section className="local-evidence bx-section" id="local-evidence">
          <div className="section-heading" data-reveal>
            <div className="section-index">03</div>
            <div>
              <p className="section-kicker">NASA is one part of the answer</p>
              <h2>Bring local crop evidence into the same view.</h2>
            </div>
            <p className="section-copy">
              BoponX shows crop calendars indexed for the selected regional evidence hub. A calendar shown here means an official source exists. It does not mean the crop has already been recommended.
            </p>
          </div>

          <div className="local-evidence-grid" data-reveal>
            <div className="region-evidence-card">
              <div className="region-card-top">
                <span>Selected evidence region</span>
                <strong>{context ? context.nearest_supported_region.evidence_region : "Choose a field"}</strong>
              </div>

              <div className="region-grid-art" aria-hidden="true">
                {Array.from({ length: 20 }).map((_, index) => <i key={index} />)}
              </div>

              <div className="coverage-lines">
                <div><span className={context?.within_bangladesh ? "coverage-ok" : ""} />NASA environmental context</div>
                <div><span className={context?.calendar_evidence?.length ? "coverage-ok" : "coverage-warn"} />Local calendar sources</div>
                <div><span className="coverage-lock" />Rotation rules still require review</div>
              </div>
            </div>

            <div className="calendar-evidence-panel">
              <div className="calendar-panel-head">
                <span>Official calendar sources</span>
                <strong>{context?.calendar_evidence?.length ?? 0}</strong>
              </div>

              <div className="crop-source-list">
                {context?.calendar_evidence?.length ? (
                  context.calendar_evidence.slice(0, 9).map((crop, index) => (
                    <a href={crop.source_url} target="_blank" rel="noreferrer" key={crop.id} className="crop-source-row">
                      <span className="crop-seq">{String(index + 1).padStart(2, "0")}</span>
                      <span>
                        <strong>{crop.name_en}</strong>
                        <small>Official BAMIS calendar source</small>
                      </span>
                      <b>↗</b>
                    </a>
                  ))
                ) : (
                  <div className="empty-evidence">
                    <span>◎</span>
                    <p>Choose a field to load crop calendar evidence for its regional hub.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>

        <section className="farm-story bx-section dark-section" id="farm-story">
          <div className="section-heading light" data-reveal>
            <div className="section-index">04</div>
            <div>
              <p className="section-kicker">Ask what a farmer can actually answer</p>
              <h2>Simple questions. No laboratory quiz.</h2>
            </div>
            <p className="section-copy">
              A farmer's experience is useful evidence. Not sure is a valid answer. BoponX does not fill missing scientific information with a guess.
            </p>
          </div>

          <form className="farmer-story-form" onSubmit={generatePlan} data-reveal>
            <fieldset>
              <legend><span>01</span>What was grown last?</legend>
              <div className="crop-choice-grid">
                {cropOptions.map(([value, label, icon]) => (
                  <button
                    type="button"
                    key={value}
                    className={previousCrop === value ? "crop-choice active" : "crop-choice"}
                    onClick={() => setPreviousCrop(previousCrop === value ? "" : value)}
                  >
                    <span className="choice-icon"><FieldIcon name={icon as IconName} /></span>
                    <strong>{label}</strong>
                  </button>
                ))}
                <button type="button" className={!previousCrop ? "crop-choice unknown active" : "crop-choice unknown"} onClick={() => setPreviousCrop("")}>
                  <span className="choice-icon"><FieldIcon name="unknown" /></span><strong>Not sure</strong>
                </button>
              </div>
            </fieldset>

            <div className="farmer-form-split">
              <fieldset>
                <legend><span>02</span>How does the field usually get water?</legend>
                <div className="answer-stack">
                  {[
                    ["rainfed", "Mostly rain", "rain"],
                    ["irrigated", "Mostly irrigation", "irrigation"],
                    ["both", "Rain and irrigation", "both"],
                    ["unknown", "Not sure", "unknown"],
                  ].map(([value, label, icon]) => (
                    <label className={waterSource === value ? "answer-card active" : "answer-card"} key={value}>
                      <input type="radio" name="water" checked={waterSource === value} onChange={() => setWaterSource(value as FarmerProfile["water_source"])} />
                      <span className="answer-icon"><FieldIcon name={icon as IconName} /></span>
                      <strong>{label}</strong>
                    </label>
                  ))}
                </div>
              </fieldset>

              <fieldset>
                <legend><span>03</span>What usually happens after heavy rain?</legend>
                <div className="answer-stack">
                  {[
                    ["drains", "Water drains quickly", "drainage"],
                    ["stays", "Water stays for a long time", "standingWater"],
                    ["sometimes", "It changes from time to time", "mixed"],
                    ["unknown", "Not sure", "unknown"],
                  ].map(([value, label, icon]) => (
                    <label className={waterAfterRain === value ? "answer-card active" : "answer-card"} key={value}>
                      <input type="radio" name="rain" checked={waterAfterRain === value} onChange={() => setWaterAfterRain(value as FarmerProfile["water_after_heavy_rain"])} />
                      <span className="answer-icon"><FieldIcon name={icon as IconName} /></span>
                      <strong>{label}</strong>
                    </label>
                  ))}
                </div>
              </fieldset>
            </div>

            <div className="farmer-form-split">
              <fieldset>
                <legend><span>04</span>Do you have a soil test report?</legend>
                <div className="soil-test-choice">
                  {[
                    ["yes", "Yes", "check"],
                    ["no", "No", "close"],
                    ["unknown", "Not sure", "unknown"],
                  ].map(([value, label, icon]) => (
                    <label className={soilTest === value ? "soil-choice active" : "soil-choice"} key={value}>
                      <input type="radio" name="soil" checked={soilTest === value} onChange={() => setSoilTest(value as FarmerProfile["soil_test"])} />
                      <span className="soil-choice-icon"><FieldIcon name={icon as IconName} /></span>
                      <span>{label}</span>
                    </label>
                  ))}
                </div>

                {soilTest === "yes" && (
                  <label className="ph-field">
                    <span>
                      <strong>pH from the report</strong>
                      <small>Optional. BoponX never guesses pH from NASA data.</small>
                    </span>
                    <input type="number" min="0" max="14" step="0.1" value={soilPh} onChange={(event) => setSoilPh(event.target.value)} placeholder="6.5" />
                  </label>
                )}
              </fieldset>

              <fieldset>
                <legend><span>05</span>What matters most right now?</legend>
                <div className="priority-stack">
                  {priorities.map(([value, label, code]) => (
                    <label className={priority === value ? "priority-choice active" : "priority-choice"} key={value}>
                      <input type="radio" name="priority" checked={priority === value} onChange={() => setPriority(value as FarmerProfile["priority"])} />
                      <span className="priority-icon"><FieldIcon name={code as IconName} /></span>
                      <strong>{label}</strong>
                    </label>
                  ))}
                </div>
              </fieldset>
            </div>

            <div className="brief-builder">
              <div>
                <span className="brief-label">Planning starts</span>
                <div className="date-pickers">
                  <select value={startMonth} onChange={(event) => setStartMonth(Number(event.target.value))} aria-label="Planning month">
                    {Array.from({ length: 12 }, (_, index) => index + 1).map((month) => <option key={month} value={month}>{String(month).padStart(2, "0")}</option>)}
                  </select>
                  <select value={startYear} onChange={(event) => setStartYear(Number(event.target.value))} aria-label="Planning year">
                    {Array.from({ length: 10 }, (_, index) => 2026 + index).map((year) => <option key={year} value={year}>{year}</option>)}
                  </select>
                </div>
              </div>

              <button type="submit" disabled={planBusy}>
                <span>
                  <small>{point ? `Field selected: ${currentLocationName}` : "Choose the field before generating the brief"}</small>
                  <strong>{planBusy ? "Building your field brief…" : "Build my 90 day field brief"}</strong>
                </span>
                <b>→</b>
              </button>
            </div>

            {!point && (
              <div className="form-location-note">
                <span>⌖</span>
                <p>You can fill in the farm questions now. Choose the field location before you generate the plan.</p>
                <button type="button" onClick={scrollToLocation}>Choose field</button>
              </div>
            )}

            {planError && <div className="error-banner">{planError}</div>}
          </form>
        </section>

        {plan && <DecisionReport brief={plan} />}

        <section className="rotation-future bx-section">
          <div className="rotation-stage" data-reveal>
            <EarthScene className="rotation-earth" accent="cyan" />
            <div className="rotation-copy">
              <p className="section-kicker">The challenge destination</p>
              <h2>Three seasons. Several strategies. Evidence beside every option.</h2>
              <p>
                The rotation explorer will compare feasible crop sequences after Bangladesh crop calendars, crop requirements, soil constraints and sequence rules are reviewed. Until then, BoponX shows the evidence pipeline without inventing a crop recommendation.
              </p>
              <div className="rotation-flow">
                <span>Field</span><i>→</i>
                <span>NASA</span><i>→</i>
                <span>Local rules</span><i>→</i>
                <span>Two or three rotations</span><i>→</i>
                <span>Farmer decides</span>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="bx-footer">
        <div className="footer-brand">
          <span className="bx-brand-mark"><i /><i /><i /></span>
          <div><strong>BoponX</strong><small>From Space to Soil</small></div>
        </div>

        <p>Independent Team EARTH.exe project. NASA does not endorse this application.</p>

        <div className="footer-links">
          <a href="https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026" target="_blank" rel="noreferrer">GitHub ↗</a>
          <a href="https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/" target="_blank" rel="noreferrer">Field Shift ↗</a>
        </div>
      </footer>
    </div>
  );
}
