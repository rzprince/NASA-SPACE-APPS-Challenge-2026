![BoponX & Team EARTH.exe Animated Hero Banner](./assets/boponx-hero-animated.svg)

[![Animated Typing Headline](https://readme-typing-svg.demolab.com?font=Inter&weight=700&size=21&duration=3200&pause=900&color=B8FF57&background=06110B00&center=true&vCenter=true&width=1000&lines=NASA+Space+Apps+Challenge+2026+%C2%B7+Field+Shift;3D+Interactive+Earth+Twin+%2B+Real-Time+NASA+Satellite+Telemetry;All+64+Districts+of+Bangladesh+%C2%B7+Bilingual+(English+%2B+%E0%A6%AC%E0%A6%BE%E0%A6%82%E0%A6%B2%E0%A6%BE);Developed+by+Rezwan+Hossain+Prince+(Team+Leader)+%26+Team+EARTH.exe)](https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026)

[![NASA Space Apps 2026](https://img.shields.io/badge/NASA_Space_Apps_2026-Field_Shift-0b3d91?style=for-the-badge&logo=nasa&logoColor=white)](https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026) [![Team EARTH.exe](https://img.shields.io/badge/Team-EARTH.exe-ff2e4c?style=for-the-badge&labelColor=06110b)](https://github.com/rzprince) [![Team Leader](https://img.shields.io/badge/Team_Leader-Rezwan_Hossain_Prince-b8ff57?style=for-the-badge&labelColor=06110b)](https://github.com/rzprince) [![Bilingual](https://img.shields.io/badge/Language-English_%2B_%E0%A6%AC%E0%A6%BE%E0%A6%82%E0%A6%B2%E0%A6%BE-38bdf8?style=for-the-badge&labelColor=06110b)](https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026) [![License](https://img.shields.io/badge/License-Apache_2.0-f59e0b?style=for-the-badge&labelColor=06110b)](https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026/blob/main/LICENSE)

## Overview

**BoponX (`বপনএক্স: মহাকাশ থেকে মাটিতে`)** is an agricultural decision-support platform created by **Team EARTH.exe** for the **2026 NASA International Space Apps Challenge** (*Challenge: Field Shift — Adapting Farms with NASA Data*).

Shifting monsoon onset dates, erratic dry spells, heat stress, and continuous monoculture cropping threaten farm livelihoods across climate-vulnerable deltas. **BoponX** bridges the gap between orbital Earth observations and field-level action by fusing multi-mission NASA satellite streams with localized agro-ecological context across **all 64 districts and 8 divisions of Bangladesh**, delivering clear, bilingual (**English + বাংলা**) guidance for farmers, extension officers, and decision-makers.

![BoponX 3-Stage Animated Workflow](./assets/boponx-workflow-animated.svg)

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
git clone https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026.git C:\BoponX
Set-Location C:\BoponX

python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt -r .\backend\requirements-dev.txt

Remove-Item Env:OFFLINE -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

**2. Open a second PowerShell window and start the web interface (`http://127.0.0.1:5173`):**
```powershell
Set-Location C:\BoponX\frontend
npm install-scripts approve esbuild@0.24.2 2>$null
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

![BoponX & Team EARTH.exe Animated Footer](./assets/earth-exe-footer-animated.svg)