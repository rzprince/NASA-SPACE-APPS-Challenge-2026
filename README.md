# BoponX · বপনএক্স
### From Space to Soil · মহাকাশ থেকে মাটিতে

**Team EARTH.exe · Bangladesh · NASA Space Apps Challenge 2026 · Field Shift: Adapting Farms with NASA Data**

BoponX is a bilingual, mobile-first farmer decision-support system. It starts with a farmer's location and observations, then brings in only the environmental and agricultural evidence relevant to that place. The intended outcome is not another weather dashboard: it is a transparent path from **field context → Earth observations → local evidence → seasonal choices → printable field plan**.

> BoponX is an independent Team EARTH.exe project. NASA and NASA partners have not endorsed this application.

## The farmer journey

1. **Choose the field area** — use browser location permission, search a Bangladesh reference region, or tap the map.
2. **See only relevant environmental context** — the map and cards focus on the selected place rather than showing national data indiscriminately.
3. **Answer simple field questions** — previous crop, water source, what happens after heavy rain, whether a soil-test report exists, and the farmer's priority.
4. **Get a distinct 90-day field brief** — Month 1 establishes the field baseline, Month 2 monitors recent conditions, and Month 3 turns the observations into the next decision checkpoint.
5. **Explore crop rotations when the evidence is ready** — crop-specific rotation alternatives remain deliberately locked until local calendars, crop requirements, soil constraints, and sequence rules are source-reviewed.

The long-term challenge flow is:

**location → NASA/local context → previous crop → water and field observations → farmer priority → feasible rotation alternatives → evidence/trade-offs → bilingual three-season roadmap + practical 90-day routine**

## What is implemented

### Location-first web experience
- Browser **Use my location** flow with permission only after a user action.
- Search for a village, upazila, district, or place in Bangladesh through a fail-closed OpenStreetMap/Nominatim location helper.
- Regional agricultural evidence hubs remain separate from the place name so BoponX does not pretend a city label is an agronomic boundary.
- Tap-to-select MapLibre map.
- Exact coordinates are used for the current request and are not persisted by the API.
- Environmental coverage, local agricultural evidence, and rotation-decision support are shown as separate states.

### NASA data and mapping
- **NASA GPM IMERG Early** recent-rainfall visualization through NASA GIBS, with the map date shown.
- **NASA POWER** selected-location recent point context plus a 2001–2020 planning-month climatology baseline; no replacement number is invented when a request fails.
- The existing integrity-checked **2024 Rajshahi NASA POWER / MERRA-2** snapshot remains available as a reproducible historical reference.
- **SMAP SPL3SMP_E** is registered as the candidate regional surface-soil-moisture source, but numeric SMAP values are not exposed until the adapter, authentication, quality handling, and 2026 advisory checks are completed.

### Farmer-first intake
BoponX does **not** ask a farmer to know soil pH by default. A numeric pH field appears only if the farmer says a soil-test report exists. The backend rejects a pH submitted without that explicit soil-test state.

Every uncertain question has an unknown/not-sure path. Unknown field information remains unknown.

### Distinct 90-day plan
The current plan is a preparation and decision-support routine, not a crop prescription:

- **Month 1 — Know the field:** establish previous-crop, water, drainage, and soil-test evidence.
- **Month 2 — Watch the change:** compare recent NASA context with field observations and follow the selected farmer priority.
- **Month 3 — Decide the next move:** review evidence, identify remaining unknowns, consult the appropriate local crop calendar, and prepare the next seasonal decision.

The three months use different objectives and different task sets.

### Location-specific crop evidence
BoponX now indexes official BAMIS crop-weather-calendar presence by regional evidence hub for major crops such as Aman/Aus/Boro rice, wheat, mustard, lentil, jute, maize (Kharif-1), and green gram (Kharif-1). The UI shows only calendars that exist for the selected regional hub.

Calendar presence is **not** treated as crop suitability or a recommendation. It is evidence that a local source exists and can be reviewed for the next rule-building stage.

### Rotation engine status
The crop-rotation endpoint still fails closed with AGRONOMIC_RULES_NOT_APPROVED. BoponX will not fabricate planting dates, crop sequences, fertilizer advice, yield gains, water-saving percentages, or soil-health scores.

## Data roles and scientific boundaries

| Evidence | Role in BoponX | What it is not |
| --- | --- | --- |
| GPM IMERG Early | Recent / near-real-time precipitation context and map layer | A future rainfall forecast or field rain gauge |
| SMAP SPL3SMP_E | Candidate regional surface-soil-moisture context | Soil pH, nutrient test, or parcel-scale chemistry |
| NASA POWER | Historical/recent gridded climate context | A measurement taken in the farmer's field |
| Farmer observations | Previous crop, water access, drainage behavior, priorities | Independently verified scientific measurements |
| BAMIS / BARC / BRRI / BARI / SRDI evidence | Candidate local crop/soil/calendar constraints | Software rules until source/reuse/agronomic review is complete |

