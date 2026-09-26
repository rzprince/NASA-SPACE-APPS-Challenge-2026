import type { Language, PlanBrief } from "./api";

function txt(language: Language, en: string, bn: string) {
  return language === "bn" ? bn : en;
}

function fmt(value: number | null | undefined, suffix: string) {
  return value === null || value === undefined ? "—" : `${new Intl.NumberFormat("en-BD", { maximumFractionDigits: 1 }).format(value)} ${suffix}`;
}

export default function DecisionReport({
  brief,
  language,
}: {
  brief: PlanBrief;
  language: Language;
}) {
  const recent = brief.recent_environment;
  const baseline = brief.historical_baseline;

  function printReport() {
    const previous = document.title;
    document.title = "BoponX-field-brief";
    window.print();
    window.setTimeout(() => {
      document.title = previous;
    }, 300);
  }

  return (
    <section className="decision-report" id="farmer-report" aria-labelledby="report-title">
      <div className="report-toolbar no-print">
        <div>
          <span className="kicker">{txt(language, "Field brief", "মাঠের সংক্ষিপ্ত পরিকল্পনা")}</span>
          <strong>{txt(language, "Ready to review", "পর্যালোচনার জন্য প্রস্তুত")}</strong>
        </div>
        <button type="button" onClick={printReport}>
          {txt(language, "Print / Save PDF", "প্রিন্ট / PDF সংরক্ষণ")}
        </button>
      </div>

      <header className="report-cover">
        <p className="report-mark">BoponX · বপনএক্স</p>
        <h2 id="report-title">{txt(language, "Your next 90 days", "আপনার আগামী ৯০ দিন")}</h2>
        <p className="report-sub">
          {brief.location.region_name_en} · {brief.location.region_name_bn}
        </p>
        <div className="report-meta-grid">
          <div>
            <span>{txt(language, "Planning window", "পরিকল্পনার সময়")}</span>
            <strong>{brief.planning_window.start} → {brief.planning_window.end}</strong>
          </div>
          <div>
            <span>{txt(language, "Farm point", "জমির পয়েন্ট")}</span>
            <strong>{brief.location.coordinates.latitude.toFixed(4)}, {brief.location.coordinates.longitude.toFixed(4)}</strong>
          </div>
          <div>
            <span>{txt(language, "Priority", "অগ্রাধিকার")}</span>
            <strong>{brief.farmer_context.priority.replaceAll("_", " ")}</strong>
          </div>
        </div>
        <div className="report-warning">
          {txt(
            language,
            "Decision support, not a crop prescription. Regional NASA data do not replace observations from your field.",
            "এটি সিদ্ধান্ত-সহায়তা, ফসলের প্রেসক্রিপশন নয়। আঞ্চলিক NASA তথ্য আপনার জমির বাস্তব পর্যবেক্ষণের বিকল্প নয়।",
          )}
        </div>
      </header>

      {(recent?.status === "available" || baseline?.status === "available") && (
        <section className="report-evidence-band">
          <div>
            <span>{txt(language, "Recent POWER period", "সাম্প্রতিক POWER সময়কাল")}</span>
            <strong>{recent?.period?.start ?? "—"} → {recent?.period?.end ?? "—"}</strong>
          </div>
          <div>
            <span>{txt(language, "Recent mean temperature", "সাম্প্রতিক গড় তাপমাত্রা")}</span>
            <strong>{fmt(recent?.summary?.temperature_mean_c, "°C")}</strong>
          </div>
          <div>
            <span>{txt(language, "Planning-month baseline", "পরিকল্পনা মাসের বেসলাইন")}</span>
            <strong>
              {baseline?.status === "available" && baseline.summary
                ? `${fmt(baseline.summary.temperature_mean_c, "°C")} · ${fmt(baseline.summary.precipitation_mean_daily_mm, "mm/day")}`
                : "—"}
            </strong>
          </div>
        </section>
      )}

      <div className="month-report-grid">
        {brief.months.map((month) => (
          <article className="month-report" key={month.planning_month}>
            <div className="month-count">{String(month.index).padStart(2, "0")}</div>
            <div className="month-heading">
              <span>{month.planning_month}</span>
              <h3>{txt(language, month.phase.en, month.phase.bn)}</h3>
              <p>{txt(language, month.objective.en, month.objective.bn)}</p>
            </div>
            <ol>
              {month.tasks.map((task) => (
                <li key={task.code}>
                  <span className="check-box" aria-hidden="true" />
                  <div>
                    <p>{language === "bn" ? task.bn : task.en}</p>
                    <small>{language === "bn" ? task.en : task.bn}</small>
                  </div>
                </li>
              ))}
            </ol>
            <div className="field-note">
              <span>{txt(language, "Field note", "মাঠের নোট")}</span>
              <i /><i />
            </div>
          </article>
        ))}
      </div>

      <section className="rotation-gate">
        <div className="gate-icon" aria-hidden="true">↻</div>
        <div>
          <span className="kicker">{txt(language, "Three-season rotation explorer", "তিন-মৌসুম ফসল আবর্তন")}</span>
          <h3>{txt(language, "Evidence gate is still active", "প্রমাণ যাচাই এখনো বাকি")}</h3>
          <p>{txt(language, brief.rotation_explorer.message_en, brief.rotation_explorer.message_bn)}</p>
        </div>
      </section>

      <section className="report-sources">
        <div>
          <span className="kicker">{txt(language, "NASA evidence", "NASA প্রমাণ")}</span>
          {brief.evidence.nasa_sources.map((source) => (
            <a href={source.source_url} target="_blank" rel="noreferrer" key={source.id}>
              <strong>{source.name}</strong>
              <span>{source.role.replaceAll("_", " ")}</span>
            </a>
          ))}
        </div>
        <div>
          <span className="kicker">{txt(language, "Local evidence", "স্থানীয় প্রমাণ")}</span>
          {brief.evidence.agricultural_sources.map((source) => (
            <a href={source.source_url} target="_blank" rel="noreferrer" key={source.name}>
              <strong>{source.name}</strong>
              <span>{source.scope}</span>
            </a>
          ))}
        </div>
        <div>
          <span className="kicker">{txt(language, "Regional crop calendars", "আঞ্চলিক ফসল ক্যালেন্ডার")}</span>
          {brief.evidence.calendar_evidence.slice(0, 8).map((crop) => (
            <a href={crop.source_url} target="_blank" rel="noreferrer" key={crop.id}>
              <strong>{language === "bn" ? crop.name_bn : crop.name_en}</strong>
              <span>{txt(language, "Official BAMIS calendar source — not a recommendation", "অফিসিয়াল BAMIS ক্যালেন্ডার উৎস — সুপারিশ নয়")}</span>
            </a>
          ))}
        </div>
      </section>

      <footer className="report-foot">
        <p>{language === "bn" ? brief.limitations.bn : brief.limitations.en}</p>
        <p>BoponX · Team EARTH.exe · Bangladesh</p>
      </footer>
    </section>
  );
}
