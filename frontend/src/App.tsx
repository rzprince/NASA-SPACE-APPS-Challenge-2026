import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import EarthScene from "./EarthScene";
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

const NASA_BANGLADESH_IMAGE =
  "https://assets.science.nasa.gov/dynamicimage/assets/science/esd/eo/images/imagerecords/148000/148203/baniachong_oli_202176.jpg";

const cropOptions = [
  ["rice", "Rice", "ধান", "⌇"],
  ["wheat", "Wheat", "গম", "⋔"],
  ["maize", "Maize", "ভুট্টা", "≋"],
  ["pulse", "Pulse", "ডাল", "◉"],
  ["mustard", "Mustard", "সরিষা", "✣"],
  ["vegetables", "Vegetables", "সবজি", "✦"],
  ["jute", "Jute", "পাট", "╱"],
  ["other", "Other", "অন্য", "○"],
] as const;

const priorities = [
  ["water", "Use water carefully", "পানি সাশ্রয় ও ব্যবস্থাপনা", "W"],
  ["soil", "Protect the soil", "মাটির যত্ন", "S"],
  ["production_stability", "Keep production stable", "স্থিতিশীল উৎপাদন", "P"],
] as const;

function t(language: Language, en: string, bn: string) {
  return language === "bn" ? bn : en;
}

function dateMinus(days: number) {
  const value = new Date(Date.now() - days * 86400000);
  return value.toISOString().slice(0, 10);
}

function formatMetric(value: number | null | undefined, suffix: string) {
  if (value === null || value === undefined) return "—";
  return `${new Intl.NumberFormat("en-BD", { maximumFractionDigits: 1 }).format(value)}${suffix}`;
}

function locationName(place: PlaceResult | null, context: LocationContext | null, language: Language) {
  if (place?.name) return place.name;
  if (!context) return t(language, "Selected field", "নির্বাচিত জমি");
  return language === "bn"
    ? context.nearest_supported_region.name_bn
    : context.nearest_supported_region.name_en;
}

