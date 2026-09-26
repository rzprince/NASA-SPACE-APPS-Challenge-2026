# BoponX · বপনএক্স
### From Space to Soil · মহাকাশ থেকে মাটিতে

**Team EARTH.exe · Bangladesh · NASA Space Apps Challenge 2026 · Field Shift: Adapting Farms with NASA Data**

BoponX is a bilingual, location-first farmer decision-support web application. It starts with a real field location, loads only the environmental and agricultural evidence relevant to that place, asks the farmer only questions they can reasonably answer, and turns the evidence into a practical 90-day decision-support routine.

The challenge destination is a transparent three-season rotation explorer that combines NASA Earth observations, local soil/agricultural evidence, crop characteristics and farmer priorities without inventing agronomic rules.

> BoponX is an independent Team EARTH.exe project. NASA and NASA partners have not endorsed this application.

## Current experience

The active web application has been rebuilt around one continuous farmer journey:

**field location → NASA evidence → local crop evidence → farmer-known facts → 90-day field brief → future three-season rotation comparison**

### Cinematic opening
- real NASA/USGS Landsat imagery of Baniachong, Bangladesh
- live WebGL/Three.js Earth visualization
- data-orbit animation for IMERG, SMAP and POWER
- responsive motion with prefers-reduced-motion fallback
- no farmer-facing release/version labels

### Field location
A farmer can:
- use browser/device geolocation after permission
- search a Bangladesh village, upazila, district or place
- select a regional fallback hub
- tap directly on the interactive map

The selected coordinates control the NASA requests and local evidence shown in the rest of the app. Exact coordinates are not persisted by default.

### NASA map and Earth signals
The map can switch between:
- OpenStreetMap navigation
- NASA GIBS true-color imagery
- NASA GIBS / GPM IMERG recent precipitation overlay

The evidence theatre keeps data roles separate:

| Source | Current BoponX role | Important boundary |
| --- | --- | --- |
| GPM IMERG Early V07B | near-real-time precipitation map evidence | not a future forecast or field rain gauge |
| NASA POWER Daily | selected-location recent gridded temperature/rainfall context | not a measurement taken inside the farmer's field |
| NASA POWER Climatology | 2001–2020 planning-month historical baseline | not current weather and not a forecast |
| SMAP SPL3SMP_E V6 | candidate regional surface-soil-moisture context | not pH, nutrients or parcel-scale chemistry |
| NASA GIBS | true-color / precipitation visualization | visualization, not a separate agronomic recommendation |

NASA currently documents IMERG Early V07B at about **4-hour minimum latency** and **0.1° / ~10 km** spatial resolution. BoponX therefore uses “near-real-time” / “latest available” language instead of “live forecast”.

### Local Bangladesh evidence
BoponX indexes official BAMIS crop-weather-calendar presence by regional evidence hub for major crops including Aman, Aus, Boro, wheat, mustard, lentil, jute, maize and green gram.

A calendar appearing in the UI means an official regional source exists. It does **not** mean that BoponX has automatically decided the crop is suitable.

### Farmer-first questions
The default workflow asks only:
- what was grown last
- how the field normally receives water
- what happens after heavy rain
- whether a soil-test report exists
- the farmer's current priority: water, soil or production stability

“I don't know / নিশ্চিত নই” is a normal answer.

Numeric pH appears only when the farmer explicitly says a soil-test report exists. The backend rejects pH without that soil-test state.

### Distinct 90-day field brief
The three months are intentionally different:

1. **Know the field** — establish previous-crop, water, drainage and soil-test evidence.
2. **Watch the change** — compare recent Earth-observation/climate context with field observations; tasks vary with farmer priority.
3. **Decide the next move** — review what is known, identify missing evidence and prepare the next seasonal decision.

The printable bilingual report includes the location, recent NASA context when available, historical baseline, local calendar sources, month-specific tasks and scientific limitations.

