# BoponX implementation status

**Reviewed:** 27 September 2026  
**Owner:** Team EARTH.exe

## Active demo candidate

The current frontend is the cinematic location aware rebuild. The latest stability pass addresses the blank screen reports seen after location selection and after generating the 90 day plan.

### Implemented

- English only farmer interface
- real NASA Landsat Bangladesh imagery
- Three.js animated Earth and satellite scene
- off screen 3D rendering pause for lower GPU load
- browser geolocation
- Bangladesh place search
- regional evidence hub fallback
- direct map point selection
- MapLibre map with OpenStreetMap as the independent base
- optional NASA GIBS true color imagery
- optional NASA GIBS IMERG rainfall layer
- selected location NASA POWER recent context
- selected month 2001 to 2020 NASA POWER climatology
- SMAP regional soil moisture evidence card with 2026 quality advisory
- location specific BAMIS crop calendar evidence
- professional SVG icons for farmer choices
- farmer questions based on observable information
- optional pH only after a soil test report is declared
- three different 90 day stages
- farmer priority changes Month 2 tasks
- defensive printable field brief
- React error recovery screen instead of a blank root
- deterministic plan generation without repeated NASA network calls
- backend tests for plan stage separation and priority sensitivity

### Deliberately gated

- quantitative SMAP values inside farmer decisions
- quantitative IMERG calculations inside the decision engine
- parcel soil chemistry
- nationwide reviewed crop rule coverage
- crop planting dates
- fertilizer and pesticide prescriptions
- yield gain claims
- water saving claims
- soil health scores
- final three season crop rotation alternatives

The rotation endpoint remains fail closed until reviewed Bangladesh crop requirements, soil constraints and sequence rules are implemented.

## Validation

Automated validation covers:

- backend tests
- three stage plan route behavior
- priority sensitive plan behavior
- frontend TypeScript check
- Vite production build

Manual validation is still required for:

- actual browser geolocation
- place search against the live geocoder
- live OpenStreetMap tiles
- NASA GIBS imagery
- NASA POWER network requests
- Samsung and desktop rendering
- Print or Save PDF
- reduced motion mode
- poor network behavior

The project should be described as a **demo candidate** until this manual acceptance pass succeeds on the machine that will be used for recording.
