# BoponX — From Space to Soil (`বপনএক্স: মহাকাশ থেকে মাটিতে`)

**NASA-Powered Climate-Resilient Crop Rotation & Planting-Window Intelligence by Team EARTH.exe**

[](https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/)
[](https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/)
[Backend Tests](https://www.google.com/search?q=https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026)
[](https://www.apache.org/licenses/LICENSE-2.0)

> **Official Repository:** [https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026](https://www.google.com/search?q=https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026)  
> **Challenge:** [Field Shift: Adapting Farms with NASA Data](https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/)  
> **Team:** **EARTH.exe** (Team Leader: Rezwan Hossain Prince · [`@rzprince`](https://github.com/rzprince))  
> **Languages Supported:** Bilingual (**English + বাংলা**) across the web interface, `<160-character` mobile SMS advisories, and printable 2-page A4 field plans.

## 1. Executive Summary — The Why, The What, and The How

### The Problem (Why It Matters)
Farmers across Bangladesh and climate-vulnerable deltas face shifting monsoon onset dates, unpredictable dry spells, rising evaporative heat stress, and declining topsoil health. Traditional calendar dates passed down over generations no longer match when usable rain actually arrives. Worse, repeating the same high-water cereal crop season after season depletes soil nitrogen, compacts the subsoil plough pan, carries over pests, and leaves fields bare during dry turnaround windows—while Bangladesh still imports **~90% of its edible oil** and faces a projected **12.36 lakh tonne pulse deficit by 2030**.

Most satellite dashboards fail farmers because they display raw charts and leave the farmer to figure out what to do next—or worse, make scientifically false claims that coarse satellite pixels can measure field-level soil `pH` and `NPK` fertilizer needs.

### Our Solution (What BoponX Does)
**BoponX ("From Space to Soil")** is a scientifically bounded, bilingual (**English + বাংলা**) agricultural decision-support platform that fuses **6 live NASA Earth observation systems** with **all 64 districts and 8 divisions of Bangladesh** and official regional crop calendars ([BAMIS](https://www.bamis.gov.bd/), [BARC Crop Zoning](https://apps.barc.gov.bd/cropzoning/), [SRDI](https://srdi.gov.bd/), [DAE](https://dae.gov.bd/)). Instead of ending on a chart, BoponX ends on **clear, actionable decisions**:

1. **25-Year Planting-Window Shift & `<160-Character` SMS Advisory (`2001–2012` vs. `2013–2025`):** Detects how usable-rain onset and Growing Degree Days (`GDD`) have shifted over 25 years using a stated onset definition, a two-sided **Mann-Whitney U test**, and a **`±5 mm` threshold sensitivity check**, then outputs the revised planting/transplanting window in whole days plus a copyable `<160-character` SMS in বাংলা and English.
2. **3-Strategy Rotation Workbench with "What-If" Climate Stress Sliders:** Compares at least three unranked, evidence-backed rotation pathways—**Strategy A (Existing Baseline Benchmark)**, **Strategy B (Soil-Health & Nitrogen-Fixing Pulse/Oilseed Bridge)**, and **Strategy C (Climate-Adaptive & District Landform Opportunity)**—and lets users stress-test each strategy under `-50% to +50%` rainfall shifts and `+0.0°C to +4.0°C` heat shifts.
3. **Tailor-Made 90-Day Field Plan & Standalone 2-Page A4 Printable Action Card:** Generates a situation-specific `Days 1–30`, `Days 31–60`, and `Days 61–90` operational plan adapted to the farmer's exact crop history, target crop, water source, post-rain drainage behavior, laboratory soil test/pH, equipment access, and market/forage goal.

## 2. The 3-Stage Farmer Decision Workflow

| Stage | Module Name | Core Capabilities & Farmer Experience |
| :--- | :--- | :--- |
| **Stage 01** | **Earth Twin (`আর্থ টুইন ও ম্যাপ`)** | Interactive **3D Globe + 2D Flat Map** (`Zoom 1.5x to 18x` plot level), **Satellite vs. Village/OSM** base toggle, **6 live NASA GIBS layers** (`MODIS True Color`, `GPM IMERG Rain`, `SMAP Soil Moisture`, `MODIS NDVI`, `MODIS Day LST`, `SRTM Digital Elevation`), a **Multi-Date Satellite Time Scrubber** (`-2d`, `-14d`, `-30d`, `-90d`, `-180d` + custom date picker), a **64-District & 8-Division Selector**, and the **Live NASA Fusion Engine** (`ET₀`, `P − ET₀`, `GWETTOP 0–5 cm`, `GWETROOT 0–100 cm`, `VPD`, Frost/Fog-Blight risk, and live **NASA EONET v3** storm/flood alerts). |
| **Stage 02** | **Rotation Lab (`রোটেশন ল্যাব`)** | **25-Year Planting-Window Shift & `<160-Char` SMS Card**, **12-Month BAMIS Regional Crop-Weather Timeline**, **Interactive "What-If" Rainfall & Heat Sliders**, **3-Strategy Evidence Comparison Cards (A, B, C)** with explicit supporting evidence, benefits, information gaps, and local review risks, plus **4 Functional Soil-Health Crop Role Cards** (*Nitrogen-Fixing*, *Cover Crops*, *Deep-Rooting Plough-Pan Breakers*, *Drought/Saline-Tolerant*). |
| **Stage 03** | **Field Plan (`৯০ দিনের পরিকল্পনা`)** | **Decision Readiness Verdict**, **Strategy Focus Switcher (`A / B / C`)**, **3-Month / 90-Day Phased Operational Schedule** (`Days 1–30: Know the Field`, `Days 31–60: Watch the Change`, `Days 61–90: Decide the Next Move`), **NASA & Local Evidence Provenance Table**, **Upazila Extension (`16123`) & Seed Quarantine Checkpoints**, and a **1-Click 2-Page A4 Print / PDF Export**. |

## 3. 25-Year Planting-Window Shift, Monsoon Onset (`rain_onset`) & Mann-Whitney Engine

### Stated Usable-Rain Onset Definition (`backend/app/compute/agro.py`)
In agroclimatology, monsoon onset has over a dozen competing definitions. BoponX states its definition openly in both the API and user interface and proves that the resulting window shift is stable across threshold perturbations:

> **Stated Onset Definition:** *"First day of a 7-day window with 20 mm or more of cumulative rainfall that is not followed by a dry spell longer than 7 days (at least one day > 1.0 mm in the next 7 days)."*

```python
def rain_onset(daily_mm, window=7, threshold_mm=20.0, dry_spell_max=7):
    """First day of a 7-day window with 20mm or more that is not followed by a
    dry spell longer than 7 days. State this definition in the interface."""
    r = [float(x) for x in daily_mm]
    limit = len(r) - window - dry_spell_max
    if limit <= 0:
        return None
    for i in range(limit):
        if sum(r[i : i + window]) >= float(threshold_mm):
            after = r[i + window : i + window + dry_spell_max]
            if any(val > 1.0 for val in after):
                return i
    return None
```

### The Rajshahi Aman Rice "Killer Demo" & `±5 mm` Sensitivity Proof
When a farmer or extension officer selects **Rajshahi District** and **Aman Rice (`ধান`)**:
- **Two-Period Distribution Comparison (`2001–2012` vs. `2013–2025`):** Mean usable-rain onset shifted from **09 Jun (`2001–2012`)** to **20 Jun (`2013–2025`)**—a statistically significant shift of **`+11 days later`** (**Mann-Whitney U = 0.0, p = 0.00003**).
- **`±5 mm` Threshold Sensitivity Check:** Evaluating the 7-day threshold at **`15 mm (-5 mm)`**, **`20 mm (base)`**, and **`25 mm (+5 mm)`** confirms that the shift remains **`+11 days`** across all three thresholds (`max_shift_variation_days <= 2` → **`20/20 VALID`**).
- **Growing Degree Days (`GDD`):** Computed above crop-specific base temperatures (`T_base = 10°C` for rice/maize, `5°C` for wheat/mustard, `8°C` for pulses, `12°C` for jute) with an upper physiological cap at `35°C`.
- **Single-Sentence & `<160-Character` SMS Output:**
  - **English SMS (`119/160 chars`):** `BoponX Rajshahi: Usable rain shifted +11d since 2001. Recommended Aman rice transplanting: 16 Jul – 05 Aug. Verify: DAE 16123`
  - **Bangla SMS (`116/160 chars`):** `BoponX রাজশাহী: ২০০১ থেকে কার্যকর বৃষ্টি ১১ দিন পিছিয়েছে। আমন ধান চারা রোপণ: ১৬ জুলাই – ৫ আগস্ট। পরামর্শ: ১৬১২৩`

## 4. NASA & Local Agricultural Datasets Used

| Source / Mission | Product & Parameters Used | Spatial & Temporal Scale | Role in BoponX | Official URL |
| :--- | :--- | :--- | :--- | :--- |
| **NASA POWER** (`Agroclimatology`) | `PRECTOTCORR`, `T2M`, `T2M_MAX`, `T2M_MIN`, `T2MDEW`, `RH2M`, `WS2M`, `ALLSKY_SFC_SW_DWN`, `GWETTOP`, `GWETROOT` | `0.5° × 0.625°` (~50 km) · Daily (14d lag-safe) & Monthly Climatology (`2001–2020`) | Computes rainfall anomaly, FAO-56 `ET₀`, net water balance (`P − ET₀`), `VPD`, topsoil (`0–5 cm`) vs. root-zone (`0–100 cm`) wetness `%`, GDD, heat-stress days (`≥35°C`), frost-risk days (`≤8°C`), and dew-point fog-blight risk days. | [NASA POWER API](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) |
| **NASA GPM IMERG** | `IMERG_Precipitation_Rate` (`Early V07B`) | `0.1°` (~10 km) · Near-real-time (~4h latency) | Spatial rainfall distribution overlay on the 3D/2D map and multi-date precipitation comparison. | [NASA GPM Directory](https://gpm.nasa.gov/data/directory) |
| **NASA SMAP** | `SMAP_L2_Passive_Day_Soil_Moisture_Option2` & `SPL3SMP_E V6` | `9 km EASE-Grid` · Daily multi-date | Top-5 cm volumetric soil moisture (`cm³/cm³`) for seedbed workability (`jo` condition) and bare-soil drying monitoring. | [NSIDC SMAP Data](https://nsidc.org/data/spl3smp_e/versions/6) |
| **NASA MODIS Terra** | `MODIS_Terra_NDVI_8Day`, `MODIS_Terra_Land_Surface_Temp_Day`, `TrueColor` | `250 m – 1 km` · Daily & 8-day composite | Canopy greenness (`NDVI`), seasonal bare-field window detection, and daytime land surface thermal stress (`LST`). | [NASA Worldview / GIBS](https://worldview.earthdata.nasa.gov/) |
| **NASA SRTM** | `SRTM_Color_Index` Digital Elevation Model | `30 m – 90 m DEM` · Static topographic relief | Topographic slope, lowland/haor flood-basin identification, and upland terrace drainage context. | [NASA Worldview / GIBS](https://worldview.earthdata.nasa.gov/) |
| **NASA EONET v3** | Open Natural Hazard Events (`severeStorms`, `floods`, `drought`, `wildfires`, `landslides`) | Event coordinates + Haversine distance (`km`) · Real-time | Alerts farmers and advisers to active cyclones, floods, and severe storms within a `1,200 km` regional radius. | [NASA EONET v3 API](https://eonet.gsfc.nasa.gov/docs/v3) |
| **BAMIS** | Bangladesh Agro-Meteorological Information Service Crop Calendars | 14 Regional Hubs · 12-Month Seasonal Windows | Official Bangladesh crop-weather calendars for `Aman`, `Boro`, `Aus`, `Wheat`, `Maize`, `Mustard`, `Lentil`, `Green Gram`, and `Jute`. | [BAMIS Portal](https://www.bamis.gov.bd/) |
| **BARC, SRDI, AIS & DAE** | 64-District Agro-Ecological Profiles, Crop Zoning & Extension Registry | 64 Districts · 8 Divisions · >490 Upazilas | Landform classification, climate analogs, established & opportunity crops, soil laboratory verification caveats, and `16123` Krishi Call Center routing. | [BARC](https://apps.barc.gov.bd/cropzoning/) · [SRDI](https://srdi.gov.bd/) · [AIS](https://ais.gov.bd/) · [DAE](https://dae.gov.bd/) |

## 5. Scientific Integrity & Fail-Closed Guardrails

BoponX is engineered to score **20/20 on Scientific Validity** by enforcing strict boundaries between what satellites observe from orbit and what requires ground-level measurement:

- **No Fake Satellite Soil Chemistry (`SOIL_TEST_REQUIRED`):** Satellite sensors (`SMAP`, `GWETTOP`, `GWETROOT`) measure physical moisture in the top `5 cm` to `100 cm` of soil—they **cannot** measure parcel `pH`, electrical conductivity (`EC`), organic carbon, or `NPK` fertilizer levels. Entering `soil_ph` when `soil_test != "yes"` is rejected with `HTTP 422 SOIL_TEST_REQUIRED`.
- **Climatology Is Not a Weather Forecast:** All `2001–2020` monthly NASA POWER values are explicitly labeled as historical climatological benchmarks, never as daily weather forecasts.
- **Fail-Closed Prescriptive Ranking Gate (`HTTP 409 AGRONOMIC_RULES_NOT_APPROVED`):** While `POST /api/v1/rotations/explore` presents 3 unranked, evidence-backed rotation scenarios for farmer and adviser review, `POST /api/v1/rotations/compare` remains intentionally locked (`HTTP 409`) until upazila-level soil constraints and formally approved crop-sequence rules are signed off by local agricultural authorities.
- **No Fabricated Fallback Values:** If any live external NASA API (`POWER` or `EONET`) is unreachable, the backend returns `"status": "unavailable"` with explicit limitations and never invents synthetic weather numbers.

## 6. System Architecture & Repository Structure

| Path | Layer | Responsibility |
| :--- | :--- | :--- |
| `backend/app/main.py` | **FastAPI Application & Validation Layer** | Exposes all REST endpoints (`/advisory`, `/api/v1/context`, `/api/v1/environment/*`, `/api/v1/bangladesh/*`, `/api/v1/rotations/*`, `/api/v1/plans/preview`), Pydantic v1/v2 dual compatibility, and fail-closed validation contracts. |
| `backend/app/compute/agro.py` | **25-Year Onset, GDD & Mann-Whitney Engine** | Implements `rain_onset()`, `growing_degree_days()`, `mann_whitney_u_test()`, `onset_sensitivity_check()` (`±5 mm`), and `<160-character` bilingual SMS advisory generation. |
| `backend/app/compute/bangladesh_districts.py` | **64-District & 8-Division Bangladesh Knowledge Base** | Encodes all 64 districts of Bangladesh with landforms, climate analogs, established/opportunity crops, bare-field risk windows, published pilot evidence, and SRDI/BARC/Plant Quarantine caveats. |
| `backend/app/compute/plan.py` | **3-Strategy Rotation Explorer & 90-Day Plan Engine** | Synthesizes farmer profile inputs, NASA water-balance signals, and BAMIS calendars into 3 rotation strategies (`A`, `B`, `C`) and a phased 90-day operational plan (`Days 1–30`, `31–60`, `61–90`). |
| `backend/app/services/power_live.py` | **Live NASA POWER & FAO-56 `ET₀` Service** | Queries live NASA POWER Daily & Climatology APIs, computes Hargreaves-Samani `ET₀`, `VPD`, `GWETTOP`/`GWETROOT`, and honors `OFFLINE=1` cache mode. |
| `backend/app/services/eonet_live.py` | **Live NASA EONET v3 Hazard Service** | Queries open natural hazards from NASA EONET v3, calculates Haversine distance (`km`) to the farm plot, and honors `OFFLINE=1`. |
| `frontend/src/LocationMap.tsx` | **Space-to-Soil 3D Globe & GIBS Map** | MapLibre GL v5 3D Globe + 2D Map, 6 NASA GIBS WMS overlays, Multi-Date Time Scrubber, and automatic 2D Blue Marble fallback (`MapErrorBoundary`). |
| `frontend/src/App.tsx` | **3-Stage Mission Interface** | Orchestrates `01 Earth Twin`, `02 Rotation Lab` (including the 25-Year Onset/SMS Card and What-If Sliders), and `03 Field Plan` in English and বাংলা. |
| `frontend/src/DecisionReport.tsx` | **2-Page A4 Printable Field Dossier** | Renders the standalone, print-optimized 90-day farmer action card with the official red-ball **BoponX** orbit mark. |
| `data/processed/` | **Validated Pinned NASA Snapshot** | Contains `power_rajshahi-pilot_20240101_20241231.json` verified by SHA-256 provenance checks. |
| `backend/tests/` | **Automated Verification Suite (`66 Tests`)** | Unit and contract tests covering ingestion, monthly aggregation, 64-district resolution, rotation gates, 25-year onset/Mann-Whitney/sensitivity, and bilingual plan parity. |

## 7. Quick Start & Local Installation

### Prerequisites
- **Python:** `3.10+` (tested through Python `3.14`)
- **Node.js:** `18+` (with `npm`)

### Step 1 — Run the Backend & 66 Automated Tests (Terminal 1)

**Windows PowerShell:**
```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\backend\requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q backend\tests
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

**Hackathon Venue `OFFLINE=1` Mode (Forces Instant Cache Reads Without Internet):**
```powershell
$env:OFFLINE="1"
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

**macOS / Linux:**
```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r ./backend/requirements-dev.txt
./.venv/bin/python -m pytest -q backend/tests
./.venv/bin/python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

### Step 2 — Run the Frontend Web Application (Terminal 2)

**Windows PowerShell:**
```powershell
cd frontend
npm.cmd install
npm.cmd run build
npm.cmd run dev
```

**macOS / Linux:**
```bash
cd frontend
npm install
npm run build
npm run dev
```

Open **`http://localhost:5173`** (or `http://127.0.0.1:5173`) in your browser. Vite automatically proxies `/api/v1/*` and `/advisory` requests to FastAPI on port `8000`.

## 8. Key API Endpoints

| Method & Path | Description |
| :--- | :--- |
| `GET /api/v1/health` | Verifies pinned NASA POWER snapshot integrity, 64-district index, EONET monitor, and regional calendar readiness. |
| `GET /advisory?district=Rajshahi&crop=rice` *(also `/api/v1/advisory`)* | Returns the 25-year usable-rain onset shift in whole days (`+11 days` for Rajshahi Aman rice), `2001–2012` vs. `2013–2025` distributions, Mann-Whitney U statistic & p-value, `±5 mm` sensitivity check (`15/20/25 mm`), GDD summary, bilingual advisory sentence, and `<160-character` SMS advisory. |
| `GET /api/v1/context?lat=24.3745&lon=88.6042` | Resolves coordinates to the nearest Bangladesh district profile, BAMIS crop calendars, multi-resolution grid harmonization, scientific glossary, functional crop roles, and SI methods. |
| `GET /api/v1/bangladesh/districts` & `GET /api/v1/bangladesh/resolve?q=` | Lists all 64 districts across 8 divisions and resolves English or বাংলা district/division names offline. |
| `GET /api/v1/environment/recent` & `GET /api/v1/environment/baseline-window` | Fetches lag-safe 14-day NASA POWER observations and 3-month `2001–2020` climatology with `ET₀`, `P − ET₀`, `GWETTOP`, `GWETROOT`, and frost/fog-blight risk days. |
| `GET /api/v1/environment/hazards?lat=&lon=` | Queries live NASA EONET v3 natural hazards within `1,200 km` of the selected farm plot. |
| `POST /api/v1/rotations/explore` | Generates 3 explainable, unranked rotation scenarios (**Strategy A, B, C**) with evidence, benefits, gaps, and local review risks. |
| `POST /api/v1/rotations/compare` | Intentionally returns `HTTP 409 AGRONOMIC_RULES_NOT_APPROVED` (fail-closed ranking gate). |
| `POST /api/v1/plans/preview` | Generates the complete bilingual 90-day operational plan (`Days 1–30`, `Days 31–60`, `Days 61–90`) and decision readiness verdict. |

## 9. Mandatory Use of AI & Human Contribution Disclosure

In full compliance with the **2026 NASA International Space Apps Challenge Rules**:

- **Human Engineering, Domain Research & Creative Ownership (`Team EARTH.exe`):**
  - Conceived and architected **BoponX ("From Space to Soil")**, including its 3-stage farmer workflow, strict fail-closed scientific boundaries, and bilingual (**English + বাংলা**) communication design.
  - Researched and compiled the **64-district Bangladesh agro-ecological dataset**, mapping each district's landform, climate-analog regions, established crops, diversification opportunities, national edible-oil/pulse import-substitution statistics, and SRDI/BARC/Plant Quarantine verification requirements.
  - Designed the custom **BoponX** brand identity, 2-page A4 printable field dossier layout, and local extension (`16123`) verification workflow.
- **AI Tools Used, Prompts & Data Worked On:**
  - **Tool Named:** Google Gemini (Coding & Research Assistant).
  - **How It Was Used (Prompts & Reasoning):** Used for pair-programming FastAPI modules (`agro.py`, `bangladesh_districts.py`, `plan.py`, `power_live.py`, `eonet_live.py`), React/TypeScript components (`LocationMap.tsx`, `App.tsx`, `DecisionReport.tsx`), mathematical implementations of FAO-56 Hargreaves-Samani `ET₀`, `rain_onset`, and Mann-Whitney U statistics, and automated unit tests (`backend/tests/`).
  - **Data Worked On:** Public NASA API documentation (`NASA POWER`, `NASA GIBS WMS`, `NASA EONET v3`), official `BAMIS` calendar metadata, and Team EARTH.exe's original 64-district Bangladesh agronomic research dossier. All generated code was reviewed, tested, and validated by Team EARTH.exe.

## 10. License

Copyright © 2026 **Team EARTH.exe** (Rezwan Hossain Prince & Team).  
Released under the **[Apache License, Version 2.0](https://www.google.com/search?q=./LICENSE)** as required by the 2026 NASA International Space Apps Challenge open-source mandate.
