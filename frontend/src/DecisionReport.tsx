import FieldIcon, { type IconName } from "./FieldIcon";
import type { PlanBrief, PlanTask, RotationScenario } from "./api";

type Lang = "en" | "bn";

const cropNameEn: Record<string, string> = {
  rice: "Rice",
  wheat: "Wheat",
  maize: "Maize",
  pulse: "Pulse (Lentil / Mungbean)",
  mustard: "Mustard",
  vegetables: "Vegetables",
  jute: "Jute",
  other: "Other crop",
};

const cropNameBn: Record<string, string> = {
  rice: "ধান",
  wheat: "গম",
  maize: "ভুট্টা",
  pulse: "ডাল (মসুর / মুগ)",
  mustard: "সরিষা",
  vegetables: "সবজি",
  jute: "পাট",
  other: "অন্যান্য ফসল",
};

function metric(value: number | null | undefined, suffix = "") {
  if (value === null || value === undefined || !Number.isFinite(value)) return "Not available";
  return `${new Intl.NumberFormat("en", { maximumFractionDigits: 1 }).format(value)}${suffix}`;
}

function taskIcon(task: PlanTask): IconName {
  const category = task.category ?? "";
  if (category.includes("soil")) return "soil";
  if (category.includes("water") || category.includes("rain") || category.includes("condition") || category.includes("observation")) return "water";
  if (category.includes("decision")) return "check";
  if (category.includes("history")) return "other";
  if (category.includes("intention")) return "stability";
  if (category.includes("local")) return "other";
  if (category.includes("monitor")) return "stability";
  if (category.includes("nasa")) return "rain";
  return "check";
}

function taskCategoryLabel(category: string | undefined, lang: Lang): string {
  const c = category ?? "";
  if (c.includes("nasa")) return lang === "bn" ? "নাসা জলবায়ু রেফারেন্স" : "NASA CLIMATE BENCHMARK";
  if (c.includes("history")) return lang === "bn" ? "ফসল ইতিহাস ও অবশিষ্টাংশ" : "CROP HISTORY & RESIDUE";
  if (c.includes("intention")) return lang === "bn" ? "বীজতলা ও জমি প্রস্তুতি" : "TARGET CROP SETUP";
  if (c.includes("observation")) return lang === "bn" ? "পানি ও নিষ্কাশন ব্যবস্থা" : "WATER & DRAINAGE ACTION";
  if (c.includes("soil")) return lang === "bn" ? "মাটি পরীক্ষা ও সার" : "SOIL & NUTRIENT ACTION";
  if (c.includes("recent")) return lang === "bn" ? "নাসা আবহাওয়া সতর্কতা" : "NASA ANOMALY ALERT";
  if (c.includes("monitor")) return lang === "bn" ? "পরিচর্যা ও পর্যবেক্ষণ" : "CROP CARE & LOGGING";
  if (c.includes("priority")) return lang === "bn" ? "কৃষকের অগ্রাধিকার পদক্ষেপ" : "PRIORITY EXECUTION";
  if (c.includes("local")) return lang === "bn" ? "স্থানীয় পঞ্জিকা ও পর্যায়" : "LOCAL CALENDAR & ROTATION";
  if (c.includes("decision")) return lang === "bn" ? "সিদ্ধান্ত ও প্রত্যয়ন" : "DECISION & EXTENSION CHECK";
  return lang === "bn" ? "মাঠের কাজ" : "FIELD ACTION";
}

