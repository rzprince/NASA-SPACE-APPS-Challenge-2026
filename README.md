&lt;div align=&quot;center&quot;&gt;

&lt;!-- LIVE ANIMATED HERO WAVE BANNER --&gt;
&lt;img src=&quot;https://capsule-render.vercel.app/api?type=waving&amp;color=0:04120b,50:0b2e1c,100:b8ff57&amp;height=230&amp;section=header&amp;text=BoponX%20%C2%B7%20%E0%A6%AC%E0%A6%AA%E0%A6%A8%E0%A6%8F%E0%A6%95%E0%A7%8D%E0%A6%B8&amp;fontSize=54&amp;fontColor=ffffff&amp;fontAlignY=38&amp;desc=From%20Space%20to%20Soil%20%E2%80%94%20Next-Generation%20Agricultural%20Decision%20Intelligence&amp;descAlignY=60&amp;descSize=18&amp;animation=fadeIn&quot; width=&quot;100%&quot; alt=&quot;BoponX Animated Header&quot; /&gt;

&lt;!-- LIVE ANIMATED TYPING SUBTITLE --&gt;
&lt;a href=&quot;https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026&quot;&gt;
  &lt;img src=&quot;https://readme-typing-svg.demolab.com?font=Inter&amp;weight=700&amp;size=22&amp;duration=3200&amp;pause=900&amp;color=B8FF57&amp;background=06110B00&amp;center=true&amp;vCenter=true&amp;width=860&amp;lines=NASA+Space+Apps+Challenge+2026+%C2%B7+Field+Shift;3D+Interactive+Earth+Twin+%2B+Real-Time+NASA+Satellite+Telemetry;All+64+Districts+of+Bangladesh+%C2%B7+Bilingual+(English+%2B+%E0%A6%AC%E0%A6%BE%E0%A6%82%E0%A6%B2%E0%A6%BE);Developed+by+Rezwan+Hossain+Prince+%26+Team+EARTH.exe&quot; alt=&quot;Animated Typing Headline&quot; /&gt;
&lt;/a&gt;

<br/>

