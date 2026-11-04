# Latest product requirements and repository traceability

**Reviewed:** 27 September 2026

| Requirement | Current state | Notes |
| --- | --- | --- |
| Cinematic professional UI | Implemented | Real NASA imagery, Three.js scenes, responsive motion and evidence led layout |
| English only farmer interface | Implemented | Language switcher removed |
| Better text fit | Implemented | Hero size and spacing rebalanced |
| Real location | Implemented | Browser location access with permission |
| Place search | Implemented | Bangladesh place search through backend geocoding |
| Choose field on map | Implemented | MapLibre point selection |
| More than one city | Implemented | Free place search plus regional evidence hubs |
| Data filtered by selected place | Implemented | Coordinates drive context, POWER requests and regional calendar evidence |
| Map must not go blank | Hardened | Independent OSM base, guarded map animation, resize handling and visible fallback messages |
| App must not go blank after plan | Hardened | deterministic fast plan request, defensive report rendering and React error boundary |
| Farmer options need real icons | Implemented | custom SVG crop, water, drainage, soil and priority icons |
| Farmer should not need scientific soil knowledge | Implemented | simple observations, Not sure choices and conditional pH |
| Three months must be different | Implemented and tested | distinct phases and disjoint task sets |
| Farmer priority affects plan | Implemented and tested | Month 2 changes for water, soil or production stability |
| Recent NASA context | Implemented | selected location NASA POWER request |
| Historical climate reference | Implemented | selected month POWER 2001 to 2020 climatology |
| Near real time rainfall map | Implemented as optional visualization | dated GIBS IMERG layer |
| Regional soil moisture | Evidence source integrated | SMAP numeric decision use remains gated |
| Local crop evidence | Partial | BAMIS calendar sources indexed by regional hub |
| Local soil evidence | Partial | farmer soil test pathway and external source direction |
| Crop characteristics | Partial | calendar evidence indexed; complete crop requirement profiles still need review |
| Three season rotation strategies | Scientifically gated | target architecture shown; final alternatives remain locked |


## 28 September farmer advice and plan personalization

| Requirement | Current state | Notes |
| --- | --- | --- |
| Record crops grown previously | Implemented | Up to four crops can be selected in order, with the most recent selected first |
| Ask what the farmer wants to grow now | Implemented | One intended crop or Not decided can be selected |
| Advise whether the current decision is ready | Implemented with scientific boundary | Advice checks regional calendar evidence, water, drainage, soil test availability, recent climate context and crop history |
| Suggest a better next step | Implemented | The system can recommend verifying drainage, water access, soil evidence or regional calendar evidence before commitment |
| Suggest other crop possibilities | Implemented as unranked evidence options | Other regionally documented BAMIS crops can be shown for investigation, but are not called better until agronomic rules are reviewed |
| Make 90 day plan different by location | Implemented | Selected coordinates drive NASA POWER context and monthly climatology |
| Make each month different | Implemented and tested | Each month has a separate objective, task codes and monthly climate reference |
| Use weather context without pretending to forecast | Implemented | Recent NASA POWER is compared with historical monthly climatology; future months use climatology only |
| Improve tiny frontend text | Implemented | Farmer controls, evidence details, plan tasks and source text received a readability pass |


## 30 October 2026 — Official 28 October NASA Challenge Brief Traceability

**Reviewed:** 30 October 2026

| 28 Oct Challenge Brief Requirement | Current State | Implementation Evidence |
| --- | --- | --- |
| Combine NASA Earth observations with local agricultural information | Implemented & Tested | `backend/app/compute/context.py`, `backend/app/compute/bangladesh_districts.py`, `backend/app/compute/local_sources.py` |
| Explore patterns in temperature, rainfall, soil moisture, heat shift, and water balance | Implemented & Tested | `backend/app/services/power_live.py`, `backend/app/compute/plan.py`, `frontend/src/App.tsx` |
| Highlight bare-field periods & vulnerable seasons | Implemented & Tested | `bare_field_risk_en` / `bare_field_risk_bn` across all 64 districts + `bare-field-banner` in Rotation Lab |
| Compare at least 3 rotation strategies, including the existing rotation | Implemented & Tested | `POST /api/v1/rotations/explore` & `Rotation Lab` compare (A) Existing Baseline, (B) Soil-Health & Pulse/Oilseed Bridge, and (C) Climate-Adaptive & District Opportunity with *Why Suggested*, *Evidence*, *Benefits*, *Gaps*, and *Local Review Risks* |
| Clarify satellite vs. ground measurements & multi-resolution grid harmonization | Implemented & Tested | `MULTI_RESOLUTION_HARMONIZATION` in `context.py` + `Grid Harmonization` tab in `App.tsx` |
| Explain scientific terms (evapotranspiration, soil moisture anomalies, NDVI, heat/frost risk, water balance) | Implemented & Tested | `SCIENTIFIC_GLOSSARY` in `context.py` + `Scientific Terms` tab in `App.tsx` (English & Bangla) |
| Connect 64-district Bangladesh soil, analog, established crop & new opportunity dataset (`bpx.pdf`) | Implemented & Tested | `backend/app/compute/bangladesh_districts.py` + `/api/v1/bangladesh/districts` + `/api/v1/bangladesh/resolve` |
| WebGL fallback (`EarthCanvasFallback`), manual coordinate recovery, and bilingual (`EN / বাংলা`) support | Implemented & Tested | `frontend/src/LocationMap.tsx`, `frontend/src/App.tsx`, `frontend/src/DecisionReport.tsx` |
| Keep final prescriptive rotation ranking fail-closed until formal agronomic sign-off | Enforced & Tested | `POST /api/v1/rotations/compare` returns `HTTP 409 AGRONOMIC_RULES_NOT_APPROVED` |
