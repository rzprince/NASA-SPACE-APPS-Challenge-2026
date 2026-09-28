# BoponX

### From Space to Soil

**Team EARTH.exe · Bangladesh · NASA Space Apps Challenge 2026 · Field Shift: Adapting Farms with NASA Data**

BoponX is a full stack field decision support platform that connects one farm location with NASA Earth observations, agroclimate context, verified agricultural sources and farmer knowledge.

The core workflow is:

**NASA Data → Farm Analysis → Crop Rotation Scenarios → Explainable Decision Support**

A farmer or adviser selects a field anywhere on Earth. BoponX resolves the environmental context for that location, connects reviewed local agriculture sources where available, records the farmer's recent crop history and priorities, and carries the same evidence into rotation exploration and a printable 90 day field plan.

> BoponX is an independent Team EARTH.exe project. NASA and NASA partners do not endorse this application.

## Earth Twin

Earth Twin is the spatial entry point for the platform.

It provides:

- a realistic Three.js Earth from space
- NASA Blue Marble as the complete global reference texture
- slow automatic Earth rotation
- drag to rotate and scroll to zoom
- tap on the globe to choose a field
- browser geolocation
- global place search
- NASA GIBS reference labels that become more visible as the camera moves closer
- optional dated MODIS Terra true color overlay
- optional GPM IMERG precipitation overlay
- optional SMAP surface soil moisture overlay
- a field marker and automatic camera move to the selected point

The NASA Blue Marble reference remains visible even when a dated overlay is incomplete or unavailable.

For Bangladesh, Earth Twin also includes a quick selector for all 8 divisions and all 64 districts.

## NASA Fusion Engine

NASA information is resolved once for the selected field and reused throughout the workflow.

### NASA POWER Daily

The selected coordinate is queried for recent:

- mean 2 m air temperature
- mean daily maximum temperature
- mean daily minimum temperature
- precipitation
- 2 m relative humidity
- 2 m wind speed

POWER values are regional gridded agroclimate context. They are not measurements made inside the farmer's field.

### NASA POWER climatology

BoponX loads a three month 2001 to 2020 climatology window for the selected coordinate and planning month.

Recent conditions can be compared with the historical reference to describe context such as:

- wetter than the selected month baseline
- near the selected month baseline
- drier than the selected month baseline
- warmer than the selected month baseline
- cooler than the selected month baseline

These comparisons are decision context, not weather forecasts.

### GPM IMERG

GPM IMERG supplies recent precipitation spatial evidence.

BoponX does not treat the IMERG layer as a future forecast or a field rain gauge.

### SMAP

SMAP supplies regional surface soil moisture context.

BoponX never treats SMAP as:

- soil pH
- nutrient chemistry
- a laboratory soil test
- parcel scale soil truth

### NASA GIBS

NASA GIBS provides the spatial delivery layer used for dated Earth observation overlays and reference labels.

## Local Data Mesh

Environmental coverage can be global while agricultural authority remains country specific. BoponX keeps those two responsibilities separate.

Reviewed national agriculture adapters currently include official sources for:

- Bangladesh
- India
- United States
- Canada
- Japan
- Brazil
- Philippines
- Sri Lanka
- Australia
- United Kingdom

For a country without a reviewed adapter, BoponX continues to provide NASA analysis and FAO references while exposing a country specific route to find the official agriculture authority. It does not label an unreviewed site as verified.

### Bangladesh agriculture layer

Bangladesh has the deepest local evidence connection in the current project:

- Ministry of Agriculture
- Department of Agricultural Extension
- Agriculture Information Service
- Bangladesh Agro Meteorological Information Service
- Bangladesh Agricultural Research Council Crop Zoning
- BAMIS crop weather calendar evidence
- FAO Crop Calendar reference

BARC crop zoning provides upazila level crop suitability and zoning reference. AIS provides crop production technology, seasonal agriculture information and farmer information services. BAMIS provides agrometeorological and crop weather calendar information.

## Farmer Context

Rotation Lab asks only information the farmer or adviser can reasonably know:

- crops recently grown in the field
- what crop is being considered now
- whether the field is mainly rainfed, irrigated, or both
- what happens after heavy rain
- whether a real soil test report exists
- the current priority: water, soil, or production stability

A farmer can choose **Not sure**.

pH is accepted only when a real soil test report exists.

## Farm Analysis

The deterministic planning engine combines:

- selected field coordinates
- recent NASA POWER context
- three monthly POWER climatology references
- regional agricultural source coverage
- recent crop history
- current crop intention
- water source
- drainage observation
- soil test availability
- farmer priority

The engine can identify evidence gaps, water or drainage risks, and whether an intended crop has a regional source that should be reviewed.

