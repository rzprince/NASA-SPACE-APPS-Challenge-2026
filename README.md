# BoponX — From Space to Soil (`Team EARTH.exe`)

**2026 NASA International Space Apps Challenge · Challenge 07: [Field Shift: Adapting Farms with NASA Data](https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/)**  
**License:** [Apache-2.0](./LICENSE)

BoponX is a bilingual (**English + বাংলা**), location-aware agricultural decision-support system that translates multi-resolution NASA Earth observations and local Bangladesh agro-ecological intelligence into:
1. **A 25-Year Planting-Window Shift & `<160-Character` SMS Advisory (`2001–2012` vs. `2013–2025`)** with a stated monsoon/usable-rain onset definition (`rain_onset`), `±5 mm` threshold sensitivity check (`15 mm / 20 mm / 25 mm`), Mann-Whitney U test, and crop-specific Growing Degree Days (`GDD`).
2. **A 3-Strategy Crop Rotation Workbench (`02 Rotation Lab`)** comparing the farmer's existing baseline rotation (**Strategy A**), a nitrogen-fixing pulse/oilseed bridge (**Strategy B**), and district landform opportunities (**Strategy C**) with interactive **"What-If" Rainfall & Heat Sliders**.
3. **A Printable 2-Page A4 90-Day Field Action Dossier (`03 Field Plan`)** tailored to the farmer's crop history, target crop, water source, post-rain drainage, lab soil test/pH, equipment access, and market/forage goal.

---

## 1. NASA & Local Agricultural Datasets Used (With Official URLs)

| Dataset / System | Spatial & Temporal Scale | Role in BoponX | Official Source URL |
| :--- | :--- | :--- | :--- |
| **NASA POWER Agroclimatology API** (`Daily & 2001–2020 Climatology`) | `0.5° × 0.625°` (~50 km) · Daily & Monthly | Provides `PRECTOTCORR` (rainfall), `T2M` / `T2M_MAX` / `T2M_MIN` (temperature & GDD), `T2MDEW` (dew/frost/fog-blight risk), `RH2M` (VPD), `WS2M`, `ALLSKY_SFC_SW_DWN` (solar radiation), `GWETTOP` (`0–5 cm` topsoil wetness), `GWETROOT` (`0–100 cm` root-zone wetness), and FAO-56 `ET₀`. | https://power.larc.nasa.gov/docs/services/api/temporal/daily/ |
| **NASA GPM IMERG Early V07B** | `0.1°` (~10 km) · Near-real-time (~4h latency) | Spatial precipitation distribution & extreme downpour visualization on the 3D/2D globe. | https://gpm.nasa.gov/data/directory |
| **NASA SMAP L3 / L2 Soil Moisture** (`SPL3SMP_E V6`) | `9 km EASE-Grid` · Daily multi-date | Top-5 cm surface soil moisture context for seedbed workability (`jo` condition). Never used to infer parcel `pH` or `NPK`. | https://nsidc.org/data/spl3smp_e/versions/6 |
| **NASA MODIS Terra Reflectance, NDVI & Land Surface Temp** | `250 m – 1 km` · Daily & 8-day composite | Canopy greenness (`MODIS_Terra_NDVI_8Day`), bare-field window detection, and daytime thermal heat stress (`MODIS_Terra_Land_Surface_Temp_Day`). | https://worldview.earthdata.nasa.gov/ |
| **NASA SRTM Digital Elevation Model** (`SRTM_Color_Index`) | `30 m – 90 m DEM` · Static relief | Topographic elevation, slope erosion context, and lowland/haor vs. terrace drainage relief. | https://worldview.earthdata.nasa.gov/ |
| **NASA EONET v3 Natural Event Tracker** | Event coordinates + radius (`km`) · Real-time | Tracks active cyclones/severe storms, floods, droughts, wildfires, and landslides near the selected farm coordinate. | https://eonet.gsfc.nasa.gov/docs/v3 |
| **Bangladesh Agro-Meteorological Information Systems (BAMIS)** | Regional hubs across Bangladesh · Seasonal | Official crop-weather calendars (`Aman`, `Boro`, `Aus`, `Wheat`, `Maize`, `Mustard`, `Lentil`, `Green Gram`, `Jute`). | https://www.bamis.gov.bd/ |
| **BARC Crop Zoning, SRDI, AIS & DAE (`16123`)** | 64 Districts / >490 Upazilas | Local landform, soil verification requirements, national import-substitution context, and human-in-the-loop extension verification. | https://apps.barc.gov.bd/cropzoning/ · https://srdi.gov.bd/ · https://dae.gov.bd/ |

