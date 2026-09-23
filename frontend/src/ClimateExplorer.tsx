import { useEffect, useMemo, useState, type CSSProperties } from "react";
import { apiGet, type ClimateSnapshot } from "./api";

type MonthRecord = {
  month: string;
  days_expected: number;
  temperature_valid_days: number;
  precipitation_valid_days: number;
  temperature_mean_c: number | null;
  precipitation_total_mm: number | null;
};
type MonthlyResponse = {
  schema_version: "boponx-monthly/v1";
  snapshot_id: string;
  provider: string;
  source_products: string[];
  source_request_url: string;
  resolution_note: string;
  scenario_note: string;
  metrics: MonthRecord[];
};
type Mode = "temperature" | "rain";
type DepthStyle = CSSProperties & { "--rain-depth": string };

const monthsEn = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const monthsBn = ["জানু", "ফেব্রু", "মার্চ", "এপ্রিল", "মে", "জুন", "জুলাই", "আগস্ট", "সেপ্টে", "অক্টো", "নভে", "ডিসে"];

function monthLabel(value: string) {
  const index = Number(value.slice(5, 7)) - 1;
  return { en: monthsEn[index] ?? value, bn: monthsBn[index] ?? value };
}
function num(value: number | null, decimals = 1): string {
  return value === null ? "—" : new Intl.NumberFormat("en-BD", { maximumFractionDigits: decimals }).format(value);
}
function axisRange(values: number[], mode: Mode) {
  if (!values.length) return { min: 0, max: 1 };
  const min = mode === "rain" ? 0 : Math.floor(Math.min(...values) / 5) * 5 - 5;
  const max = Math.ceil(Math.max(...values) / 5) * 5 + (mode === "rain" ? 5 : 5);
  return { min, max: max <= min ? min + 1 : max };
}
function lineSegments(values: (number | null)[], y: (n: number) => number) {
  const segments: string[][] = [];
  let current: string[] = [];
  values.forEach((value, index) => {
    if (value === null) {
      if (current.length) segments.push(current);
      current = [];
    } else {
      current.push(`${62 + index * 52},${y(value)}`);
    }
  });
  if (current.length) segments.push(current);
  return segments;
}