### Three-season rotation explorer
The visible rotation section explains the target architecture, but crop-specific rotation output remains fail-closed through AGRONOMIC_RULES_NOT_APPROVED.

BoponX will not fabricate:
- planting/transplanting dates
- crop sequences
- pH
- nutrient values
- yield gains
- water-saving percentages
- soil-health scores
- weather forecasts
- NASA endorsement

The next scientific gate is to translate source-reviewed Bangladesh crop calendars, crop requirements, local soil constraints and crop-sequence rules into deterministic testable rule packs.

## API

| Endpoint | Purpose |
| --- | --- |
| GET /api/v1/health | application/data readiness |
| GET /api/v1/areas | Bangladesh agricultural evidence-hub references |
| GET /api/v1/places/search?q= | Bangladesh place search |
| GET /api/v1/places/reverse?lat=&lon= | optional label for a GPS/map point |
| GET /api/v1/context?lat=&lon= | location-specific NASA/local evidence context |
| GET /api/v1/agronomy/calendars?region= | BAMIS calendar-presence evidence |
| GET /api/v1/environment/recent?lat=&lon= | selected-location recent NASA POWER context |
| GET /api/v1/environment/baseline?lat=&lon=&month= | selected-month 2001–2020 POWER climatology |
| POST /api/v1/farms/validate | validate farmer-known context without inventing unknowns |
| POST /api/v1/plans/preview | generate the distinct 90-day field brief |
| GET /api/v1/crops | fails closed until crop profiles pass review |
| POST /api/v1/rotations/compare | fails closed until agronomic rules are approved |

The older pinned Rajshahi POWER snapshot remains only as a reproducible regression/provenance artifact and is not the active website's primary experience.

## Run locally on Windows

From repository root:

    py -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r .\backend\requirements-dev.txt
    .\.venv\Scripts\python.exe -m pytest -q backend\tests
    .\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

In a second terminal:

    cd frontend
    npm.cmd install
    npm.cmd run build
    npm.cmd run dev

Open http://localhost:5173.

If port 8000 is already occupied:

    netstat -ano | findstr :8000
    taskkill /PID <PID> /F

Then start the backend again.

## Visual/data credits

The website uses a real NASA Earth Observatory / USGS Landsat image of **Baniachong, Bangladesh** from “Fine-Tuning Irrigation in Asia” as a visual case study and opening image.

- NASA Earth Observatory story: https://science.nasa.gov/earth/earth-observatory/fine-tuning-irrigation-in-asia-148203/
- NASA/USGS Landsat image credit: Earth Observatory / Lauren Dauphin using Landsat data from the U.S. Geological Survey
- NASA GIBS / Worldview: https://worldview.earthdata.nasa.gov/
- OpenStreetMap tiles/geocoding retain their own attribution and usage terms.

## Primary scientific sources

- Field Shift challenge: https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/
- GPM IMERG: https://gpm.nasa.gov/data/imerg
- GPM data directory: https://gpm.nasa.gov/data/directory
- SMAP SPL3SMP_E V6: https://nsidc.org/data/spl3smp_e/versions/6
- NASA POWER Daily API: https://power.larc.nasa.gov/docs/services/api/temporal/daily/
- NASA POWER Climatology API: https://power.larc.nasa.gov/docs/services/api/temporal/climatology/
- BAMIS crop-weather calendars: https://www.bamis.gov.bd/en/calendar
- BARC crop zoning: https://apps.barc.gov.bd/cropzoning/

## Competition compliance note

The supplied 2026 Participant FAQ and Bangladesh local prescreening materials should be reconciled with the Dhaka Local Lead before presenting pre-event implementation as competition work. Repository history is kept explicit rather than disguising when implementation occurred.

## Team

Rezwan Hossain Prince · MD. Khairul Islam · Md. Siam Rayhan · Iftekhar Azad Ether · Tulip Mondal
