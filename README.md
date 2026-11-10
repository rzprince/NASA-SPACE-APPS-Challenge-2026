![BoponX Animated Header](https://capsule-render.vercel.app/api?type=waving&color=0:04120b,50:0b2e1c,100:b8ff57&height=230&section=header&text=BoponX%20%C2%B7%20%E0%A6%AC%E0%A6%AA%E0%A6%A8%E0%A6%8F%E0%A6%95%E0%A7%8D%E0%A6%B8&fontSize=54&fontColor=ffffff&fontAlignY=38&desc=From%20Space%20to%20Soil%20%E2%80%94%20Next-Generation%20Agricultural%20Decision%20Intelligence&descAlignY=60&descSize=18&animation=fadeIn)

[![Animated Typing Headline](https://readme-typing-svg.demolab.com?font=Inter&weight=700&size=22&duration=3200&pause=900&color=B8FF57&background=06110B00&center=true&vCenter=true&width=1000&lines=NASA+Space+Apps+Challenge+2026+%C2%B7+Field+Shift;3D+Interactive+Earth+Twin+%2B+Real-Time+NASA+Satellite+Telemetry;All+64+Districts+of+Bangladesh+%C2%B7+Bilingual+(English+%2B+%E0%A6%AC%E0%A6%BE%E0%A6%82%E0%A6%B2%E0%A6%BE);Developed+by+Rezwan+Hossain+Prince+(Team+Leader)+%26+Team+EARTH.exe)](https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026)

[![NASA Space Apps 2026](https://img.shields.io/badge/NASA_Space_Apps_2026-Field_Shift-0b3d91?style=for-the-badge&logo=nasa&logoColor=white)](https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026) [![Team EARTH.exe](https://img.shields.io/badge/Team-EARTH.exe-b8ff57?style=for-the-badge&labelColor=06110b)](https://github.com/rzprince) [![Team Leader](https://img.shields.io/badge/Team_Leader-Rezwan_Hossain_Prince-22c55e?style=for-the-badge&labelColor=06110b)](https://github.com/rzprince) [![Bilingual](https://img.shields.io/badge/Language-English_%2B_%E0%A6%AC%E0%A6%BE%E0%A6%82%E0%A6%B2%E0%A6%BE-38bdf8?style=for-the-badge&labelColor=06110b)](https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026) [![License](https://img.shields.io/badge/License-Apache_2.0-f59e0b?style=for-the-badge&labelColor=06110b)](https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026/blob/main/LICENSE)

## Overview

**BoponX (`বপনএক্স: মহাকাশ থেকে মাটিতে`)** is an agricultural decision-support platform created for the **2026 NASA International Space Apps Challenge** (*Challenge: Field Shift — Adapting Farms with NASA Data*).

Shifting monsoon onset dates, erratic dry spells, heat stress, and continuous monoculture cropping threaten farm livelihoods across climate-vulnerable deltas. **BoponX** bridges the gap between orbital Earth observations and field-level action by fusing multi-mission NASA satellite streams with localized agro-ecological context across **all 64 districts and 8 divisions of Bangladesh**, delivering clear, bilingual (**English + বাংলা**) guidance for farmers, extension officers, and decision-makers.

![Workflow Animation](https://readme-typing-svg.demolab.com?font=DM+Mono&weight=500&size=16&duration=2800&pause=1000&color=38BDF8&background=06110B00&center=true&vCenter=true&width=1000&lines=01+Location+%E2%86%92+3D+Earth+Twin+%26+Live+NASA+Telemetry;02+Analysis+%E2%86%92+Planting-Window+Shift+%26+Rotation+Workbench;03+Field+Plan+%E2%86%92+90-Day+Bilingual+Action+Sheet+%26+SMS+Advisory)

## Core Experience

| Stage | Module | What It Delivers |
| :--- | :--- | :--- |
| **01 · Location** | **3D Earth Twin & Telemetry Hub** | Interactive 3D Globe and 2D field map with live [NASA GIBS / Worldview](https://worldview.earthdata.nasa.gov/) satellite layers, 64-district Bangladesh quick-locator, agroclimatic water balance via [NASA POWER](https://power.larc.nasa.gov/docs/services/api/temporal/daily/), and live natural hazard tracking via [NASA EONET v3](https://eonet.gsfc.nasa.gov/docs/v3). |
| **02 · Analysis** | **Planting-Window & Rotation Lab** | Multi-decade usable-rain onset shift detection, single-segment mobile SMS farmer advisories (`EN` & `বাংলা`), interactive climate stress-testing sliders, and multi-season crop-rotation exploration grounded in [BAMIS](https://www.bamis.gov.bd/), [BARC](https://barc.gov.bd/), and [SRDI](https://srdi.gov.bd/) references. |
| **03 · 90-Day Plan** | **Printable Field Action Card** | A standalone, offline-ready 90-day field plan organized into three 30-day operational phases (`Days 1–30`, `Days 31–60`, `Days 61–90`) with verifiable source attribution and [DAE](https://dae.gov.bd/) (`16123`) extension routing. |

## Floating Field Assistant

The BoponX logo opens a floating assistant available throughout the dashboard. It uses the dashboard's current NASA and location data to answer supported questions and can control these app features:

- Navigate to Location, Analysis, and the 90-Day Plan.
- Show NASA GPM rainfall, SMAP soil-moisture, MODIS NDVI and temperature, or true-colour map layers.
- Select a Bangladesh district or division, or request the browser's current GPS location.
- Switch English/Bangla, set the intended crop and change the farmer priority.
- Generate the 90-day plan using the currently selected field profile.

Type a request or use the microphone in a browser with Web Speech Recognition support (for example, Chrome or Edge); microphone access requires permission. The assistant is a built-in, command-oriented helper, not a generative AI service. It does not send chat messages to an LLM. Voice recognition is provided by the browser and its processing/privacy behavior depends on that browser. Satellite wetness is not a soil pH/NPK test, and assistant outputs should be verified with local agricultural extension staff.

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

- **Developed by:** [Rezwan Hossain Prince](https://github.com/rzprince) (Team Leader) and **Team EARTH.exe**
- **Competition:** 2026 NASA International Space Apps Challenge
- **License:** Released under the [Apache License 2.0](https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026/blob/main/LICENSE)

![BoponX Animated Footer](https://capsule-render.vercel.app/api?type=waving&color=0:b8ff57,50:0b2e1c,100:04120b&height=110&section=footer)#   N a s a - S p a c e - A p p - C h a t b o t  
 #   N a s a - S p a c e - A p p - C h a t b o t  
 