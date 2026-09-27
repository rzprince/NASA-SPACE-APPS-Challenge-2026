import type { PlanBrief } from "./api";

function metric(value: number | null | undefined, suffix: string) {
  if (value === null || value === undefined) return "Not available";
  return `${new Intl.NumberFormat("en-BD", { maximumFractionDigits: 1 }).format(value)}${suffix}`;
}

export default function DecisionReport({ brief }: { brief: PlanBrief }) {
  const recent = brief.recent_environment;
  const baseline = brief.historical_baseline;

  function printBrief() {
    const previous = document.title;
    document.title = "BoponX field brief";
    window.print();
    window.setTimeout(() => {
      document.title = previous;
    }, 300);
  }

  return (
    <section className="field-brief-section bx-section" id="field-brief">
      <div className="brief-screen" data-reveal>
        <div className="brief-screen-bar no-print">
          <div>
            <span className="brief-status-dot" />
            <span>FIELD BRIEF READY</span>
          </div>
          <button type="button" onClick={printBrief}>Print or save PDF ↗</button>
        </div>

        <header className="brief-hero">
          <div>
            <p className="section-kicker">The next 90 days</p>
            <h2>Three months. Three different jobs.</h2>
          </div>

          <div className="brief-place">
            <span>{brief.location.region_name_en}</span>
            <strong>Field decision brief</strong>
            <small>{brief.location.coordinates.latitude.toFixed(4)}° N | {brief.location.coordinates.longitude.toFixed(4)}° E</small>
          </div>
        </header>

        <div className="brief-evidence-strip">
          <div>
            <span>Recent temperature</span>
            <strong>{metric(recent?.summary?.temperature_mean_c, "°C")}</strong>
            <small>{recent?.period ? `${recent.period.start} to ${recent.period.end}` : "Recent NASA POWER data unavailable"}</small>
          </div>

          <div>
            <span>Recent rainfall</span>
            <strong>{metric(recent?.summary?.precipitation_total_mm, " mm")}</strong>
            <small>NASA POWER regional climate context</small>
          </div>

          <div>
            <span>Planning month baseline</span>
            <strong>{metric(baseline?.summary?.temperature_mean_c, "°C")}</strong>
            <small>{baseline?.baseline_period ? `${baseline.baseline_period.start_year} to ${baseline.baseline_period.end_year}` : "Historical baseline unavailable"}</small>
          </div>

          <div>
            <span>Local calendar sources</span>
            <strong>{brief.evidence.calendar_evidence.length}</strong>
            <small>BAMIS | {brief.location.region_name_en}</small>
          </div>
        </div>

        <div className="brief-timeline">
          {brief.months.map((month, index) => (
            <article className="brief-month" key={month.planning_month}>
              <div className="month-rail">
                <span>{String(month.index).padStart(2, "0")}</span>
                {index < brief.months.length - 1 && <i />}
              </div>

              <div className="month-content">
                <div className="month-title-row">
                  <div>
                    <small>{month.planning_month}</small>
                    <h3>{month.phase.en}</h3>
                  </div>
                  <span className="month-name">{month.month_name.en}</span>
                </div>

                <p className="month-objective">{month.objective.en}</p>

                <div className="month-task-grid">
                  {month.tasks.map((task, taskIndex) => (
                    <div className="brief-task" key={task.code}>
                      <span>{String(taskIndex + 1).padStart(2, "0")}</span>
                      <div><strong>{task.en}</strong></div>
                    </div>
                  ))}
                </div>

                <div className="field-notes-lines">
                  <span>Farmer or adviser notes</span>
                  <i /><i />
                </div>
              </div>
            </article>
          ))}
        </div>

        <div className="rotation-lock-panel">
          <div className="rotation-lock-icon"><span>↻</span><i /></div>
          <div>
            <p className="section-kicker">Three season rotation explorer</p>
            <h3>The evidence review is still active.</h3>
            <p>{brief.rotation_explorer.message_en}</p>
          </div>
          <span className="lock-chip">NOT YET PRESCRIPTIVE</span>
        </div>

        <div className="brief-source-columns">
          <div>
            <span className="brief-source-title">NASA evidence</span>
            {brief.evidence.nasa_sources.map((source) => (
              <a href={source.source_url} target="_blank" rel="noreferrer" key={source.id}>
                <strong>{source.name}</strong>
                <small>{source.role.replaceAll("_", " ")}</small>
              </a>
            ))}
          </div>

          <div>
            <span className="brief-source-title">Local evidence</span>
            {brief.evidence.calendar_evidence.slice(0, 8).map((crop) => (
              <a href={crop.source_url} target="_blank" rel="noreferrer" key={crop.id}>
                <strong>{crop.name_en}</strong>
                <small>BAMIS calendar source | not a recommendation</small>
              </a>
            ))}
          </div>
        </div>

        <footer className="brief-footer">
          <p>{brief.limitations.en}</p>
          <span>BoponX | Team EARTH.exe | Bangladesh</span>
        </footer>
      </div>
    </section>
  );
}
