import { useRef, type PointerEvent } from "react";

/**
 * Stylized, CSS-extruded Bangladesh silhouette.
 * Boundary: Natural Earth ne_110m_admin_0_countries, Bangladesh feature,
 * public domain. This is cartographic artwork, not survey-grade geography.
 * Rivers, terrain shading, radar rings and satellite graphics are illustrative.
 * The Rajshahi marker is the provisional POWER API reference point.
 */
const COUNTRY = "M494.9 468.5 L493.1 533.0 L461.7 519.4 L467.6 591.8 L441.9 544.9 L436.7 499.0 L419.5 455.7 L381.9 403.3 L299.0 399.7 L307.2 436.8 L279.0 486.9 L240.7 468.7 L227.6 485.0 L202.1 475.2 L167.3 467.2 L153.3 393.1 L122.1 325.4 L137.4 271.2 L82.0 247.0 L102.0 214.2 L158.2 180.7 L93.3 133.1 L125.1 72.0 L196.4 110.9 L239.3 115.3 L247.3 177.9 L332.9 190.3 L416.4 188.9 L468.3 204.3 L426.8 280.5 L386.5 285.6 L358.7 336.9 L408.0 383.5 L422.7 326.0 L447.5 325.7 L494.9 468.5 Z";

export default function BangladeshAtlas({ dataReady }: { dataReady: boolean }) {
  const stage = useRef<HTMLDivElement>(null);
  function onMove(event: PointerEvent<HTMLDivElement>) {
    if (event.pointerType !== "mouse" || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const element = stage.current;
    if (!element) return;
    const box = element.getBoundingClientRect();
    const x = (event.clientX - box.left) / box.width - 0.5;
    const y = (event.clientY - box.top) / box.height - 0.5;
    element.style.setProperty("--atlas-y", `${(x * 11).toFixed(2)}deg`);
    element.style.setProperty("--atlas-x", `${(-y * 9).toFixed(2)}deg`);
  }
  function reset() {
    stage.current?.style.setProperty("--atlas-y", "0deg");
    stage.current?.style.setProperty("--atlas-x", "0deg");
  }
  return (
    <section className="atlas-section" id="atlas" aria-labelledby="atlas-title">
      <div className="atlas-copy">
        <span className="atlas-kicker">EARTH.exe / BANGLADESH TERRAIN SYSTEM <b lang="bn">· বাংলাদেশ ভূদৃশ্য</b></span>
        <h2 id="atlas-title">One country.<br /><em>Every field matters.</em></h2>
        <p className="atlas-title-bn" lang="bn">এক দেশ। প্রতিটি জমিই গুরুত্বপূর্ণ।</p>
        <p className="atlas-description">
          An immersive view of Bangladesh, grounded in one verified regional pilot—not a claim of nationwide farm coverage.
          <span lang="bn">বাংলাদেশের ত্রিমাত্রিক ধারণাগত দৃশ্য। যাচাইকৃত ডেটা এখন শুধু রাজশাহী অঞ্চলের পাইলটের জন্য; সারা দেশের জমির তথ্য নয়।</span>
        </p>
        <div className="atlas-proof">
          <span className={dataReady ? "atlas-led active" : "atlas-led"} />
          <div><strong>{dataReady ? "2024 NASA data connected" : "Waiting for pilot data"}</strong>
            <span lang="bn">{dataReady ? "২০২৪ সালের NASA ডেটা সংযুক্ত" : "পাইলট ডেটার অপেক্ষায়"}</span></div>
        </div>
        <a className="atlas-cta" href="#farm"><span>Start my three-month brief <small lang="bn">আমার তিন মাসের প্রস্তুতি পরিকল্পনা</small></span><b aria-hidden="true">↗</b></a>
        <p className="atlas-fine">Map source: Natural Earth 1:110m, public domain. Regional pin: provisional POWER coordinate. Visual effects are artwork, not observations.
          <span lang="bn">মানচিত্র: Natural Earth। পিন: NASA POWER-এর অস্থায়ী রেফারেন্স পয়েন্ট।</span>
        </p>
      </div>
      <figure className="atlas-canvas" aria-label="Illustrative three-dimensional Bangladesh outline with a Rajshahi pilot location pin">
        <div className="atlas-stage" ref={stage} onPointerMove={onMove} onPointerLeave={reset} aria-hidden="true">
          <div className="atlas-grid" />
          <div className="atlas-radar radar-a" /><div className="atlas-radar radar-b" />
          <div className="atlas-compass"><span>N</span><i /><span lang="bn">উত্তর</span></div>
          <div className="atlas-world">
            <svg className="atlas-country" viewBox="0 0 590 670" preserveAspectRatio="xMidYMid meet">
              <defs>
                <linearGradient id="atlasLand" x1="0" x2="1" y1="0" y2="1">
                  <stop offset="0" stopColor="#d8eba0" /><stop offset=".31" stopColor="#9bbd71" />
                  <stop offset=".68" stopColor="#3b7752" /><stop offset="1" stopColor="#164737" />
                </linearGradient>
                <linearGradient id="atlasRiver" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0" stopColor="#8de2e9" stopOpacity=".13"/><stop offset=".5" stopColor="#adeaf0" stopOpacity=".75"/>
                  <stop offset="1" stopColor="#5db1c7" stopOpacity=".18"/>
                </linearGradient>
                <radialGradient id="atlasBeacon">
                  <stop offset="0" stopColor="#fff2bc" /><stop offset=".5" stopColor="#ed344d" /><stop offset="1" stopColor="#d6193c" stopOpacity=".1" />
                </radialGradient>
                <clipPath id="atlasClip"><path d={COUNTRY}/></clipPath>
                <pattern id="atlasFields" patternUnits="userSpaceOnUse" width="25" height="25" patternTransform="rotate(24)">
                  <path d="M0 0 V25 M0 0 H25" stroke="#eff3c7" strokeOpacity=".17" strokeWidth="2"/>
                  <path d="M7 0 V25 M15 0 V25" stroke="#183c30" strokeOpacity=".14" strokeWidth="1.4"/>
                </pattern>
              </defs>
              {Array.from({ length: 12 }).map((_,i) => (
                <path key={i} d={COUNTRY} transform={`translate(0 ${30-i*2.1})`}
                  fill={i > 7 ? "#1f674a" : "#0a302a"} stroke="#a2cc8290" strokeWidth=".6"/>
              ))}
              <path d={COUNTRY} fill="url(#atlasLand)" stroke="#d6f7ad" strokeWidth="2.6" />
              <g clipPath="url(#atlasClip)">
                <path d="M0 0 H590 V670 H0Z" fill="url(#atlasFields)"/>
                <path d="M55 175 Q170 240 274 240 T555 450 M140 80 Q260 185 240 320 T458 590" fill="none"
                  stroke="url(#atlasRiver)" strokeWidth="25" strokeLinecap="round"/>
                <path d="M220 80 Q270 255 375 365 T535 630 M62 293 Q170 314 265 440 T495 600" fill="none"
                  stroke="#a3e4ec" strokeOpacity=".28" strokeWidth="7" strokeLinecap="round"/>
                <g className="atlas-scan"><path d="M65 210 L565 210" stroke="#eafdc5" strokeOpacity=".55" strokeWidth="2.5"/></g>
              </g>
              <path d={COUNTRY} fill="none" stroke="#f3ffca" strokeOpacity=".6" strokeWidth="1" />
              <g className="atlas-marker">
                <circle cx="128.4" cy="258.9" r="37" fill="none" stroke="#ecf9c9" strokeOpacity=".6" strokeWidth="1.4"/>
                <circle cx="128.4" cy="258.9" r="23" fill="none" stroke="#f73b57" strokeOpacity=".8" strokeWidth="2"/>
                <circle cx="128.4" cy="258.9" r="10" fill="url(#atlasBeacon)" />
                <circle cx="128.4" cy="258.9" r="4" fill="#ffe6a5"/>
                <path d="M143 247 L198 205 L310 205" fill="none" stroke="#f7f2d0" strokeOpacity=".9" strokeWidth="1.4"/>
                <text x="203" y="196" fill="#fff9df" fontSize="14" fontWeight="800" letterSpacing="2">RAJSHAHI</text>
                <text x="203" y="217" fill="#cde9bc" fontSize="13" fontWeight="650">রাজশাহী পাইলট</text>
              </g>
            </svg>
          </div>
          <span className="atlas-orb orb-one"/><span className="atlas-orb orb-two"/>
          <div className="atlas-hud">
            <span>24.37° N / 88.60° E</span><b>01 / 01 <i>ACTIVE PILOT</i></b>
          </div>
        </div>
        <figcaption className="atlas-caption">BANGLADESH / CONCEPTUAL MAP <span lang="bn">· বাংলাদেশ / ধারণাগত মানচিত্র</span></figcaption>
      </figure>
    </section>
  );
}
