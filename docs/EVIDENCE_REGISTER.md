# BoponX evidence register and scientific-method boundary
**Snapshot reviewed:** NASA POWER pilot, acquired 23 September 2026.  
**Purpose:** Permit a judge or developer to trace every quantitative claim.

## Pinned historical environmental input

| Field | Recorded value / interpretation |
| --- | --- |
| Provider and service | NASA Langley POWER, Daily Point API, API response v2.10.0 |
| Origin of requested meteorology | MERRA-2 reanalysis (`header.sources = ["MERRA2"]`), **not direct satellite retrieval** |
| Period | 2024-01-01 through 2024-12-31; 366 dates |
| Time convention | LST (local solar time), as returned by POWER |
| Reference point | 24.37° N, 88.60° E; provisional Rajshahi region, **not surveyed field coordinates** |
| Variables | `T2M`, daily mean near-surface temperature in °C; `PRECTOTCORR`, corrected daily precipitation in mm/day |
| Valid days | 366/366 for both requested variables in the pinned response |
| Derived annual summary | Mean of valid daily `T2M`: 25.71254098360656 °C; precipitation sum: 1,863.19 mm over complete 2024 |
| Raw SHA-256 | `512420f8cd947e21a84aa1e43292674be7e047fadfbcdd4ae4b3684647726495` |
| Original request | `https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M%2CPRECTOTCORR&community=AG&latitude=24.37&longitude=88.6&start=20240101&end=20241231&format=JSON&time-standard=LST` |
| Retrieval timestamp | 2026-09-23T12:22:07.952761+00:00 |
| Distribution | Original response + processed JSON in the dated NASA-validation workflow artifact; **not committed to Git** |

**How the monthly indicator is calculated:** For month `m`, the backend
counts expected calendar days in the selected period and valid daily values.
If all dates have valid `T2M`, it reports `sum(T2M_daily)/days_expected`
as the month's mean in °C. If all have valid `PRECTOTCORR`, it reports
`sum(PRECTOTCORR_daily)` as a total in mm. A missing date or invalid
observation suppresses the complete-month figure (`null`). Dates are checked
against the requested range; duplicates and unrecognized units fail closed.
No gaps are estimated. Synthetic test fixtures are never published as NASA
measurements.

**Spatial meaning:** NASA POWER provides meteorological parameters at their
source grid resolution. Its MERRA-2 meteorology is approximately 0.5° latitude
by 0.625° longitude, not a meter-level map or an individual field measurement.
An entered coordinate selects gridded context. A 2024-only snapshot cannot
prove a changing long-term climate trend or predict the next planting season.
No crop suitability, irrigation saving or yield benefit is calculated.

**Source references and correct credit**
- NASA POWER Daily API: https://power.larc.nasa.gov/docs/services/api/temporal/daily/
- POWER source-grid methodology: https://power.larc.nasa.gov/docs/methodology/data/sources/
- POWER citation/acknowledgement policy: https://power.larc.nasa.gov/docs/referencing/
- Original NASA validation run: https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026/actions/runs/35860018103

NASA requests the POWER service name, version and access date in work products,
and asks for notification when data are transmitted to other researchers.
The repository's MIT software license does not grant additional rights over
external data or images.

## Agricultural sources — **research, not integrated data**

| Organization / source | Intended evidence | Status and constraint |
| --- | --- | --- |
| Bangladesh Rice Research Institute rice calendars | Local Aus/Aman/Boro crop-calendar and variety research | Public source identified; variety, region and date constraints require expert review before software rules. https://brri.gov.bd/pages/static-pages/6922dea6933eb65569e1c55f |
| Bangladesh Department of Agricultural Extension, BAMIS | Official crop-weather calendar references | Public calendar index identified; no calendar extracted, copied or converted to an approved algorithm. https://www.bamis.gov.bd/en/calendar |
| Bangladesh Agricultural Research Council (BARC), crop zoning | Soil/crop-suitability research and local zoning | Dataset-specific permission, geography and interpretation review required. https://apps.barc.gov.bd/cropzoning/ |
| BARC crop-calendar portal | Candidate crop-calendar source | Access and reuse restrictions apply; its portal states a commercial-use restriction. No restricted extract is bundled. https://apps.barc.gov.bd/cropcalendar/ |

**No local soil measurements have been independently verified.** Farmer-entered
soil pH, texture, previous crop and irrigation are user statements. Unknown
values remain unknown. Crop rotation is blocked until the reviewed references
can be translated into deterministic constraints.

## Earth-observation expansion — not yet integrated

- Candidate: GPM IMERG Final daily precipitation (version and spatial/temporal
  aggregation, QA, Earthdata access and terms require confirmation):
  https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGDF_07/summary
- Candidate: NASA SMAP regional surface-soil-moisture product, not a field soil
  test: https://nsidc.org/data/spl3smp_e/versions/6

The published 2026 challenge summary requires NASA Earth observations to
inform decisions. This prototype's POWER/MERRA-2 reanalysis establishes an
environmental-data pipeline, but it does **not yet demonstrate material use of
a validated direct Earth-observation product in the rotation engine**.

## Deterministic three-month preparation brief

The `POST /api/v1/plans/preview` endpoint uses the farmer's explicitly entered
profile, chosen planning start month/year, optional *farmer-considered* crop
and primary priority. It aligns each of the next **three calendar months**
with the **same calendar month in the one validated historical 2024 dataset**.
For example, November 2026 is shown beside observed **November 2024** rainfall
and mean temperature with the historical year displayed; this is **not a
November 2026 weather forecast**. Missing historical months yield `null`,
not an invented estimate. Bilingual tasks involve field logging, confirming
missing information and discussing locally validated crop calendars with
the agricultural extension service. No crop, sowing date, fertilizer,
irrigation volume or numeric benefit is recommended. Crop-rotation comparison
continues to fail closed pending local agronomic review.

The report can be printed to **A4 PDF using the browser's native printing
system**, which preserves locally available Bengali fonts. The API neither
stores the farmer profile nor returns a pre-rendered PDF binary. The PDF
exists on the farmer's device only after the user chooses Save as PDF.

## UI imagery and intellectual honesty

The Bangladesh map silhouette adapts Natural Earth 1:110m country geometry (public domain; https://www.naturalearthdata.com/about/terms-of-use/); the pilot pin represents 24.37° N, 88.60° E and is not a surveyed farm location. The SVG rivers/terrain effects are original illustration, not geospatial river data.

The animated orbital field/satellite scene is original conceptual CSS-3D
artwork. The rainfall columns are a transformation of the pinned *historical*
monthly indicator. Neither is an actual satellite image, geographic field
boundary, flood map, soil-moisture observation or future-weather scenario.
