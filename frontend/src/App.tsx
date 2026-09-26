import { useEffect, useMemo, useState, type FormEvent } from "react";
import LocationMap from "./LocationMap";
import DecisionReport from "./DecisionReport";
import {
  ApiError,
  apiGet,
  apiPost,
  type Area,
  type FarmerProfile,
  type Language,
  type LocationContext,
  type PlaceResult,
  type PlanBrief,
  type PowerBaseline,
  type RecentEnvironment,
  type Status,
} from "./api";

type Point = { latitude: number; longitude: number };

const cropOptions = [
  ["rice", "ধান"],
  ["wheat", "গম"],
  ["maize", "ভুট্টা"],
  ["pulse", "ডাল"],
  ["mustard", "সরিষা"],
  ["vegetables", "সবজি"],
  ["jute", "পাট"],
  ["other", "অন্য ফসল"],
] as const;

function t(language: Language, en: string, bn: string) {
  return language === "bn" ? bn : en;
}

function todayMinus(days: number) {
  const d = new Date(Date.now() - days * 86400000);
  return d.toISOString().slice(0, 10);
}

function statusLabel(status: Status, language: Language) {
  if (status === "loading") return t(language, "Loading", "লোড হচ্ছে");
  if (status === "ready") return t(language, "Ready", "প্রস্তুত");
  if (status === "unavailable") return t(language, "Unavailable", "পাওয়া যায়নি");
  return t(language, "Waiting", "অপেক্ষায়");
}

