# BoponX

### From Space to Soil

**Team EARTH.exe · Bangladesh · NASA Space Apps Challenge 2026 · Field Shift: Adapting Farms with NASA Data**

BoponX is no longer designed as a scrolling information site. It is a full stack **Earth intelligence mission control for farm decisions**.

The farmer selects one field anywhere on Earth. BoponX builds a single evidence stack for that location, combines NASA Earth observations and agroclimate context with verified local agricultural sources and farmer knowledge, then carries that evidence into a rotation sandbox and a printable 90 day action card.

> BoponX is an independent Team EARTH.exe project. NASA and NASA partners do not endorse this application.

## Why the product was rebuilt

The earlier prototype repeated the same information across several sections. NASA products appeared as separate cards rather than one decision pipeline. The new architecture is intentionally different:

**Earth Twin → NASA Fusion Engine → Local Data Mesh → Farmer Context → Rotation Lab → Farmer Action Card**

NASA evidence is resolved once, then reused by the decision engine. Local sources are shown once in the Local Data Mesh. The printable action card contains usable instructions and source names instead of depending on clickable links.

## Earth Twin

The main interface is an interactive global Earth selector.

A farmer or adviser can:

- allow browser location access
- search any village, district, city or country
- tap directly on the interactive globe
- switch NASA spatial layers without leaving the selected field

The selected coordinate drives the NASA POWER queries and the local source lookup.

### Spatial NASA layers

The Earth Twin currently exposes:

- **NASA GIBS true color imagery**
- **GPM IMERG V07B precipitation visualization**
- **SMAP surface soil moisture visualization**

The map always keeps a standard OpenStreetMap base available. A NASA imagery failure cannot prevent field selection.

## NASA Fusion Engine

The right side of Earth Twin is a single evidence engine instead of several repeated NASA sections.

### NASA POWER Daily

BoponX requests the current selected location for:

- mean 2 m air temperature
- mean daily maximum temperature
- mean daily minimum temperature
- precipitation
- 2 m relative humidity
- 2 m wind speed

These values are regional gridded agroclimate context, not measurements taken inside the farmer's field.

### NASA POWER climatology

BoponX also requests a three month 2001 to 2020 climatology window for the selected point.

The engine compares recent POWER rainfall and temperature context with the selected month historical reference. This produces transparent context such as:

- wetter than baseline
- near baseline
- drier than baseline
- warmer than baseline
- cooler than baseline

These are contextual comparisons, not weather forecasts.

### GPM IMERG

The map exposes IMERG V07B recent precipitation spatial evidence. NASA currently documents the Early Run at about 4 hour minimum latency and 0.1 degree, roughly 10 km, spatial resolution.

IMERG is never described as a future weather forecast or as a rain gauge inside the field.

### SMAP

The map exposes regional surface soil moisture spatial context.

BoponX never treats SMAP as:

- soil pH
- nutrient chemistry
- a laboratory soil test
- parcel scale truth

The 2026 SMAP geolocation advisory remains documented in the evidence register.

## Decision Readiness

The Earth Twin shows a **Decision Readiness** value.

This is not a crop suitability score.

It only measures whether the decision workflow has enough evidence loaded, such as:

- field coordinates
- recent NASA context
- historical baseline
- country information
- verified local source adapter
- crop history
- farmer intention
- water and drainage observations

This keeps the visual impact of a mission control interface without pretending that a UI score is agronomic science.

## Local Data Mesh

There is no single reliable API containing every government's agricultural information.

BoponX therefore uses a **verified adapter architecture** instead of inventing worldwide local data.

Currently reviewed adapters include:

- Bangladesh Department of Agricultural Extension / BAMIS
- Bangladesh Agricultural Research Council crop zoning
- India Meteorological Department Agromet Advisory Services
- USDA Web Soil Survey
- USDA Climate Hubs
- Australian Department of Agriculture, Fisheries and Forestry soil and climate references
- UK DEFRA agricultural climate reference
- FAO Crop Calendar as the global intergovernmental fallback

Bangladesh remains the deepest local evidence implementation because BoponX has indexed regional BAMIS crop weather calendar presence.

For a country without a reviewed national adapter, NASA analysis still works globally, but the interface clearly says that verified local agricultural evidence still needs to be connected.

That behavior is deliberate. BoponX does not fabricate a government dataset simply to make the map look complete.

## Farmer Context

The Rotation Lab asks only information the farmer is likely to know:

- recent crops grown in the field
- what crop the farmer is considering now
- whether the field is mostly rainfed, irrigated, or both
- whether water drains or remains after heavy rain
- whether a real soil test report exists
- current priority: water, soil, or production stability

A farmer can still choose **Not sure**.

pH is only accepted when the farmer says a real soil test report exists.

## Rotation Lab

The new Rotation Lab looks and behaves like a decision workspace rather than a questionnaire page.

It carries forward only decision-relevant Earth signals:

- field location
- recent rainfall context
- verified local source coverage
- farmer crop intention

