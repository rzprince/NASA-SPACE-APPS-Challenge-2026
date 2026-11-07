import type { EvidenceLabel, PlanBrief, PlanTask } from "./api";

type Lang = "en" | "bn";

const EVIDENCE_BADGE_LABELS: Record<EvidenceLabel, { en: string; bn: string }> = {
  observed_nasa: {
    en: "observed_nasa",
    bn: "observed_nasa · নাসা পর্যবেক্ষণ",
  },
  derived_from_nasa: {
    en: "derived_from_nasa",
    bn: "derived_from_nasa · নাসা হতে গণনাকৃত",
  },
  official_local_reference: {
    en: "official_local_reference",
    bn: "official_local_reference · সরকারি স্থানীয় সূত্র",
  },
  rule_based: {
    en: "rule_based",
    bn: "rule_based · কৃষি নিয়মভিত্তিক",
  },
  preliminary_estimate: {
    en: "preliminary_estimate",
    bn: "preliminary_estimate · প্রাথমিক প্রাক্কলন",
  },
};

export function BoponXLogoMark({ size = 40, className = "" }: { size?: number; className?: string }) {
  return (
    <img
      src="/boponx-logo-icon.png"
      width={size}
      height={size}
      alt="BoponX Logo"
      className={`boponx-logo-svg boponx-logo-icon-img ${className}`.trim()}
      draggable={false}
    />
  );
}

export function BoponXFullLogo({ height = 46, className = "" }: { height?: number; className?: string }) {
  return (
    <img
      src="/boponx-logo-full.png"
      style={{ height: `${height}px`, width: "auto" }}
      alt="BoponX — From Space to Soil | মহাকাশ থেকে মাটিতে"
      className={`boponx-full-logo-img ${className}`.trim()}
      draggable={false}
    />
  );
}