---

## 2. Stated Monsoon / Usable-Rain Onset Definition & Scientific Boundaries

- **Stated Onset Definition (`backend/app/compute/agro.py`):**
  > *"First day of a 7-day window with 20 mm or more of cumulative rainfall that is not followed by a dry spell longer than 7 days (at least one day > 1.0 mm in the next 7 days)."*
- **`±5 mm` Threshold Sensitivity Check:** Every `/advisory` response evaluates the onset shift across `15 mm (-5 mm)`, `20 mm (base)`, and `25 mm (+5 mm)` 7-day thresholds alongside a two-sided **Mann-Whitney U test** (`2001–2012` vs. `2013–2025`).
- **Strict Fail-Closed Boundaries:**
  - Satellite soil moisture (`SMAP`, `GWETTOP`, `GWETROOT`) measures physical moisture saturation, **never** laboratory soil `pH`, salinity (`EC`), or `NPK` nutrients.
  - 20-year monthly climatology (`2001–2020`) is a historical benchmark, **never** a daily weather forecast.
  - Prescriptive crop suitability ranking (`POST /api/v1/rotations/compare`) remains fail-closed (`HTTP 409 AGRONOMIC_RULES_NOT_APPROVED`) until local agronomic rules are formally approved by extension authorities.

---

## 3. Running Locally (Online & `OFFLINE=1` Venue Mode)

### Terminal 1 — FastAPI Backend (Port `8000`)
```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\backend\requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q backend\tests

# Standard mode (live NASA APIs + automatic cache/fallback):
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

# Optional OFFLINE=1 mode (forces instant local cache reads for hackathon venue demos):
$env:OFFLINE="1"; .\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

### Terminal 2 — React + TypeScript Frontend (Port `5173`)
```powershell
cd frontend
npm.cmd install
npm.cmd run build
npm.cmd run dev
```

### Key API Endpoints
- `GET /advisory?district=Rajshahi&crop=rice` (also `GET /api/v1/advisory?district=&crop=`): Returns the 25-year onset shift in whole days, `2001–2012` vs. `2013–2025` distributions, Mann-Whitney U statistic & p-value, `±5 mm` sensitivity check, GDD summary, bilingual advisory sentence, and `<160-character` SMS advisory.
- `GET /api/v1/context?lat=24.3745&lon=88.6042`: Resolves 64-district Bangladesh profile, BAMIS calendars, multi-resolution harmonization, scientific glossary, functional crop roles, and SI methods.
- `GET /api/v1/environment/recent`, `GET /api/v1/environment/baseline-window`, `GET /api/v1/environment/hazards`: Live NASA POWER & EONET v3 diagnostics.
- `POST /api/v1/rotations/explore` & `POST /api/v1/plans/preview`: Generates the 3 rotation exploration strategies and the tailored 90-day field plan.

---

## 4. Mandatory Use of AI & Human Contribution Disclosure

In accordance with the **2026 NASA International Space Apps Challenge Rules**:
- **Human Engineering, Domain Research & Creative Design (`Team EARTH.exe`):**
  - Formulated the **BoponX ("From Space to Soil")** system architecture, fail-closed scientific integrity gates, and 3-stage farmer workflow (`01 Earth Twin` → `02 Rotation Lab` → `03 Field Plan`).
  - Compiled and structured the 64-district Bangladesh agro-ecological dataset (`bpx.pdf`), including landform classifications, climate analogs, established/opportunity crops, national edible-oil/pulse import-substitution context, and SRDI/BARC/Plant Quarantine verification rules.
  - Designed the official **BoponX** visual identity, 2-page A4 printable field dossier layout, and bilingual (`English + বাংলা`) farmer communication strategy.
- **AI Tools Used & Prompts / Data Worked On:**
  - **Tool:** Google Gemini (Coding & Research Assistant).
  - **Prompts & Tasks:** Assisted in pair-programming FastAPI endpoints (`agro.py`, `power_live.py`, `eonet_live.py`, `bangladesh_districts.py`, `plan.py`), writing React/TypeScript UI components (`LocationMap.tsx`, `App.tsx`, `DecisionReport.tsx`), implementing FAO-56 `ET₀`, `rain_onset`, and Mann-Whitney U statistical calculations, and writing automated unit tests (`backend/tests/`).
  - **Data Worked On:** Public NASA API documentation (`NASA POWER`, `GIBS WMS`, `EONET v3`), official `BAMIS` calendar metadata, and Team EARTH.exe's curated 64-district Bangladesh research notes. No proprietary or copyrighted third-party content was used.
