import { useEffect, useMemo, useState, type FormEvent } from "react";
import {
  ApiError,
  apiGet,
  apiPost,
  type ClimateDay,
  type ClimateSnapshot,
  type FarmProfile,
  type FarmValidation,
  type Location,
  type Status,
} from "./api";

const initialFarm: FarmProfile = {
  location_id: "rajshahi-pilot",
  previous_crop: null,
  soil_ph: null,
  soil_texture: "unknown",
  irrigation_mode: "unknown",
  priorities: [],
};

const priorityLabels: Record<FarmProfile["priorities"][number], string> = {
  water: "Reduce water-related exposure",
  soil: "Protect soil over time",
  production_stability: "Prioritize production stability",
};

function format(value: number, digits = 1): string {
  return new Intl.NumberFormat("en-BD", { maximumFractionDigits: digits }).format(value);
}

function temperatureSegments(days: ClimateDay[]): string[] {
  const numbers = days.flatMap((day) => (day.T2M === null ? [] : [day.T2M]));
  if (!numbers.length) return [];
  const low = Math.min(...numbers);
  const high = Math.max(...numbers);
  const span = high - low || 1;
  const segments: string[] = [];
  let current: string[] = [];
  days.forEach((day, index) => {
    if (day.T2M === null) {
      if (current.length) segments.push(current.join(" "));
      current = [];
      return;
    }
    const x = 18 + (index / Math.max(days.length - 1, 1)) * 604;
    const y = 150 - ((day.T2M - low) / span) * 122;
    current.push(`${x.toFixed(1)},${y.toFixed(1)}`);
  });
  if (current.length) segments.push(current.join(" "));
  return segments;
}