It displays multiple **exploration paths** so the user can reason across three seasons.

These paths are deliberately labelled as exploration, not ranked prescriptions.

BoponX will not claim that one crop sequence is agronomically superior until reviewed local crop requirements, soil constraints and crop sequence rules are encoded.

This scientific gate is more important than making a visually impressive but unsupported recommendation.

## 90 day Farmer Action Card

The final output was redesigned around an illiterate or low literacy farmer use case.

The printed card no longer depends on clickable links.

It contains:

- the field name and coordinates
- a plain language decision message
- rainfall and temperature context
- three visually separated months
- a limited number of concrete actions per month
- evidence source names
- scientific limitations

Digital source links remain available in the application for advisers and judges, but the printed card is usable on its own.

## Global versus local capability

| Capability | Coverage |
| --- | --- |
| Global field selection | Global |
| NASA POWER recent agroclimate | Global point query |
| NASA POWER climatology | Global point query |
| GPM IMERG visualization | Global except product limitations near poles |
| SMAP soil moisture visualization | Global land product coverage |
| NASA GIBS Earth imagery | Global |
| FAO Crop Calendar reference | Multi-country global reference |
| Verified government agriculture adapters | Country by country, only after review |
| Bangladesh regional crop calendar index | Implemented |
| Final agronomic crop rotation ranking | Still evidence gated |

## Technology

BoponX intentionally uses a focused stack instead of adding languages only to increase code volume.

### Frontend

- React
- TypeScript
- Vite
- MapLibre GL globe projection
- NASA GIBS WMS layers
- custom mission control UI
- responsive and print layouts

### Backend

- Python
- FastAPI
- deterministic planning logic
- NASA POWER service adapters
- verified local source registry
- source indexed Bangladesh agronomy evidence
- automated tests

Adding Go, Node, Next.js, or another framework would not improve the scientific decision pipeline by itself. The architecture favors traceability, testability and demo reliability over unnecessary technology count.

## API

| Endpoint | Purpose |
| --- | --- |
| GET /api/v1/health | application readiness |
| GET /api/v1/places/search?q= | global place search |
| GET /api/v1/places/reverse?lat=&lon= | global reverse geocoding |
| GET /api/v1/context?lat=&lon= | global NASA context and Bangladesh deep local evidence |
| GET /api/v1/local-sources?country_code= | verified national agriculture source registry |
| GET /api/v1/agronomy/calendars?region= | Bangladesh BAMIS regional calendar index |
| GET /api/v1/environment/recent?lat=&lon= | recent selected location NASA POWER context |
| GET /api/v1/environment/baseline-window?lat=&lon=&start_month= | three month POWER climatology window |
| POST /api/v1/farms/validate | validate farmer known information |
| POST /api/v1/plans/preview | deterministic 90 day decision support plan |
| POST /api/v1/rotations/compare | remains fail closed until agronomic sequence rules are approved |

## Run locally on Windows

From repository root:

    py -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r .\backend\requirements-dev.txt
    .\.venv\Scripts\python.exe -m pytest -q backend\tests
    .\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

Second terminal:

    cd frontend
    npm.cmd install
    npm.cmd run build
    npm.cmd run dev

Open:

    http://localhost:5173

## Demo acceptance checklist

Before recording the competition video:

- select a field on the globe
- test current location permission
- search a place outside Bangladesh
- test Bangladesh place selection
- switch true color, IMERG and SMAP layers
- confirm recent POWER values load or show a truthful unavailable state
- confirm three month climatology loads
- confirm Bangladesh shows BAMIS / BARC in Local Data Mesh
- confirm another reviewed country shows its official source adapter
- confirm an unreviewed country shows global fallback rather than invented government data
- enter crop history and farmer intention
- open Rotation Lab
- run the decision engine
- print the Farmer Action Card
- test the full path on the presentation laptop and phone

## Primary scientific and agricultural sources

- Field Shift challenge  
  https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/

- GPM IMERG  
  https://gpm.nasa.gov/data/imerg

- GPM precipitation data directory  
  https://gpm.nasa.gov/data/directory

- SMAP SPL3SMP_E Version 6  
  https://nsidc.org/data/spl3smp_e/versions/6

- NASA POWER Daily API  
  https://power.larc.nasa.gov/docs/services/api/temporal/daily/

- NASA POWER Climatology API  
  https://power.larc.nasa.gov/docs/services/api/temporal/climatology/

- NASA Worldview / GIBS  
  https://worldview.earthdata.nasa.gov/

- FAO Crop Calendar  
  https://cropcalendar.apps.fao.org/

- Bangladesh Agro-Meteorological Information Service  
  https://www.bamis.gov.bd/

- BARC Crop Zoning  
  https://apps.barc.gov.bd/cropzoning/

## Team

**Rezwan Hossain Prince — Team Leader**

MD. Khairul Islam  
Md. Siam Rayhan  
Iftekhar Azad Ether  
Tulip Mondal