function statusCopy(status: Status, language: Language) {
  if (status === "loading") return t(language, "loading", "লোড হচ্ছে");
  if (status === "ready") return t(language, "connected", "সংযুক্ত");
  if (status === "unavailable") return t(language, "unavailable", "পাওয়া যায়নি");
  return t(language, "waiting", "অপেক্ষায়");
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
  const [navSolid, setNavSolid] = useState(false);
  const didAutoLocate = useRef(false);

  const imergDate = useMemo(() => dateMinus(1), []);
  const currentLocationName = locationName(selectedPlace, context, language);

  useEffect(() => {
    apiGet<{ areas: Area[] }>("/api/v1/areas")
      .then((payload) => setAreas(payload.areas))
      .catch(() => setAreas([]));
  }, []);

  useEffect(() => {
    const onScroll = () => setNavSolid(window.scrollY > 30);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) entry.target.classList.add("revealed");
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -8% 0px" },
    );
    document.querySelectorAll("[data-reveal]").forEach((node) => observer.observe(node));
    return () => observer.disconnect();
  }, [plan, context]);

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
        area.name_bn.includes(search.trim()) ||
        area.evidence_region.toLowerCase().includes(query),
    );
  }, [areas, search]);

  const recentRain = recent?.status === "available" ? recent.summary?.precipitation_total_mm : null;
  const recentTemp = recent?.status === "available" ? recent.summary?.temperature_mean_c : null;
  const baselineRain = baseline?.status === "available" ? baseline.summary?.precipitation_mean_daily_mm : null;
  const baselineTemp = baseline?.status === "available" ? baseline.summary?.temperature_mean_c : null;

  function scrollToLocation() {
    document.getElementById("field-locator")?.scrollIntoView({
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
      block: "start",
    });
  }

  function chooseArea(area: Area) {
    setSelectedPlace(null);
    setPoint({ latitude: area.latitude, longitude: area.longitude });
    setSearch("");
    setPlaceResults([]);
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
        window.setTimeout(scrollToLocation, 100);
      },
      () => {
        setGpsBusy(false);
        setLocationError(
          t(
            language,
            "Location permission was not granted. Search a place or tap the map instead.",
            "অবস্থানের অনুমতি পাওয়া যায়নি। জায়গা খুঁজুন বা মানচিত্রে ট্যাপ করুন।",
          ),
        );
      },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 },
    );
  }

  async function generatePlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!point || !context?.within_bangladesh) {
      setPlanError(t(language, "Choose a field location inside Bangladesh first.", "প্রথমে বাংলাদেশের ভেতরে একটি জমির অবস্থান বেছে নিন।"));
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
        include_climate_baseline: true,
      });
      setPlan(payload);
      window.setTimeout(() => {
        document.getElementById("field-brief")?.scrollIntoView({
          behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
          block: "start",
        });
      }, 120);
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
            <small>বপনএক্স</small>
          </span>
        </a>

        <nav className="bx-links" aria-label="Primary">
          <a href="#field-locator">{t(language, "Field", "জমি")}</a>
          <a href="#earth-signals">{t(language, "NASA evidence", "NASA প্রমাণ")}</a>
          <a href="#farm-story">{t(language, "Farm story", "জমির তথ্য")}</a>
          <a href="#field-brief">{t(language, "Plan", "পরিকল্পনা")}</a>
        </nav>

        <div className="bx-nav-actions">
          <button type="button" className="language-pill" onClick={() => setLanguage((value) => (value === "bn" ? "en" : "bn"))}>
            {language === "bn" ? "EN" : "বাংলা"}
          </button>
          <button type="button" className="locate-mini" onClick={useMyLocation}>
            <span>⌖</span>
            {t(language, "Locate field", "জমি খুঁজুন")}
          </button>
        </div>
      </header>

      <main id="top">
        <section className="cinematic-hero">
          <div className="hero-photo" aria-hidden="true">
            <img src={NASA_BANGLADESH_IMAGE} alt="" />
            <div className="hero-photo-overlay" />
          </div>
          <EarthScene className="hero-earth" />
          <div className="hero-grid" aria-hidden="true" />
          <div className="hero-scan" aria-hidden="true" />

          <div className="hero-content">
            <div className="hero-kicker">
              <span className="live-dot" />
              <span>NASA Space Apps 2026 · Field Shift</span>
            </div>

            <h1>
              <span>{t(language, "Your field.", "আপনার জমি।")}</span>
              <span className="hero-accent">{t(language, "Earth evidence.", "পৃথিবীর প্রমাণ।")}</span>
              <span>{t(language, "A better next move.", "আরও ভালো পরবর্তী সিদ্ধান্ত।")}</span>
            </h1>

            <p className="hero-lead">
              {t(
                language,
                "BoponX starts from the farmer's real location, brings in only the NASA and local evidence relevant to that place, and turns it into an understandable seasonal decision workflow.",
                "BoponX কৃষকের বাস্তব অবস্থান থেকে শুরু করে, শুধু সেই জায়গার প্রাসঙ্গিক NASA ও স্থানীয় প্রমাণ আনে, তারপর সেটিকে সহজ মৌসুমি সিদ্ধান্তের ধাপে রূপ দেয়।",
              )}
            </p>

            <div className="hero-actions">
              <button type="button" className="hero-primary" onClick={useMyLocation}>
                <span className="hero-primary-icon">⌖</span>
                <span>
                  <strong>{gpsBusy ? t(language, "Finding your field…", "আপনার জমি খোঁজা হচ্ছে…") : t(language, "Use my location", "আমার অবস্থান ব্যবহার করুন")}</strong>
                  <small>{t(language, "Browser permission required", "ব্রাউজারের অনুমতি প্রয়োজন")}</small>
                </span>
                <b>→</b>
              </button>
              <button type="button" className="hero-secondary" onClick={scrollToLocation}>
                {t(language, "Search or choose on map", "সার্চ বা মানচিত্রে বেছে নিন")}
              </button>
            </div>

            <div className="hero-source-line">
              <span>GPM IMERG</span>
              <i />
              <span>SMAP</span>
              <i />
              <span>NASA POWER</span>
              <i />
              <span>BAMIS / BARC</span>
            </div>
          </div>

          <div className="hero-data-stack" aria-hidden="true">
            <div className="floating-data-card data-card-a">
              <span>PRECIPITATION</span>
              <strong>IMERG</strong>
              <small>V07B · near-real-time</small>
            </div>
            <div className="floating-data-card data-card-b">
              <span>SOIL MOISTURE</span>
              <strong>SMAP</strong>
              <small>9 km · regional context</small>
            </div>
            <div className="floating-data-card data-card-c">
              <span>CLIMATE</span>
              <strong>POWER</strong>
              <small>recent + baseline</small>
            </div>
          </div>

          <div className="hero-credit">
            {t(language, "Real NASA Landsat image · Baniachong, Bangladesh", "বাস্তব NASA Landsat ছবি · বানিয়াচং, বাংলাদেশ")}
          </div>
        </section>

        <section className="source-marquee" aria-label="Data sources">
          <div className="source-track">
            {["NASA GPM IMERG Early V07B", "NASA GIBS", "SMAP SPL3SMP_E V6", "NASA POWER", "BAMIS", "BARC", "Farmer observations"].map((item) => (
              <span key={item}><i />{item}</span>
            ))}
          </div>
        </section>

        <section className="field-locator bx-section" id="field-locator">
          <div className="section-heading" data-reveal>
            <div className="section-index">01</div>
            <div>
              <p className="section-kicker">{t(language, "Start from one real place", "একটি বাস্তব জায়গা থেকে শুরু")}</p>
              <h2>{t(language, "Show me where the field is.", "জমিটা কোথায়, দেখান।")}</h2>
            </div>
            <p className="section-copy">
              {t(
                language,
                "BoponX never shows the whole country's data to one farmer. The selected point controls the map, NASA queries, climate baseline and local agricultural evidence.",
                "BoponX একজন কৃষককে পুরো দেশের ডেটা দেখায় না। নির্বাচিত পয়েন্টই মানচিত্র, NASA কুয়েরি, জলবায়ু বেসলাইন ও স্থানীয় কৃষি প্রমাণ নির্ধারণ করে।",
              )}
            </p>
          </div>

          <div className="location-command" data-reveal>
            <div className="location-search-panel">
              <div className="location-mode-title">
                <span className="mini-index">A</span>
                <div>
                  <strong>{t(language, "Detect, search, or tap", "লোকেশন নিন, সার্চ করুন বা ট্যাপ করুন")}</strong>
                  <small>{t(language, "The farmer chooses the field; NASA supplies the environmental context.", "কৃষক জমি বেছে নেন; NASA পরিবেশগত প্রেক্ষাপট দেয়।")}</small>
                </div>
              </div>

              <button type="button" className="detect-button" onClick={useMyLocation} disabled={gpsBusy}>
                <span className="detect-radar"><i /><i /></span>
                <span>
                  <strong>{gpsBusy ? t(language, "Detecting…", "খোঁজা হচ্ছে…") : t(language, "Detect my current location", "আমার বর্তমান অবস্থান নিন")}</strong>
                  <small>{t(language, "Uses browser GPS only after permission", "অনুমতির পর ব্রাউজার GPS ব্যবহার করে")}</small>
                </span>
                <b>⌖</b>
              </button>

              <label className="place-search-box">
                <span className="search-symbol">⌕</span>
                <input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder={t(language, "Search village, upazila, district…", "গ্রাম, উপজেলা, জেলা খুঁজুন…")}
                  aria-label={t(language, "Search a Bangladesh place", "বাংলাদেশের জায়গা খুঁজুন")}
                />
                {search && <button type="button" onClick={() => setSearch("")}>×</button>}
              </label>

              {search && (
                <div className="place-suggestions">
                  {placeSearchStatus === "loading" && (
                    <div className="searching-row"><span className="spinner" />{t(language, "Searching Bangladesh…", "বাংলাদেশে খোঁজা হচ্ছে…")}</div>
                  )}
                  {placeResults.slice(0, 6).map((place, index) => (
                    <button type="button" key={`${place.latitude}-${place.longitude}-${index}`} onClick={() => choosePlace(place)}>
                      <span className="suggestion-pin">⌖</span>
                      <span>
                        <strong>{place.name ?? place.address.village ?? place.address.town ?? t(language, "Selected place", "নির্বাচিত জায়গা")}</strong>
                        <small>{[place.address.village, place.address.upazila, place.address.district, place.address.division].filter(Boolean).join(" · ")}</small>
                      </span>
                    </button>
                  ))}
                  {placeResults.length === 0 && placeSearchStatus !== "loading" && filteredAreas.slice(0, 6).map((area) => (
                    <button type="button" key={area.id} onClick={() => chooseArea(area)}>
                      <span className="suggestion-pin">◎</span>
                      <span>
                        <strong>{language === "bn" ? area.name_bn : area.name_en}</strong>
                        <small>{t(language, "regional evidence hub", "আঞ্চলিক প্রমাণ হাব")}</small>
                      </span>
                    </button>
                  ))}
                </div>
              )}

              <div className="privacy-note">
                <span>◌</span>
                <p>
                  <strong>{t(language, "Location stays temporary.", "অবস্থান অস্থায়ী থাকে।")}</strong>
                  {t(language, " BoponX does not save exact coordinates by default.", " BoponX ডিফল্টভাবে সঠিক স্থানাঙ্ক সংরক্ষণ করে না।")}
                </p>
              </div>

              {locationError && <div className="error-banner">{locationError}</div>}
            </div>

            <div className="location-map-panel">
              <LocationMap point={point} onPick={(value) => { setSelectedPlace(null); setPoint(value); }} language={language} imergDate={imergDate} />

              <div className={point ? "field-lock active" : "field-lock"}>
                <div className="field-lock-head">
                  <span className="field-lock-status"><i />{point ? t(language, "FIELD LOCKED", "জমি নির্ধারিত") : t(language, "WAITING FOR FIELD", "জমির অপেক্ষায়")}</span>
                  <span>{contextStatus !== "idle" && statusCopy(contextStatus, language)}</span>
                </div>
                <strong>{point ? currentLocationName : t(language, "Choose a field point", "জমির পয়েন্ট বেছে নিন")}</strong>
                {point && (
                  <>
                    <p>{point.latitude.toFixed(5)}° N · {point.longitude.toFixed(5)}° E</p>
                    {selectedPlace && (
                      <small>{[selectedPlace.address.village, selectedPlace.address.upazila, selectedPlace.address.district, selectedPlace.address.division].filter(Boolean).join(" · ")}</small>
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
              <p className="section-kicker">{t(language, "Earth intelligence, filtered by place", "অবস্থানভিত্তিক Earth intelligence")}</p>
              <h2>{point ? currentLocationName : t(language, "Choose a field to wake the data.", "ডেটা চালু করতে জমি বেছে নিন।")}</h2>
            </div>
            <p className="section-copy">
              {t(
                language,
                "Each source has one job. Recent rainfall, regional soil moisture, recent climate and historical baseline stay separate so the farmer can see what the evidence actually means.",
                "প্রতিটি উৎসের কাজ আলাদা। সাম্প্রতিক বৃষ্টি, আঞ্চলিক মাটির আর্দ্রতা, সাম্প্রতিক জলবায়ু ও ঐতিহাসিক বেসলাইন আলাদা থাকে—যাতে প্রমাণের অর্থ পরিষ্কার থাকে।",
              )}
            </p>
          </div>

          <div className="signal-stage" data-reveal>
            <article className="signal-card signal-rain">
              <div className="signal-card-top">
                <span className="source-badge live"><i />{t(language, "Near-real-time", "নিকট-বাস্তব সময়")}</span>
                <span className="signal-number">01</span>
              </div>
              <div className="signal-visual rain-visual">
                <span className="rain-column r1" /><span className="rain-column r2" /><span className="rain-column r3" /><span className="rain-column r4" />
                <div className="rain-radar"><i /><i /><i /></div>
              </div>
              <h3>GPM IMERG Early</h3>
              <p>{t(language, "Recent precipitation evidence around the selected field.", "নির্বাচিত জমির আশেপাশের সাম্প্রতিক বৃষ্টির প্রমাণ।")}</p>
              <dl>
                <div><dt>{t(language, "Map date", "মানচিত্র তারিখ")}</dt><dd>{imergDate}</dd></div>
                <div><dt>{t(language, "Resolution", "রেজোলিউশন")}</dt><dd>0.1° · ~10 km</dd></div>
                <div><dt>{t(language, "Minimum latency", "সর্বনিম্ন লেটেন্সি")}</dt><dd>~4 h</dd></div>
              </dl>
            </article>

            <article className="signal-card signal-power">
              <div className="signal-card-top">
                <span className={`source-badge ${recentStatus}`}><i />{statusCopy(recentStatus, language)}</span>
                <span className="signal-number">02</span>
              </div>
              <div className="signal-metric">
                <strong>{formatMetric(recentTemp, "°C")}</strong>
                <span>{t(language, "recent period mean", "সাম্প্রতিক সময়ের গড়")}</span>
              </div>
              <div className="signal-metric secondary">
                <strong>{formatMetric(recentRain, " mm")}</strong>
                <span>{t(language, "complete-period rainfall", "সম্পূর্ণ সময়ের বৃষ্টি")}</span>
              </div>
              <h3>NASA POWER</h3>
              <p>
                {recent?.period
                  ? `${recent.period.start} → ${recent.period.end} · ${recent.period.time_standard}`
                  : t(language, "Select a field to request recent gridded context.", "সাম্প্রতিক গ্রিডভিত্তিক তথ্য পেতে জমি বেছে নিন।")}
              </p>
            </article>

            <article className="signal-card signal-baseline">
              <div className="signal-card-top">
                <span className={`source-badge ${baselineStatus}`}><i />{statusCopy(baselineStatus, language)}</span>
                <span className="signal-number">03</span>
              </div>
              <div className="baseline-rings" aria-hidden="true"><i /><i /><i /></div>
              <div className="signal-metric">
                <strong>{formatMetric(baselineTemp, "°C")}</strong>
                <span>{t(language, "planning-month climate mean", "পরিকল্পনা মাসের জলবায়ু গড়")}</span>
              </div>
              <div className="signal-metric secondary">
                <strong>{formatMetric(baselineRain, " mm/day")}</strong>
                <span>{t(language, "climatological daily rain", "ক্লাইমেটোলজিক্যাল দৈনিক বৃষ্টি")}</span>
              </div>
              <h3>POWER 2001–2020</h3>
              <p>{t(language, "Historical reference for the selected planning month. Not a forecast.", "নির্বাচিত পরিকল্পনা মাসের ঐতিহাসিক রেফারেন্স। এটি পূর্বাভাস নয়।")}</p>
            </article>

            <article className="signal-card signal-soil">
              <div className="signal-card-top">
                <span className="source-badge review"><i />{t(language, "QA-gated", "QA-গেটেড")}</span>
                <span className="signal-number">04</span>
              </div>
              <div className="soil-cube" aria-hidden="true">
                <span className="soil-face top" /><span className="soil-face left" /><span className="soil-face right" />
                <i className="soil-wave w1" /><i className="soil-wave w2" /><i className="soil-wave w3" />
              </div>
              <h3>SMAP SPL3SMP_E V6</h3>
              <p>{t(language, "Regional surface-soil-moisture context. Numeric use stays gated until the authenticated adapter and 2026 QA checks are complete.", "আঞ্চলিক উপরিভাগের মাটির আর্দ্রতার প্রেক্ষাপট। authenticated adapter ও ২০২৬ QA যাচাই শেষ না হওয়া পর্যন্ত সংখ্যাগত ব্যবহার বন্ধ।")}</p>
              <dl>
                <div><dt>{t(language, "Resolution", "রেজোলিউশন")}</dt><dd>9 km · daily</dd></div>
                <div><dt>{t(language, "Never used as", "কখনো ব্যবহার নয়")}</dt><dd>soil pH</dd></div>
              </dl>
            </article>
          </div>

          <div className="data-quality-banner" data-reveal>
            <span className="quality-icon">!</span>
            <div>
              <strong>{t(language, "2026 SMAP quality note", "২০২৬ SMAP ডেটা-গুণমান নোট")}</strong>
              <p>{t(language, "NSIDC reports a geolocation issue affecting Standard/NRT products from 14 May to 28 July 2026. BoponX keeps those dates behind a quality gate.", "NSIDC ১৪ মে থেকে ২৮ জুলাই ২০২৬ পর্যন্ত Standard/NRT ডেটায় geolocation সমস্যা রিপোর্ট করেছে। BoponX ওই সময়ের ডেটা quality gate-এর পেছনে রাখে।")}</p>
            </div>
          </div>
        </section>

        <section className="nasa-story bx-section">
          <div className="nasa-story-media" data-reveal>
            <img src={NASA_BANGLADESH_IMAGE} alt={t(language, "NASA Landsat view of Baniachong, Bangladesh, surrounded by agricultural fields", "NASA Landsat-এ বানিয়াচং, বাংলাদেশ ও আশেপাশের কৃষিজমি")} />
            <div className="image-coordinate">24.50° N · 91.35° E</div>
            <div className="image-caption">
              <span>NASA / USGS Landsat</span>
              <strong>{t(language, "Baniachong, Bangladesh", "বানিয়াচং, বাংলাদেশ")}</strong>
            </div>
          </div>
          <div className="nasa-story-copy" data-reveal>
            <p className="section-kicker">{t(language, "A real Bangladesh precedent", "বাংলাদেশে বাস্তব NASA উদাহরণ")}</p>
            <h2>{t(language, "Satellite evidence should change a decision—not decorate a dashboard.", "স্যাটেলাইট প্রমাণ সিদ্ধান্ত বদলাবে—ড্যাশবোর্ড সাজাবে না।")}</h2>
            <p>
              {t(
                language,
                "NASA Earth Observatory documented the use of Landsat and other satellite information around Baniachong to support irrigation decisions. BoponX follows the same principle: Earth observations are useful only when they connect to a farmer's next choice.",
                "NASA Earth Observatory বানিয়াচং অঞ্চলে সেচ সিদ্ধান্তে Landsat ও অন্যান্য স্যাটেলাইট তথ্য ব্যবহারের উদাহরণ নথিভুক্ত করেছে। BoponX একই নীতি অনুসরণ করে: Earth observation তখনই মূল্যবান, যখন তা কৃষকের পরবর্তী সিদ্ধান্তের সঙ্গে যুক্ত হয়।",
              )}
            </p>
            <a href="https://science.nasa.gov/earth/earth-observatory/fine-tuning-irrigation-in-asia-148203/" target="_blank" rel="noreferrer">
              {t(language, "Open NASA Earth Observatory story", "NASA Earth Observatory প্রতিবেদন খুলুন")} ↗
            </a>
          </div>
        </section>

        <section className="local-evidence bx-section" id="local-evidence">
          <div className="section-heading" data-reveal>
            <div className="section-index">03</div>
            <div>
              <p className="section-kicker">{t(language, "NASA is only half the answer", "NASA হলো উত্তরের এক অংশ")}</p>
              <h2>{t(language, "Bring the field's local evidence into the same frame.", "স্থানীয় কৃষি প্রমাণকে একই ফ্রেমে আনুন।")}</h2>
            </div>
            <p className="section-copy">
              {t(
                language,
                "BoponX only surfaces crop calendars indexed for the selected regional evidence hub. A calendar appearing here means a source exists—not that the crop is automatically recommended.",
                "BoponX নির্বাচিত আঞ্চলিক evidence hub-এর জন্য ইনডেক্স করা ফসল ক্যালেন্ডারই দেখায়। এখানে কোনো ক্যালেন্ডার দেখা মানে উৎস আছে—ফসলটি স্বয়ংক্রিয়ভাবে সুপারিশ করা হয়েছে এমন নয়।",
              )}
            </p>
          </div>

          <div className="local-evidence-grid" data-reveal>
            <div className="region-evidence-card">
              <div className="region-card-top">
                <span>{t(language, "Selected evidence region", "নির্বাচিত evidence region")}</span>
                <strong>{context ? context.nearest_supported_region.evidence_region : "—"}</strong>
              </div>
              <div className="region-grid-art" aria-hidden="true">
                {Array.from({ length: 20 }).map((_, index) => <i key={index} />)}
              </div>
              <div className="coverage-lines">
                <div><span className={context?.within_bangladesh ? "coverage-ok" : ""} />{t(language, "NASA environmental context", "NASA পরিবেশগত প্রেক্ষাপট")}</div>
                <div><span className={context?.calendar_evidence?.length ? "coverage-ok" : "coverage-warn"} />{t(language, "Local calendar sources", "স্থানীয় ক্যালেন্ডার উৎস")}</div>
                <div><span className="coverage-lock" />{t(language, "Rotation rules: review gate", "Rotation rules: review gate")}</div>
              </div>
            </div>

            <div className="calendar-evidence-panel">
              <div className="calendar-panel-head">
                <span>{t(language, "Official calendar sources", "অফিসিয়াল ক্যালেন্ডার উৎস")}</span>
                <strong>{context?.calendar_evidence?.length ?? 0}</strong>
              </div>
              <div className="crop-source-list">
                {context?.calendar_evidence?.length ? (
                  context.calendar_evidence.slice(0, 9).map((crop, index) => (
                    <a href={crop.source_url} target="_blank" rel="noreferrer" key={crop.id} className="crop-source-row">
                      <span className="crop-seq">{String(index + 1).padStart(2, "0")}</span>
                      <span>
                        <strong>{language === "bn" ? crop.name_bn : crop.name_en}</strong>
                        <small>{language === "bn" ? crop.name_en : crop.name_bn}</small>
                      </span>
                      <b>↗</b>
                    </a>
                  ))
                ) : (
                  <div className="empty-evidence">
                    <span>◎</span>
                    <p>{t(language, "Choose a field to load only the crop-calendar evidence tied to its regional hub.", "আঞ্চলিক হাবের প্রাসঙ্গিক ফসল ক্যালেন্ডার দেখতে জমি বেছে নিন।")}</p>
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
              <p className="section-kicker">{t(language, "Ask what a farmer can actually answer", "কৃষক যা সত্যিই জানেন, সেটাই জিজ্ঞেস করুন")}</p>
              <h2>{t(language, "No laboratory quiz.", "কোনো ল্যাবরেটরি কুইজ নয়।")}</h2>
            </div>
            <p className="section-copy">
              {t(
                language,
                "The farmer's experience is evidence too. Unknown is a valid answer. BoponX never fills a scientific blank with a guess.",
                "কৃষকের অভিজ্ঞতাও প্রমাণ। ‘জানি না’ একটি বৈধ উত্তর। BoponX বৈজ্ঞানিক তথ্যের ঘাটতি অনুমান দিয়ে পূরণ করে না।",
              )}
            </p>
          </div>

          <form className="farmer-story-form" onSubmit={generatePlan} data-reveal>
            <fieldset disabled={!point || !context?.within_bangladesh}>
              <legend><span>01</span>{t(language, "What was grown last?", "আগে কী চাষ হয়েছিল?")}</legend>
              <div className="crop-choice-grid">
                {cropOptions.map(([value, en, bn, icon]) => (
                  <button
                    type="button"
                    key={value}
                    className={previousCrop === value ? "crop-choice active" : "crop-choice"}
                    onClick={() => setPreviousCrop(previousCrop === value ? "" : value)}
                  >
                    <span>{icon}</span>
                    <strong>{t(language, en, bn)}</strong>
                  </button>
                ))}
                <button type="button" className={!previousCrop ? "crop-choice unknown active" : "crop-choice unknown"} onClick={() => setPreviousCrop("")}>
                  <span>?</span><strong>{t(language, "Not sure", "নিশ্চিত নই")}</strong>
                </button>
              </div>
            </fieldset>

            <div className="farmer-form-split">
              <fieldset disabled={!point || !context?.within_bangladesh}>
                <legend><span>02</span>{t(language, "How does the field get water?", "জমিতে পানি আসে কীভাবে?")}</legend>
                <div className="answer-stack">
                  {[
                    ["rainfed", "Mostly rain", "মূলত বৃষ্টি", "☂"],
                    ["irrigated", "Mostly irrigation", "মূলত সেচ", "≈"],
                    ["both", "Rain + irrigation", "বৃষ্টি + সেচ", "≋"],
                    ["unknown", "Not sure", "নিশ্চিত নই", "?"],
                  ].map(([value, en, bn, icon]) => (
                    <label className={waterSource === value ? "answer-card active" : "answer-card"} key={value}>
                      <input type="radio" name="water" checked={waterSource === value} onChange={() => setWaterSource(value as FarmerProfile["water_source"])} />
                      <span className="answer-icon">{icon}</span>
                      <strong>{t(language, en, bn)}</strong>
                    </label>
                  ))}
                </div>
              </fieldset>

              <fieldset disabled={!point || !context?.within_bangladesh}>
                <legend><span>03</span>{t(language, "After heavy rain?", "ভারী বৃষ্টির পর?")}</legend>
                <div className="answer-stack">
                  {[
                    ["drains", "Water drains quickly", "পানি দ্রুত নেমে যায়", "↘"],
                    ["stays", "Water stays a long time", "পানি অনেকক্ষণ থাকে", "◫"],
                    ["sometimes", "It depends", "সময়ভেদে আলাদা", "↔"],
                    ["unknown", "Not sure", "নিশ্চিত নই", "?"],
                  ].map(([value, en, bn, icon]) => (
                    <label className={waterAfterRain === value ? "answer-card active" : "answer-card"} key={value}>
                      <input type="radio" name="rain" checked={waterAfterRain === value} onChange={() => setWaterAfterRain(value as FarmerProfile["water_after_heavy_rain"])} />
                      <span className="answer-icon">{icon}</span>
                      <strong>{t(language, en, bn)}</strong>
                    </label>
                  ))}
                </div>
              </fieldset>
            </div>

            <div className="farmer-form-split">
              <fieldset disabled={!point || !context?.within_bangladesh}>
                <legend><span>04</span>{t(language, "Do you have a soil-test report?", "মাটি পরীক্ষার রিপোর্ট আছে?")}</legend>
                <div className="soil-test-choice">
                  {[
                    ["yes", "Yes", "হ্যাঁ"],
                    ["no", "No", "না"],
                    ["unknown", "Not sure", "নিশ্চিত নই"],
                  ].map(([value, en, bn]) => (
                    <label className={soilTest === value ? "soil-choice active" : "soil-choice"} key={value}>
                      <input type="radio" name="soil" checked={soilTest === value} onChange={() => setSoilTest(value as FarmerProfile["soil_test"])} />
                      <span>{t(language, en, bn)}</span>
                    </label>
                  ))}
                </div>
                {soilTest === "yes" && (
                  <label className="ph-field">
                    <span>
                      <strong>{t(language, "pH from the report", "রিপোর্টের pH")}</strong>
                      <small>{t(language, "Optional. Never inferred from NASA data.", "ঐচ্ছিক। NASA ডেটা থেকে অনুমান করা হয় না।")}</small>
                    </span>
                    <input type="number" min="0" max="14" step="0.1" value={soilPh} onChange={(event) => setSoilPh(event.target.value)} placeholder="6.5" />
                  </label>
                )}
              </fieldset>

              <fieldset disabled={!point || !context?.within_bangladesh}>
                <legend><span>05</span>{t(language, "What matters most now?", "এখন সবচেয়ে গুরুত্বপূর্ণ কী?")}</legend>
                <div className="priority-stack">
                  {priorities.map(([value, en, bn, code]) => (
                    <label className={priority === value ? "priority-choice active" : "priority-choice"} key={value}>
                      <input type="radio" name="priority" checked={priority === value} onChange={() => setPriority(value as FarmerProfile["priority"])} />
                      <span>{code}</span>
                      <strong>{t(language, en, bn)}</strong>
                    </label>
                  ))}
                </div>
              </fieldset>
            </div>

            <div className="brief-builder">
              <div>
                <span className="brief-label">{t(language, "Planning starts", "পরিকল্পনা শুরু")}</span>
                <div className="date-pickers">
                  <select value={startMonth} onChange={(event) => setStartMonth(Number(event.target.value))}>
                    {Array.from({ length: 12 }, (_, index) => index + 1).map((month) => <option key={month} value={month}>{String(month).padStart(2, "0")}</option>)}
                  </select>
                  <select value={startYear} onChange={(event) => setStartYear(Number(event.target.value))}>
                    {Array.from({ length: 10 }, (_, index) => 2026 + index).map((year) => <option key={year} value={year}>{year}</option>)}
                  </select>
                </div>
              </div>
              <button type="submit" disabled={!point || !context?.within_bangladesh || planBusy}>
                <span>
                  <small>{t(language, "Generate decision-support routine", "সিদ্ধান্ত-সহায়তা রুটিন তৈরি করুন")}</small>
                  <strong>{planBusy ? t(language, "Building…", "তৈরি হচ্ছে…") : t(language, "Build my 90-day field brief", "আমার ৯০ দিনের মাঠ পরিকল্পনা তৈরি করুন")}</strong>
                </span>
                <b>→</b>
              </button>
            </div>

            {!point && <p className="form-lock-message">{t(language, "Choose the field first. The farmer form unlocks after location.", "প্রথমে জমি বেছে নিন। অবস্থান নির্ধারণের পর ফর্মটি চালু হবে।")}</p>}
            {planError && <div className="error-banner">{planError}</div>}
          </form>
        </section>

        {plan && <DecisionReport brief={plan} language={language} />}

        <section className="rotation-future bx-section">
          <div className="rotation-stage" data-reveal>
            <EarthScene className="rotation-earth" accent="cyan" />
            <div className="rotation-copy">
              <p className="section-kicker">{t(language, "The challenge destination", "চ্যালেঞ্জের মূল গন্তব্য")}</p>
              <h2>{t(language, "Three seasons. Multiple strategies. Evidence beside every option.", "তিন মৌসুম। একাধিক কৌশল। প্রতিটি বিকল্পের পাশে প্রমাণ।")}</h2>
              <p>
                {t(
                  language,
                  "The rotation explorer will compare feasible sequences only after Bangladesh crop calendars, crop requirements, soil constraints and sequence rules are source-reviewed. Until then, BoponX shows the evidence pipeline without inventing a crop recommendation.",
                  "Bangladesh-এর crop calendar, crop requirement, soil constraint ও crop-sequence rule উৎস-পর্যালোচনা শেষ হওয়ার পরই rotation explorer কার্যকর sequence তুলনা করবে। তার আগে BoponX প্রমাণের pipeline দেখায়, কিন্তু ফসলের সুপারিশ বানিয়ে দেয় না।",
                )}
              </p>
              <div className="rotation-flow">
                <span>{t(language, "Field", "জমি")}</span><i>→</i>
                <span>NASA</span><i>→</i>
                <span>{t(language, "Local rules", "স্থানীয় নিয়ম")}</span><i>→</i>
                <span>{t(language, "2–3 rotations", "২–৩ rotation")}</span><i>→</i>
                <span>{t(language, "Farmer decides", "কৃষক সিদ্ধান্ত নেন")}</span>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="bx-footer">
        <div className="footer-brand">
          <span className="bx-brand-mark"><i /><i /><i /></span>
          <div><strong>BoponX · বপনএক্স</strong><small>{t(language, "From Space to Soil", "মহাকাশ থেকে মাটিতে")}</small></div>
        </div>
        <p>{t(language, "Independent Team EARTH.exe project · NASA does not endorse this application.", "Team EARTH.exe-এর স্বাধীন প্রকল্প · NASA এই অ্যাপ্লিকেশনকে অনুমোদন বা endorsement দেয়নি।")}</p>
        <div className="footer-links">
          <a href="https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026" target="_blank" rel="noreferrer">GitHub ↗</a>
          <a href="https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/" target="_blank" rel="noreferrer">Field Shift ↗</a>
        </div>
      </footer>
    </div>
  );
}
