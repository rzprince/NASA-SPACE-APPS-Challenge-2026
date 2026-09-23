import FieldScene from "./FieldScene";
import BangladeshAtlas from "./BangladeshAtlas";
import FarmReport, { type PlanBrief } from "./FarmReport";
import ClimateExplorer from "./ClimateExplorer";
import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import {
  ApiError,
  apiGet,
  apiPost,
  type ClimateSnapshot,
  type FarmProfile,
  type FarmValidation,
  type Location,
  type Status,
} from "./api";

const planningMonths: {en:string;bn:string}[] = [
  {en:"January",bn:"জানুয়ারি"},{en:"February",bn:"ফেব্রুয়ারি"},
  {en:"March",bn:"মার্চ"},{en:"April",bn:"এপ্রিল"},
  {en:"May",bn:"মে"},{en:"June",bn:"জুন"},
  {en:"July",bn:"জুলাই"},{en:"August",bn:"আগস্ট"},
  {en:"September",bn:"সেপ্টেম্বর"},{en:"October",bn:"অক্টোবর"},
  {en:"November",bn:"নভেম্বর"},{en:"December",bn:"ডিসেম্বর"},
];

const initialFarm: FarmProfile = {
  location_id: "rajshahi-pilot",
  previous_crop: null,
  soil_ph: null,
  soil_texture: "unknown",
  irrigation_mode: "unknown",
  priorities: [],
};

const priorityLabels: Record<FarmProfile["priorities"][number], { en: string; bn: string }> = {
  water: { en: "Water resilience", bn: "পানি ব্যবস্থাপনা" },
  soil: { en: "Soil health", bn: "মাটির স্বাস্থ্য" },
  production_stability: { en: "Production stability", bn: "উৎপাদন স্থিতিশীলতা" },
};

const soilLabels = {
  unknown: { en: "Unknown / not tested", bn: "অজানা / পরীক্ষা করা হয়নি" },
  sandy: { en: "Sandy", bn: "বেলে" },
  loamy: { en: "Loamy", bn: "দোআঁশ" },
  clayey: { en: "Clayey", bn: "এঁটেল" },
} as const;

const irrigationLabels = {
  unknown: { en: "Unknown", bn: "অজানা" },
  none: { en: "No irrigation", bn: "সেচ নেই" },
  limited: { en: "Limited irrigation", bn: "সীমিত সেচ" },
  reliable: { en: "Reliable irrigation", bn: "নির্ভরযোগ্য সেচ" },
} as const;

function Duo({
  en,
  bn,
  as = "span",
  className = "",
}: {
  en: ReactNode;
  bn: ReactNode;
  as?: "span" | "p" | "div";
  className?: string;
}) {
  const Tag = as;
  return (
    <Tag className={`duo ${className}`}>
      <span className="duo-en">{en}</span>
      <span className="duo-bn" lang="bn">{bn}</span>
    </Tag>
  );
}

function format(value: number, digits = 1): string {
  return new Intl.NumberFormat("en-BD", { maximumFractionDigits: digits }).format(value);
}

function StatusTag({ status }: { status: Status }) {
  const label =
    status === "ready"
      ? { en: "NASA dataset validated", bn: "NASA ডেটা যাচাই হয়েছে" }
      : status === "loading"
        ? { en: "Checking data", bn: "ডেটা যাচাই হচ্ছে" }
        : { en: "Dataset not loaded", bn: "ডেটাসেট লোড হয়নি" };
  return (
    <span className={`status-pill ${status}`}>
      <span aria-hidden="true" className="status-dot" />
      <Duo en={label.en} bn={label.bn} />
    </span>
  );
}

function SectionIndex({ n, en, bn }: { n: string; en: string; bn: string }) {
  return (
    <div className="section-index">
      <span>{n}</span>
      <Duo en={en} bn={bn} />
    </div>
  );
}

