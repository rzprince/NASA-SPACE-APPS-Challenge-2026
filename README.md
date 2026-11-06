# BoponX — From Space to Soil (`বপনএক্স: মহাকাশ থেকে মাটিতে`)

**Climate-Resilient Crop Rotation & Planting-Window Decision Support by Team EARTH.exe**

[![NASA Space Apps 2026](https://img.shields.io/badge/NASA_Space_Apps_2026-The_Next_Frontier-0b3d91?style=for-the-badge)](https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/)
[![Challenge 07](https://img.shields.io/badge/Challenge_07-Field_Shift:_Adapting_Farms_with_NASA_Data-b8ff57?style=for-the-badge&labelColor=06110b)](https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/)
[![Backend Tests](https://img.shields.io/badge/Pytest_Suite-114_Passed-22c55e?style=for-the-badge&labelColor=06110b)](https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026)
[![License](https://img.shields.io/badge/License-Apache_2.0-38bdf8?style=for-the-badge&labelColor=06110b)](https://www.apache.org/licenses/LICENSE-2.0)

> **Official Repository:** [https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026](https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026)  
> **Challenge:** [Field Shift: Adapting Farms with NASA Data](https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/)  
> **Team:** **EARTH.exe** (Team Leader: Rezwan Hossain Prince · [`@rzprince`](https://github.com/rzprince))  
> **Data Attribution:** `Data: NASA POWER / EONET / GIBS` · Local Agronomic Reference: [BAMIS](https://www.bamis.gov.bd/) / [BARC](https://apps.barc.gov.bd/cropzoning/) / [SRDI](https://srdi.gov.bd/) / [DAE](https://dae.gov.bd/) (`16123`)  
> **Languages Supported:** Bilingual (**English + বাংলা**) across the web interface, `<160-character` GSM-7 / `≤70-character` UCS-2 mobile SMS advisories, and printable 1–2 page A4 field plans.

## 1. Executive Summary — The Why, The What, and The How

### The Problem (Why It Matters)
Farmers across Bangladesh and climate-vulnerable deltas face shifting monsoon onset dates, unpredictable dry spells, rising evaporative heat stress, and declining topsoil health. Traditional calendar dates passed down over generations no longer match when usable rain actually arrives. Worse, repeating the same high-water cereal crop season after season depletes soil nitrogen, compacts the subsoil plough pan, carries over pests, and leaves fields bare during dry turnaround windows—while Bangladesh still imports **~90% of its edible oil** and faces a projected **12.36 lakh tonne pulse deficit by 2030**.

Most satellite dashboards fail farmers because they display raw charts and leave the farmer to figure out what to do next—or worse, make scientifically false claims that coarse satellite pixels can measure field-level soil `pH` and `NPK` fertilizer needs.

### Our Solution (What BoponX Does)
**BoponX ("From Space to Soil")** is a scientifically bounded, bilingual (**English + বাংলা**) agricultural decision-support platform that combines **real NASA Earth observation systems (`Data: NASA POWER / EONET / GIBS`)** with **all 64 districts and 8 divisions of Bangladesh** and official regional crop calendars ([BAMIS](https://www.bamis.gov.bd/), [BARC Crop Zoning](https://apps.barc.gov.bd/cropzoning/), [SRDI](https://srdi.gov.bd/), [DAE](https://dae.gov.bd/)). Instead of ending on a chart, BoponX ends on **clear, traceable actions**:

1. **Planting-Window Shift & SMS Advisory (`2001–2012` vs. `2013–latest`), computed from real NASA POWER daily rainfall:** finds the usable-rain onset of every year starting `01 May` with a stated agronomic definition, compares the two periods with a two-sided **Mann-Whitney U test**, reports a robust **Hodges-Lehmann shift with a seeded bootstrap 95% confidence interval**, checks the whole record with **Mann-Kendall / Sen slope**, computes **seasonal water balance (`P − ET₀`)** for Kharif-2 (`Jun–Oct`) and Rabi (`Nov–Mar`), and tests sensitivity to threshold, window length, dry-spell length, and search start. The BAMIS planting window is moved **only** when the shift is statistically reliable (`p < 0.05`) and the crop is monsoon-linked; otherwise the advisory states `"no reliable shift"`.
2. **3-Strategy Rotation Workbench with "What-If" Climate Stress Sliders:** Compares three unranked, evidence-backed rotation pathways—**Strategy A (Existing Baseline Benchmark)**, **Strategy B (Soil-Health & Nitrogen-Fixing Pulse/Oilseed Bridge)**, and **Strategy C (Climate-Adaptive & District Landform Opportunity)**—and lets users stress-test each strategy under `-50% to +50%` rainfall shifts and `+0.0°C to +4.0°C` heat shifts.
3. **5-Part 90-Day Field Planner & Standalone A4 Printable Action Sheet:** Generates a structured `Days 1–30`, `Days 31–60`, and `Days 61–90` timeline where every task carries a leap-year-safe computed `date_range`, one clear bilingual action, the `reason` (data signal or rule behind it), an explicit API `source` identifier, an `evidence_label` (`observed_nasa` / `derived_from_nasa` / `official_local_reference` / `rule_based` / `preliminary_estimate`), and a print checkbox, accompanied by a real-signal **Watch List** and `"Verify with DAE 16123"` footer.

## 2. The 3-Stage Farmer Decision Workflow

| Stage | Module Name | Core Capabilities & Farmer Experience |
| :--- | :--- | :--- |
| **Stage 01** | **Location (`অবস্থান ও ম্যাপ`)** | Interactive **3D Globe + 2D Flat Map** (`Zoom 1.5x to 18x` plot level), **Satellite vs. Village/OSM** base toggle, **6 NASA GIBS layers** (`MODIS True Color`, `GPM IMERG Rain`, `SMAP Soil Moisture`, `MODIS NDVI`, `MODIS Day LST`, `SRTM Digital Elevation`), a **Multi-Date Satellite Time Scrubber**, a **64-District & 8-Division Selector**, and the **NASA Fusion Engine** (`ET₀`, `P − ET₀`, `GWETTOP 0–5 cm`, `GWETROOT 0–100 cm`, `VPD`, Frost/Fog-Blight risk, `data_origin`/`retrieved_at`/`lag_days` freshness indicator, and live **NASA EONET v3** agricultural hazard classification). |
| **Stage 02** | **Analysis (`বিশ্লেষণ ও পর্যায়`)** | **Planting-Window Shift & `<160-Char` GSM-7 / `≤70-Char` UCS-2 SMS Card** (showing Hodges-Lehmann shift, 95% CI, Mann-Whitney $U$/$p$, Sen slope, `how_computed`, `shared_with` grid-cell neighbours, and `evidence_types`), **12-Month BAMIS Regional Crop-Weather Timeline**, **Interactive "What-If" Rainfall & Heat Sliders**, **3-Strategy Evidence Comparison Cards (A, B, C)**, and **4 Functional Soil-Health Crop Role Cards**. |
| **Stage 03** | **90-Day Plan (`৯০ দিনের পরিকল্পনা`)** | **5-Part Printable A4 Field Planner**: **(1) Header** (BoponX logo, district, crop, plan start date, `"NASA data through <date>"`, language, BAMIS baseline window & conditional shifted window), **(2) Three Phases (`Days 1–30`, `31–60`, `61–90`)**, **(3) Tasks Timeline** (print checkbox, computed `date_range`, action, reason, `source`, and `evidence_label` badge), **(4) Short Watch List** built strictly from real signals, and **(5) Footer** (`"Verify with DAE 16123"`, limitations sentence, and short provenance). |

## 3. Planting-Window Shift Engine (Real NASA POWER Data)

### Stated usable-rain onset definition (`backend/app/compute/agro.py`, `onset_stats.py`)
> *"First day (scanning from 01 May) of a 7-day window with 20 mm or more of cumulative rainfall that is not followed by a dry spell longer than 7 days (at least one day > 1.0 mm in the next 7 days); candidate windows containing any missing day are skipped, never imputed."*

Days with missing NASA values (`-999.0` fill value or negative precipitation) are **skipped, never imputed**. Years with less than 95% valid rainfall in `[01 May .. 31 Aug]` are excluded and listed in `data_quality.years_excluded`. Literature basis (Stern et al. 1981, 1982; Sivakumar 1988; Marteau et al. 2009; BMD/BAMIS criteria) and pre-monsoon *Kalbaishakhi* screening are documented in [`docs/METHODS.md`](./docs/METHODS.md) and [`docs/VALIDATION.md`](./docs/VALIDATION.md).

### Reproduce the snapshots & onset table (when online)
```bash
# 1. Download all 40 unique NASA POWER grid cells covering all 64 Bangladesh districts (2001-01-01 to present)
python -m scripts.build_snapshot

# 2. Compute and write data/processed/onset_results.json + print the Markdown summary table
python -m scripts.build_onset_results

# 3. Start the server in strict offline snapshot mode
OFFLINE=1 python -m uvicorn backend.app.main:app --port 8000
curl "http://127.0.0.1:8000/advisory?district=Rajshahi&crop=rice"
```

> **Note on Sandbox Build Archive:** If `data/processed/power_history/` contains only `.gitkeep` (because the build sandbox had outbound internet disabled), `/advisory` and `/api/v1/environment/*` fail closed with `status: "UNAVAILABLE"` and `data_origin: "unavailable"`—never inventing fallback numbers. Run `python -m scripts.build_snapshot && python -m scripts.build_onset_results` once on an online machine or trigger `.github/workflows/snapshot.yml` in GitHub Actions to populate `data/processed/power_history/` and `data/processed/onset_results.json`.

## 4. NASA & Local Agricultural Datasets Used

| Source / Mission | Product & Parameters Used | Spatial & Temporal Scale | Role in BoponX | Official URL |
| :--- | :--- | :--- | :--- | :--- |
| **NASA POWER** (`Agroclimatology`) | `PRECTOTCORR`, `T2M`, `T2M_MAX`, `T2M_MIN`, `T2MDEW`, `RH2M`, `WS2M`, `ALLSKY_SFC_SW_DWN`, `GWETTOP`, `GWETROOT` | `0.5° × 0.625°` (~50 km) · Daily (`2001–present`, 7d lag-safe) & Monthly Climatology (`2001–2020`) | Computes usable-rain onset (`2001–2012` vs `2013–latest`), GDD, seasonal & 14-day FAO-56 `ET₀` and `P − ET₀`, `VPD`, topsoil (`0–5 cm`) & root-zone (`0–100 cm`) wetness `%`, heat-stress days (`≥35°C`), frost-risk days (`≤8°C`), and fog-blight risk days. | [NASA POWER API](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) |
| **NASA GPM IMERG** | `IMERG_Precipitation_Rate` (`Early V07B`) | `0.1°` (~10 km) · Near-real-time (~4h latency) | Visual NASA GIBS precipitation layer + optional numeric cross-check (`backend/app/services/imerg_check.py`) when `NASA_EARTHDATA_TOKEN` is set. | [NASA GPM Directory](https://gpm.nasa.gov/data/directory) |
| **NASA SMAP** | `SMAP_L2_Passive_Day_Soil_Moisture_Option2` & `SPL3SMP_E V6` | `9 km EASE-Grid` · Daily multi-date | Visual NASA GIBS top-5 cm soil moisture layer for seedbed workability context. | [NSIDC SMAP Data](https://nsidc.org/data/spl3smp_e/versions/6) |
| **NASA MODIS Terra & SRTM** | `MODIS_Terra_NDVI_8Day`, `MODIS_Terra_Land_Surface_Temp_Day`, `TrueColor`, `SRTM_Color_Index` | `30 m – 1 km` · Daily / 8-day / Static DEM | Visual NASA GIBS layers for canopy greenness (`NDVI`), bare-field windows, daytime surface heat (`LST`), and topographic relief (`SRTM`). | [NASA Worldview / GIBS](https://worldview.earthdata.nasa.gov/) |
| **NASA EONET v3** | Open Natural Hazard Events (`severeStorms`, `floods`, `drought`, `landslides` vs `wildfires`) | Event coordinates + Haversine distance (`km`) · Real-time | Filters hydrometeorological hazards (`affects_field_operations = True`) within `1,200 km` and injects a `rule_based` drainage & DAE (`16123`) check task into Phase 1 of the 90-day plan. | [NASA EONET v3 API](https://eonet.gsfc.nasa.gov/docs/v3) |
| **BAMIS, BARC, SRDI, AIS & DAE** | Regional Crop Calendars & 64-District Agro-Ecological Profiles | 64 Districts · 8 Divisions · 14 BAMIS Hubs | Official baseline crop windows (`official_local_reference`), landform & climate-analog profiles (`preliminary_estimate`), soil lab verification gates, and `16123` Krishi Call Center routing. | [BAMIS](https://www.bamis.gov.bd/) · [BARC](https://apps.barc.gov.bd/cropzoning/) · [SRDI](https://srdi.gov.bd/) · [DAE](https://dae.gov.bd/) |

## 5. Scientific Integrity & Fail-Closed Guardrails

- **No fabricated data (`test_no_fabrication_guard.py`).** Production code in `backend/app/` is continuously scanned by `backend/tests/test_no_fabrication_guard.py` to forbid synthetic rainfall or onset generators.
- **Explicit evidence labels.** Every advisory metric and every 90-day planner task carries one of five labels: `observed_nasa`, `derived_from_nasa`, `official_local_reference`, `rule_based`, or `preliminary_estimate`.
- **No fake satellite soil chemistry (`422 SOIL_TEST_REQUIRED`).** Submitting `soil_ph` without `soil_test="yes"` is rejected with `HTTP 422 SOIL_TEST_REQUIRED`.
- **Fail-closed prescriptive ranking gate (`409 AGRONOMIC_RULES_NOT_APPROVED`).** `/api/v1/rotations/explore` returns 3 unranked scenarios; `/api/v1/rotations/compare` stays locked with `HTTP 409 AGRONOMIC_RULES_NOT_APPROVED`.

See [`docs/METHODS.md`](./docs/METHODS.md), [`docs/LIMITATIONS.md`](./docs/LIMITATIONS.md), and [`docs/VALIDATION.md`](./docs/VALIDATION.md).

## 6. Quick Start & Local Installation

### Option A — Windows PowerShell Helper (`scripts/run.ps1`)
```powershell
.\scripts\run.ps1 setup      # create .venv and install pinned backend + frontend dependencies
.\scripts\run.ps1 snapshot   # download 40 NASA POWER grid-cell snapshots & build onset_results.json (requires internet)
.\scripts\run.ps1 test       # run offline backend pytest suite (114 tests) + frontend TypeScript build
.\scripts\run.ps1 backend    # start FastAPI backend on http://127.0.0.1:8000
.\scripts\run.ps1 frontend   # start Vite frontend on http://127.0.0.1:5173
```

### Option B — Manual Commands (macOS / Linux / Windows)
```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r backend/requirements.txt -r backend/requirements-dev.txt
OFFLINE=1 ./.venv/bin/python -m pytest -q backend/tests
./.venv/bin/python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal:
```bash
cd frontend
npm install
npm run build
npm run dev
```

## 7. Mandatory Use of AI & Human Contribution Disclosure

In full compliance with the **2026 NASA International Space Apps Challenge Rules**:
- **Human Engineering, Domain Research & Creative Ownership (`Team EARTH.exe`):** Conceived and architected **BoponX ("From Space to Soil")**, researched the 64-district Bangladesh agro-ecological dataset, designed the BoponX brand mark and 3-stage workflow, and verified all agronomic rules and disclosures.
- **AI Tools Used:** Google Gemini and Claude (Anthropic) were used as coding and documentation assistants for FastAPI/React implementation, statistical functions (`agro.py`, `onset_stats.py`, `power_history.py`, `plan.py`), unit tests (`backend/tests/`), and documentation (`docs/METHODS.md`, `docs/LIMITATIONS.md`, `docs/VALIDATION.md`). **Team action required:** review all updated files and confirm this disclosure before final submission.

## 8. License

Copyright © 2026 **Team EARTH.exe** (Rezwan Hossain Prince & Team).  
Released under the **[Apache License, Version 2.0](./LICENSE)**.