Every numeric environmental output should retain its dataset/product, time period, units, spatial meaning, quality/availability status, and source.

## Current APIs

| Endpoint | Purpose |
| --- | --- |
| GET /api/v1/health | Data/context readiness |
| GET /api/v1/areas | Bangladesh regional evidence reference points |
| GET /api/v1/places/search?q= | Bangladesh place search for farmer location selection |
| GET /api/v1/places/reverse?lat=&lon= | Optional reverse-geocode label for a map/GPS point |
| GET /api/v1/context?lat=&lon= | Resolve the selected location to local coverage/evidence context |
| GET /api/v1/agronomy/calendars?region= | Official BAMIS calendar-presence evidence for a regional hub |
| GET /api/v1/environment/recent?lat=&lon= | Selected-location recent NASA POWER context |
| GET /api/v1/environment/baseline?lat=&lon=&month= | Selected-month 2001–2020 NASA POWER climatology |
| GET /api/v1/climate/rajshahi-pilot | Integrity-gated pinned historical pilot |
| GET /api/v1/climate/rajshahi-pilot/monthly | Deterministic monthly aggregation of the pinned pilot |
| POST /api/v1/farms/validate | Validate farmer-known context without inventing unknowns |
| POST /api/v1/plans/preview | Generate the distinct three-month / 90-day field brief |
| GET /api/v1/crops | Empty until crop profiles pass source review |
| POST /api/v1/rotations/compare | Fails closed until local agronomic rules are approved |

## Run locally on Windows

From the repository root:

    py -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r .\backend\requirements-dev.txt
    .\.venv\Scripts\python.exe -m pytest -q backend\tests
    .\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

In a second terminal:

    cd frontend
    npm.cmd install
    npm.cmd run build
    npm.cmd run dev

Open the Vite address, normally http://localhost:5173.

## Verified historical pilot

The existing reproducible pilot remains:
- reference point: **24.37° N, 88.60° E**, near Rajshahi
- period: **2024-01-01 to 2024-12-31**
- variables: T2M and PRECTOTCORR
- NASA POWER daily API, Agroclimatology community, LST
- returned source product: **MERRA-2 reanalysis**
- valid dates: **366/366**
- pinned raw SHA-256: 512420f8cd947e21a84aa1e43292674be7e047fadfbcdd4ae4b3684647726495

It is a regional gridded reference, not a surveyed farm measurement and not a forecast.

## Competition compliance note

The supplied 2026 NASA Participant FAQ states that challenge summaries are released September 17, full challenge statements on October 28, and that teams are not allowed to begin working on challenge solutions before the hackathon. The Bangladesh local materials separately request an October prescreening concept video.

Because those instructions create a material eligibility question for any pre-built implementation, **Team EARTH.exe should obtain written clarification from the Dhaka Local Lead before presenting or merging pre-event implementation as competition work.** This repository keeps the engineering work auditable rather than hiding when it was created.

## Project principles

- NASA data is evidence, not decoration.
- Scientific calculations and future agronomic rules are deterministic and testable.
- Missing information stays missing.
- Regional satellite/reanalysis context is not represented as a field measurement.
- “Latest available” observations are timestamped; stale data are never silently shown as current.
- Bangla is a first-class interface language.
- Core functionality works without decorative motion.
- No visible release/version branding is used in the farmer experience.

## Sources

- NASA Space Apps Field Shift: https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/
- NASA GPM / IMERG: https://gpm.nasa.gov/data/imerg
- NASA GPM data directory: https://gpm.nasa.gov/data/directory
- NASA Worldview / GIBS: https://worldview.earthdata.nasa.gov/
- NASA POWER Daily API: https://power.larc.nasa.gov/docs/services/api/temporal/daily/
- SMAP SPL3SMP_E: https://nsidc.org/data/spl3smp_e/versions/6
- BAMIS crop-weather calendars: https://www.bamis.gov.bd/en/calendar
- BARC crop zoning: https://apps.barc.gov.bd/cropzoning/

Software source code is under the repository's MIT license. External datasets, map tiles, imagery, agricultural sources, and third-party assets retain their own terms.

**Team EARTH.exe:** Rezwan Hossain Prince · MD. Khairul Islam · Md. Siam Rayhan · Iftekhar Azad Ether · Tulip Mondal