export default function App() {
  const [locations, setLocations] = useState<Location[]>([]);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [climate, setClimate] = useState<ClimateSnapshot | null>(null);
  const [climateStatus, setClimateStatus] = useState<Status>("loading");
  const [climateMessage, setClimateMessage] = useState("");
  const [farm, setFarm] = useState<FarmProfile>(initialFarm);
  const [farmResult, setFarmResult] = useState<FarmValidation | null>(null);
  const [farmError, setFarmError] = useState("");
  const [farmBusy, setFarmBusy] = useState(false);
  const [startMonth, setStartMonth] = useState<number>(() => (new Date().getMonth()+1)%12+1);
  const [startYear, setStartYear] = useState<number>(() => Math.min(2035,Math.max(2026,new Date().getFullYear()+(new Date().getMonth()===11?1:0))));
  const [candidateCrop, setCandidateCrop] = useState("");
  const [brief, setBrief] = useState<PlanBrief | null>(null);

  useEffect(() => {
    let active = true;
    apiGet<{ status: string }>("/api/v1/health")
      .then(() => { if (active) setApiOnline(true); })
      .catch(() => { if (active) setApiOnline(false); });
    apiGet<{ locations: Location[] }>("/api/v1/locations")
      .then((data) => { if (active) setLocations(data.locations); })
      .catch(() => {});
    apiGet<ClimateSnapshot>("/api/v1/climate/rajshahi-pilot")
      .then((data) => {
        if (!active) return;
        if (data.evidence.ingestion_origin !== "nasa_power_https") {
          setClimateStatus("unavailable");
          setClimateMessage("This snapshot is not a verified NASA POWER acquisition.");
          return;
        }
        setClimate(data);
        setClimateStatus("ready");
      })
      .catch((error: unknown) => {
        if (!active) return;
        setClimateStatus("unavailable");
        setClimateMessage(error instanceof ApiError ? error.message : "Climate data could not be loaded.");
      });
    return () => { active = false; };
  }, []);

  const location = locations.find((item) => item.id === farm.location_id);
  const rainCoverage = climate?.summary.coverage.PRECTOTCORR;
  const tempCoverage = climate?.summary.coverage.T2M;

  function changeFarm<K extends keyof FarmProfile>(key: K, value: FarmProfile[K]) {
    setFarm((current) => ({ ...current, [key]: value }));
    setFarmResult(null);
    setBrief(null);
    setFarmError("");
  }

  async function validateFarm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFarmBusy(true);
    setFarmError("");
    setFarmResult(null);
    try {
      const checked = await apiPost<FarmValidation>("/api/v1/farms/validate", farm);
      setFarmResult(checked);
      const report = await apiPost<PlanBrief>("/api/v1/plans/preview", {
        farm, start_month: startMonth, start_year: startYear,
        candidate_crop: candidateCrop.trim() || null,
      });
      setBrief(report);
      window.setTimeout(() => document.getElementById("boponx-report")?.scrollIntoView({
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth"
      }), 70);
    } catch (error) {
      setFarmError(error instanceof ApiError ? error.message : "Farm inputs could not be validated.");
    } finally {
      setFarmBusy(false);
    }
  }

  return (
    <div className="site">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="BoponX home">
          <span className="brand-emblem" aria-hidden="true">
            <span className="flag-sun" />
            <span className="seed-stroke" />
          </span>
          <span className="brand-word">Bopon<span>X</span></span>
          <span className="brand-sub" lang="bn">বপনএক্স</span>
        </a>
        <nav aria-label="Primary">
          <a href="#climate"><Duo en="Climate" bn="জলবায়ু" /></a>
          <a href="#farm"><Duo en="My plan" bn="আমার পরিকল্পনা" /></a>
          <a className="nav-github" href="https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026" target="_blank" rel="noreferrer">
            <Duo en="Source code" bn="সোর্স কোড" /> <span aria-hidden="true">↗</span>
          </a>
        </nav>
      </header>

      <main id="top">
        <section className="hero">
          <div className="hero-grid-lines" aria-hidden="true" />
          <div className="hero-copy">
            <div className="eyebrow">
              <span className="eyebrow-sun" aria-hidden="true" />
              <Duo en="An EARTH.exe initiative · NASA Space Apps 2026" bn="EARTH.exe উদ্যোগ · NASA Space Apps 2026" />
            </div>

            <div className="hero-title-wrap">
              <p className="hero-bengali-title" lang="bn">মহাকাশ থেকে মাটিতে</p>
              <h1>From <span>Space</span><br />to Soil.</h1>
            </div>

            <Duo
              as="p"
              className="hero-lead"
              en="A climate-resilient crop-rotation decision platform designed for farmers, advisers and communities."
              bn="কৃষক, কৃষি পরামর্শক ও স্থানীয় মানুষের জন্য জলবায়ু-সহনশীল ফসল আবর্তন সিদ্ধান্ত সহায়তা প্ল্যাটফর্ম।"
            />

            <div className="hero-actions">
              <a className="button primary" href="#farm">
                <Duo en="Create my 3-month brief" bn="আমার তিন মাসের প্রস্তুতি নোট" />
                <span aria-hidden="true">↗</span>
              </a>
              <a className="button ghost" href="#climate">
                <Duo en="Explore NASA climate data" bn="NASA জলবায়ু ডেটা দেখুন" />
                <span aria-hidden="true">↓</span>
              </a>
            </div>

            <div className="hero-meta">
              <StatusTag status={climateStatus} />
              <span className={`api-state ${apiOnline === false ? "down" : ""}`}>
                <span aria-hidden="true" className="status-dot" />
                <Duo
                  en={apiOnline === false ? "API disconnected" : "Rajshahi pilot · Bangladesh"}
                  bn={apiOnline === false ? "API সংযোগ নেই" : "রাজশাহী পাইলট · বাংলাদেশ"}
                />
              </span>
            </div>
          </div>

          <FieldScene />
        </section>

        <section className="trust-strip" aria-label="BoponX principles">
          <div><b>NASA</b><Duo en="Data at the core" bn="মূল শক্তি হলো ডেটা" /></div>
          <div><b>01</b><Duo en="Deterministic science" bn="যাচাইযোগ্য বিজ্ঞান" /></div>
          <div><b>02</b><Duo en="Local context" bn="স্থানীয় বাস্তবতা" /></div>
          <div><b>03</b><Duo en="Explainable decisions" bn="ব্যাখ্যাযোগ্য সিদ্ধান্ত" /></div>
        </section>

        <BangladeshAtlas dataReady={climateStatus === "ready"} />

        <section className="section climate-section" id="climate" aria-labelledby="climate-heading">
          <div className="section-heading-row">
            <SectionIndex n="01" en="Environmental context" bn="পরিবেশগত প্রেক্ষাপট" />
            <div className="section-title-block">
              <h2 id="climate-heading">See the climate.<br /><span>See the evidence.</span></h2>
              <p lang="bn">জলবায়ু দেখুন। প্রমাণ দেখুন।</p>
            </div>
            <Duo
              as="p"
              className="section-description"
              en="The pilot shows 2024 regional historical temperature and rainfall from NASA POWER / MERRA-2 reanalysis. These are not direct satellite rainfall readings, field measurements or future forecasts."
              bn="পাইলটে NASA POWER / MERRA-2 পুনর্বিশ্লেষণ থেকে ২০২৪ সালের আঞ্চলিক তাপমাত্রা ও বৃষ্টির ইতিহাস দেখানো হচ্ছে। এগুলো সরাসরি স্যাটেলাইটে মাপা বৃষ্টি, নির্দিষ্ট জমির মাপ বা ভবিষ্যৎ পূর্বাভাস নয়।"
            />
          </div>

          <div className="climate-frame">
            <div className="frame-top">
              <div>
                <Duo className="frame-label" en="Selected region" bn="নির্বাচিত অঞ্চল" />
                <strong>{location?.name ?? "Rajshahi regional pilot"}</strong>
                <span className="subline">{location ? `${location.latitude}° N · ${location.longitude}° E` : "24.37° N · 88.60° E"} · provisional reference point</span>
                <span className="subline bn" lang="bn">অস্থায়ী আঞ্চলিক রেফারেন্স পয়েন্ট</span>
              </div>
              <StatusTag status={climateStatus} />
            </div>

            {climate ? (
              <>
                <div className="metric-grid">
                  <article className="metric-card">
                    <Duo className="metric-label" en="Mean temperature · valid days" bn="গড় তাপমাত্রা · বৈধ দিন" />
                    <strong>{format(climate.summary.temperature_mean_valid_days)}<small> {climate.variables.T2M.provider_unit === "C" ? "°C" : climate.variables.T2M.provider_unit}</small></strong>
                    <Duo as="p" en={`${tempCoverage?.valid_days ?? "—"} of ${tempCoverage?.expected_days ?? "—"} days reported`} bn={`${tempCoverage?.valid_days ?? "—"} / ${tempCoverage?.expected_days ?? "—"} দিনের ডেটা পাওয়া গেছে`} />
                  </article>

                  <article className="metric-card feature">
                    <Duo className="metric-label" en="Period precipitation" bn="সময়ের মোট বৃষ্টিপাত" />
                    <strong>
                      {climate.summary.precipitation_total_full_period === null
                        ? "Incomplete"
                        : format(climate.summary.precipitation_total_full_period, 2)}
                      {climate.summary.precipitation_total_full_period !== null && <small> {climate.variables.PRECTOTCORR.provider_unit.replace("/day", "")}</small>}
                    </strong>
                    <Duo as="p" en={`${rainCoverage?.valid_days ?? "—"} of ${rainCoverage?.expected_days ?? "—"} days reported`} bn={`${rainCoverage?.valid_days ?? "—"} / ${rainCoverage?.expected_days ?? "—"} দিনের বৃষ্টিপাত ডেটা`} />
                  </article>

                  <article className="metric-card">
                    <Duo className="metric-label" en="Historical period" bn="ঐতিহাসিক সময়কাল" />
                    <strong className="date-metric">{climate.period.start.slice(0, 4) === climate.period.end.slice(0, 4) ? `Jan–Dec ${climate.period.start.slice(0, 4)}` : `${climate.period.start.slice(0, 7)} – ${climate.period.end.slice(0, 7)}`}</strong>
                    <Duo as="p" en={`Daily records · ${climate.period.time_standard} (local solar time) · NASA POWER`} bn="দৈনিক রেকর্ড · স্থানীয় সৌর সময় · NASA POWER" />
                  </article>
                </div>

                <ClimateExplorer snapshot={climate} />

                <details className="evidence">
                  <summary>
                    <Duo en="View NASA evidence and limitations" bn="NASA প্রমাণ ও সীমাবদ্ধতা দেখুন" />
                    <span aria-hidden="true">↗</span>
                  </summary>
                  <dl>
                    <div><dt><Duo en="Provider" bn="উৎস" /></dt><dd>{climate.evidence.provider}</dd></div>
                    <div><dt><Duo en="Snapshot" bn="স্ন্যাপশট" /></dt><dd>{climate.evidence.snapshot_id}</dd></div>
                    <div><dt><Duo en="Underlying data product" bn="মূল ডেটা উৎস" /></dt><dd>{climate.evidence.source_products.join(", ") || "Not reported"} · reanalysis / পুনর্বিশ্লেষণ; not direct satellite rainfall / সরাসরি স্যাটেলাইটে মাপা বৃষ্টি নয়</dd></div>
                    <div><dt><Duo en="Source kind" bn="ডেটার ধরন" /></dt><dd>{climate.evidence.data_kind}</dd></div>
                    <div><dt><Duo en="Raw SHA-256" bn="র’ SHA-256" /></dt><dd className="hash">{climate.evidence.raw_sha256}</dd></div>
                  </dl>
                  <a href={climate.evidence.source_request_url} target="_blank" rel="noreferrer">
                    <Duo en="View original POWER request" bn="মূল POWER রিকোয়েস্ট দেখুন" /> ↗
                  </a>
                </details>
              </>
            ) : (
              <div className="climate-empty" role="status">
                <span className="empty-orbit" aria-hidden="true"><i /><b /></span>
                <Duo
                  as="div"
                  className="empty-heading"
                  en={climateStatus === "loading" ? "Checking the data pipeline…" : "NASA climate data is not loaded yet"}
                  bn={climateStatus === "loading" ? "ডেটা পাইপলাইন যাচাই হচ্ছে…" : "NASA জলবায়ু ডেটা এখনো লোড হয়নি"}
                />
                <Duo
                  as="p"
                  en={climateStatus === "loading" ? "BoponX is looking for the verified pilot snapshot." : climateMessage}
                  bn={climateStatus === "loading" ? "BoponX যাচাইকৃত পাইলট স্ন্যাপশট খুঁজছে।" : "যাচাইকৃত ডেটা পাওয়া গেলে এই অংশটি স্বয়ংক্রিয়ভাবে সক্রিয় হবে।"}
                />
                <Duo
                  as="p"
                  className="empty-caption"
                  en="No sample climate values are substituted."
                  bn="কোনো নমুনা বা কল্পিত জলবায়ু মান দেখানো হচ্ছে না।"
                />
              </div>
            )}
          </div>
        </section>

        <section className="section farm-section" id="farm" aria-labelledby="farm-heading">
          <div className="section-heading-row">
            <SectionIndex n="02" en="Farm context" bn="খামারের প্রেক্ষাপট" />
            <div className="section-title-block">
              <h2 id="farm-heading">Your farm.<br /><span>Your priorities.</span></h2>
              <p lang="bn">আপনার খামার। আপনার অগ্রাধিকার।</p>
            </div>
            <Duo
              as="p"
              className="section-description"
              en="Record only what you know. Unknown soil characteristics stay unknown; BoponX does not silently invent missing information."
              bn="আপনি যা জানেন শুধু সেটিই দিন। মাটির অজানা তথ্য অজানাই থাকবে; BoponX কোনো অনুপস্থিত তথ্য নিজের মতো করে বানাবে না।"
            />
          </div>

          <div className="farm-layout">
            <form className="farm-form" onSubmit={validateFarm}>
              <div className="form-head">
                <div>
                  <Duo className="form-overline" en="Pilot farm profile" bn="পাইলট খামার প্রোফাইল" />
                  <h3>Tell BoponX what you know. <span lang="bn">যা জানেন, সেটাই বলুন।</span></h3>
                </div>
                <div className="form-badge">BD · 01</div>
              </div>

              <div className="form-grid">
                <label>
                  <Duo en="Regional pilot location" bn="পাইলট অঞ্চল" />
                  <select value={farm.location_id} onChange={(e) => changeFarm("location_id", e.target.value as FarmProfile["location_id"])}>
                    <option value="rajshahi-pilot">Rajshahi · রাজশাহী</option>
                  </select>
                  <span className="form-helper">Provisional regional pilot · <span lang="bn">অস্থায়ী আঞ্চলিক পাইলট</span></span>
                </label>

                <label>
                  <Duo en="Previous crop" bn="আগের ফসল" />
                  <input value={farm.previous_crop ?? ""} onChange={(e) => changeFarm("previous_crop", e.target.value || null)} placeholder="Unknown · অজানা" maxLength={80} />
                </label>

                <label>
                  <Duo en="Known soil pH" bn="জানা মাটির pH" />
                  <input type="number" min="0" max="14" step="0.1" value={farm.soil_ph ?? ""} onChange={(e) => changeFarm("soil_ph", e.target.value === "" ? null : Number(e.target.value))} placeholder="Unknown · অজানা" />
                </label>

                <label>
                  <Duo en="Soil texture" bn="মাটির ধরন" />
                  <select value={farm.soil_texture} onChange={(e) => changeFarm("soil_texture", e.target.value as FarmProfile["soil_texture"])}>
                    {Object.entries(soilLabels).map(([value, labels]) => <option key={value} value={value}>{labels.en} · {labels.bn}</option>)}
                  </select>
                </label>

                <label>
                  <Duo en="Irrigation availability" bn="সেচ সুবিধা" />
                  <select value={farm.irrigation_mode} onChange={(e) => changeFarm("irrigation_mode", e.target.value as FarmProfile["irrigation_mode"])}>
                    {Object.entries(irrigationLabels).map(([value, labels]) => <option key={value} value={value}>{labels.en} · {labels.bn}</option>)}
                  </select>
                </label>

                <label>
                  <Duo en="Primary planning priority" bn="প্রধান পরিকল্পনা অগ্রাধিকার" />
                  <select value={farm.priorities[0] ?? ""} onChange={(e) => changeFarm("priorities", e.target.value ? [e.target.value as FarmProfile["priorities"][number]] : [])}>
                    <option value="">Choose · নির্বাচন করুন</option>
                    {Object.entries(priorityLabels).map(([value, labels]) => <option value={value} key={value}>{labels.en} · {labels.bn}</option>)}
                  </select>
                </label>
              </div>

              <div className="plan-inputs">
                <div className="plan-inputs__headline">
                  <strong>Build my printable 3-month brief</strong>
                  <span lang="bn">আমার তিন মাসের প্রিন্টযোগ্য প্রস্তুতি নোট তৈরি করুন</span>
                </div>
                <div className="plan-inputs__grid">
                  <label>
                    <Duo en="Start month" bn="শুরুর মাস" />
                    <select value={startMonth} onChange={(e)=>{setStartMonth(Number(e.target.value));setBrief(null)}}>
                      {planningMonths.map((month,index)=><option value={index+1} key={month.en}>{month.en} · {month.bn}</option>)}
                    </select>
                  </label>
                  <label>
                    <Duo en="Start year" bn="শুরুর বছর" />
                    <select value={startYear} onChange={(e)=>{setStartYear(Number(e.target.value));setBrief(null)}}>
                      {Array.from({length:10},(_,i)=>2026+i).map(year=><option value={year} key={year}>{year}</option>)}
                    </select>
                  </label>
                  <label className="plan-inputs__candidate">
                    <Duo en="Crop you are considering (optional; not a BoponX recommendation)" bn="আপনি যে ফসলের কথা ভাবছেন (ঐচ্ছিক; BoponX-এর সুপারিশ নয়)" />
                    <input type="text" maxLength={80} value={candidateCrop} onChange={(e)=>{setCandidateCrop(e.target.value);setBrief(null)}} placeholder="Your own crop idea · আপনার ভাবনায় ফসল" />
                  </label>
                </div>
              </div>

              <Duo
                as="p"
                className="form-privacy"
                en="Your inputs produce a printable three-month preparation brief. No account is created, and this form does not save your farm profile. It does not select crops or planting dates."
                bn="আপনার তথ্য থেকে প্রিন্টযোগ্য তিন মাসের প্রস্তুতি নোট তৈরি হবে। কোনো অ্যাকাউন্ট তৈরি বা খামারের তথ্য সংরক্ষণ করা হয় না। এটি ফসল বা বপনের তারিখ নির্ধারণ করে না।"
              />

              <button className="button primary submit-button" type="submit" disabled={farmBusy}>
                <Duo en={farmBusy ? "Preparing your brief…" : "Generate my 3-month brief"} bn={farmBusy ? "প্রস্তুতি নোট তৈরি হচ্ছে…" : "আমার তিন মাসের নোট তৈরি করুন"} />
                <span aria-hidden="true">↗</span>
              </button>

              {farmError && (
                <div className="form-feedback error" role="alert">
                  <Duo en={farmError} bn="খামারের তথ্য যাচাই করা যায়নি।" />
                </div>
              )}

              {farmResult && (
                <div className="form-feedback success" role="status">
                  <Duo as="div" className="feedback-title" en="Farm inputs recorded for validation." bn="খামারের তথ্য যাচাইয়ের জন্য গ্রহণ করা হয়েছে।" />
                  <Duo
                    as="p"
                    en={farmResult.missing_inputs.length ? `Still unknown: ${farmResult.missing_inputs.join(", ").replaceAll("_", " ")}.` : "All requested fields are supplied."}
                    bn={farmResult.missing_inputs.length ? `অজানা: ${farmResult.missing_inputs.map(x=>({
                      previous_crop:"আগের ফসল",soil_ph:"মাটির pH",
                      soil_texture:"মাটির ধরন",irrigation_mode:"সেচ সুবিধা",priorities:"অগ্রাধিকার",
                    }[x] ?? x)).join(" · ")}।` : "চাওয়া সব তথ্য দেওয়া হয়েছে।"}
                  />
                </div>
              )}
            </form>

            <aside className="planning-aside">
              <div className="planning-topline"><span>03</span><Duo en="Your next steps" bn="আপনার পরবর্তী পদক্ষেপ" /></div>
              <div className="three-season">
                <span>01</span><i /><span>02</span><i /><span>03</span>
              </div>
              <h3>Start with<br /><em>3 months.</em></h3>
              <p lang="bn" className="aside-bn">শুরু করুন পরবর্তী ৩ মাসের প্রস্তুতি দিয়ে।</p>
              <Duo
                as="p"
                en="Submit your farm details for a printable, bilingual field-preparation checklist and 2024 NASA historical context. Reviewed crop-rotation advice is a separate development gate."
                bn="আপনার তথ্য দিন, প্রিন্টযোগ্য বাংলা-ইংরেজি প্রস্তুতি তালিকা ও ২০২৪ সালের NASA ঐতিহাসিক তথ্য পান। ফসল আবর্তন পরামর্শ আলাদা গবেষণা-যাচাইয়ের কাজ।"
              />
              <div className="aside-state"><span className="status-dot" aria-hidden="true" /><Duo en="Printable brief available · crop rules pending" bn="প্রস্তুতি নোট প্রস্তুত · ফসলের নিয়ম যাচাই বাকি" /></div>
              <Duo as="p" className="aside-footnote" en="No fictional yield, soil-health score or water-saving estimate is shown." bn="কোনো কল্পিত ফলন, মাটির স্বাস্থ্য স্কোর বা পানি সাশ্রয়ের অনুমান দেখানো হয় না।" />
            </aside>
          </div>
        </section>

        {brief && <FarmReport brief={brief} />}

        <section className="manifesto">
          <div className="manifesto-flag" aria-hidden="true"><span /></div>
          <div>
            <Duo className="manifesto-kicker" en="Built in Bangladesh · engineered for trust" bn="বাংলাদেশে নির্মিত · বিশ্বাসের জন্য প্রকৌশল" />
            <h2>Local roots.<br /><span>Orbital perspective.</span></h2>
            <p lang="bn">স্থানীয় শিকড়। মহাকাশের দৃষ্টিভঙ্গি।</p>
          </div>
          <Duo
            as="p"
            className="manifesto-copy"
            en="BoponX is designed by Team EARTH.exe to make NASA environmental evidence understandable and traceable; agricultural choices remain with farmers and their local advisers."
            bn="Team EARTH.exe-এর BoponX NASA পরিবেশগত তথ্য সহজবোধ্য ও যাচাইযোগ্য করে। কৃষি সিদ্ধান্ত নেবেন কৃষক ও তাঁদের স্থানীয় পরামর্শক।"
          />
        </section>
      </main>

      <footer>
        <div className="footer-brand">
          <b>Bopon<span>X</span></b>
          <Duo en="From Space to Soil" bn="মহাকাশ থেকে মাটিতে" />
        </div>
        <div><Duo en="By Team EARTH.exe · Bangladesh · 2026" bn="Team EARTH.exe · বাংলাদেশ · ২০২৬" /></div>
        <a href="https://power.larc.nasa.gov/docs/services/api/temporal/daily/" target="_blank" rel="noreferrer">
          <Duo en="NASA POWER documentation" bn="NASA POWER ডকুমেন্টেশন" /> ↗
        </a>
      </footer>
    </div>
  );
}
