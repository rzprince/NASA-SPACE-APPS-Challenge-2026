import type { CalendarEvidence, NasaSource, PlanBrief, PlanMonth } from "./api";

function metric(value: number | null | undefined, suffix: string) {
  if (value === null || value === undefined || !Number.isFinite(value)) return "Not available";
  return `${new Intl.NumberFormat("en-BD", { maximumFractionDigits: 1 }).format(value)}${suffix}`;
}

function safeArray<T>(value: T[] | null | undefined): T[] {
  return Array.isArray(value) ? value : [];
}

export default function DecisionReport({ brief }: { brief: PlanBrief }) {
  const recent = brief?.recent_environment ?? null;
  const baseline = brief?.historical_baseline ?? null;
  const months = safeArray<PlanMonth>(brief?.months);
  const nasaSources = safeArray<NasaSource>(brief?.evidence?.nasa_sources);
  const calendars = safeArray<CalendarEvidence>(brief?.evidence?.calendar_evidence);
  const latitude = Number(brief?.location?.coordinates?.latitude);
  const longitude = Number(brief?.location?.coordinates?.longitude);
  const regionName = brief?.location?.region_name_en || "Selected field";
  const limitation = brief?.limitations?.en || "This field brief is decision support, not a crop prescription or weather forecast.";
  const rotationMessage =
    brief?.rotation_explorer?.message_en ||
    "Rotation alternatives remain behind evidence review until local crop and sequence rules are approved.";

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
      <div className="brief-screen">
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
            <span>{regionName}</span>
            <strong>Field decision brief</strong>
            <small>
              {Number.isFinite(latitude) && Number.isFinite(longitude)
                ? `${latitude.toFixed(4)}° N | ${longitude.toFixed(4)}° E`
                : "Coordinates unavailable"}
            </small>
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
            <strong>{calendars.length}</strong>
            <small>BAMIS | {regionName}</small>
          </div>
        </div>

        {months.length === 3 ? (
          <div className="brief-timeline">
            {months.map((month, index) => (
              <article className="brief-month" key={month?.planning_month || index}>
                <div className="month-rail">
                  <span>{String(month?.index ?? index + 1).padStart(2, "0")}</span>
                  {index < months.length - 1 && <i />}
                </div>

                <div className="month-content">
                  <div className="month-title-row">
                    <div>
                      <small>{month?.planning_month || "Planning month"}</small>
                      <h3>{month?.phase?.en || "Field review"}</h3>
                    </div>
                    <span className="month-name">{month?.month_name?.en || ""}</span>
                  </div>

                  <p className="month-objective">{month?.objective?.en || "Review field evidence before the next decision."}</p>

                  <div className="month-task-grid">
                    {safeArray(month?.tasks).map((task, taskIndex) => (
                      <div className="brief-task" key={task?.code || taskIndex}>
                        <span>{String(taskIndex + 1).padStart(2, "0")}</span>
                        <div><strong>{task?.en || "Review the available field evidence."}</strong></div>
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
        ) : (
          <div className="report-recovery-note">
            The plan response was incomplete. Return to the farm questions and build the field brief again.
          </div>
        )}

        <div className="rotation-lock-panel">
          <div className="rotation-lock-icon"><span>↻</span><i /></div>
          <div>
            <p className="section-kicker">Three season rotation explorer</p>
            <h3>The evidence review is still active.</h3>
            <p>{rotationMessage}</p>
          </div>
          <span className="lock-chip">NOT YET PRESCRIPTIVE</span>
        </div>

        <div className="brief-source-columns">
          <div>
            <span className="brief-source-title">NASA evidence</span>
            {nasaSources.map((source, index) => (
              <a href={source?.source_url || "#"} target="_blank" rel="noreferrer" key={source?.id || index}>
                <strong>{source?.name || "NASA source"}</strong>
                <small>{String(source?.role || "evidence").replaceAll("_", " ")}</small>
              </a>
            ))}
          </div>

          <div>
            <span className="brief-source-title">Local evidence</span>
            {calendars.slice(0, 8).map((crop, index) => (
              <a href={crop?.source_url || "#"} target="_blank" rel="noreferrer" key={crop?.id || index}>
                <strong>{crop?.name_en || "Regional crop calendar"}</strong>
                <small>BAMIS calendar source | not a recommendation</small>
              </a>
            ))}
          </div>
        </div>

        <footer className="brief-footer">
          <p>{limitation}</p>
          <span>BoponX | Team EARTH.exe | Bangladesh</span>
        </footer>
      </div>
    </section>
  );
}
