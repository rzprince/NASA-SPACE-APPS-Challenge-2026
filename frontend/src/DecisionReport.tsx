import type { AgriculturalSource, PlanBrief, PlanMonth } from "./api";

function metric(value: number | null | undefined, suffix = "") {
  if (value === null || value === undefined || !Number.isFinite(value)) return "Unavailable";
  return `${new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 }).format(value)}${suffix}`;
}

function safeArray<T>(value: T[] | null | undefined): T[] {
  return Array.isArray(value) ? value : [];
}

function taskIcon(category?: string) {
  const icons: Record<string, string> = {
    nasa_context: "◎",
    field_history: "↺",
    farmer_intention: "→",
    field_observation: "◉",
    soil_evidence: "▦",
    recent_conditions: "≋",
    monitoring: "⌁",
    farmer_priority: "◇",
    local_evidence: "⌂",
    decision_advice: "✓",
    decision_record: "□",
  };
  return icons[category ?? ""] ?? "•";
}

export default function DecisionReport({
  brief,
  localSources,
  onBack,
  onEarth,
}: {
  brief: PlanBrief;
  localSources: AgriculturalSource[];
  onBack: () => void;
  onEarth: () => void;
}) {
  const months = safeArray<PlanMonth>(brief?.months);
  const advice = brief?.decision_advice;
  const recent = brief?.recent_environment;
  const conditions = brief?.conditions;
  const region = brief?.location?.region_name_en || brief?.farmer_context?.country_name || "Selected field";

  function printBrief() {
    const previous = document.title;
    document.title = "BoponX Farmer Brief";
    window.print();
    window.setTimeout(() => {
      document.title = previous;
    }, 300);
  }

  function readBrief() {
    if (!("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const text = [
      `BoponX farmer brief for ${region}.`,
      advice?.verdict ?? "",
      advice?.better_next_step ? `Next step. ${advice.better_next_step}` : "",
      ...months.flatMap((month) => [
        `${month.month_name.en}. ${month.phase.en}. ${month.objective.en}`,
        ...safeArray(month.tasks).map((task) => task.en),
      ]),
    ].filter(Boolean).join(" ");
    const speech = new SpeechSynthesisUtterance(text);
    speech.rate = 0.92;
    speech.pitch = 1;
    window.speechSynthesis.speak(speech);
  }

  return (
    <section className="farmer-brief">
      <div className="brief-toolbar no-print">
        <div>
          <button type="button" onClick={onBack}>← Rotation Lab</button>
          <button type="button" onClick={onEarth}>Earth selector</button>
        </div>
        <div>
          <button type="button" onClick={readBrief}>◉ Read aloud</button>
          <button type="button" className="print-command" onClick={printBrief}>Print farmer brief</button>
        </div>
      </div>

      <div className="brief-paper">
        <header className="brief-command-header">
          <div className="brief-mark">
            <span className="brief-mark-icon"><i /><i /><i /></span>
            <div>
              <strong>BoponX</strong>
              <small>FARMER DECISION BRIEF</small>
            </div>
          </div>
          <div className="brief-location">
            <span>{region}</span>
            <strong>{brief.location.coordinates.latitude.toFixed(4)}° · {brief.location.coordinates.longitude.toFixed(4)}°</strong>
            <small>{brief.planning_window.start} → {brief.planning_window.end}</small>
          </div>
        </header>

        <section className="brief-action">
          <div className="brief-action-code">NEXT MOVE</div>
          <div>
            <h1>{advice?.verdict ?? "Review the field evidence before deciding."}</h1>
            <p>{advice?.better_next_step ?? "Use the three month routine below to reduce uncertainty before the next crop decision."}</p>
          </div>
          <div className="brief-action-status">
            <span>{advice?.status?.replaceAll("_", " ") ?? "EVIDENCE REVIEW"}</span>
            <strong>{brief.farmer_context.intended_crop ? brief.farmer_context.intended_crop.toUpperCase() : "NOT DECIDED"}</strong>
          </div>
        </section>

        <section className="brief-signal-strip">
          <div>
            <span>RECENT TEMP</span>
            <strong>{metric(recent?.summary?.temperature_mean_c, "°C")}</strong>
          </div>
          <div>
            <span>RECENT RAIN</span>
            <strong>{metric(recent?.summary?.precipitation_total_mm, " mm")}</strong>
          </div>
          <div>
            <span>RAIN SIGNAL</span>
            <strong>{conditions?.rain_signal?.replaceAll("_", " ") ?? "unavailable"}</strong>
          </div>
          <div>
            <span>WATER</span>
            <strong>{brief.farmer_context.water_source.replaceAll("_", " ")}</strong>
          </div>
          <div>
            <span>PRIORITY</span>
            <strong>{brief.farmer_context.priority.replaceAll("_", " ")}</strong>
          </div>
        </section>

        {advice && (
          <section className="brief-why">
            <div>
              <span className="brief-section-code">WHY THIS ADVICE</span>
              <h2>Evidence behind the next move</h2>
            </div>
            <div className="brief-reasons">
              {safeArray(advice.reasons).map((reason, index) => (
                <div key={index}>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <p>{reason}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="brief-plan">
          <div className="brief-plan-head">
            <div>
              <span className="brief-section-code">90 DAY ROUTINE</span>
              <h2>Three months. Three jobs.</h2>
            </div>
            <p>Use this page in the field. Tick tasks when they are done. A link is not required to follow the routine.</p>
          </div>

          <div className="brief-months">
            {months.map((month, monthIndex) => (
              <article className="brief-month-card" key={month.planning_month}>
                <div className="brief-month-top">
                  <span>{String(monthIndex + 1).padStart(2, "0")}</span>
                  <div>
                    <small>{month.planning_month}</small>
                    <strong>{month.month_name.en}</strong>
                  </div>
                </div>

                <h3>{month.phase.en}</h3>
                <p className="brief-month-objective">{month.objective.en}</p>

                {month.context?.baseline && (
                  <div className="brief-climate">
                    <span>NASA POWER historical reference</span>
                    <strong>
                      {metric(month.context.baseline.temperature_mean_c, "°C")}
                      {" · "}
                      {metric(month.context.baseline.precipitation_mean_daily_mm, " mm/day")}
                    </strong>
                    <small>Reference only. Not a forecast.</small>
                  </div>
                )}

                <div className="brief-tasks">
                  {safeArray(month.tasks).map((task, taskIndex) => (
                    <div className="brief-task-row" key={task.code || taskIndex}>
                      <span className="brief-task-check">□</span>
                      <span className="brief-task-icon">{taskIcon(task.category)}</span>
                      <div>
                        <strong>{task.en}</strong>
                        {task.reason && <small>{task.reason}</small>}
                      </div>
                    </div>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="advisor-handoff">
          <div className="advisor-icon">⌂</div>
          <div>
            <span className="brief-section-code">WHEN EXPERT HELP IS NEEDED</span>
            <h2>Take this page to a local agriculture adviser.</h2>
            <p>
              Bring the printed brief, any soil test report, and the farmer's field notes. The adviser can review local crop rules and soil information without asking the farmer to open a web link.
            </p>
          </div>
          <div className="advisor-checklist">
            <span>□ Soil report if available</span>
            <span>□ Previous crop history</span>
            <span>□ Water and drainage notes</span>
            <span>□ This printed BoponX brief</span>
          </div>
        </section>

        <section className="expert-evidence no-print">
          <details>
            <summary>
              <span>EXPERT EVIDENCE APPENDIX</span>
              <strong>Sources, products, and provenance</strong>
            </summary>
            <div className="expert-grid">
              <div>
                <span className="expert-title">NASA sources used in this decision pipeline</span>
                {safeArray(brief.evidence?.nasa_sources).map((source) => (
                  <a href={source.source_url} target="_blank" rel="noreferrer" key={source.id}>
                    <strong>{source.name}</strong>
                    <small>{source.product} · {source.spatial}</small>
                    <p>{source.boundary}</p>
                  </a>
                ))}
              </div>
              <div>
                <span className="expert-title">Verified local source pathways</span>
                {localSources.length ? localSources.map((source) => (
                  <a href={source.source_url} target="_blank" rel="noreferrer" key={source.name}>
                    <strong>{source.name}</strong>
                    <small>{source.agency}</small>
                  </a>
                )) : (
                  <p className="expert-gap">No verified local government adapter is onboarded for this country. BoponX did not invent one.</p>
                )}
              </div>
            </div>
          </details>
        </section>

        <footer className="brief-disclaimer">
          <strong>Decision support, not prescription.</strong>
          <p>{brief.limitations.en}</p>
          <span>EARTH.exe · NASA Space Apps Challenge 2026 · Independent project</span>
        </footer>
      </div>
    </section>
  );
}
