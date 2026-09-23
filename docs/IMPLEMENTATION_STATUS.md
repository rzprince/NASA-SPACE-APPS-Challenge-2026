# BoponX implementation status — October prescreening preview

**Last reviewed:** 23 September 2026 · **Owner:** Team EARTH.exe

## Implemented in the repository

- Python NASA POWER daily acquisition, schema/unit/missing-value checks and historical processing.
- Original 2024 Rajshahi-area response independently acquired in GitHub Actions:
  366/366 valid temperature and precipitation dates; SHA-256 recorded and source
  product identified as **MERRA-2 reanalysis**.
- Raw-vs-processed pinned snapshot verification script and synthetic tamper tests.
- FastAPI climate/health/location/farm-input endpoints and coverage-aware historical
  monthly aggregation (mean °C; total mm only with complete daily coverage).
- React + TypeScript interface with English/Bangla presentation, enhanced Bangla
  readability, original pointer-responsive CSS-3D environmental artwork and
  3D historical rainfall columns, accessible monthly picker/table, evidence drawer
  and responsive farm intake.
- Automated Python test and frontend build workflows. Crop-comparison API explicitly
  returns `AGRONOMIC_RULES_NOT_APPROVED`.

## Not completed or not represented as completed

- Local agronomic review of crop calendars, soil and sequence rules; no user-facing
  crop rotation outcomes, water-saving predictions, soil scores or yield claims.
- Validated direct satellite-observation product integrated into the decision engine
  (IMERG/SMAP remain candidates); POWER meteorology is MERRA-2 reanalysis.
- Public hosted app, separate mobile app, installed offline PWA, full language
  localization of every technical message, field usability study and final video.
- Submission itself; the team must upload/test the actual public video and links.

## Release checks still requiring a person

Confirm the user's existing extracted NASA ZIP in `data/raw` and
`data/processed`; run `python -m scripts.verify_pilot` before recording.
Test 360px Android layout, desktop layout, Bangla readability, month buttons,
evidence links, reduced-motion mode and offline local demo. Record the actual
240-second concept-focused video only after those checks pass.

See `docs/OCTOBER_1_PRESCREEN.md` and `docs/EVIDENCE_REGISTER.md`.

**Critical distinction:** This prescreening preview demonstrates a credible
data-to-user workflow and the architecture for rotation analysis. It is not yet
the completed Field Shift decision-support engine. Full challenge materials and
local submission details must be rechecked at their official release.
