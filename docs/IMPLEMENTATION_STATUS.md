# BoponX implementation status
**Reviewed:** 26 September 2026 · **Owner:** Team EARTH.exe

## Active product

The active React experience is now the cinematic location-first rebuild. The old Rajshahi-only visual shell is no longer part of the frontend tree.

### Implemented
- real NASA Landsat Bangladesh imagery in the opening and evidence story
- WebGL/Three.js animated Earth / satellite scene
- motion-led opening, map transitions, signal cards, scrolling reveals, 3D field/evidence visuals and animated closing section
- prefers-reduced-motion fallback
- browser geolocation with automatic use when permission was already granted
- explicit geolocation button when permission still needs user action
- Bangladesh place search (village/upazila/district/place)
- regional evidence-hub fallback
- map-pin field selection
- MapLibre map
- NASA GIBS true-color imagery toggle
- NASA GIBS / GPM IMERG recent-rainfall layer toggle
- selected-location NASA POWER recent context
- selected-month 2001–2020 NASA POWER climatology
- separate SMAP evidence/QA card with the 2026 geolocation advisory
- location-specific BAMIS crop-calendar evidence
- farmer questions based on observable/known information
- optional pH only after a soil-test report is declared
- three different 90-day phases with priority-sensitive tasks
- printable bilingual field brief
- rotation explorer target architecture shown without fabricated crop recommendations

### Deliberately gated
- quantitative SMAP values inside farmer decisions
- quantitative IMERG precipitation calculations inside the decision engine
- authoritative parcel soil chemistry
- nationwide reviewed crop-rule coverage
- crop-specific planting/transplanting dates
- fertilizer/pesticide prescriptions
- crop yield/water-saving/soil-health outcome claims
- actual 2–3 three-season rotation alternatives

The rotation endpoint continues to fail closed until reviewed Bangladesh crop requirements, soil constraints and sequence rules are implemented.

## Validation status

Automated CI covers:
- backend test suite
- frontend TypeScript typecheck
- Vite production build

Manual QA remains necessary for:
- actual map tile/GIBS rendering
- NASA POWER network availability
- geolocation permission allowed/denied
- place search
- desktop visual quality
- Samsung/Android visual quality
- Bangla typography
- reduced-motion mode
- Print / Save PDF
- poor-network / external-source failure states
