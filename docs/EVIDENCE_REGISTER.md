# BoponX evidence register and scientific boundary
**Reviewed:** 26 September 2026

BoponX separates near-real-time Earth observation, regional environmental context, historical/reanalysis context, farmer-entered observations, and reviewed local agronomic rules. A value from one class must never be silently promoted into another.

## GPM IMERG Early / NASA GIBS
Purpose in the current web app:
- dated recent-rainfall map layer over the selected farmer area
- establishes a direct NASA Earth-observation path in the interface

Official NASA material identifies IMERG V07B as the current algorithm and describes Early Run as the lowest-latency product. Documented minimum latency is about four hours; gridded resolution is 0.1 degree / roughly 10 km and 30-minute products are available.

BoponX wording is **near-real-time** or **latest available**, never “live forecast”.

Current implementation:
- NASA GIBS IMERG NRT map layer is wired into MapLibre
- the map date is displayed
- quantitative IMERG-derived farmer decisions are not enabled yet

Sources:
https://gpm.nasa.gov/data/directory
https://gpm.nasa.gov/data/imerg
https://worldview.earthdata.nasa.gov/

## SMAP SPL3SMP_E Version 6
Intended role: regional surface-soil-moisture context.

It is not soil pH, a nutrient test, or parcel-level laboratory chemistry.

Current NSIDC material describes SPL3SMP_E Version 6 as a daily 9 km EASE-Grid surface-soil-moisture product. Direct data access requires Earthdata Login.

NSIDC reports a geolocation issue affecting SMAP Standard/NRT products from 14 May through 28 July 2026. BoponX does not expose numeric SMAP values for affected dates until current status and QA handling are verified.

Source:
https://nsidc.org/data/spl3smp_e/versions/6

## NASA POWER selected-location context
The API can request daily T2M and PRECTOTCORR for the farmer-selected coordinates. The current endpoint asks for a recent 14-day window ending seven days before today to reduce failures from upstream latency.

The response records the exact request URL, reports valid-day coverage, suppresses a precipitation total when any requested day is missing, reports unavailable when a request fails, and never substitutes a fabricated number.

POWER values are gridded regional context and are not measurements taken in the farmer's field.

Source:
https://power.larc.nasa.gov/docs/services/api/temporal/daily/

## Pinned 2024 Rajshahi POWER snapshot
- Reference point: 24.37° N, 88.60° E
- Period: 2024-01-01 through 2024-12-31
- Variables: T2M, PRECTOTCORR
- Time convention: LST
- Returned source: MERRA-2 reanalysis
- Valid dates: 366/366
- Mean valid daily T2M: 25.71254098360656 °C
- Full-period precipitation: 1,863.19 mm
- Raw SHA-256: 512420f8cd947e21a84aa1e43292674be7e047fadfbcdd4ae4b3684647726495

A single historical year cannot establish a climate trend or predict a future planting season.

## Location context
The current resolver uses a Bangladesh bounding box plus regional evidence reference points for Dhaka, Mymensingh, Cumilla, Chattogram, Sylhet, Rangpur, Dinajpur, Bogura, Rajshahi, Jashore, Faridpur, Khulna, Barishal, and Rangamati. The nearest-reference calculation uses deterministic Haversine distance.

These points do not claim to be official administrative polygons or agro-ecological-zone boundaries. They are a regional evidence-routing layer.

## Bangladesh agricultural evidence
Current source index:
- BAMIS / Department of Agricultural Extension crop-weather calendar index: https://www.bamis.gov.bd/en/calendar
- BARC crop zoning: https://apps.barc.gov.bd/cropzoning/
- BRRI rice resources: https://brri.gov.bd/
- BARI/SRDI materials remain candidate evidence sources

No local crop calendar has yet been converted into a software recommendation rule in this redesign.

## Farmer-entered evidence
Current farmer questions focus on location, previous crop, rain-fed/irrigated/both/unknown, heavy-rain drainage behavior, whether a soil-test report exists, and farmer priority.

Numeric pH is optional and accepted only if the farmer explicitly indicates a soil-test report exists. Unknown answers remain unknown.

## 90-day plan semantics
The current plan is not a crop schedule:
1. **Know the field** — build the baseline.
2. **Watch the change** — compare NASA regional context with field observations.
3. **Decide the next move** — review evidence and prepare the next seasonal decision.

Crop-specific instructions remain blocked until source-reviewed local crop/soil/rotation rules exist.


## Regional BAMIS calendar index

The application now stores a small, reviewed index of **calendar presence**, not agronomic rules, for major crops and BAMIS regional hubs. The index is based on the official BAMIS crop-weather-calendar pages and is used only to decide which source links are relevant to the selected regional evidence hub.

Current indexed crops:
- Rice Aman
- Rice Aus
- Rice Boro
- Wheat
- Mustard
- Lentil
- Jute
- Maize (Kharif-1)
- Green Gram (Kharif-1)

A crop appearing in this index means only that BAMIS publishes a regional crop-weather calendar for that crop. It does **not** mean BoponX has concluded that the crop is suitable for the farmer's field.

Official source root:
https://www.bamis.gov.bd/en/calendar

## Place-name resolution

OpenStreetMap Nominatim is used only to help a farmer search a Bangladesh place name or label a selected coordinate. It is not a NASA source, soil source, or agronomic source. The agricultural evidence region is still resolved separately so a place label is never silently treated as an official agricultural boundary.

If Nominatim is unavailable, GPS/map-pin selection and the regional-evidence fallback still work.