export default function ClimateExplorer({ snapshot }: { snapshot: ClimateSnapshot }) {
  const [monthly, setMonthly] = useState<MonthlyResponse | null>(null);
  const [error, setError] = useState("");
  const [mode, setMode] = useState<Mode>("rain");
  const [selected, setSelected] = useState(0);

  useEffect(() => {
    let active = true;
    setMonthly(null);
    setError("");
    apiGet<MonthlyResponse>(`/api/v1/climate/${snapshot.location_id}/monthly`)
      .then((data) => {
        if (!active) return;
        if (data.snapshot_id !== snapshot.evidence.snapshot_id) {
          setError("Climate snapshots do not match / জলবায়ু স্ন্যাপশট মিলছে না।");
          return;
        }
        setMonthly(data);
      })
      .catch(() => { if (active) setError("Monthly climate analysis is unavailable / মাসিক জলবায়ু বিশ্লেষণ পাওয়া যাচ্ছে না।"); });
    return () => { active = false; };
  }, [snapshot.evidence.snapshot_id, snapshot.location_id]);

  const values = useMemo(
    () => monthly?.metrics.map((month) => mode === "rain" ? month.precipitation_total_mm : month.temperature_mean_c) ?? [],
    [monthly, mode],
  );
  const numeric = values.filter((value): value is number => value !== null);
  const axis = axisRange(numeric, mode);
  const y = (value: number) => 179 - ((value - axis.min) / (axis.max - axis.min)) * 137;
  const active = monthly?.metrics[selected] ?? null;
  const unit = mode === "rain" ? "mm" : "°C";
  const range = Math.max(...numeric, 1);

  if (!monthly) {
    return <div className="monthly-state" role="status">
      <span aria-hidden="true" className="monthly-state__spinner" />
      {error || "Loading verified monthly history / যাচাইকৃত মাসিক তথ্য লোড হচ্ছে"}
    </div>;
  }

  return (
    <div className="monthly-explorer">
      <div className="monthly-explorer__head">
        <div>
          <span className="micro-label">NASA POWER / 2024 HISTORY <span lang="bn">· ২০২৪ সালের ঐতিহাসিক তথ্য</span></span>
          <h3>Climate in context <span lang="bn">· জলবায়ুর প্রেক্ষাপট</span></h3>
          <p>One historical year. Twelve documented months. No forecast. <span lang="bn">এক বছরের ঐতিহাসিক তথ্য—ভবিষ্যৎ পূর্বাভাস নয়।</span></p>
        </div>
        <div className="monthly-switch" role="group" aria-label="Choose historical climate variable">
          <button type="button" className={mode === "rain" ? "active" : ""} aria-pressed={mode === "rain"} onClick={() => setMode("rain")}>Rainfall <small lang="bn">বৃষ্টি</small></button>
          <button type="button" className={mode === "temperature" ? "active" : ""} aria-pressed={mode === "temperature"} onClick={() => setMode("temperature")}>Temperature <small lang="bn">তাপমাত্রা</small></button>
        </div>
      </div>

      <div className="monthly-explorer__body">
        <div className="monthly-plot">
          <div className="monthly-plot__topline">
            <span>{mode === "rain" ? "MONTHLY RAINFALL · মাসিক বৃষ্টিপাত" : "MONTHLY TEMPERATURE · মাসিক তাপমাত্রা"}</span>
            <strong>{unit}</strong>
          </div>
          <p className="mobile-chart-hint">Swipe to see all months → <span lang="bn">সব মাস দেখতে পাশে সোয়াইপ করুন →</span></p>
          <svg className="monthly-plot__svg" viewBox="0 0 690 250" role="img"
            aria-label={mode === "rain" ? "Historical monthly precipitation in millimetres; incomplete months omitted" : "Historical monthly mean temperature in degrees Celsius; incomplete months omitted"}>
            {[0, 1, 2, 3].map((index) => {
              const value = axis.max - (axis.max - axis.min) * index / 3;
              const pos = y(value);
              return <g key={index}><line x1="62" x2="638" y1={pos} y2={pos} className="monthly-plot__grid" />
                <text x="48" y={pos + 4} textAnchor="end" className="monthly-plot__axis">{num(value, 0)}</text></g>;
            })}
            {mode === "rain" ? values.map((value, index) => {
              const height = value === null ? 0 : Math.max(0, 179 - y(value));
              return <rect key={index} x={49 + index * 52} y={value === null ? 179 : y(value)}
                width="26" height={height} rx="6" className={`monthly-plot__bar ${selected === index ? "selected" : ""}`}
                onClick={() => setSelected(index)} aria-label={`${monthLabel(monthly.metrics[index].month).en} rainfall: ${num(value)} mm`} />;
            }) : lineSegments(values, y).map((segment, index) =>
              <polyline key={index} points={segment.join(" ")} className="monthly-plot__line" />,
            )}
            {mode === "temperature" && values.map((value, index) => value === null ? null :
              <circle key={index} cx={62 + index * 52} cy={y(value)} r={selected === index ? 6 : 3.5}
                className={`monthly-plot__dot ${selected === index ? "selected" : ""}`}
                onClick={() => setSelected(index)} />,
            )}
            {monthly.metrics.map((month, index) =>
              <text key={month.month} x={62 + index * 52} y="223" textAnchor="middle"
                className={`monthly-plot__month ${selected === index ? "selected" : ""}`}>
                {monthLabel(month.month).en}
              </text>,
            )}
          </svg>
          <div className="month-picker" role="group" aria-label="Select a month for historical details">
            {monthly.metrics.map((month, index) =>
              <button type="button" key={month.month} className={selected === index ? "active" : ""}
                aria-pressed={selected === index} onClick={() => setSelected(index)}>
                <span>{monthLabel(month.month).en}</span><small lang="bn">{monthLabel(month.month).bn}</small>
              </button>,
            )}
          </div>
        </div>

        <aside className="monthly-detail" aria-live="polite">
          <div className="monthly-detail__overline">SELECTED MONTH <span lang="bn">· নির্বাচিত মাস</span></div>
          <h4>{active ? monthLabel(active.month).en : "—"}<span lang="bn">{active ? monthLabel(active.month).bn : ""}</span></h4>
          <div className="monthly-detail__metric"><span>Rainfall <small lang="bn">বৃষ্টিপাত</small></span>
            <strong>{num(active?.precipitation_total_mm ?? null)} <small>mm</small></strong>
            <span className="monthly-detail__coverage">{active?.precipitation_valid_days ?? 0}/{active?.days_expected ?? 0} valid days · বৈধ দিন</span>
          </div>
          <div className="monthly-detail__metric"><span>Mean temperature <small lang="bn">গড় তাপমাত্রা</small></span>
            <strong>{num(active?.temperature_mean_c ?? null)} <small>°C</small></strong>
            <span className="monthly-detail__coverage">{active?.temperature_valid_days ?? 0}/{active?.days_expected ?? 0} valid days · বৈধ দিন</span>
          </div>
          <p>Historical regional context, not an individual farm measurement.<span lang="bn">এটি আঞ্চলিক ঐতিহাসিক তথ্য; নির্দিষ্ট জমির পরিমাপ নয়।</span></p>
        </aside>
      </div>

      <section className="rain-terrain" aria-label="Interactive three-dimensional historical rainfall visualization">
        <div className="rain-terrain__intro">
          <div><span className="micro-label">3D DATA LANDSCAPE <span lang="bn">· ত্রিমাত্রিক ডেটা চিত্র</span></span>
            <h4>Twelve months. One landscape.<span lang="bn">বারো মাসের বৃষ্টি, এক দৃশ্য।</span></h4></div>
          <p>Column height represents the validated monthly precipitation total. Not satellite imagery or topography.<span lang="bn">স্তম্ভের উচ্চতা মাসিক বৃষ্টিপাত বোঝায়; এটি স্যাটেলাইট ছবি বা ভূমিরূপ নয়।</span></p>
        </div>
        <div className="rain-terrain__selected" aria-live="polite">
          <div><b>SELECTED HISTORICAL MONTH</b><small lang="bn">নির্বাচিত ঐতিহাসিক মাস · ২০২৪ সাল</small></div>
          <strong>{active ? monthLabel(active.month).en : "—"} · {num(active?.precipitation_total_mm ?? null)} mm <small lang="bn">{active ? monthLabel(active.month).bn : ""} · ঐতিহাসিক বৃষ্টি</small></strong>
        </div>
        <div className="rain-terrain__viewport">
          <div className="rain-terrain__plane" role="group" aria-label="Select one of twelve historical monthly precipitation columns">
            {monthly.metrics.map((record, index) => {
              const total = record.precipitation_total_mm;
              const depth = total === null ? 0 : Math.max(7, Math.round((total / range) * 110));
              const style: DepthStyle = { "--rain-depth": `${depth}px` };
              return <button key={record.month} type="button"
                className={`rain-terrain__column ${selected === index ? "selected" : ""} ${total === null ? "missing" : ""}`}
                style={style} aria-label={`${monthLabel(record.month).en}, rainfall ${total === null ? "missing" : `${num(total)} millimetres`}`}
                aria-pressed={selected === index} onClick={() => { setSelected(index); setMode("rain"); }}>
                <span className="rain-terrain__column-top" />
                <span className="rain-terrain__column-front" />
                <span className="rain-terrain__column-side" />
                <span className="rain-terrain__column-name">{monthLabel(record.month).en}</span>
              </button>;
            })}
          </div>
        </div>
      </section>

      <details className="monthly-access-table">
        <summary>Accessible month-by-month data table <span lang="bn">· মাসভিত্তিক তথ্যের তালিকা</span></summary>
        <div className="monthly-access-table__scroll"><table>
          <thead><tr><th scope="col">Month<br /><span lang="bn">মাস</span></th>
            <th scope="col">Rainfall (mm)<br /><span lang="bn">বৃষ্টিপাত</span></th>
            <th scope="col">Temperature (°C)<br /><span lang="bn">তাপমাত্রা</span></th>
            <th scope="col">Coverage<br /><span lang="bn">ডেটার পরিমাণ</span></th></tr></thead>
          <tbody>{monthly.metrics.map((month) => <tr key={month.month}>
            <th scope="row">{monthLabel(month.month).en} · {monthLabel(month.month).bn}</th>
            <td>{num(month.precipitation_total_mm)}</td>
            <td>{num(month.temperature_mean_c)}</td>
            <td>{month.precipitation_valid_days}/{month.days_expected} rain; {month.temperature_valid_days}/{month.days_expected} temp</td>
          </tr>)}</tbody>
        </table></div>
        <p>“—” means incomplete or missing data. A monthly total is not shown unless every expected daily reading is valid. <span lang="bn">যে মাসে ডেটা অসম্পূর্ণ, সেখানে পূর্ণ মাসের মান দেখানো হয়নি।</span></p>
      </details>
    </div>
  );
}
