import FieldIcon, { type IconName } from "./FieldIcon";
import type { PlanBrief, PlanTask } from "./api";

function metric(value: number | null | undefined, suffix = "") {
  if (value === null || value === undefined || !Number.isFinite(value)) return "Not available";
  return `${new Intl.NumberFormat("en", { maximumFractionDigits: 1 }).format(value)}${suffix}`;
}

function taskIcon(task: PlanTask): IconName {
  const category = task.category ?? "";
  if (category.includes("soil")) return "soil";
  if (category.includes("water") || category.includes("rain") || category.includes("condition")) return "water";
  if (category.includes("decision")) return "check";
  if (category.includes("history")) return "other";
  if (category.includes("intention")) return "stability";
  if (category.includes("local")) return "other";
  if (category.includes("monitor")) return "stability";
  if (category.includes("nasa")) return "rain";
  return "check";
}

export default function DecisionReport({ brief, placeName }: { brief: PlanBrief; placeName: string }) {
  const advice = brief.decision_advice;
  const months = Array.isArray(brief.months) ? brief.months : [];
  const recent = brief.recent_environment?.status === "available" ? brief.recent_environment.summary : undefined;
  const isBangladesh =
    brief.evidence.agricultural_sources.some((source) =>
      source.name.toLowerCase().includes("bangladesh") ||
      source.name.toLowerCase().includes("bamis") ||
      source.name.toLowerCase().includes("agriculture information service"),
    );

  function printPlan() {
    const previous = document.title;
    document.title = `BoponX Field Plan | ${placeName}`;
    window.print();
    window.setTimeout(() => (document.title = previous), 250);
  }

  return (
    <section className="field-plan-shell">
      <header className="plan-console-head no-print">
        <div>
          <span>FIELD PLAN READY</span>
          <strong>{placeName}</strong>
        </div>
        <button onClick={printPlan}>Print or save field plan</button>
      </header>

      <div className="farmer-action-card premium-plan">
        <header className="action-card-head premium">
          <div className="action-brand">
            <span className="action-mark">BX</span>
            <div>
              <strong>BoponX</strong>
              <small>NASA Data → Farm Analysis → Rotation Scenarios → Explainable Decision Support</small>
            </div>
          </div>
          <div className="action-field">
            <span>SELECTED FIELD</span>
            <strong>{placeName}</strong>
            <small>{brief.location.coordinates.latitude.toFixed(4)}° N · {brief.location.coordinates.longitude.toFixed(4)}° E</small>
          </div>
        </header>

        <section className="plan-hero-grid">
          <div className="action-decision premium">
            <span className="action-label">DECISION MESSAGE</span>
            <h1>{advice?.verdict ?? "Your field evidence is ready for review."}</h1>
            <p>{advice?.better_next_step ?? "Review the three month actions before the next seasonal decision."}</p>
            <div className="decision-boundary">
              <FieldIcon name="stability" />
              <span>Decision support, not an automatic crop prescription. Local agronomic evidence stays visible beside NASA context.</span>
            </div>
          </div>

          <aside className="field-signal-board">
            <div className="signal-board-title">
              <span>FIELD SIGNALS</span>
              <strong>What changed around this field</strong>
            </div>
            <div className="signal-board-grid">
              <article>
                <FieldIcon name="rain" />
                <span>Recent rain</span>
                <strong>{metric(recent?.precipitation_total_mm, " mm")}</strong>
              </article>
              <article>
                <FieldIcon name="stability" />
                <span>Recent mean temperature</span>
                <strong>{metric(recent?.temperature_mean_c, "°C")}</strong>
              </article>
              <article>
                <FieldIcon name="water" />
                <span>Rain signal</span>
                <strong>{brief.conditions?.rain_signal?.replaceAll("_", " ") ?? "unknown"}</strong>
              </article>
              <article>
                <FieldIcon name="soil" />
                <span>Temperature signal</span>
                <strong>{brief.conditions?.temperature_signal?.replaceAll("_", " ") ?? "unknown"}</strong>
              </article>
            </div>
          </aside>
        </section>

        {advice?.reasons?.length ? (
          <section className="why-panel">
            <div>
              <span className="action-label">WHY BOPONX SAYS THIS</span>
              <strong>Evidence behind the advice</strong>
            </div>
            <ul>
              {advice.reasons.slice(0, 5).map((reason, index) => (
                <li key={index}><span>{String(index + 1).padStart(2, "0")}</span>{reason}</li>
              ))}
            </ul>
          </section>
        ) : null}

        <section className="action-months premium">
          {months.map((month) => (
            <article key={month.planning_month}>
              <header>
                <div className="month-number">{String(month.index).padStart(2, "0")}</div>
                <div>
                  <span>{month.planning_month}</span>
                  <strong>{month.month_name.en}</strong>
                  <small>{month.phase.en}</small>
                </div>
              </header>

              <div className="month-objective-box">
                <span>THIS MONTH'S JOB</span>
                <p>{month.objective.en}</p>
              </div>

              {month.context?.baseline && (
                <div className="month-climate-ribbon">
                  <span>Historical NASA POWER reference</span>
                  <strong>
                    {metric(month.context.baseline.temperature_mean_c, "°C")}
                    {" · "}
                    {metric(month.context.baseline.precipitation_mean_daily_mm, " mm/day")}
                  </strong>
                </div>
              )}

              <div className="visual-task-list">
                {month.tasks.slice(0, 5).map((task) => (
                  <div className="visual-task" key={task.code}>
                    <span className="visual-task-icon"><FieldIcon name={taskIcon(task)} /></span>
                    <div>
                      <strong>{task.en}</strong>
                      {task.reason && <small>{task.reason}</small>}
                    </div>
                  </div>
                ))}
              </div>
            </article>
          ))}
        </section>

        <section className="farmer-support-strip">
          <div>
            <span className="action-label">LOCAL SUPPORT</span>
            <strong>{isBangladesh ? "Bangladesh Agriculture Call Center: 16123" : "Use the local extension or agriculture authority shown in BoponX."}</strong>
            <p>
              {isBangladesh
                ? "The printed plan does not require a clickable website. A farmer or family member can call 16123 or take this card to the local agriculture extension office."
                : "The printed plan is designed to work without clicking a link. Source names are written below so an adviser can verify the evidence."}
            </p>
          </div>
          <div className="support-symbol"><FieldIcon name="check" /></div>
        </section>

        <section className="action-evidence premium">
          <div>
            <span className="action-label">NASA EVIDENCE USED</span>
            <div className="evidence-name-grid">
              <p><b>NASA POWER Daily</b><span>Recent agroclimate context</span></p>
              <p><b>NASA POWER Climatology</b><span>Monthly historical reference</span></p>
              <p><b>GPM IMERG</b><span>Recent precipitation spatial evidence</span></p>
              <p><b>SMAP</b><span>Regional surface soil moisture context</span></p>
            </div>
          </div>
          <div>
            <span className="action-label">LOCAL EVIDENCE USED</span>
            <div className="evidence-name-grid">
              {brief.evidence.agricultural_sources.slice(0, 5).map((source) => (
                <p key={source.name}><b>{source.name}</b><span>{source.scope}</span></p>
              ))}
              {brief.evidence.agricultural_sources.length === 0 && (
                <p><b>Local source review needed</b><span>No reviewed national adapter was available for this field.</span></p>
              )}
            </div>
          </div>
        </section>

        <section className="plan-limitations">
          <FieldIcon name="unknown" />
          <div>
            <span className="action-label">IMPORTANT BOUNDARY</span>
            <p>{brief.limitations.en}</p>
            <p>NASA satellite and gridded products are not treated as field pH, nutrient chemistry, a field rain gauge, or a guaranteed crop outcome.</p>
          </div>
        </section>

        <footer className="action-footer premium">
          <strong>Team EARTH.exe · BoponX</strong>
          <span>From Space to Soil</span>
          <small>Independent NASA Space Apps Challenge 2026 project. NASA does not endorse BoponX.</small>
        </footer>
      </div>
    </section>
  );
}
