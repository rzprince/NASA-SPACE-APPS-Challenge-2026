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
