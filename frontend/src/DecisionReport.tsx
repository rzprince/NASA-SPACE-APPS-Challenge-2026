import type { PlanBrief } from "./api";

function metric(value: number | null | undefined, suffix = "") {
  if (value === null || value === undefined || !Number.isFinite(value)) return "Not available";
  return `${new Intl.NumberFormat("en", { maximumFractionDigits: 1 }).format(value)}${suffix}`;
}

export default function DecisionReport({ brief, placeName }: { brief: PlanBrief; placeName: string }) {
  const advice = brief.decision_advice;
  const months = Array.isArray(brief.months) ? brief.months : [];
  const recent = brief.recent_environment?.status === "available" ? brief.recent_environment.summary : undefined;

  function printPlan() {
    const previous = document.title;
    document.title = "BoponX Farmer Action Card";
    window.print();
    window.setTimeout(() => (document.title = previous), 250);
  }

  return (
    <section className="field-plan-shell">
      <header className="plan-console-head no-print">
        <div>
          <span>FIELD PLAN | READY</span>
          <strong>{placeName}</strong>
        </div>
        <button onClick={printPlan}>Print Farmer Action Card</button>
      </header>

      <div className="farmer-action-card">
        <header className="action-card-head">
          <div className="action-brand">
            <span className="action-mark">BX</span>
            <div><strong>BoponX</strong><small>From Space to Soil</small></div>
          </div>
          <div className="action-field">
            <span>FIELD</span>
            <strong>{placeName}</strong>
            <small>{brief.location.coordinates.latitude.toFixed(4)}°, {brief.location.coordinates.longitude.toFixed(4)}°</small>
          </div>
        </header>

        <section className="action-decision">
          <span className="action-label">WHAT BOPONX SEES</span>
          <h1>{advice?.verdict ?? "Your field evidence is ready for review."}</h1>
          <p>{advice?.better_next_step ?? "Review the three month actions before the next seasonal decision."}</p>
          <div className="action-signal-row">
            <div><span>RAIN</span><strong>{brief.conditions?.rain_signal?.replaceAll("_", " ") ?? "unknown"}</strong></div>
            <div><span>TEMP</span><strong>{brief.conditions?.temperature_signal?.replaceAll("_", " ") ?? "unknown"}</strong></div>
            <div><span>RECENT RAIN</span><strong>{metric(recent?.precipitation_total_mm, " mm")}</strong></div>
            <div><span>RECENT TEMP</span><strong>{metric(recent?.temperature_mean_c, "°C")}</strong></div>
          </div>
        </section>

        <section className="action-months">
          {months.map((month) => (
            <article key={month.planning_month}>
              <header>
                <span>MONTH {month.index}</span>
                <strong>{month.month_name.en}</strong>
                <small>{month.phase.en}</small>
              </header>
              <p>{month.objective.en}</p>
              <ol>
                {month.tasks.slice(0, 5).map((task) => <li key={task.code}>{task.en}</li>)}
              </ol>
            </article>
          ))}
        </section>

        <section className="action-evidence">
          <div>
            <span className="action-label">EVIDENCE USED</span>
            <p>NASA POWER recent agroclimate and historical baseline</p>
            <p>GPM IMERG recent precipitation layer</p>
            <p>SMAP surface soil moisture layer</p>
            <p>{brief.evidence.calendar_evidence.length ? "Bangladesh official crop weather calendar evidence" : "FAO or verified local source review required"}</p>
            <p>Farmer crop history, water, drainage, soil test status and priority</p>
          </div>
          <div>
            <span className="action-label">IMPORTANT</span>
            <p>{brief.limitations.en}</p>
            <p>No NASA product is treated as field pH, nutrient chemistry or a crop prescription.</p>
          </div>
        </section>

        <footer className="action-footer">
          <strong>Team EARTH.exe</strong>
          <span>NASA Space Apps Challenge 2026 | Field Shift</span>
          <small>Independent project. NASA does not endorse BoponX.</small>
        </footer>
      </div>
    </section>
  );
}