BoponX does not invent a crop suitability score when reviewed crop requirements or sequence rules are missing.

## Rotation Lab

Rotation Lab carries forward the field evidence instead of repeating the NASA dashboard.

Where enough regional crop evidence exists, it can display several exploration paths across three seasons. These paths remain clearly separated from final agronomic ranking.

Where the required local crop evidence is missing, BoponX shows an evidence gate instead of fabricating crop names or crop sequences.

## 90 Day Field Plan

The field plan is designed to remain useful when printed.

It contains:

- the selected field and coordinates
- an explainable decision message
- recent rainfall and temperature context
- the reasons behind the advice
- three visually separated monthly stages
- a monthly NASA POWER historical reference
- action icons and plain language tasks
- local support information
- NASA source names
- local agriculture source names
- scientific limitations

For Bangladesh, the printed plan also shows the Agriculture Call Center number **16123**, so the printed output does not depend on clicking a website link.

## Global and local capability

| Capability | Coverage |
| --- | --- |
| 3D field selection | Global |
| Global place search | Global |
| NASA POWER recent agroclimate | Global point query |
| NASA POWER climatology | Global point query |
| GPM IMERG visualization | Global product coverage subject to product limits |
| SMAP soil moisture visualization | Global land product coverage subject to product limits |
| NASA Blue Marble reference Earth | Global |
| NASA GIBS reference labels | Global |
| FAO Crop Calendar reference | Multi country |
| Reviewed national agriculture adapters | Country by country |
| Bangladesh district selection | 64 districts |
| Bangladesh regional crop weather evidence | Connected through BAMIS evidence hubs |
| Final universal crop rotation ranking | Evidence gated |

## Scientific boundaries

BoponX does not claim that:

- NASA data measure field pH or nutrients
- a satellite grid cell is the same as a field sensor
- historical climatology is a weather forecast
- an official crop calendar automatically proves field suitability
- an exploration path is a validated crop rotation
- NASA endorses BoponX

The final crop rotation ranking layer remains dependent on reviewed crop requirements, soil constraints and crop sequence rules.

## Technology

### Frontend

- React
- TypeScript
- Vite
- Three.js
- OrbitControls and globe ray casting
- NASA Earth imagery and GIBS overlays
- responsive mission control interface
- print optimized farmer field plan

### Backend

- Python
- FastAPI
- deterministic decision logic
- NASA POWER service adapters
- global geocoding
- verified national agriculture source registry
- Bangladesh crop calendar evidence index
- automated tests

## API

| Endpoint | Purpose |
| --- | --- |
| GET /api/v1/health | application readiness |
| GET /api/v1/places/search?q= | global place search |
| GET /api/v1/places/reverse?lat=&lon= | global reverse geocoding |
| GET /api/v1/context?lat=&lon= | NASA context and Bangladesh deep local evidence |
| GET /api/v1/local-sources?country_code= | reviewed national agriculture source registry |
| GET /api/v1/agronomy/calendars?region= | Bangladesh BAMIS regional crop calendar index |
| GET /api/v1/environment/recent?lat=&lon= | recent selected location NASA POWER context |
| GET /api/v1/environment/baseline-window?lat=&lon=&start_month= | three month NASA POWER climatology window |
| POST /api/v1/farms/validate | validate farmer known information |
| POST /api/v1/plans/preview | deterministic 90 day field decision plan |
| POST /api/v1/rotations/compare | remains fail closed until agronomic sequence rules are approved |

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

Open:

    http://localhost:5173

## Primary scientific and agricultural sources

- Field Shift challenge  
  https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/

- NASA Blue Marble  
  https://science.nasa.gov/earth/earth-observatory/blue-marble-next-generation/

- NASA GIBS  
  https://nasa-gibs.github.io/gibs-api-docs/

- GPM IMERG  
  https://gpm.nasa.gov/data/imerg

- SMAP SPL3SMP_E Version 6  
  https://nsidc.org/data/spl3smp_e/versions/6

- NASA POWER Daily API  
  https://power.larc.nasa.gov/docs/services/api/temporal/daily/

- NASA POWER Climatology API  
  https://power.larc.nasa.gov/docs/services/api/temporal/climatology/

- Bangladesh Agriculture Information Service  
  https://ais.gov.bd/

- Bangladesh Agro Meteorological Information Service  
  https://www.bamis.gov.bd/

- Bangladesh Agricultural Research Council Crop Zoning  
  https://apps.barc.gov.bd/cropzoning/

- FAO Crop Calendar  
  https://cropcalendar.apps.fao.org/

## Team

**Rezwan Hossain Prince · Team Leader**

MD. Khairul Islam  
Md. Siam Rayhan  
Iftekhar Azad Ether  
Tulip Mondal
