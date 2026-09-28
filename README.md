# BoponX

### From Space to Soil

**Team EARTH.exe | Bangladesh | NASA Space Apps Challenge 2026 | Field Shift: Adapting Farms with NASA Data**

BoponX is a location aware farmer decision support web application. It starts with a real field location, loads only the environmental and agricultural evidence that matters for that place, asks simple questions a farmer can realistically answer, and turns that information into a clear 90 day field brief.

The challenge destination is a transparent three season crop rotation explorer that combines NASA Earth observations, local agricultural evidence, crop characteristics and farmer priorities. Crop specific rotation recommendations remain locked until Bangladesh agronomic rules have been reviewed and encoded as deterministic rules.

> BoponX is an independent Team EARTH.exe project. NASA and NASA partners do not endorse this application.

## Current demo flow

**Field location → NASA evidence → local crop evidence → farmer observations → 90 day field brief → three season rotation architecture**

### 1. Field location

A farmer can choose the field in three ways:

1. Allow browser location access
2. Search a Bangladesh village, upazila, district or city
3. Choose a point directly on the map

The selected coordinates control the NASA requests and the regional crop calendar evidence. Exact coordinates are not stored by default.

### 2. NASA evidence for the selected place

BoponX keeps each data source in a clear role.

| Source | Current role | Scientific boundary |
| --- | --- | --- |
| GPM IMERG Early V07B | dated recent rainfall visualization | not a future forecast and not a field rain gauge |
| NASA POWER Daily | recent selected location temperature and rainfall context | regional gridded context, not a field measurement |
| NASA POWER Climatology | 2001 to 2020 planning month reference | historical climate context, not current weather |
| SMAP SPL3SMP E V6 | regional surface soil moisture context | never treated as pH, nutrients or parcel chemistry |
| NASA GIBS | true color and precipitation map imagery | visualization only |

The map always loads a standard OpenStreetMap base first. NASA imagery is optional, so a NASA map layer failure does not stop field selection.

### 3. Local agricultural evidence

BoponX routes the selected field to the nearest supported Bangladesh agricultural evidence region and shows official BAMIS crop calendar sources associated with that region.

A crop calendar appearing in the interface means a source exists. It does not mean BoponX has recommended that crop.

### 4. Farmer questions

The interface asks only practical questions:

- What was grown last
- How the field usually gets water
- What happens after heavy rain
- Whether a soil test report exists
- What matters most now

Every section supports a clear **Not sure** choice.

Soil pH is optional and appears only when the farmer says a soil test report exists. BoponX never infers pH from NASA data.

### New personalized farmer decision inputs

The farmer workflow now records a short crop history instead of only one previous crop. The farmer can also state which crop they are considering now.

BoponX uses those choices to create a decision readiness advisory. The advisory checks:

- whether the intended crop has an indexed official regional BAMIS calendar source
- recent NASA POWER rainfall context compared with the selected month historical climatology
- whether the field is mainly rainfed or irrigated
- what happens after heavy rain
- whether a soil test report exists
- the farmer priority
- recent crop history

The advisory can say that a crop is reasonable to explore, that more verification is needed, or that a water or drainage issue should be checked first. It does not rank crop suitability until reviewed agronomic crop requirements and sequence rules are available.

### Personalized three month climate plan

BoponX now requests a three month NASA POWER climatology window for the selected coordinates. Each planning month receives its own historical temperature and rainfall reference.

This means two farmers in different locations, two different starting months, or two different field situations can receive different 90 day tasks even when they use the same application.

The monthly climate references are historical context, not weather forecasts.

### 5. 90 day field brief

The plan is intentionally divided into three different stages:

1. **Know the field**  
   Build a reliable baseline from previous crop, water, drainage and soil test information.

2. **Watch the change**  
   Compare recent NASA context with field observations. This stage changes with the farmer priority.

3. **Decide the next move**  
   Review the evidence, identify missing information and prepare the next seasonal decision.

The frontend uses NASA information that was already loaded for the selected field. Generating the 90 day brief does not repeat slow external NASA requests, which keeps the demo responsive.

### 6. Three season rotation explorer

The closing section shows the intended challenge architecture:

**Field → NASA evidence → local agronomic rules → several feasible rotations → farmer decision**

The actual rotation endpoint remains fail closed until reviewed Bangladesh crop requirements, soil constraints and crop sequence rules are available.

BoponX does not fabricate:

- planting dates
- crop sequences
- pH
- nutrient values
- yield gains
- water saving percentages
- soil health scores
- weather forecasts
- NASA endorsement