export default function DecisionReport({
  brief,
  placeName,
  lang = "en",
  onLangChange,
  startYear,
  startMonth,
  startDay = 1,
  onStartDateChange,
}: {
  brief: PlanBrief;
  placeName: string;
  lang?: Lang;
  onLangChange?: (next: Lang) => void;
  selectedStrategyId?: string;
  onSelectStrategy?: (id: string) => void;
  startYear?: number;
  startMonth?: number;
  startDay?: number;
  onStartDateChange?: (year: number, month: number, day: number) => void;
}) {
  const header = brief.planner_header;
  const wg = brief.window_guidance;
  const months = Array.isArray(brief.months) ? brief.months : [];
  const watchList = Array.isArray(brief.watch_list) ? brief.watch_list : [];
  const district = brief.location.district_profile ?? null;

  const districtDisplay =
    lang === "bn"
      ? header?.district_bn ?? district?.name_bn ?? brief.location.region_name_bn ?? placeName
      : header?.district_en ?? district?.name_en ?? brief.location.region_name_en ?? placeName;

  const cropDisplay =
    lang === "bn"
      ? header?.crop_bn ?? "পরবর্তী মৌসুমি ফসল"
      : header?.crop_en ?? "Next Seasonal Crop";

  const startDateIso =
    header?.plan_start_date ??
    brief.planning_window.start_date ??
    `${brief.planning_window.start}-01`;

  const endDateIso =
    header?.plan_end_date ??
    brief.planning_window.end_date ??
    brief.planning_window.end;

  const dataStatus = brief.data_status ?? (brief.recent_environment?.status === "available" ? "AVAILABLE" : "UNAVAILABLE");
  const dataThroughText =
    lang === "bn"
      ? header?.data_through_label_bn ??
        (brief.data_through ? `NASA তথ্য সর্বশেষ: ${brief.data_through}` : "NASA তথ্য: অনুপস্থিত (অফলাইন)")
      : header?.data_through_label_en ??
        (brief.data_through ? `NASA data through ${brief.data_through}` : "NASA data: UNAVAILABLE (offline)");

  function printPlan() {
    const previous = document.title;
    document.title = `BoponX 90-Day Plan | ${districtDisplay} | ${startDateIso}`;
    window.print();
    window.setTimeout(() => (document.title = previous), 250);
  }

  function handleDateInputChange(value: string) {
    if (!onStartDateChange || !value) return;
    const parts = value.split("-").map((p) => Number(p));
    if (parts.length === 3 && parts.every((n) => Number.isFinite(n))) {
      const [y, m, d] = parts;
      if (y >= 2026 && y <= 2035 && m >= 1 && m <= 12 && d >= 1 && d <= 31) {
        onStartDateChange(y, m, d);
      }
    }
  }

  const currentIsoDate =
    startYear && startMonth
      ? `${String(startYear).padStart(4, "0")}-${String(startMonth).padStart(2, "0")}-${String(startDay ?? 1).padStart(2, "0")}`
      : startDateIso;

  return (
    <section className="field-plan-shell">
      {/* Screen-Only Toolbar */}
      <header className="plan-console-head no-print">
        <div className="console-head-left">
          <span>{lang === "bn" ? "০৩ · ৯০ দিনের মাঠ পরিকল্পনা" : "03 · 90-DAY FIELD PLANNER"}</span>
          <strong>
            {districtDisplay} · {cropDisplay} · {startDateIso} → {endDateIso}
          </strong>
        </div>

        <div className="plan-console-actions">
          {onStartDateChange && (
            <label className="plan-date-picker-label">
              <span>{lang === "bn" ? "শুরুর তারিখ:" : "Plan start date:"}</span>
              <input
                type="date"
                min="2026-01-01"
                max="2035-12-31"
                value={currentIsoDate}
                onChange={(e) => handleDateInputChange(e.target.value)}
                aria-label={lang === "bn" ? "পরিকল্পনা শুরুর তারিখ" : "Plan start date"}
              />
            </label>
          )}

          {onLangChange && (
            <div className="lang-switch" role="group" aria-label="Plan language">
              <button
                type="button"
                className={lang === "en" ? "active" : ""}
                onClick={() => onLangChange("en")}
              >
                English
              </button>
              <button
                type="button"
                className={lang === "bn" ? "active" : ""}
                onClick={() => onLangChange("bn")}
              >
                বাংলা
              </button>
            </div>
          )}

          <button type="button" className="print-btn" onClick={printPlan}>
            {lang === "bn" ? "A4 প্রিন্ট / PDF সংরক্ষণ" : "Print A4 / Save PDF"}
          </button>
        </div>
      </header>

      {/* Printable A4 Sheet — Strictly 5-Part Spec v2 Structure */}
      <article className="farmer-action-card boponx-90day-sheet" aria-label="90-Day Field Plan">
        {/* 1. HEADER: BoponX logo, district, crop, plan start date, "NASA data through <date>", language */}
        <header className="planner-part1-header">
          <div className="planner-brand-row">
            <div className="planner-brand-mark">
              <BoponXFullLogo height={50} />
              <div className="planner-brand-sub">
                <small>
                  {lang === "bn"
                    ? "তথ্যসূত্র: NASA POWER / EONET / GIBS · স্থানীয় কৃষি প্রমাণ"
                    : "Data: NASA POWER / EONET / GIBS · Local Agronomic Evidence"}
                </small>
              </div>
            </div>
            <div className="planner-data-status-pill" data-status={dataStatus}>
              <span>{dataThroughText}</span>
              <b>{lang === "bn" ? "ভাষা: বাংলা (BN)" : "Language: English (EN)"}</b>
            </div>
          </div>

          <div className="planner-meta-strip">
            <div className="planner-meta-cell">
              <span>{lang === "bn" ? "জেলা ও অঞ্চল" : "DISTRICT"}</span>
              <strong>{districtDisplay}</strong>
              <small>
                {brief.location.coordinates.latitude.toFixed(4)}° N, {brief.location.coordinates.longitude.toFixed(4)}° E
              </small>
            </div>
            <div className="planner-meta-cell">
              <span>{lang === "bn" ? "নির্বাচিত ফসল" : "TARGET CROP"}</span>
              <strong>{cropDisplay}</strong>
              <small>
                {lang === "bn"
                  ? `অগ্রাধিকার: ${brief.farmer_context.priority === "water" ? "পানি সাশ্রয়" : brief.farmer_context.priority === "soil" ? "মাটির স্বাস্থ্য" : "উৎপাদন স্থিতিশীলতা"}`
                  : `Priority: ${brief.farmer_context.priority.replace(/_/g, " ")}`}
              </small>
            </div>
            <div className="planner-meta-cell">
              <span>{lang === "bn" ? "পরিকল্পনা শুরুর তারিখ (৯০ দিন)" : "PLAN START DATE (90 DAYS)"}</span>
              <strong>{startDateIso}</strong>
              <small>{lang === "bn" ? `সমাপ্তি: ${endDateIso}` : `Through ${endDateIso}`}</small>
            </div>
            <div className="planner-meta-cell">
              <span>{lang === "bn" ? "সরকারি BAMIS বপন সময়" : "BAMIS BASELINE WINDOW"}</span>
              <strong>
                {lang === "bn"
                  ? wg?.bamis_baseline_window.bn ?? "সরকারি পঞ্জিকা"
                  : wg?.bamis_baseline_window.en ?? "Official calendar"}
              </strong>
              <small className="evidence-inline-tag">official_local_reference</small>
            </div>
            {wg?.shift_reliable && wg.shifted_window ? (
              <div className="planner-meta-cell highlight-shifted">
                <span>{lang === "bn" ? "পরিবর্তিত বপন সময় (নির্ভরযোগ্য)" : "SHIFTED WINDOW (RELIABLE)"}</span>
                <strong>{lang === "bn" ? wg.shifted_window.bn : wg.shifted_window.en}</strong>
                <small className="evidence-inline-tag">
                  rule_based ({wg.shifted_window.applied_shift_days >= 0 ? `+${wg.shifted_window.applied_shift_days}` : wg.shifted_window.applied_shift_days}d)
                </small>
              </div>
            ) : (
              <div className="planner-meta-cell">
                <span>{lang === "bn" ? "বপন সময় সমন্বয়" : "WINDOW SHIFT STATUS"}</span>
                <strong>{lang === "bn" ? "BAMIS ভিত্তি সময় অপরিবর্তিত" : "Keep BAMIS Baseline"}</strong>
                <small>
                  {lang === "bn"
                    ? "নির্ভরযোগ্য পরিবর্তন না থাকায় সময় সরানো হয়নি"
                    : "No statistically reliable shift applied"}
                </small>
              </div>
            )}
          </div>

          {dataStatus === "UNAVAILABLE" && (
            <div className="planner-unavailable-banner" role="status">
              <strong>{lang === "bn" ? "NASA তথ্য বর্তমানে অনুপস্থিত (UNAVAILABLE): " : "NASA Telemetry Currently UNAVAILABLE: "}</strong>
              <span>
                {lang === "bn"
                  ? "সিস্টেমটি অফলাইন মোডে রয়েছে বা যাচাইকৃত স্ন্যাপশট পাওয়া যায়নি। কোনো কাল্পনিক সংখ্যা তৈরি করা হয়নি; নিচের কাজগুলো কৃষকের তথ্য, সরকারি BAMIS পঞ্জিকা এবং যাচাইকৃত কৃষি নিয়মের ওপর ভিত্তি করে তৈরি।"
                  : "The system is offline or no verified NASA POWER snapshot is present for this cell. No weather numbers are invented; tasks below come strictly from your field profile, BAMIS calendars, and documented agronomic rules."}
              </span>
            </div>
          )}
        </header>

        {/* 2 & 3. THREE PHASES (Days 1–30, 31–60, 61–90) & TIMELINE OF TASKS */}
        <section className="planner-part2-phases" aria-label="Three 30-day planning phases">
          {months.map((month) => {
            const phaseSpanLabel =
              lang === "bn"
                ? month.day_span?.bn ?? `দিন ${(month.index - 1) * 30 + 1}–${month.index * 30}`
                : month.day_span?.en ?? `Days ${(month.index - 1) * 30 + 1}–${month.index * 30}`;
            const phaseDatesLabel =
              lang === "bn"
                ? month.date_range?.bn ?? month.planning_month
                : month.date_range?.en ?? month.planning_month;
            const phaseTitle = lang === "bn" ? month.phase.bn : month.phase.en;
            const phaseObj = lang === "bn" ? month.objective.bn : month.objective.en;

            return (
              <div className="planner-phase-block" key={month.planning_month + "-" + month.index}>
                <div className="planner-phase-header">
                  <div className="planner-phase-badge-group">
                    <span className="planner-phase-pill">{phaseSpanLabel}</span>
                    <strong className="planner-phase-title">{phaseTitle}</strong>
                  </div>
                  <span className="planner-phase-dates">{phaseDatesLabel}</span>
                </div>
                <p className="planner-phase-objective">{phaseObj}</p>

                <div className="planner-timeline-list" role="list">
                  {month.tasks.map((task: PlanTask) => {
                    const evLabel: EvidenceLabel = task.evidence_label ?? "rule_based";
                    const evBadge = EVIDENCE_BADGE_LABELS[evLabel] ?? EVIDENCE_BADGE_LABELS.rule_based;
                    const taskDateStr =
                      lang === "bn"
                        ? task.date_range?.bn || phaseDatesLabel
                        : task.date_range?.en || phaseDatesLabel;
                    const actionText = lang === "bn" ? task.bn : task.en;
                    const reasonText = lang === "bn" ? (task.reason_bn ?? task.reason) : task.reason;

                    return (
                      <div className="planner-task-row" role="listitem" key={task.code}>
                        <label className="planner-task-check-wrap">
                          <input
                            type="checkbox"
                            className="planner-task-checkbox"
                            aria-label={actionText}
                          />
                          <span className="planner-check-box-ui" aria-hidden="true" />
                        </label>

                        <div className="planner-task-body">
                          <div className="planner-task-top">
                            <span className="planner-task-daterange">{taskDateStr}</span>
                            <span className={`planner-evidence-badge ev-${evLabel}`}>
                              {lang === "bn" ? evBadge.bn : evBadge.en}
                            </span>
                          </div>

                          <p className="planner-task-action">{actionText}</p>

                          <div className="planner-task-reason-row">
                            <small className="planner-task-reason">
                              <strong>{lang === "bn" ? "কারণ / সংকেত: " : "Reason / Signal: "}</strong>
                              {reasonText}
                            </small>
                            {task.source && (
                              <code className="planner-task-source">{task.source}</code>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </section>

        {/* 4. SHORT "WATCH LIST" BUILT ONLY FROM REAL SIGNALS */}
        <section className="planner-part4-watchlist" aria-label="Real-signal agroclimate and hazard watch list">
          <div className="planner-watchlist-head">
            <strong>
              {lang === "bn"
                ? "পর্যবেক্ষণ তালিকা (Watch List — কেবল প্রকৃত সংকেত থেকে নির্মিত)"
                : "Watch List (Built Strictly from Real Signals)"}
            </strong>
            <span>Data: NASA POWER / EONET / GIBS</span>
          </div>
          <ul className="planner-watchlist-items">
            {watchList.map((item) => {
              const evBadge = EVIDENCE_BADGE_LABELS[item.evidence_label] ?? EVIDENCE_BADGE_LABELS.rule_based;
              return (
                <li key={item.id} className="planner-watchlist-item">
                  <div className="watchlist-item-meta">
                    <code>{item.signal}</code>
                    <span className={`planner-evidence-badge ev-${item.evidence_label}`}>
                      {lang === "bn" ? evBadge.bn : evBadge.en}
                    </span>
                  </div>
                  <p>{lang === "bn" ? item.bn : item.en}</p>
                </li>
              );
            })}
          </ul>
        </section>

        {/* 5. FOOTER: "Verify with DAE 16123", the limitations sentence, and short provenance. Nothing else. */}
        <footer className="planner-part5-footer">
          <div className="planner-footer-verify">
            <strong>
              {lang === "bn"
                ? brief.footer?.verify_bn ?? "কৃষি বাতায়ন ১৬১২৩ নম্বরে যাচাই করুন (Verify with DAE 16123)"
                : brief.footer?.verify_en ?? "Verify with DAE 16123"}
            </strong>
            <span>
              {lang === "bn"
                ? brief.footer?.provenance_bn ?? "তথ্যসূত্র: NASA POWER / EONET / GIBS · স্থানীয় রেফারেন্স: BAMIS / BARC / SRDI"
                : brief.footer?.provenance_en ?? "Data: NASA POWER / EONET / GIBS · Official local reference: BAMIS / BARC / SRDI"}
            </span>
          </div>
          <p className="planner-footer-limitations">
            {lang === "bn" ? brief.limitations.bn : brief.limitations.en}
          </p>
        </footer>
      </article>
    </section>
  );
}