export default function DecisionReport({
  brief,
  placeName,
  lang = "en",
  onLangChange,
  selectedStrategyId = "B",
  onSelectStrategy,
}: {
  brief: PlanBrief;
  placeName: string;
  lang?: Lang;
  onLangChange?: (next: Lang) => void;
  selectedStrategyId?: string;
  onSelectStrategy?: (id: string) => void;
}) {
  const advice = brief.decision_advice;
  const months = Array.isArray(brief.months) ? brief.months : [];
  const recent = brief.recent_environment?.status === "available" ? brief.recent_environment.summary : undefined;
  const district = brief.location.district_profile ?? null;
  const scenarios: RotationScenario[] = brief.rotation_explorer?.scenarios ?? [];
  const activeScenario =
    scenarios.find((s) => s.id === selectedStrategyId) ?? scenarios[1] ?? scenarios[0] ?? null;

  const fc = brief.farmer_context;
  const prevCropsList = fc.previous_crops?.length
    ? fc.previous_crops
    : fc.previous_crop
      ? [fc.previous_crop]
      : [];
  const prevCropsText = prevCropsList.length
    ? prevCropsList.map((c) => (lang === "bn" ? cropNameBn[c] ?? c : cropNameEn[c] ?? c)).join(" → ")
    : (lang === "bn" ? "উল্লেখ নেই" : "Not specified");
  const intendedText = fc.intended_crop
    ? (lang === "bn" ? cropNameBn[fc.intended_crop] ?? fc.intended_crop : cropNameEn[fc.intended_crop] ?? fc.intended_crop)
    : (lang === "bn" ? "সিদ্ধান্ত হয়নি" : "Not decided");

  const waterText =
    fc.water_source === "rainfed"
      ? (lang === "bn" ? "মূলত বৃষ্টিনির্ভর" : "Mostly rainfed")
      : fc.water_source === "irrigated"
        ? (lang === "bn" ? "মূলত সেচনির্ভর" : "Mostly irrigated")
        : fc.water_source === "both"
          ? (lang === "bn" ? "বৃষ্টি ও সেচ উভয়ই" : "Rain + Irrigation")
          : (lang === "bn" ? "নিশ্চিত নয়" : "Unknown");

  const drainageText =
    fc.water_after_heavy_rain === "drains"
      ? (lang === "bn" ? "দ্রুত পানি নেমে যায়" : "Drains quickly")
      : fc.water_after_heavy_rain === "stays"
        ? (lang === "bn" ? "পানি জমে থাকে (জলাবদ্ধতা ঝুঁকি)" : "Water stays (Waterlogging risk)")
        : fc.water_after_heavy_rain === "sometimes"
          ? (lang === "bn" ? "মাঝে মাঝে জমে" : "Drains slowly / changes")
          : (lang === "bn" ? "নিশ্চিত নয়" : "Unknown");

  const soilText =
    fc.soil_test === "yes"
      ? (fc.soil_ph != null ? `Lab Verified (pH ${fc.soil_ph})` : "Lab Report Available")
      : fc.soil_test === "no"
        ? (lang === "bn" ? "রিপোর্ট নেই (SRDI পরীক্ষা প্রয়োজন)" : "No lab report (SRDI test needed)")
        : (lang === "bn" ? "নিশ্চিত নয়" : "Not sure");

  const priorityText =
    fc.priority === "water"
      ? (lang === "bn" ? "পানি সাশ্রয় ও সেচ দক্ষতা" : "Water Saving & Irrigation Efficiency")
      : fc.priority === "soil"
        ? (lang === "bn" ? "মাটির স্বাস্থ্য ও জৈব পদার্থ" : "Soil Health & Organic Matter")
        : (lang === "bn" ? "উৎপাদন স্থিতিশীলতা ও ঝুঁকি হ্রাস" : "Production Stability & Risk Buffer");

  const isBangladesh =
    Boolean(district) ||
    (brief.evidence?.agricultural_sources ?? []).some((source) =>
      source.name.toLowerCase().includes("bangladesh") ||
      source.name.toLowerCase().includes("bamis") ||
      source.name.toLowerCase().includes("agriculture information service"),
    );

  function printPlan() {
    const previous = document.title;
    document.title = `BoponX 90-Day Field Plan | ${placeName}`;
    window.print();
    window.setTimeout(() => (document.title = previous), 250);
  }

  return (
    <section className="field-plan-shell">
      {/* Screen-Only Control Bar */}
      <header className="plan-console-head no-print">
        <div className="console-head-left">
          <span>03 · TAILORED 90-DAY FIELD ACTION DOSSIER</span>
          <strong>{placeName} · {brief.planning_window.start} to {brief.planning_window.end}</strong>
        </div>

        <div className="plan-console-actions">
          {scenarios.length > 1 && onSelectStrategy && (
            <div className="strategy-focus-picker" role="group" aria-label="Select strategy focus">
              <span>{lang === "bn" ? "কৌশল ফোকাস:" : "Focus Strategy:"}</span>
              {scenarios.map((sc) => (
                <button
                  type="button"
                  key={sc.id}
                  className={activeScenario?.id === sc.id ? "active" : ""}
                  onClick={() => onSelectStrategy(sc.id)}
                >
                  Strategy {sc.id}
                </button>
              ))}
            </div>
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

          <button className="print-btn" onClick={printPlan}>
            {lang === "bn" ? "প্রিন্ট / PDF সংরক্ষণ করুন 🖨️" : "Print / Save as PDF 🖨️"}
          </button>
        </div>
      </header>

      {/* Printable Document Sheet */}
      <div className="farmer-action-card premium-plan">
        {/* Document Header with Official BoponX Red-Ball Orbit Logo */}
        <header className="action-card-head premium">
          <div className="action-brand">
            <span className="brand-orbit print-orbit"><i /><b /></span>
            <div>
              <strong>BoponX · From Space to Soil</strong>
              <small>Team EARTH.exe · NASA Earth Observation + Local Agronomy + Farmer Situation Decision Plan</small>
            </div>
          </div>
          <div className="action-field">
            <span>{lang === "bn" ? "নির্বাচিত খামার ও পরিকল্পনা মেয়াদ" : "SELECTED FIELD & 90-DAY SPAN"}</span>
            <strong>{placeName}</strong>
            <small>
              {brief.location.coordinates.latitude.toFixed(4)}° N, {brief.location.coordinates.longitude.toFixed(4)}° E
              {district ? ` · ${district.name_en} (${district.name_bn})` : ""}
              {` · Window: ${brief.planning_window.start} → ${brief.planning_window.end}`}
            </small>
          </div>
        </header>

        {/* Farmer Situation & Input Summary Ribbon */}
        <section className="farmer-situation-ribbon">
          <div className="situation-cell">
            <span>{lang === "bn" ? "পূর্ববর্তী ফসল ধারা" : "RECENT CROP HISTORY"}</span>
            <strong>{prevCropsText}</strong>
          </div>
          <div className="situation-cell highlight">
            <span>{lang === "bn" ? "পরিকল্পিত পরবর্তী ফসল" : "TARGET NEXT CROP"}</span>
            <strong>{intendedText}</strong>
          </div>
          <div className="situation-cell">
            <span>{lang === "bn" ? "পানির উৎস" : "WATER SOURCE"}</span>
            <strong>{waterText}</strong>
          </div>
          <div className="situation-cell">
            <span>{lang === "bn" ? "ভারী বৃষ্টির পর নিষ্কাশন" : "POST-RAIN DRAINAGE"}</span>
            <strong>{drainageText}</strong>
          </div>
          <div className="situation-cell">
            <span>{lang === "bn" ? "মাটি পরীক্ষা ও pH" : "SOIL TEST & pH"}</span>
            <strong>{soilText}</strong>
          </div>
          <div className="situation-cell">
            <span>{lang === "bn" ? "প্রধান অগ্রাধিকার" : "PRIMARY PRIORITY"}</span>
            <strong>{priorityText}</strong>
          </div>
        </section>

        {/* Executive Decision Verdict + NASA Agroclimate Scorecard */}
        <section className="plan-hero-grid">
          <div className="action-decision premium">
            <div className="decision-status-pill" data-status={advice?.status ?? "READY"}>
              {advice?.status?.replace(/_/g, " ") ?? "DECISION PREPARATION READY"}
            </div>
            <h1>{advice?.verdict ?? "Your field evidence and 90-day operational plan are ready."}</h1>
            <p className="next-step-callout">
              <strong>{lang === "bn" ? "তাৎক্ষণিক করণীয়: " : "Immediate Recommended Action: "}</strong>
              {advice?.better_next_step ?? "Follow the Month 1–3 field preparation and monitoring schedule below."}
            </p>

            {advice?.reasons?.length ? (
              <div className="verdict-reasons-box">
                <span className="action-label">
                  {lang === "bn" ? "আপনার খামারের পরিস্থিতি ও প্রমাণের বিশ্লেষণ" : "SITUATION & EVIDENCE DIAGNOSIS FOR THIS FIELD"}
                </span>
                <ul>
                  {(advice?.reasons ?? []).map((reason, index) => (
                    <li key={index}>
                      <b>{String(index + 1).padStart(2, "0")}</b>
                      <span>{reason}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>

          <aside className="field-signal-board">
            <div className="signal-board-title">
              <span>NASA AGROCLIMATE & WATER DIAGNOSTICS</span>
              <strong>{lang === "bn" ? "খামারের চারপাশের উপগ্রহ সংকেত" : "Resolved Satellite & Grid Signals"}</strong>
            </div>
            <div className="signal-board-grid">
              <article>
                <FieldIcon name="rain" />
                <span>{lang === "bn" ? "সাম্প্রতিক বৃষ্টি (১৪ দিন)" : "Recent Rain (14d)"}</span>
                <strong>{metric(recent?.precipitation_total_mm, " mm")}</strong>
              </article>
              <article>
                <FieldIcon name="water" />
                <span>{lang === "bn" ? "বৃষ্টিপাত সংকেত" : "Rainfall Anomaly"}</span>
                <strong>{brief.conditions?.rain_signal?.replace(/_/g, " ") ?? "near baseline"}</strong>
              </article>
              <article>
                <FieldIcon name="stability" />
                <span>{lang === "bn" ? "গড় / সর্বোচ্চ তাপমাত্রা" : "Mean / Max Temp"}</span>
                <strong>
                  {metric(recent?.temperature_mean_c, "°")} / {metric(recent?.temperature_max_mean_c, "°C")}
                </strong>
              </article>
              <article>
                <FieldIcon name="soil" />
                <span>{lang === "bn" ? "বাষ্পীভবন চাহিদা (ET₀)" : "FAO-56 Evap (ET₀)"}</span>
                <strong>{metric(recent?.et0_mean_daily_mm ?? brief.conditions?.et0_daily_mm, " mm/d")}</strong>
              </article>
              <article>
                <FieldIcon name="water" />
                <span>{lang === "bn" ? "পানির ভারসাম্য (P−ET₀)" : "Water Balance (P−ET₀)"}</span>
                <strong>{metric(recent?.water_balance_daily_mm ?? brief.conditions?.water_balance_daily_mm, " mm/d")}</strong>
              </article>
              <article>
                <FieldIcon name="check" />
                <span>{lang === "bn" ? "আর্দ্রতা ও বাতাস" : "Humidity & Wind"}</span>
                <strong>
                  {metric(recent?.relative_humidity_mean_pct, "%")} · {metric(recent?.wind_speed_mean_m_s, " m/s")}
                </strong>
              </article>
            </div>
          </aside>
        </section>

        {/* District Profile + Active Rotation Strategy Focus Strip */}
        <section className="plan-context-duo">
          {district && (
            <div className="plan-district-strip">
              <span className="action-label">{lang === "bn" ? "স্থানীয় ৬৪-জেলার মাটি ও ফসলের প্রেক্ষাপট" : "LOCAL 64-DISTRICT LANDFORM & CROP CONTEXT"}</span>
              <strong>
                {lang === "bn"
                  ? `${district.name_bn} জেলা (${district.division_bn} বিভাগ) — ${district.landform_bn}`
                  : `${district.name_en} District (${district.division_en} Division) — ${district.landform_en}`}
              </strong>
              <p>
                {lang === "bn"
                  ? `প্রতিষ্ঠিত ফসল: ${district.established_crops_bn.join(", ")} · নতুন সুযোগ: ${district.opportunity_crops_bn.join(", ")} · মিল থাকা অঞ্চল: ${district.analog_regions_bn}`
                  : `Established crops: ${district.established_crops_en.join(", ")} · Diversification opportunities: ${district.opportunity_crops_en.join(", ")} · Climate analogs: ${district.analog_regions_en}`}
              </p>
              <p className="bare-risk-line">
                <b>{lang === "bn" ? "খালি জমির ঝুঁকি: " : "Bare-Field Risk Window: "}</b>
                {lang === "bn" ? district.bare_field_risk_bn : district.bare_field_risk_en}
              </p>
            </div>
          )}

          {activeScenario && (
            <div className="plan-active-strategy-box">
              <span className="action-label">
                {lang === "bn"
                  ? `নির্বাচিত ফসল পর্যায় ফোকাস (কৌশল ${activeScenario.id})`
                  : `ACTIVE ROTATION STRATEGY FOCUS (STRATEGY ${activeScenario.id})`}
              </span>
              <strong>{lang === "bn" ? activeScenario.title_bn : activeScenario.title_en}</strong>
              <div className="active-seq-pills">
                {(lang === "bn" ? activeScenario.crops_bn : activeScenario.crops_en).map((crop, idx) => (
                  <span key={`${crop}-${idx}`}>
                    <small>{lang === "bn" ? `মৌসুম ${idx + 1}` : `S${idx + 1}`}:</small> {crop}
                  </span>
                ))}
              </div>
              <p>{lang === "bn" ? activeScenario.why_suggested_bn : activeScenario.why_suggested_en}</p>
            </div>
          )}
        </section>

        {/* Core 90-Day Staged Operational Plan (Days 1-30, Days 31-60, Days 61-90) */}
        <section className="plan-section-header">
          <div>
            <span className="action-label">
              {lang === "bn" ? "ধাপভিত্তিক ৯০ দিনের মাঠের কর্মপরিকল্পনা" : "STAGED 90-DAY OPERATIONAL FIELD SCHEDULE"}
            </span>
            <h2>
              {lang === "bn"
                ? `দিন ১ থেকে দিন ৯০ — ${intendedText} ও আপনার জমির পরিস্থিতির জন্য সুনির্দিষ্ট পদক্ষেপ`
                : `Days 1 to 90 — Tailored Field Actions for ${intendedText} (${waterText} · ${drainageText})`}
            </h2>
          </div>
          <small>
            {lang === "bn"
              ? "প্রতিটি মাসের কাজ আপনার নির্বাচিত ফসল, পানির উৎস, নিষ্কাশন, মাটি পরীক্ষা ও অগ্রাধিকার অনুযায়ী সাজানো হয়েছে"
              : "Each stage adapts to your crop history, target crop, water/drainage status, soil report, and NASA baseline"}
          </small>
        </section>

        <section className="action-months premium">
          {months.map((month) => {
            const daySpan =
              month.index === 1 ? "DAYS 1–30" : month.index === 2 ? "DAYS 31–60" : "DAYS 61–90";
            const daySpanBn =
              month.index === 1 ? "দিন ১–৩০" : month.index === 2 ? "দিন ৩১–৬০" : "দিন ৬১–৯০";
            return (
              <article key={month.planning_month} className="month-stage-card">
                <header>
                  <div className="month-number">{String(month.index).padStart(2, "0")}</div>
                  <div className="month-head-copy">
                    <div className="month-head-meta">
                      <span>{month.planning_month}</span>
                      <b>{lang === "bn" ? daySpanBn : daySpan}</b>
                    </div>
                    <strong>{lang === "bn" ? month.month_name.bn : month.month_name.en}</strong>
                    <small>{lang === "bn" ? month.phase.bn : month.phase.en}</small>
                  </div>
                </header>

                <div className="month-objective-box">
                  <span>{lang === "bn" ? "এই ৩০ দিনের মূল লক্ষ্য" : "STAGE OBJECTIVE"}</span>
                  <p>{lang === "bn" ? month.objective.bn : month.objective.en}</p>
                </div>

                {month.context?.baseline && (
                  <div className="month-climate-ribbon">
                    <span>{lang === "bn" ? "ঐতিহাসিক NASA POWER মানদণ্ড (২০০১–২০২০)" : "NASA POWER 2001–2020 Monthly Benchmark"}</span>
                    <strong>
                      Temp: {metric(month.context.baseline.temperature_mean_c, "°C")}
                      {" · "}
                      Rain: {metric(month.context.baseline.precipitation_mean_daily_mm, " mm/d")}
                      {month.context.baseline.et0_mean_daily_mm != null
                        ? ` · ET₀: ${metric(month.context.baseline.et0_mean_daily_mm, " mm/d")}`
                        : ""}
                    </strong>
                  </div>
                )}

                <div className="visual-task-list">
                  {(month?.tasks ?? []).map((task, idx) => (
                    <div className="visual-task" key={task.code}>
                      <span className="visual-task-icon">
                        <FieldIcon name={taskIcon(task)} />
                      </span>
                      <div className="visual-task-body">
                        <div className="task-tag-row">
                          <span className="task-cat-tag">{taskCategoryLabel(task.category, lang)}</span>
                          <em className="task-step-num">#{idx + 1}</em>
                        </div>
                        <strong>{lang === "bn" ? task.bn : task.en}</strong>
                        {(lang === "bn" ? task.reason_bn ?? task.reason : task.reason) && (
                          <small>
                            <b>{lang === "bn" ? "কেন জরুরি: " : "Why it matters: "}</b>
                            {lang === "bn" ? (task.reason_bn ?? task.reason) : task.reason}
                          </small>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </article>
            );
          })}
        </section>

        {/* 3-Strategy Comparison Matrix on the Printable Card */}
        {scenarios.length > 0 && (
          <section className="plan-rotation-summary">
            <div className="rotation-summary-head">
              <span className="action-label">
                {lang === "bn"
                  ? "৩টি তুলনাকৃত ফসল পর্যায় (বিদ্যমান ধারা সহ — স্থানীয় কৃষি কর্মকর্তার সাথে পর্যালোচনার জন্য)"
                  : "3-STRATEGY ROTATION COMPARISON MATRIX (INCLUDING EXISTING ROTATION — FOR ADVISER REVIEW)"}
              </span>
              <small>
                {lang === "bn"
                  ? "ক্লিক করে ফোকাস পরিবর্তন করুন অথবা কৃষি অফিসে ৩টি বিকল্পই দেখান"
                  : "Click any card on screen to set focus, or review all 3 options with your extension officer"}
              </small>
            </div>
            <div className="plan-rotation-grid">
              {scenarios.map((sc) => {
                const isSelected = activeScenario?.id === sc.id;
                return (
                  <div
                    key={sc.id}
                    className={`plan-rotation-item ${isSelected ? "selected-focus" : ""}`}
                    onClick={() => onSelectStrategy && onSelectStrategy(sc.id)}
                    role={onSelectStrategy ? "button" : undefined}
                    tabIndex={onSelectStrategy ? 0 : undefined}
                  >
                    <div className="plan-rot-top">
                      <span>STRATEGY {sc.id}</span>
                      {isSelected && <b>{lang === "bn" ? "নির্বাচিত ফোকাস" : "ACTIVE FOCUS"}</b>}
                    </div>
                    <strong>{lang === "bn" ? sc.title_bn : sc.title_en}</strong>
                    <p className="plan-rotation-seq">
                      {(lang === "bn" ? sc.crops_bn : sc.crops_en).join(" → ")}
                    </p>
                    <small>{lang === "bn" ? sc.why_suggested_bn : sc.why_suggested_en}</small>
                    {sc.local_review_risks?.[0] && (
                      <div className="plan-rot-risk">
                        <b>{lang === "bn" ? "যাচাইয়ের বিষয়: " : "Verify locally: "}</b>
                        {sc.local_review_risks[0]}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </section>
        )}

        {/* Extension Support Strip */}
        <section className="farmer-support-strip">
          <div>
            <span className="action-label">LOCAL AGRICULTURAL EXTENSION SUPPORT</span>
            <strong>{isBangladesh ? "Bangladesh Agriculture Call Center: 16123 (কৃষি কল সেন্টার: ১৬১২৩ — টোল ফ্রি পরামর্শ)" : "Consult the local agriculture extension authority listed below."}</strong>
            <p>
              {isBangladesh
                ? (lang === "bn"
                  ? "প্রিন্ট করা এই ৯০ দিনের পরিকল্পনাটি ইন্টারনেট ছাড়াই ব্যবহারযোগ্য। বীজ বপন, সারের মাত্রা বা বালাই দমনের চূড়ান্ত পরামর্শের জন্য ১৬১২৩ নম্বরে কল করুন অথবা এই কার্ডটি আপনার ইউনিয়ন/উপজেলা উপসহকারী কৃষি কর্মকর্তার (SAAO / DAE) কাছে নিয়ে যান।"
                  : "This printed 90-day dossier works offline in the field. Call 16123 or bring this sheet to your Union/Upazila Sub-Assistant Agriculture Officer (SAAO / DAE) to confirm variety selection and soil test fertilizer rates.")
                : "This printed dossier is designed to work without internet links. Bring it to your local extension adviser to verify cultivar maturity and soil test rates."}
            </p>
          </div>
          <div className="support-symbol"><FieldIcon name="check" /></div>
        </section>

        {/* Traceable Evidence Register */}
        <section className="action-evidence premium">
          <div>
            <span className="action-label">NASA EARTH OBSERVATIONS & MODELS USED</span>
            <div className="evidence-name-grid">
              <p><b>NASA POWER Daily (0.5°×0.625°)</b><span>14-day lag-safe temperature, rain, RH, wind & FAO-56 ET₀</span></p>
              <p><b>NASA POWER Climatology (2001–2020)</b><span>3-month historical temperature, rain & water-balance benchmark</span></p>
              <p><b>GPM IMERG Early V07B (~10 km)</b><span>Near-real-time spatial precipitation context (not a forecast)</span></p>
              <p><b>SMAP SPL3SMP_E V6 (9 km)</b><span>Regional top-5 cm soil moisture context (not pH or NPK)</span></p>
            </div>
          </div>
          <div>
            <span className="action-label">LOCAL AGRONOMIC & SOIL SOURCES USED</span>
            <div className="evidence-name-grid">
              {(brief.evidence?.agricultural_sources ?? []).slice(0, 6).map((source) => (
                <p key={source.name}><b>{source.name}</b><span>{source.scope}</span></p>
              ))}
              {(brief.evidence?.agricultural_sources ?? []).length === 0 && (
                <p><b>Local source review needed</b><span>No reviewed national adapter was available for this field.</span></p>
              )}
            </div>
          </div>
        </section>

        {/* Scientific Integrity Boundary */}
        <section className="plan-limitations">
          <FieldIcon name="unknown" />
          <div>
            <span className="action-label">SCIENTIFIC BOUNDARY & VERIFICATION NOTICE</span>
            <p>{lang === "bn" ? brief.limitations.bn : brief.limitations.en}</p>
            <p>
              {lang === "bn"
                ? "সতর্কতা: উপগ্রহ ডেটা কখনোই মাঠের মাটির pH বা সারের বিকল্প নয়। জেলার মাটির ধরন ও ফসলের সুযোগ প্রাথমিক অনুমান—উপজেলা পর্যায়ে SRDI, BMD, BARC ও উদ্ভিদ সংগনিরোধ/জাতীয় বীজ বোর্ডের অনুমোদন যাচাই করে চূড়ান্ত সিদ্ধান্ত নিন।"
                : "Caution: Satellite grids never replace a laboratory soil test. District soil/analog profiles are preliminary estimates requiring upazila-level SRDI, BMD, and BARC verification, plus Plant Quarantine and National Seed Board clearance for new seeds."}
            </p>
          </div>
        </section>

        <footer className="action-footer premium">
          <strong>Team EARTH.exe · BoponX (From Space to Soil)</strong>
          <span>NASA Space Apps Challenge 2026 · Field Shift: Adapting Farms with NASA Data</span>
          <small>Independent Team EARTH.exe decision-support project. NASA does not endorse BoponX.</small>
        </footer>
      </div>
    </section>
  );
}