## Demo stability work

The current frontend includes:

- English only farmer interface
- real NASA and USGS Landsat imagery from Bangladesh
- Three.js Earth animation with off screen rendering paused to reduce GPU load
- MapLibre map with OpenStreetMap as the independent base
- optional NASA GIBS true color and IMERG overlays
- guarded map animation so a bad map update cannot crash the whole interface
- visible loading and map failure messages
- professional line icons for crops, water, drainage, soil test and farmer priorities
- a React error boundary so an unexpected interface exception shows a recovery screen instead of a blank page
- defensive 90 day report rendering
- automated backend tests for three distinct plan stages and priority sensitive Month 2 tasks
- frontend TypeScript checking and Vite production build in CI

## API

| Endpoint | Purpose |
| --- | --- |
| GET /api/v1/health | application and data readiness |
| GET /api/v1/areas | Bangladesh agricultural evidence hubs |
| GET /api/v1/places/search?q= | Bangladesh place search |
| GET /api/v1/places/reverse?lat=&lon= | optional label for a selected point |
| GET /api/v1/context?lat=&lon= | location specific NASA and local evidence context |
| GET /api/v1/agronomy/calendars?region= | BAMIS calendar evidence |
| GET /api/v1/environment/recent?lat=&lon= | selected location NASA POWER recent context |
| GET /api/v1/environment/baseline?lat=&lon=&month= | selected month 2001 to 2020 POWER climatology |
| GET /api/v1/environment/baseline-window?lat=&lon=&start_month= | three consecutive monthly POWER climatology references for the 90 day plan |
| POST /api/v1/farms/validate | validate farmer context without inventing unknowns |
| POST /api/v1/plans/preview | generate the deterministic three stage 90 day brief |
| GET /api/v1/crops | remains empty until crop profiles pass review |
| POST /api/v1/rotations/compare | remains locked until agronomic rules are approved |

## Run locally on Windows

From the repository root:

    py -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r .\backend\requirements-dev.txt
    .\.venv\Scripts\python.exe -m pytest -q backend\tests
    .\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

Open a second terminal:

    cd frontend
    npm.cmd install
    npm.cmd run build
    npm.cmd run dev

Open:

    http://localhost:5173

For mobile testing on the same private network:

    npm.cmd run dev -- --host 0.0.0.0

The backend can be exposed on the private network with:

    .\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

Do not disable the firewall. Allow only the private network prompt if Windows asks.

## Demo acceptance check

Before recording the competition demo, verify this complete flow on the actual presentation laptop and phone:

- homepage image and 3D Earth render correctly
- browser location allowed and denied paths both work
- place search works
- map point selection works
- NASA overlays can be toggled
- selecting a field updates regional evidence
- recent POWER and climatology either show real values or a clear unavailable state
- farmer options show icons and remain selectable
- the 90 day brief appears without a blank screen
- Month 1, Month 2 and Month 3 have different tasks
- Print or Save PDF is readable
- reduced motion mode remains usable

Passing automated CI is necessary, but live network and browser behavior still require this manual demo check.

## Visual and data credits

The website uses NASA Earth Observatory and USGS Landsat imagery of **Baniachong, Bangladesh** from the NASA story **Fine Tuning Irrigation in Asia**.

- NASA Earth Observatory: https://science.nasa.gov/earth/earth-observatory/fine-tuning-irrigation-in-asia-148203/
- NASA GIBS and Worldview: https://worldview.earthdata.nasa.gov/
- OpenStreetMap tiles and Nominatim retain their own attribution and usage terms

## Primary scientific sources

- Field Shift challenge: https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/
- GPM IMERG: https://gpm.nasa.gov/data/imerg
- GPM data directory: https://gpm.nasa.gov/data/directory
- SMAP SPL3SMP E Version 6: https://nsidc.org/data/spl3smp_e/versions/6
- NASA POWER Daily API: https://power.larc.nasa.gov/docs/services/api/temporal/daily/
- NASA POWER Climatology API: https://power.larc.nasa.gov/docs/services/api/temporal/climatology/
- BAMIS crop weather calendars: https://www.bamis.gov.bd/en/calendar
- BARC crop zoning: https://apps.barc.gov.bd/cropzoning/

## Team

Rezwan Hossain Prince (TEAM LEADER)

MD. Khairul Islam  
Md. Siam Rayhan  
Iftekhar Azad Ether  
Tulip Mondal
