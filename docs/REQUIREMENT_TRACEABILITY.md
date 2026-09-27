# Latest product requirements → repository traceability
**Reviewed:** 26 September 2026

| Requirement | Current state | Notes |
| --- | --- | --- |
| Completely new UI/UX | Implemented | Active frontend was replaced with a new cinematic evidence-led journey |
| Do not look like old AI-generated dashboard | Implemented structurally | Old card/hero components are no longer in frontend tree; manual visual QA still required |
| Real website imagery | Implemented | Real NASA/USGS Landsat Baniachong image + live GIBS imagery |
| Heavy 3D/motion from opening to ending | Implemented with performance guardrail | Three.js Earth/satellite scene, map tilt, scroll reveals, 3D field/grid/evidence animation, animated closing; reduced-motion supported |
| No visible v0.x/V1 labels | Implemented | Search confirms old release strings are absent |
| Use current location | Implemented | auto-use when browser permission is already granted; otherwise explicit permission button |
| Search specific locations | Implemented | Bangladesh village/upazila/district/place search |
| Choose location on map | Implemented | MapLibre click-to-pin |
| More than one city | Implemented | free place search + multiple evidence hubs |
| Show only data relevant to selected area | Implemented structurally | selected coordinates drive context, POWER requests and local calendar evidence |
| NASA true-color map | Implemented | GIBS true-color toggle |
| NASA near-real-time rainfall | Implemented as dated GIBS/IMERG layer | V07B near-real-time semantics, not forecast |
| Recent 2026 climate context | Implemented through selected-location NASA services | POWER recent context; GIBS/IMERG current layer |
| Historical context | Implemented | POWER 2001–2020 selected-month climatology |
| Regional surface soil moisture | Source integrated / numeric decision use gated | SMAP SPL3SMP_E V6 with 2026 QA advisory |
| Farmer should not need scientific soil knowledge | Implemented | observable questions, unknown option, conditional pH only with report |
| 3 months must not repeat | Implemented | distinct phases + disjoint task sets + priority-sensitive Month 2 |
| Local soil information | Partial | farmer soil-test pathway + BARC/SRDI direction; no parcel soil chemistry database |
| Crop characteristics | Partial | BAMIS regional crop-calendar sources indexed; requirement profiles still under review |
| Farmer priorities affect output | Implemented for 90-day plan | water/soil/stability changes monitoring task |
| Three-season rotation strategies | Scientifically gated | target UI/pipeline shown, endpoint still fail-closed until agronomic rule packs are reviewed |
| Recommend exact crops now | Not enabled | would exceed current evidence; project shows evidence pipeline instead of inventing prescription |

## Why not every NASA dataset

The project uses the NASA products that have direct decision relevance for the challenge:
- GPM IMERG
- SMAP
- NASA POWER
- GIBS

Adding unrelated NASA datasets would increase complexity without improving the farmer decision.


## 27 September screenshot driven fixes

| Reported issue | Fix |
| --- | --- |
| Bangla only interface | Active interface is now English only |
| Text too large and badly fitted | Hero scale, width and spacing were reduced and rebalanced |
| Map becomes blank | OpenStreetMap is now the independent base layer and NASA overlays are added after map load |
| Page becomes blank after scrolling | Reveal content is visible by default and no longer depends on observer timing |
| Farmer options are low opacity and blocked | Questions are always interactive; only final plan generation requires a selected field |
| Location choice does not update area workflow | GPS, place search and map pin all set the same selected coordinate state |
| Front image feels too dark | NASA Landsat image treatment is brighter and a second real NASA crop image is used in the story section |
