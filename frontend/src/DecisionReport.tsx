import type { Language, PlanBrief } from "./api";

function t(language: Language, en: string, bn: string) {
  return language === "bn" ? bn : en;
}

function metric(value: number | null | undefined, suffix: string) {
  if (value === null || value === undefined) return "—";
  return `${new Intl.NumberFormat("en-BD", { maximumFractionDigits: 1 }).format(value)}${suffix}`;
}

export default function DecisionReport({ brief, language }: { brief: PlanBrief; language: Language }) {
  const recent = brief.recent_environment;
  const baseline = brief.historical_baseline;

  function printBrief() {
    const previous = document.title;
    document.title = "BoponX-field-brief";
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
            <span>{t(language, "FIELD BRIEF GENERATED", "মাঠ পরিকল্পনা তৈরি হয়েছে")}</span>
          </div>
          <button type="button" onClick={printBrief}>{t(language, "Print / Save PDF", "প্রিন্ট / PDF সংরক্ষণ")} ↗</button>
        </div>

        <header className="brief-hero">
          <div>
            <p className="section-kicker">{t(language, "The next 90 days", "আগামী ৯০ দিন")}</p>
            <h2>{t(language, "Three months. Three different jobs.", "তিন মাস। তিনটি আলাদা কাজ।")}</h2>
          </div>
          <div className="brief-place">
            <span>{brief.location.region_name_en}</span>
            <strong>{brief.location.region_name_bn}</strong>
            <small>{brief.location.coordinates.latitude.toFixed(4)}° N · {brief.location.coordinates.longitude.toFixed(4)}° E</small>
          </div>
        </header>

        <div className="brief-evidence-strip">
          <div>
            <span>{t(language, "Recent temperature", "সাম্প্রতিক তাপমাত্রা")}</span>
            <strong>{metric(recent?.summary?.temperature_mean_c, "°C")}</strong>
            <small>{recent?.period ? `${recent.period.start} → ${recent.period.end}` : t(language, "unavailable", "পাওয়া যায়নি")}</small>
          </div>
          <div>
            <span>{t(language, "Recent rainfall", "সাম্প্রতিক বৃষ্টি")}</span>
            <strong>{metric(recent?.summary?.precipitation_total_mm, " mm")}</strong>
            <small>{t(language, "NASA POWER regional context", "NASA POWER আঞ্চলিক প্রেক্ষাপট")}</small>
          </div>
          <div>
            <span>{t(language, "Planning-month baseline", "পরিকল্পনা মাসের বেসলাইন")}</span>
            <strong>{metric(baseline?.summary?.temperature_mean_c, "°C")}</strong>
            <small>{baseline?.baseline_period ? `${baseline.baseline_period.start_year}–${baseline.baseline_period.end_year}` : "2001–2020"}</small>
          </div>
          <div>
            <span>{t(language, "Local calendar sources", "স্থানীয় ক্যালেন্ডার উৎস")}</span>
            <strong>{brief.evidence.calendar_evidence.length}</strong>
            <small>BAMIS · {brief.location.region_name_en}</small>
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
                    <h3>{t(language, month.phase.en, month.phase.bn)}</h3>
                  </div>
                  <span className="month-name">{t(language, month.month_name.en, month.month_name.bn)}</span>
                </div>
                <p className="month-objective">{t(language, month.objective.en, month.objective.bn)}</p>
                <div className="month-task-grid">
                  {month.tasks.map((task, taskIndex) => (
                    <div className="brief-task" key={task.code}>
                      <span>{String(taskIndex + 1).padStart(2, "0")}</span>
                      <div>
                        <strong>{language === "bn" ? task.bn : task.en}</strong>
                        <small>{language === "bn" ? task.en : task.bn}</small>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="field-notes-lines">
                  <span>{t(language, "Farmer / adviser notes", "কৃষক / পরামর্শকের নোট")}</span>
                  <i /><i />
                </div>
              </div>
            </article>
          ))}
        </div>

        <div className="rotation-lock-panel">
          <div className="rotation-lock-icon"><span>↻</span><i /></div>
          <div>
            <p className="section-kicker">{t(language, "Three-season rotation explorer", "তিন-মৌসুম ফসল আবর্তন")}</p>
            <h3>{t(language, "The evidence gate is active.", "প্রমাণ যাচাইয়ের গেট সক্রিয়।")}</h3>
            <p>{t(language, brief.rotation_explorer.message_en, brief.rotation_explorer.message_bn)}</p>
          </div>
          <span className="lock-chip">{t(language, "NOT YET PRESCRIPTIVE", "এখনও প্রেসক্রিপশন নয়")}</span>
        </div>

        <div className="brief-source-columns">
          <div>
            <span className="brief-source-title">NASA</span>
            {brief.evidence.nasa_sources.map((source) => (
              <a href={source.source_url} target="_blank" rel="noreferrer" key={source.id}>
                <strong>{source.name}</strong>
                <small>{source.role.replaceAll("_", " ")}</small>
              </a>
            ))}
          </div>
          <div>
            <span className="brief-source-title">{t(language, "Local evidence", "স্থানীয় প্রমাণ")}</span>
            {brief.evidence.calendar_evidence.slice(0, 8).map((crop) => (
              <a href={crop.source_url} target="_blank" rel="noreferrer" key={crop.id}>
                <strong>{language === "bn" ? crop.name_bn : crop.name_en}</strong>
                <small>{t(language, "BAMIS calendar source · not a recommendation", "BAMIS ক্যালেন্ডার উৎস · সুপারিশ নয়")}</small>
              </a>
            ))}
          </div>
        </div>

        <footer className="brief-footer">
          <p>{language === "bn" ? brief.limitations.bn : brief.limitations.en}</p>
          <span>BoponX · Team EARTH.exe · Bangladesh</span>
        </footer>
      </div>
    </section>
  );
}
