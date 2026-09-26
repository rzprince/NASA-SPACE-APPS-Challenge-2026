# BoponX requirement traceability
**Reviewed:** 26 September 2026

This file maps the latest product instructions to the actual repository state. It exists to prevent the team from saying a feature is complete when it is only planned.

| Requirement | Repository status | Evidence / boundary |
| --- | --- | --- |
| New professional location-first UI/UX | Implemented in active React UI | Human-designed field/evidence visual system; manual Samsung/desktop visual QA still required |
| No visible release/version labels | Implemented | No farmer-facing v0.x/V1 branding |
| Farmer can use current location | Implemented | Browser geolocation after explicit tap; exact coordinates are not persisted by default |
| Farmer can search a more specific place | Implemented | Bangladesh place search through OpenStreetMap Nominatim, with map-pin fallback |
| Farmer can choose directly on a map | Implemented | MapLibre + OpenStreetMap basemap |
| NASA map/evidence layer | Implemented | NASA GIBS IMERG NRT rainfall layer |
| Show only location-relevant information | Implemented structurally | Selected point controls context, recent POWER query, baseline, regional evidence hub and BAMIS calendar links |
| More than one city/region | Implemented | Place search is not limited to one city; agricultural evidence is routed to multiple BAMIS-style regional hubs |
| Use 2026 NASA observations | Partly implemented | 2026 IMERG NRT imagery and selected-location NASA services are used; SMAP numeric adapter remains pending |
| Near-real-time rainfall | Implemented as map evidence | GPM IMERG Early / NRT layer; never called a forecast |
| Regional surface soil moisture | Source integrated, numeric adapter pending | SMAP SPL3SMP_E V6; never used as pH; 2026 geolocation advisory is shown |
| Recent climate context | Implemented | NASA POWER recent selected-point query |
| Historical context, not only recent data | Implemented | NASA POWER 2001–2020 selected-month climatology plus existing pinned 2024 Rajshahi snapshot |
| Ask only simple farmer-known questions | Implemented | Previous crop, water source, waterlogging observation, soil-test availability, farmer priority |
| Do not require soil pH | Implemented | pH appears only if a soil-test report exists; backend enforces this |
| Different Month 1/2/3 plan | Implemented | Three deterministic phases with disjoint task sets and priority-sensitive Month 2 |
| Local crop evidence | Partly implemented | BAMIS calendar-presence index is location-specific; calendar contents are not yet encoded as rules |
| Local soil information | Not complete | Soil-test path + BARC/SRDI evidence direction exist; no authoritative parcel soil database is yet integrated |
| Crop characteristics | Not complete | Official calendar sources are indexed; crop requirement profiles still need agronomic review |
| Farmer priorities affect the result | Implemented for 90-day routine | Water/soil/stability priority changes monitoring tasks; future rotation ordering still waits on rule packs |
| Compare three-season rotation strategies | Not complete by design | Endpoint fails closed until source-reviewed crop requirements, soil constraints and sequence rules exist |
| Recommend crops to farmers | Not yet enabled | BoponX must not invent a recommendation from weather alone |
| Real-time crop recommendation | Not scientifically supported | Near-real-time Earth observations can update context, but agronomic recommendations still require reviewed local rules |
| Nationwide decision coverage | Not claimed | Environmental context can cover Bangladesh; agronomic support is separately gated by evidence |

## What “NASA datasets 2026” means in this project

BoponX does **not** attempt to use every NASA dataset published in 2026. That would add noise rather than decision value.

The current challenge-relevant NASA stack is:
- GPM IMERG Early / GIBS for recent precipitation evidence
- SMAP SPL3SMP_E for regional surface-soil-moisture context once the authenticated adapter and QA path are complete
- NASA POWER for recent/historical climate context and climatology

Every NASA source has a distinct role and an explicit “what it cannot tell us” boundary.

## Final scientific gap before the core challenge engine is real

The remaining core work is to turn reviewed Bangladesh evidence into deterministic crop/soil/rotation rule packs. Only after that gate should BoponX show 2–3 real three-season rotation alternatives and explain why each passed or failed.