function StatusTag({ status }: { status: Status }) {
  const label =
    status === "ready" ? "NASA dataset validated" :
    status === "loading" ? "Checking data availability" : "Dataset not loaded";
  return <span className={`status-pill ${status}`}><span aria-hidden="true" className="status-dot" />{label}</span>;
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
        setClimateMessage(
          error instanceof ApiError ? error.message : "Climate data could not be loaded.",
        );
      });
    return () => { active = false; };
  }, []);

  const chartSegments = useMemo(() => temperatureSegments(climate?.daily ?? []), [climate]);
  const location = locations.find((item) => item.id === farm.location_id);
  const rainCoverage = climate?.summary.coverage.PRECTOTCORR;
  const tempCoverage = climate?.summary.coverage.T2M;

  function changeFarm<K extends keyof FarmProfile>(key: K, value: FarmProfile[K]) {
    setFarm((current) => ({ ...current, [key]: value }));
    setFarmResult(null);
    setFarmError("");
  }

  async function validateFarm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFarmBusy(true);
    setFarmError("");
    setFarmResult(null);
    try {
      setFarmResult(await apiPost<FarmValidation>("/api/v1/farms/validate", farm));
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
          <span className="brand-mark" aria-hidden="true">B<span>x</span></span>
          <span>Bopon<span className="brand-x">X</span></span>
        </a>
        <nav aria-label="Primary">
          <a href="#climate">NASA data</a>
          <a href="#farm">Farm setup</a>
          <a className="nav-github" href="https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026" target="_blank" rel="noreferrer">
            Source code <span aria-hidden="true">↗</span>
          </a>
        </nav>
      </header>

      <main id="top">
        <section className="hero">
          <div className="hero-copy">
            <div className="eyebrow"><span className="eyebrow-line" /> AN EARTH.exe INITIATIVE · NASA SPACE APPS 2026</div>
            <h1>From <span>Space</span><br />to Soil.</h1>
            <p className="hero-lead">Better farming decisions begin with evidence. BoponX connects NASA environmental data with the farm information farmers know.</p>
            <p className="hero-note">বপন (Bopon) means sowing. X reflects our space-powered approach.</p>
            <div className="hero-actions">
              <a className="button primary" href="#climate">Explore NASA climate data <span aria-hidden="true">↗</span></a>
              <a className="button secondary" href="#farm">Set up a pilot farm <span aria-hidden="true">↓</span></a>
            </div>
            <div className="hero-meta"><StatusTag status={climateStatus} /><span>{apiOnline === false ? "API disconnected" : "Regional pilot · Rajshahi, Bangladesh"}</span></div>
          </div>
          <div className="hero-visual" aria-label="Stylized Earth observation graphic with satellite and farmland layers">
            <div className="orb orb-outer" /><div className="orb orb-middle" /><div className="orb orb-inner" />
            <div className="orbit-label top-label">EARTH OBSERVATION <span>01 / 03</span></div>
            <div className="visual-satellite" aria-hidden="true">✳</div>
            <div className="visual-land" aria-hidden="true"><i /><i /><i /><i /><i /></div>
            <div className="orbit-label bottom-label">NASA DATA <span>→</span> LOCAL DECISIONS</div>
          </div>
        </section>

        <section className="section climate-section" id="climate" aria-labelledby="climate-heading">
          <div className="section-intro">
            <div><p className="section-kicker">01 / ENVIRONMENTAL CONTEXT</p><h2 id="climate-heading">See the climate.<br /><span>See the evidence.</span></h2></div>
            <p>Our first pilot uses the NASA POWER daily service for a regional reference point. These are historical environmental estimates, not field measurements or forecasts.</p>
          </div>
          <div className="climate-frame">
            <div className="frame-top">
              <div><span className="frame-label">SELECTED REGION</span><strong>{location?.name ?? "Rajshahi regional pilot"}</strong><span className="subline">{location ? `${location.latitude}° N · ${location.longitude}° E` : "24.37° N · 88.60° E"} · provisional reference point</span></div>
              <StatusTag status={climateStatus} />
            </div>

            {climate ? (
              <>
                <div className="metric-grid">
                  <div className="metric-card"><span>MEAN TEMPERATURE · VALID DAYS</span><strong>{format(climate.summary.temperature_mean_valid_days)}<small> {climate.variables.T2M.provider_unit}</small></strong><p>{tempCoverage?.valid_days ?? "—"} of {tempCoverage?.expected_days ?? "—"} days reported</p></div>
                  <div className="metric-card"><span>PERIOD PRECIPITATION</span><strong>{climate.summary.precipitation_total_full_period === null ? "Incomplete" : format(climate.summary.precipitation_total_full_period, 2)}{climate.summary.precipitation_total_full_period !== null && <small> {climate.variables.PRECTOTCORR.provider_unit.replace("/day", "")}</small>}</strong><p>{rainCoverage?.valid_days ?? "—"} of {rainCoverage?.expected_days ?? "—"} days reported; full-period total requires complete coverage</p></div>
                  <div className="metric-card"><span>HISTORICAL PERIOD</span><strong className="date-metric">{climate.period.start.slice(0, 4)}<small> → </small>{climate.period.end.slice(0, 4)}</strong><p>Daily records · {climate.period.time_standard} · NASA POWER</p></div>
                </div>
                <div className="chart-card"><div className="chart-heading"><div><span className="frame-label">DAILY HISTORICAL SERIES</span><h3>Near-surface temperature</h3></div><span className="chart-key"><i /> {climate.variables.T2M.provider_unit}</span></div>
                  {chartSegments.length ? (
                    <svg viewBox="0 0 640 180" role="img" aria-label="NASA POWER historical daily temperature; missing readings are shown as breaks" className="data-chart">
                      {[28, 89, 150].map((y) => <line key={y} x1="18" x2="622" y1={y} y2={y} className="gridline" />)}
                      {chartSegments.map((points, index) => <polyline key={index} points={points} className="data-line" />)}
                    </svg>
                  ) : <p className="empty-text">No valid temperature series is available.</p>}
                  <div className="chart-axis"><span>{climate.period.start}</span><span>Gaps are not interpolated</span><span>{climate.period.end}</span></div>
                </div>
                <details className="evidence"><summary>View NASA evidence and limitations <span aria-hidden="true">↗</span></summary>
                  <dl><div><dt>Provider</dt><dd>{climate.evidence.provider}</dd></div><div><dt>Snapshot</dt><dd>{climate.evidence.snapshot_id}</dd></div><div><dt>Source kind</dt><dd>{climate.evidence.data_kind}</dd></div><div><dt>Raw SHA-256</dt><dd className="hash">{climate.evidence.raw_sha256}</dd></div></dl>
                  <a href={climate.evidence.source_request_url} target="_blank" rel="noreferrer">View original POWER request ↗</a>
                </details>
              </>
            ) : (
              <div className="climate-empty" role="status"><span className="empty-icon" aria-hidden="true">⌁</span><h3>{climateStatus === "loading" ? "Checking the data pipeline…" : "NASA climate data is not loaded yet"}</h3><p>{climateStatus === "loading" ? "The app is looking for the verified pilot snapshot." : climateMessage}</p><p className="empty-caption">No sample climate values are substituted. After the NASA POWER acquisition runs successfully, this screen will display the validated observations.</p></div>
            )}
          </div>
        </section>

        <section className="section farm-section" id="farm" aria-labelledby="farm-heading">
          <div className="section-intro"><div><p className="section-kicker">02 / FARM CONTEXT</p><h2 id="farm-heading">Your farm.<br /><span>Your priorities.</span></h2></div><p>Record the information you know. Unknown soil characteristics stay unknown; BoponX never invents missing inputs.</p></div>
          <div className="farm-layout">
            <form className="farm-form" onSubmit={validateFarm}>
              <div className="form-grid">
                <label>Regional pilot location<select value={farm.location_id} onChange={(e) => changeFarm("location_id", e.target.value as FarmProfile["location_id"])}><option value="rajshahi-pilot">Rajshahi regional pilot</option></select></label>
                <label>Previous crop <span>(farmer-provided)</span><input value={farm.previous_crop ?? ""} onChange={(e) => changeFarm("previous_crop", e.target.value || null)} placeholder="Leave blank if unknown" maxLength={80} /></label>
                <label>Known soil pH <span>(optional)</span><input type="number" min="0" max="14" step="0.1" value={farm.soil_ph ?? ""} onChange={(e) => changeFarm("soil_ph", e.target.value === "" ? null : Number(e.target.value))} placeholder="Unknown" /></label>
                <label>Soil texture<select value={farm.soil_texture} onChange={(e) => changeFarm("soil_texture", e.target.value as FarmProfile["soil_texture"])}><option value="unknown">Unknown / not tested</option><option value="sandy">Sandy</option><option value="loamy">Loamy</option><option value="clayey">Clayey</option></select></label>
                <label>Irrigation availability<select value={farm.irrigation_mode} onChange={(e) => changeFarm("irrigation_mode", e.target.value as FarmProfile["irrigation_mode"])}><option value="unknown">Unknown</option><option value="none">No irrigation</option><option value="limited">Limited irrigation</option><option value="reliable">Reliable irrigation</option></select></label>
                <label>Primary planning priority<select value={farm.priorities[0] ?? ""} onChange={(e) => changeFarm("priorities", e.target.value ? [e.target.value as FarmProfile["priorities"][number]] : [])}><option value="">Choose a priority</option>{Object.entries(priorityLabels).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
              </div>
              <p className="form-privacy">This step validates your inputs with the API. It does not create an account or save a farm profile.</p>
              <button className="button primary submit-button" type="submit" disabled={farmBusy}>{farmBusy ? "Validating…" : "Validate farm inputs"} <span aria-hidden="true">↗</span></button>
              {farmError && <p className="form-feedback error" role="alert">{farmError}</p>}
              {farmResult && <div className="form-feedback" role="status"><strong>Farm inputs recorded for validation.</strong><p>{farmResult.missing_inputs.length ? `Still unknown: ${farmResult.missing_inputs.join(", ").replaceAll("_", " ")}.` : "All requested fields are supplied."} Values have not been independently verified.</p></div>}
            </form>
            <aside className="planning-aside"><p className="section-kicker">03 / NEXT DEVELOPMENT GATE</p><h3>Plan the next<br />3 seasons.</h3><p>Crop-rotation comparisons will unlock after local crop profiles, calendars and soil constraints are source-reviewed.</p><div className="aside-state"><span className="status-dot" aria-hidden="true" /> AGRONOMIC RULE REVIEW PENDING</div><p className="aside-footnote">No fictional yield, soil-health score or water-saving estimate is shown.</p></aside>
          </div>
        </section>
        <section className="bottom-callout"><span>EARTH.exe / BANGLADESH</span><h2>Built for decisions.<br /><em>Grounded in evidence.</em></h2><p>Prototype milestone 02 · NASA Space Apps Challenge 2026 · Field Shift: Adapting Farms with NASA Data</p></section>
      </main>
      <footer><span>Bopon<span className="brand-x">X</span> · From Space to Soil</span><span>By Team EARTH.exe · 2026</span><a href="https://power.larc.nasa.gov/docs/services/api/temporal/daily/" target="_blank" rel="noreferrer">NASA POWER documentation ↗</a></footer>
    </div>
  );
}
