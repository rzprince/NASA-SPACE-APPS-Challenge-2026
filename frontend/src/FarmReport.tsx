import { useEffect } from "react";

export type PlanTask = { code: string; en: string; bn: string };
export type PlanMonth = {
  month_index: number;
  planning_month: string;
  historical_reference_month: string | null;
  historical_temperature_c: number | null;
  historical_precipitation_mm: number | null;
  historical_valid_days: { temperature: number; precipitation: number; expected: number };
  tasks: PlanTask[];
};
export type PlanBrief = {
  schema_version: "boponx-preparation-brief/v1";
  status: "DRAFT_NOT_AN_AGRONOMIC_CROP_PLAN";
  location_id: string;
  farm: {
    previous_crop: string | null;
    soil_ph: number | null;
    soil_texture: string;
    irrigation_mode: string;
    priority: string | null;
    priority_label: [string,string] | null;
    candidate_crop_farmer_entered: string | null;
    missing_inputs: { field: string; en: string; bn: string }[];
  };
  planning_window: {start:string;end:string};
  months: PlanMonth[];
  evidence: {
    provider:string;source_products:string[];snapshot_id:string;
    source_request_url:string;historical_year:string;time_standard:string;
  };
  limitations: {en:string;bn:string};
};

const monthNames = [
  ["January","জানুয়ারি"],["February","ফেব্রুয়ারি"],["March","মার্চ"],
  ["April","এপ্রিল"],["May","মে"],["June","জুন"],
  ["July","জুলাই"],["August","আগস্ট"],["September","সেপ্টেম্বর"],
  ["October","অক্টোবর"],["November","নভেম্বর"],["December","ডিসেম্বর"]
];
const soilText:Record<string,[string,string]> = {
  unknown:["Not tested","পরীক্ষা করা হয়নি"],sandy:["Sandy","বেলে"],
  loamy:["Loamy","দোআঁশ"],clayey:["Clayey","এঁটেল"]
};
const waterText:Record<string,[string,string]> = {
  unknown:["Unknown","অজানা"],none:["No irrigation","সেচ নেই"],
  limited:["Limited irrigation","সীমিত সেচ"],reliable:["Reliable irrigation","নির্ভরযোগ্য সেচ"]
};
function monthLabel(value:string):[string,string] {
  const year=value.slice(0,4);
  const month=Number(value.slice(5,7));
  return [`${monthNames[month-1]?.[0] ?? value} ${year}`,`${monthNames[month-1]?.[1] ?? value} ${new Intl.NumberFormat("bn-BD",{useGrouping:false}).format(Number(year))}`];
}
function fmt(n:number|null,d=1) {
  return n===null ? "—" : new Intl.NumberFormat("en-BD",{maximumFractionDigits:d}).format(n);
}