export default function App() {
  const [language, setLanguage] = useState<Language>("bn");
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

  const imergDate = useMemo(() => todayMinus(1), []);

  useEffect(() => {
    apiGet<{ areas: Area[] }>("/api/v1/areas")
      .then((payload) => setAreas(payload.areas))
      .catch(() => setAreas([]));
  }, []);

  useEffect(() => {
    const query = search.trim();
    if (query.length < 2) {
      setPlaceResults([]);
      setPlaceSearchStatus("idle");
      return;
    }
    const controller = new AbortController();
    setPlaceSearchStatus("loading");
    const timer = window.setTimeout(() => {
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
    }, 320);
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
      setSelectedPlace(null);
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
        if (!controller.signal.aborted) setRecentStatus("unavailable");
      });

    return () => controller.abort();
  }, [point]);

  useEffect(() => {
    if (!point) return;
    const controller = new AbortController();
    setBaselineStatus("loading");

    apiGet<{ place: PlaceResult | null }>(
      `/api/v1/places/reverse?lat=${point.latitude}&lon=${point.longitude}`,
      controller.signal,
    )
      .then((payload) => {
        if (payload.place) setSelectedPlace(payload.place);
      })
      .catch(() => {
        // Reverse geocoding is optional; the map/context flow still works.
      });

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
        area.name_bn.includes(search.trim()) ||
        area.evidence_region.toLowerCase().includes(query),
    );
  }, [areas, search]);

  function chooseArea(area: Area) {
    setSelectedPlace(null);
    setPoint({ latitude: area.latitude, longitude: area.longitude });
    setSearch("");
    setPlaceResults([]);
    window.setTimeout(() => {
      document.getElementById("location-workspace")?.scrollIntoView({
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
        block: "start",
      });
    }, 50);
  }

  function choosePlace(place: PlaceResult) {
    setSelectedPlace(place);
    setPoint({ latitude: place.latitude, longitude: place.longitude });
    setSearch("");
    setPlaceResults([]);
  }

  function useMyLocation() {
    setLocationError("");
    if (!navigator.geolocation) {
      setLocationError(t(language, "This browser does not provide location access.", "এই ব্রাউজারে অবস্থান ব্যবহারের সুবিধা নেই।"));
      return;
    }
    setGpsBusy(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setGpsBusy(false);
        setSelectedPlace(null);
        setPoint({
          latitude: Number(position.coords.latitude.toFixed(5)),
          longitude: Number(position.coords.longitude.toFixed(5)),
        });
      },
      () => {
        setGpsBusy(false);
        setLocationError(
          t(
            language,
            "Location permission was not granted. Search an area or tap the map instead.",
            "অবস্থানের অনুমতি পাওয়া যায়নি। এলাকা খুঁজুন বা মানচিত্রে ট্যাপ করুন।",
          ),
        );
      },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 },
    );
  }

  async function generatePlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!point || !context?.within_bangladesh) {
      setPlanError(t(language, "Choose a Bangladesh field location first.", "প্রথমে বাংলাদেশের একটি জমির অবস্থান বেছে নিন।"));
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
        include_recent_power: true,
      });
      setPlan(payload);
      window.setTimeout(() => {
        document.getElementById("farmer-report")?.scrollIntoView({
          behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
          block: "start",
        });
      }, 80);
    } catch (error) {
      setPlanError(error instanceof ApiError ? error.message : "The plan could not be generated.");
    } finally {
      setPlanBusy(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="site-header">
        <a href="#top" className="brand-lockup" aria-label="BoponX home">
          <span className="brand-seed" aria-hidden="true">◒</span>
          <span>
            <b>BoponX</b>
            <small>বপনএক্স</small>
          </span>
        </a>
        <nav className="header-nav" aria-label="Primary navigation">
          <a href="#location-workspace">{t(language, "My field", "আমার জমি")}</a>
          <a href="#how-it-works">{t(language, "How it works", "কীভাবে কাজ করে")}</a>
          <a href="#evidence">{t(language, "Evidence", "প্রমাণ")}</a>
        </nav>
        <button
          className="language-switch"
          type="button"
          onClick={() => setLanguage((value) => (value === "bn" ? "en" : "bn"))}
        >
          {language === "bn" ? "English" : "বাংলা"}
        </button>
      </header>

      <main id="top">
        <section className="hero-new">
          <div className="hero-field-lines" aria-hidden="true" />
          <div className="hero-copy-new">
            <p className="eyebrow-new">
              {t(language, "Field decisions from Earth evidence", "পৃথিবীর তথ্য থেকে জমির সিদ্ধান্ত")}
            </p>
            <h1>
              {t(
                language,
                "Start with the field. Bring in the right data.",
                "শুরু হোক আপনার জমি থেকে। তথ্য আসুক শুধু প্রয়োজনমতো।",
              )}
            </h1>
            <p className="hero-intro">
              {t(
                language,
                "BoponX connects a farmer's own observations with location-specific NASA environmental context and reviewed local agricultural evidence. It is designed to compare seasonal choices—not to bury a farmer in charts.",
                "BoponX কৃষকের নিজের অভিজ্ঞতাকে অবস্থানভিত্তিক NASA পরিবেশগত তথ্য এবং যাচাইকৃত স্থানীয় কৃষি প্রমাণের সঙ্গে যুক্ত করে। লক্ষ্য হলো মৌসুমি সিদ্ধান্ত তুলনা করা—কৃষককে চার্টের ভিড়ে হারিয়ে দেওয়া নয়।",
              )}
            </p>
            <div className="hero-cta-row">
              <a className="primary-cta" href="#location-workspace">
                {t(language, "Choose my field", "আমার জমি বেছে নিন")}
                <span aria-hidden="true">→</span>
              </a>
              <span className="hero-note">
                {t(language, "No account. No location saved by default.", "কোনো অ্যাকাউন্ট নয়। ডিফল্টভাবে অবস্থান সংরক্ষণও নয়।")}
              </span>
            </div>
          </div>

          <div className="hero-system" aria-label={t(language, "BoponX decision flow", "BoponX সিদ্ধান্ত প্রবাহ")}>
            <div className="system-node farmer">
              <span>01</span>
              <strong>{t(language, "Your field", "আপনার জমি")}</strong>
              <small>{t(language, "Location + what you know", "অবস্থান + আপনি যা জানেন")}</small>
            </div>
            <i aria-hidden="true" />
            <div className="system-node earth">
              <span>02</span>
              <strong>{t(language, "Earth context", "পৃথিবীর প্রেক্ষাপট")}</strong>
              <small>NASA IMERG · SMAP · POWER</small>
            </div>
            <i aria-hidden="true" />
            <div className="system-node decision">
              <span>03</span>
              <strong>{t(language, "Season decision", "মৌসুমি সিদ্ধান্ত")}</strong>
              <small>{t(language, "Compare, explain, print", "তুলনা, ব্যাখ্যা, প্রিন্ট")}</small>
            </div>
          </div>
        </section>

        <section className="location-section" id="location-workspace">
          <div className="section-intro">
            <p className="section-number">01</p>
            <div>
              <span className="kicker">{t(language, "Location first", "প্রথমে অবস্থান")}</span>
              <h2>{t(language, "Where is your field?", "আপনার জমি কোথায়?")}</h2>
            </div>
            <p>
              {t(
                language,
                "Choose a place once. BoponX then limits the environmental and agricultural evidence to that area.",
                "একবার জায়গা বেছে নিন। এরপর BoponX শুধু সেই এলাকার প্রাসঙ্গিক পরিবেশ ও কৃষি তথ্য দেখাবে।",
              )}
            </p>
          </div>

          <div className="location-actions">
            <button className="gps-button" type="button" onClick={useMyLocation} disabled={gpsBusy}>
              <span className="gps-icon" aria-hidden="true">⌖</span>
              <span>
                <strong>{gpsBusy ? t(language, "Finding location…", "অবস্থান খোঁজা হচ্ছে…") : t(language, "Use my location", "আমার অবস্থান ব্যবহার করুন")}</strong>
                <small>{t(language, "Permission is requested only when you tap.", "শুধু ট্যাপ করলে অনুমতি চাওয়া হবে।")}</small>
              </span>
            </button>

            <label className="area-search">
              <span>{t(language, "Search place", "জায়গা খুঁজুন")}</span>
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder={t(language, "Village, upazila, district…", "গ্রাম, উপজেলা, জেলা…")}
              />
            </label>
          </div>

          {search && (
            <div className="area-results place-results">
              {placeResults.slice(0, 6).map((place, index) => (
                <button
                  key={`${place.latitude}-${place.longitude}-${index}`}
                  type="button"
                  onClick={() => choosePlace(place)}
                >
                  <strong>{place.name ?? place.address.village ?? place.address.town ?? t(language, "Selected place", "নির্বাচিত জায়গা")}</strong>
                  <small>
                    {[place.address.upazila, place.address.district, place.address.division]
                      .filter(Boolean)
                      .join(" · ")}
                  </small>
                </button>
              ))}
              {placeResults.length === 0 && filteredAreas.slice(0, 6).map((area) => (
                <button key={area.id} type="button" onClick={() => chooseArea(area)}>
                  <strong>{language === "bn" ? area.name_bn : area.name_en}</strong>
                  <small>{language === "bn" ? area.name_en : area.name_bn}</small>
                </button>
              ))}
              {placeSearchStatus === "loading" && (
                <p>{t(language, "Searching Bangladesh places…", "বাংলাদেশের জায়গা খোঁজা হচ্ছে…")}</p>
              )}
              {placeSearchStatus !== "loading" && placeResults.length === 0 && filteredAreas.length === 0 && (
                <p>{t(language, "No match found. Tap the map to choose the field directly.", "মিল পাওয়া যায়নি। সরাসরি জমি বেছে নিতে মানচিত্রে ট্যাপ করুন।")}</p>
              )}
            </div>
          )}

          <div className="map-and-context">
            <LocationMap point={point} onPick={setPoint} language={language} imergDate={imergDate} />

            <aside className="context-panel">
              {!point && (
                <div className="context-empty">
                  <span className="context-compass" aria-hidden="true">◎</span>
                  <h3>{t(language, "Choose one place", "একটি জায়গা বেছে নিন")}</h3>
                  <p>{t(language, "GPS, search, or a tap on the map all lead to the same location-aware workflow.", "GPS, সার্চ বা মানচিত্রে ট্যাপ—সব পথেই একই অবস্থানভিত্তিক প্রক্রিয়া শুরু হবে।")}</p>
                </div>
              )}

              {point && (
                <>
                  <div className="context-head">
                    <div>
                      <span className="kicker">{t(language, "Selected field area", "নির্বাচিত জমির এলাকা")}</span>
                      <h3>
                        {selectedPlace?.name ??
                          (context
                            ? language === "bn"
                              ? context.nearest_supported_region.name_bn
                              : context.nearest_supported_region.name_en
                            : t(language, "Resolving area…", "এলাকা শনাক্ত হচ্ছে…"))}
                      </h3>
                    </div>
                    <span className={`context-status ${contextStatus}`}>{statusLabel(contextStatus, language)}</span>
                  </div>

                  {selectedPlace && (
                    <div className="place-detail-line">
                      <span>{selectedPlace.address.village ?? selectedPlace.address.town ?? ""}</span>
                      <span>{selectedPlace.address.upazila ?? ""}</span>
                      <span>{selectedPlace.address.district ?? ""}</span>
                    </div>
                  )}

                  <div className="coordinate-line">
                    <span>{point.latitude.toFixed(4)}°</span>
                    <span>{point.longitude.toFixed(4)}°</span>
                    <small>{t(language, "used for this request", "এই অনুরোধের জন্য ব্যবহৃত")}</small>
                  </div>

                  {context && (
                    <div className="coverage-stack">
                      <div>
                        <span className="coverage-icon ready" />
                        <p>
                          <strong>{t(language, "NASA environmental context", "NASA পরিবেশগত তথ্য")}</strong>
                          <small>{t(language, "Available for this Bangladesh location", "এই বাংলাদেশের অবস্থানের জন্য পাওয়া যায়")}</small>
                        </p>
                      </div>
                      <div>
                        <span className="coverage-icon review" />
                        <p>
                          <strong>{t(language, "Local agricultural evidence", "স্থানীয় কৃষি প্রমাণ")}</strong>
                          <small>{t(language, "Regional sources identified; rules still under review", "আঞ্চলিক উৎস শনাক্ত; নিয়ম এখনও পর্যালোচনায়")}</small>
                        </p>
                      </div>
                      <div>
                        <span className="coverage-icon locked" />
                        <p>
                          <strong>{t(language, "Crop-rotation decision", "ফসল আবর্তন সিদ্ধান্ত")}</strong>
                          <small>{t(language, "Locked until evidence rules are approved", "প্রমাণভিত্তিক নিয়ম অনুমোদন না হওয়া পর্যন্ত বন্ধ")}</small>
                        </p>
                      </div>
                    </div>
                  )}

                  {locationError && <p className="inline-error">{locationError}</p>}
                </>
              )}
            </aside>
          </div>
        </section>

        {point && context && (
          <section className="signal-section" id="evidence">
            <div className="section-intro compact">
              <p className="section-number">02</p>
              <div>
                <span className="kicker">{t(language, "Only what matters here", "শুধু এই এলাকার প্রয়োজনীয় তথ্য")}</span>
                <h2>{t(language, "Earth signals for this location", "এই অবস্থানের Earth signals")}</h2>
              </div>
              <p>
                {t(
                  language,
                  "Each source has a different job. BoponX keeps recent rainfall, soil-moisture context, and climate history separate.",
                  "প্রতিটি উৎসের কাজ আলাদা। BoponX সাম্প্রতিক বৃষ্টি, মাটির আর্দ্রতার প্রেক্ষাপট এবং জলবায়ু ইতিহাস আলাদা রাখে।",
                )}
              </p>
            </div>

            <div className="signal-grid">
              <article>
                <span className="signal-type nrt">{t(language, "Near-real-time", "নিকট-বাস্তব সময়")}</span>
                <h3>GPM IMERG Early</h3>
                <p>{t(language, "Recent rainfall layer for the selected map area.", "নির্বাচিত মানচিত্র এলাকার সাম্প্রতিক বৃষ্টির স্তর।")}</p>
                <dl>
                  <div><dt>{t(language, "Map date", "মানচিত্রের তারিখ")}</dt><dd>{imergDate}</dd></div>
                  <div><dt>{t(language, "Resolution", "রেজোলিউশন")}</dt><dd>0.1° · ~10 km</dd></div>
                  <div><dt>{t(language, "Latency", "লেটেন্সি")}</dt><dd>{t(language, "minimum ~4 h", "সর্বনিম্ন ~৪ ঘণ্টা")}</dd></div>
                </dl>
              </article>

              <article>
                <span className="signal-type eo">{t(language, "Earth observation", "Earth observation")}</span>
                <h3>SMAP</h3>
                <p>{t(language, "Regional surface-soil-moisture context. Never treated as soil pH.", "আঞ্চলিক উপরিভাগের মাটির আর্দ্রতার প্রেক্ষাপট। কখনোই soil pH হিসেবে ধরা হয় না।")}</p>
                <dl>
                  <div><dt>{t(language, "Product", "প্রোডাক্ট")}</dt><dd>SPL3SMP_E V6</dd></div>
                  <div><dt>{t(language, "Resolution", "রেজোলিউশন")}</dt><dd>9 km · daily</dd></div>
                  <div><dt>{t(language, "App status", "অ্যাপ স্ট্যাটাস")}</dt><dd>{t(language, "adapter pending", "অ্যাডাপ্টার বাকি")}</dd></div>
                </dl>
              </article>

              <article>
                <span className="signal-type history">{t(language, "Climate context", "জলবায়ু প্রেক্ষাপট")}</span>
                <h3>NASA POWER</h3>
                <p>{t(language, "Selected-location gridded temperature and rainfall context.", "নির্বাচিত অবস্থানের গ্রিডভিত্তিক তাপমাত্রা ও বৃষ্টির প্রেক্ষাপট।")}</p>
                {recentStatus === "loading" && <p className="loading-copy">{t(language, "Checking latest available point context…", "সর্বশেষ পাওয়া পয়েন্ট তথ্য দেখা হচ্ছে…")}</p>}
                {recent?.status === "available" && (
                  <div className="recent-metrics">
                    <div><strong>{recent.summary?.temperature_mean_c ?? "—"}°C</strong><span>{t(language, "period mean", "সময়ের গড়")}</span></div>
                    <div><strong>{recent.summary?.precipitation_total_mm ?? "—"} mm</strong><span>{t(language, "complete-period rain", "সম্পূর্ণ সময়ের বৃষ্টি")}</span></div>
                  </div>
                )}
                {recentStatus === "unavailable" && (
                  <p className="unavailable-note">{t(language, "Recent POWER query unavailable. No value was substituted.", "সাম্প্রতিক POWER কুয়েরি পাওয়া যায়নি। কোনো বিকল্প সংখ্যা বানানো হয়নি।")}</p>
                )}
              </article>

              <article>
                <span className="signal-type baseline">{t(language, "Historical baseline", "ঐতিহাসিক ভিত্তি")}</span>
                <h3>{t(language, "POWER climatology", "POWER ক্লাইমেটোলজি")}</h3>
                <p>{t(language, "A 2001–2020 reference for the selected planning month, used as context—not as a forecast.", "নির্বাচিত পরিকল্পনা মাসের ২০০১–২০২০ রেফারেন্স; এটি প্রেক্ষাপট, পূর্বাভাস নয়।")}</p>
                {baselineStatus === "loading" && <p className="loading-copy">{t(language, "Loading baseline…", "বেসলাইন লোড হচ্ছে…")}</p>}
                {baseline?.status === "available" && baseline.summary && (
                  <div className="recent-metrics">
                    <div><strong>{baseline.summary.temperature_mean_c ?? "—"}°C</strong><span>{t(language, "monthly climate mean", "মাসিক জলবায়ু গড়")}</span></div>
                    <div><strong>{baseline.summary.precipitation_mean_daily_mm ?? "—"} mm/day</strong><span>{t(language, "climatological daily rain", "ক্লাইমেটোলজিক্যাল দৈনিক বৃষ্টি")}</span></div>
                  </div>
                )}
                {baselineStatus === "unavailable" && (
                  <p className="unavailable-note">{t(language, "Baseline unavailable. No value was invented.", "বেসলাইন পাওয়া যায়নি। কোনো সংখ্যা বানানো হয়নি।")}</p>
                )}
              </article>
            </div>

            <div className="advisory-strip">
              <strong>{t(language, "2026 data-quality note", "২০২৬ ডেটা-গুণমান নোট")}</strong>
              <p>{t(language, "SMAP Standard/NRT products had a reported geolocation issue for 14 May–28 July 2026. Affected dates must be checked before use.", "SMAP Standard/NRT ডেটায় ১৪ মে–২৮ জুলাই ২০২৬ সময়ের জন্য geolocation সমস্যা রিপোর্ট করা হয়েছিল। ওই সময়ের ডেটা ব্যবহারের আগে অবস্থা যাচাই করতে হবে।")}</p>
            </div>

            <div className="regional-evidence">
              <div className="regional-evidence-head">
                <div>
                  <span className="kicker">{t(language, "Local crop evidence", "স্থানীয় ফসলের প্রমাণ")}</span>
                  <h3>{t(language, "Calendars published for this regional hub", "এই আঞ্চলিক হাবের জন্য প্রকাশিত ক্যালেন্ডার")}</h3>
                </div>
                <p>{t(language, "These links mean an official BAMIS crop-weather calendar exists for the regional hub. They are not crop recommendations.", "এই লিংকগুলো শুধু দেখায় যে আঞ্চলিক হাবটির জন্য অফিসিয়াল BAMIS ফসল-আবহাওয়া ক্যালেন্ডার আছে। এগুলো ফসলের সুপারিশ নয়।")}</p>
              </div>
              <div className="calendar-chip-grid">
                {context.calendar_evidence.length > 0 ? context.calendar_evidence.slice(0, 9).map((crop) => (
                  <a href={crop.source_url} target="_blank" rel="noreferrer" key={crop.id}>
                    <strong>{language === "bn" ? crop.name_bn : crop.name_en}</strong>
                    <small>{language === "bn" ? crop.name_en : crop.name_bn}</small>
                  </a>
                )) : (
                  <p>{t(language, "No indexed BAMIS calendar evidence for this regional hub yet.", "এই আঞ্চলিক হাবের জন্য এখনও ইনডেক্স করা BAMIS ক্যালেন্ডার প্রমাণ নেই।")}</p>
                )}
              </div>
            </div>
          </section>
        )}

        <section className="farmer-section" id="farmer">
          <div className="section-intro">
            <p className="section-number">03</p>
            <div>
              <span className="kicker">{t(language, "What the farmer already knows", "কৃষক যা আগে থেকেই জানেন")}</span>
              <h2>{t(language, "No laboratory quiz.", "কোনো ল্যাবরেটরি কুইজ নয়।")}</h2>
            </div>
            <p>
              {t(
                language,
                "Answer from experience. Every uncertain question has an 'I don't know' path.",
                "অভিজ্ঞতা থেকে উত্তর দিন। প্রতিটি অনিশ্চিত প্রশ্নেই ‘জানি না’ অপশন আছে।",
              )}
            </p>
          </div>

          <form className="farmer-form-new" onSubmit={generatePlan}>
            <fieldset disabled={!point || !context?.within_bangladesh}>
              <legend>{t(language, "1 · What was grown last?", "১ · আগে কী চাষ হয়েছিল?")}</legend>
              <div className="choice-grid crops">
                {cropOptions.map(([en, bn]) => (
                  <button
                    type="button"
                    key={en}
                    className={previousCrop === en ? "choice active" : "choice"}
                    onClick={() => setPreviousCrop(previousCrop === en ? "" : en)}
                  >
                    <span className="crop-glyph" aria-hidden="true">{en === "rice" ? "⌇" : en === "mustard" ? "✣" : "◌"}</span>
                    <strong>{language === "bn" ? bn : en[0].toUpperCase() + en.slice(1)}</strong>
                  </button>
                ))}
                <button type="button" className={!previousCrop ? "choice unknown active" : "choice unknown"} onClick={() => setPreviousCrop("")}>
                  <strong>{t(language, "Not sure", "নিশ্চিত নই")}</strong>
                </button>
              </div>
            </fieldset>

            <div className="form-two">
              <fieldset disabled={!point || !context?.within_bangladesh}>
                <legend>{t(language, "2 · How does the field usually get water?", "২ · জমিতে সাধারণত পানি আসে কীভাবে?")}</legend>
                <div className="choice-stack">
                  {[
                    ["rainfed", "Mostly rain", "মূলত বৃষ্টি"],
                    ["irrigated", "Mostly irrigation", "মূলত সেচ"],
                    ["both", "Rain + irrigation", "বৃষ্টি + সেচ"],
                    ["unknown", "Not sure", "নিশ্চিত নই"],
                  ].map(([value, en, bn]) => (
                    <label className={waterSource === value ? "radio-card active" : "radio-card"} key={value}>
                      <input type="radio" name="water" checked={waterSource === value} onChange={() => setWaterSource(value as FarmerProfile["water_source"])} />
                      <span>{t(language, en, bn)}</span>
                    </label>
                  ))}
                </div>
              </fieldset>

              <fieldset disabled={!point || !context?.within_bangladesh}>
                <legend>{t(language, "3 · After heavy rain, what usually happens?", "৩ · ভারী বৃষ্টির পর সাধারণত কী হয়?")}</legend>
                <div className="choice-stack">
                  {[
                    ["drains", "Water drains quickly", "পানি দ্রুত নেমে যায়"],
                    ["stays", "Water stays a long time", "পানি অনেকক্ষণ থাকে"],
                    ["sometimes", "It depends", "সময়ভেদে আলাদা"],
                    ["unknown", "Not sure", "নিশ্চিত নই"],
                  ].map(([value, en, bn]) => (
                    <label className={waterAfterRain === value ? "radio-card active" : "radio-card"} key={value}>
                      <input type="radio" name="drainage" checked={waterAfterRain === value} onChange={() => setWaterAfterRain(value as FarmerProfile["water_after_heavy_rain"])} />
                      <span>{t(language, en, bn)}</span>
                    </label>
                  ))}
                </div>
              </fieldset>
            </div>

            <fieldset disabled={!point || !context?.within_bangladesh}>
              <legend>{t(language, "4 · Do you have a soil-test report?", "৪ · আপনার কাছে কি মাটি পরীক্ষার রিপোর্ট আছে?")}</legend>
              <div className="soil-test-row">
                {[
                  ["yes", "Yes", "হ্যাঁ"],
                  ["no", "No", "না"],
                  ["unknown", "Not sure", "নিশ্চিত নই"],
                ].map(([value, en, bn]) => (
                  <label className={soilTest === value ? "radio-card compact active" : "radio-card compact"} key={value}>
                    <input type="radio" name="soiltest" checked={soilTest === value} onChange={() => setSoilTest(value as FarmerProfile["soil_test"])} />
                    <span>{t(language, en, bn)}</span>
                  </label>
                ))}
                {soilTest === "yes" && (
                  <label className="ph-optional">
                    <span>{t(language, "pH from report (optional)", "রিপোর্টের pH (ঐচ্ছিক)")}</span>
                    <input type="number" min="0" max="14" step="0.1" value={soilPh} onChange={(event) => setSoilPh(event.target.value)} placeholder="e.g. 6.5" />
                  </label>
                )}
              </div>
              <p className="field-help">{t(language, "BoponX never guesses pH from satellite data.", "BoponX স্যাটেলাইট ডেটা থেকে কখনো pH অনুমান করে না।")}</p>
            </fieldset>

            <fieldset disabled={!point || !context?.within_bangladesh}>
              <legend>{t(language, "5 · What matters most right now?", "৫ · এখন সবচেয়ে গুরুত্বপূর্ণ কী?")}</legend>
              <div className="priority-grid">
                {[
                  ["water", "Use water carefully", "পানি সাশ্রয় ও ব্যবস্থাপনা"],
                  ["soil", "Protect the soil", "মাটির যত্ন"],
                  ["production_stability", "Stable production", "স্থিতিশীল উৎপাদন"],
                ].map(([value, en, bn]) => (
                  <label className={priority === value ? "priority-card active" : "priority-card"} key={value}>
                    <input type="radio" name="priority" checked={priority === value} onChange={() => setPriority(value as FarmerProfile["priority"])} />
                    <span className="priority-mark" aria-hidden="true" />
                    <strong>{t(language, en, bn)}</strong>
                  </label>
                ))}
              </div>
            </fieldset>

            <div className="plan-window">
              <label>
                <span>{t(language, "Start month", "শুরুর মাস")}</span>
                <select value={startMonth} onChange={(event) => setStartMonth(Number(event.target.value))}>
                  {Array.from({ length: 12 }, (_, index) => index + 1).map((month) => (
                    <option value={month} key={month}>{month}</option>
                  ))}
                </select>
              </label>
              <label>
                <span>{t(language, "Year", "বছর")}</span>
                <select value={startYear} onChange={(event) => setStartYear(Number(event.target.value))}>
                  {Array.from({ length: 10 }, (_, index) => 2026 + index).map((year) => (
                    <option value={year} key={year}>{year}</option>
                  ))}
                </select>
              </label>
              <button type="submit" className="generate-button" disabled={!point || !context?.within_bangladesh || planBusy}>
                {planBusy ? t(language, "Building field brief…", "মাঠের পরিকল্পনা তৈরি হচ্ছে…") : t(language, "Build my 90-day field brief", "আমার ৯০ দিনের মাঠ পরিকল্পনা তৈরি করুন")}
                <span aria-hidden="true">→</span>
              </button>
            </div>
            {planError && <p className="inline-error">{planError}</p>}
          </form>
        </section>

        {plan && <DecisionReport brief={plan} language={language} />}

        <section className="how-section" id="how-it-works">
          <div className="section-intro compact">
            <p className="section-number">04</p>
            <div>
              <span className="kicker">{t(language, "Under the surface", "ভেতরের প্রক্রিয়া")}</span>
              <h2>{t(language, "Evidence moves in one direction.", "প্রমাণ এক দিকেই এগোয়।")}</h2>
            </div>
            <p>{t(language, "NASA data informs the context. Reviewed agricultural rules constrain the options. The farmer keeps the decision.", "NASA ডেটা প্রেক্ষাপট দেয়। যাচাইকৃত কৃষি নিয়ম বিকল্প সীমিত করে। সিদ্ধান্ত থাকে কৃষকের হাতে।")}</p>
          </div>

          <div className="pipeline">
            <div><span>1</span><strong>{t(language, "Location", "অবস্থান")}</strong><small>GPS · search · map</small></div>
            <i />
            <div><span>2</span><strong>{t(language, "Earth evidence", "Earth evidence")}</strong><small>IMERG · SMAP · POWER</small></div>
            <i />
            <div><span>3</span><strong>{t(language, "Local evidence", "স্থানীয় প্রমাণ")}</strong><small>BAMIS · BARC · reviewed rules</small></div>
            <i />
            <div><span>4</span><strong>{t(language, "Comparison", "তুলনা")}</strong><small>{t(language, "deterministic rules", "deterministic নিয়ম")}</small></div>
            <i />
            <div><span>5</span><strong>{t(language, "Farmer decision", "কৃষকের সিদ্ধান্ত")}</strong><small>{t(language, "explain · print · verify", "ব্যাখ্যা · প্রিন্ট · যাচাই")}</small></div>
          </div>
        </section>
      </main>

      <footer className="site-footer">
        <div>
          <strong>BoponX · বপনএক্স</strong>
          <p>{t(language, "From Space to Soil", "মহাকাশ থেকে মাটিতে")}</p>
        </div>
        <p>{t(language, "Team EARTH.exe · Bangladesh · NASA Space Apps Challenge 2026", "Team EARTH.exe · বাংলাদেশ · NASA Space Apps Challenge 2026")}</p>
        <a href="https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026" target="_blank" rel="noreferrer">
          GitHub ↗
        </a>
      </footer>
    </div>
  );
}