&lt;!-- MISSION &amp; STATUS BADGES --&gt;
[NASA Space Apps 2026](https://www.google.com/search?q=https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026)
[](https://github.com/rzprince)
[](https://github.com/rzprince)
[Bilingual](https://www.google.com/search?q=https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026)
[License](https://www.google.com/search?q=./LICENSE)

&lt;/div&gt;

## Overview

**BoponX (`বপনএক্স: মহাকাশ থেকে মাটিতে`)** is an agricultural decision-support platform created for the **2026 NASA International Space Apps Challenge** (*Challenge: Field Shift — Adapting Farms with NASA Data*).

Shifting monsoon onset dates, erratic dry spells, heat stress, and continuous monoculture cropping threaten farm livelihoods across climate-vulnerable deltas. **BoponX** bridges the gap between orbital Earth observations and field-level action by fusing multi-mission NASA satellite streams with localized agro-ecological context across **all 64 districts and 8 divisions of Bangladesh**, delivering clear, bilingual (**English + বাংলা**) guidance for farmers, extension officers, and decision-makers.

&lt;div align=&quot;center&quot;&gt;
  &lt;img src=&quot;https://readme-typing-svg.demolab.com?font=DM+Mono&amp;weight=500&amp;size=15&amp;duration=2800&amp;pause=1000&amp;color=38BDF8&amp;background=06110B00&amp;center=true&amp;vCenter=true&amp;width=780&amp;lines=01+Location+%E2%86%92+3D+Earth+Twin+%26+Live+NASA+Telemetry;02+Analysis+%E2%86%92+Planting-Window+Shift+%26+Rotation+Workbench;03+Field+Plan+%E2%86%92+90-Day+Bilingual+Action+Sheet+%26+SMS+Advisory&quot; alt=&quot;Workflow Animation&quot; /&gt;
&lt;/div&gt;

## Core Experience

| Stage | Module | What It Delivers |
| :--- | :--- | :--- |
| **01 · Location** | **3D Earth Twin & Telemetry Hub** | Interactive 3D Globe and 2D field map with live [NASA GIBS / Worldview](https://worldview.earthdata.nasa.gov/) satellite layers, 64-district Bangladesh quick-locator, agroclimatic water balance via [NASA POWER](https://power.larc.nasa.gov/docs/services/api/temporal/daily/), and live natural hazard tracking via [NASA EONET v3](https://eonet.gsfc.nasa.gov/docs/v3). |
| **02 · Analysis** | **Planting-Window & Rotation Lab** | Multi-decade usable-rain onset shift detection, single-segment mobile SMS farmer advisories (`EN` & `বাংলা`), interactive climate stress-testing sliders, and multi-season crop-rotation exploration grounded in [BAMIS](https://www.bamis.gov.bd/), [BARC](https://barc.gov.bd/), and [SRDI](https://srdi.gov.bd/) references. |
| **03 · 90-Day Plan** | **Printable Field Action Card** | A standalone, offline-ready 90-day field plan organized into three 30-day operational phases (`Days 1–30`, `Days 31–60`, `Days 61–90`) with verifiable source attribution and [DAE](https://dae.gov.bd/) (`16123`) extension routing. |

## Earth Observation & Local Data Ecosystem

| Mission / Authority | Role in BoponX | Official Source |
| :--- | :--- | :--- |
| **NASA POWER** | Daily agroclimatology, rainfall, temperature, evaporative demand, and root-zone wetness context | [NASA POWER API](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) |
| **NASA GPM IMERG** | High-resolution precipitation monitoring and multi-date storm comparison | [NASA GPM IMERG](https://gpm.nasa.gov/data/imerg) |
| **NASA SMAP** | Surface soil moisture context for seedbed readiness | [NSIDC SMAP](https://nsidc.org/data/spl3smp_e/versions/6) |
| **NASA GIBS / MODIS / SRTM** | Canopy greenness (`NDVI`), daytime land surface temperature (`LST`), and topographic relief | [NASA Worldview](https://worldview.earthdata.nasa.gov/) |
| **NASA EONET v3** | Near-real-time cyclone, flood, and severe storm tracking | [NASA EONET v3](https://eonet.gsfc.nasa.gov/docs/v3) |
| **Bangladesh Agricultural Authorities** | Regional crop calendars, agro-ecological zone references, and farmer helpline (`16123`) | [BAMIS](https://www.bamis.gov.bd/) · [BARC](https://barc.gov.bd/) · [SRDI](https://srdi.gov.bd/) · [DAE](https://dae.gov.bd/) |

## Quick Start — How to Run

### Prerequisites
- **Python** `3.10+`
- **Node.js** `18+` and **npm**

### Run on Windows (PowerShell)

**1. Clone the repository and start the backend API (`http://127.0.0.1:8000`):**
```powershell
git clone https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026.git
cd NASA-SPACE-APPS-Challenge-2026

python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt -r .\backend\requirements-dev.txt

Remove-Item Env:OFFLINE -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

**2. Open a second PowerShell window and start the web interface (`http://127.0.0.1:5173`):**
```powershell
cd NASA-SPACE-APPS-Challenge-2026\frontend
npm install
npm run dev
```

### Run on macOS / Linux (Terminal)

**1. Clone the repository and start the backend API (`http://127.0.0.1:8000`):**
```bash
git clone https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026.git
cd NASA-SPACE-APPS-Challenge-2026

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt -r backend/requirements-dev.txt

unset OFFLINE
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

**2. Open a second Terminal tab and start the web interface (`http://127.0.0.1:5173`):**
```bash
cd NASA-SPACE-APPS-Challenge-2026/frontend
npm install
npm run dev
```

## Team & Authorship

- **Developed by:** [Rezwan Hossain Prince](https://github.com/rzprince) and **Team EARTH.exe**
- **Competition:** 2026 NASA International Space Apps Challenge
- **License:** Released under the [Apache License 2.0](https://www.google.com/search?q=./LICENSE)

&lt;div align=&quot;center&quot;&gt;
  &lt;img src=&quot;https://capsule-render.vercel.app/api?type=waving&amp;color=0:b8ff57,50:0b2e1c,100:04120b&amp;height=110&amp;section=footer&quot; width=&quot;100%&quot; alt=&quot;BoponX Animated Footer&quot; /&gt;
&lt;/div&gt;