export default function FarmReport({brief}:{brief:PlanBrief}) {
  useEffect(() => {
    if (window.location.hash === "#boponx-report") {
      document.getElementById("boponx-report")?.scrollIntoView({behavior:"smooth"});
    }
  },[brief]);
  function printBrief() {
    const previous=document.title;
    document.title=`BoponX_3_month_preparation_${brief.planning_window.start}`;
    window.print();
    window.setTimeout(() => {document.title=previous},1500);
  }
  const [firstEn,firstBn]=monthLabel(brief.planning_window.start);
  const [lastEn,lastBn]=monthLabel(brief.planning_window.end);
  return <section className="report-section" id="boponx-report" aria-labelledby="report-title">
    <div className="report-shell">
      <div className="report-toolbar">
        <div className="report-toolbar__status"><i aria-hidden="true"/>DRAFT GENERATED · <span lang="bn">খসড়া তৈরি হয়েছে</span></div>
        <button type="button" className="report-print" onClick={printBrief}>
          <span>Print / Save as PDF <small lang="bn">প্রিন্ট / PDF হিসেবে সংরক্ষণ</small></span>
          <b aria-hidden="true">↗</b>
        </button>
      </div>
      <header className="report-cover report-print-header">
        <div className="report-cover__meta"><span>EARTH.exe / BOPONX</span><span>BD · PILOT 01</span></div>
        <span className="report-overline">YOUR THREE-MONTH FIELD BRIEF · <b lang="bn">আপনার তিন মাসের জমির প্রস্তুতি নোট</b></span>
        <h2 id="report-title">Your farm.<br/><em>Your next steps.</em></h2>
        <p className="report-cover__bangla" lang="bn">আপনার জমি। পরবর্তী তিন মাসের প্রস্তুতি ও পর্যবেক্ষণ।</p>
        <div className="report-period"><span>{firstEn} → {lastEn}<small lang="bn">{firstBn} → {lastBn}</small></span><strong>03 <i>MONTHS</i></strong></div>
        <div className="report-warning" role="note">
          <strong>PREPARATION BRIEF — NOT A CROP PRESCRIPTION</strong>
          <span lang="bn">এটি প্রস্তুতি ও পর্যবেক্ষণের খসড়া — কোনো ফসল বা বপনের নির্দেশ নয়।</span>
          <p>{brief.limitations.en}</p><p lang="bn">{brief.limitations.bn}</p>
        </div>
        <div className="report-facts">
          <div><span>Region <small lang="bn">অঞ্চল</small></span><strong>Rajshahi pilot <small lang="bn">রাজশাহী পাইলট</small></strong></div>
          <div><span>Priority <small lang="bn">অগ্রাধিকার</small></span><strong>{brief.farm.priority_label?.[0] ?? "Not selected"}<small lang="bn">{brief.farm.priority_label?.[1] ?? "নির্বাচিত হয়নি"}</small></strong></div>
          <div><span>Soil <small lang="bn">মাটি</small></span><strong>{soilText[brief.farm.soil_texture]?.[0] ?? "Unknown"}<small lang="bn">{soilText[brief.farm.soil_texture]?.[1] ?? "অজানা"}</small></strong></div>
          <div><span>Irrigation <small lang="bn">সেচ</small></span><strong>{waterText[brief.farm.irrigation_mode]?.[0] ?? "Unknown"}<small lang="bn">{waterText[brief.farm.irrigation_mode]?.[1] ?? "অজানা"}</small></strong></div>
        </div>
        <div className="report-personal">
          <div><b>Previous crop / <span lang="bn">আগের ফসল</span></b><span>{brief.farm.previous_crop ?? "Not supplied · দেওয়া হয়নি"}</span></div>
          <div><b>Known soil pH / <span lang="bn">মাটির pH</span></b><span>{brief.farm.soil_ph ?? "Not tested · পরীক্ষা করা হয়নি"}</span></div>
          <div><b>Farmer-considered crop / <span lang="bn">কৃষকের বিবেচনায় ফসল</span></b><span>{brief.farm.candidate_crop_farmer_entered ?? "Not supplied · দেওয়া হয়নি"}<small> Not a BoponX recommendation · BoponX-এর সুপারিশ নয়</small></span></div>
        </div>
        {brief.farm.missing_inputs.length > 0 && <div className="report-missing">
          <strong>Information to confirm · <span lang="bn">যে তথ্য যাচাই করা প্রয়োজন</span></strong>
          <p>{brief.farm.missing_inputs.map(x=>x.en).join(" · ")}</p>
          <p lang="bn">{brief.farm.missing_inputs.map(x=>x.bn).join(" · ")}</p>
        </div>}
      </header>
      <div className="report-months">
        {brief.months.map((month) => {
          const [en,bn]=monthLabel(month.planning_month);
          const [refEn,refBn]=month.historical_reference_month ? monthLabel(month.historical_reference_month):["Unavailable","পাওয়া যায়নি"];
          return <article className="report-month report-print-page" key={month.planning_month}>
            <div className="report-month__header"><div><span>MONTH {String(month.month_index).padStart(2,"0")} / 03 <small lang="bn">· মাস {new Intl.NumberFormat("bn-BD",{useGrouping:false}).format(month.month_index)}</small></span>
              <h3>{en}<b lang="bn">{bn}</b></h3></div><div className="report-month__index">{String(month.month_index).padStart(2,"0")}</div></div>
            <div className="report-reference">
              <div><span>Historical rainfall · <b lang="bn">ঐতিহাসিক বৃষ্টিপাত</b></span><strong>{fmt(month.historical_precipitation_mm)} <small>mm</small></strong></div>
              <div><span>Historical temperature · <b lang="bn">ঐতিহাসিক তাপমাত্রা</b></span><strong>{fmt(month.historical_temperature_c)} <small>°C</small></strong></div>
              <p>Reference: NASA POWER / MERRA-2, {refEn} ({month.historical_valid_days.precipitation}/{month.historical_valid_days.expected} valid rainfall days).
                <span lang="bn">উৎস: NASA POWER / MERRA-2, {refBn}। এটি {en}-এর আবহাওয়ার পূর্বাভাস নয়।</span>
              </p>
            </div>
            <div className="report-task-heading">MY FIELD ROUTINE <span lang="bn">· আমার জমির পর্যবেক্ষণ তালিকা</span><small>✓ Check items only after completing them / কাজ শেষ হলে টিক দিন</small></div>
            <ol className="report-tasks">
              {month.tasks.map((task,index)=><li key={task.code}>
                <label><input type="checkbox" aria-label={task.en} /><span className="report-task-count">{String(index+1).padStart(2,"0")}</span>
                  <span className="report-task-copy"><span>{task.en}</span><span lang="bn">{task.bn}</span></span>
                </label>
              </li>)}
            </ol>
            <div className="report-notes"><strong>Field notes / <span lang="bn">জমির নোট</span></strong>
              <div className="report-note-lines" aria-hidden="true"><i/><i/><i/></div></div>
            <div className="report-month__footer">BoponX · Team EARTH.exe <span>Historic data ≠ forecast · <b lang="bn">ঐতিহাসিক তথ্য ≠ পূর্বাভাস</b></span></div>
          </article>;
        })}
      </div>
      <section className="report-evidence">
        <div><strong>Traceable evidence · <span lang="bn">যাচাইযোগ্য প্রমাণ</span></strong>
          <p>Original NASA POWER historical data. Source product: {brief.evidence.source_products.join(", ")||"unreported"}. Snapshot: <code>{brief.evidence.snapshot_id}</code>. Local solar time: {brief.evidence.time_standard}.</p>
          <p lang="bn">NASA POWER-এর ঐতিহাসিক তথ্য। ডেটার ধরন: পুনর্বিশ্লেষণ; স্থানীয় জমির পরিমাপ নয়।</p></div>
        <a href={brief.evidence.source_request_url} target="_blank" rel="noreferrer">Original source / <span lang="bn">মূল উৎস</span> ↗</a>
      </section>
      <p className="report-download-tip">Choose <b>Save as PDF</b> in your browser's print dialog. On Android, choose <b>Print → Save as PDF</b>.
        <span lang="bn">প্রিন্ট মেনুতে <b>Save as PDF</b> নির্বাচন করুন। এই নোটটি আপনার ফোন বা কম্পিউটারে PDF হিসেবে সংরক্ষণ হবে।</span></p>
    </div>
  </section>;
}
