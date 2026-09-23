# BoponX implementation status — milestone 02

**Development date:** 23 September 2026. **Branch:** `feat/boponx-climate-ui-farm-intake`.

## Delivered in code

- NASA POWER daily acquisition script and validated on-disk snapshot format (milestone 01).
- FastAPI health, pilot locations, climate read, farm-input validation and crop-read endpoints.
- A deliberate `AGRONOMIC_RULES_NOT_APPROVED` response from comparison until sources are validated.
- Climate API rejects snapshots marked as synthetic or local/unverified.
- Mobile-first React + TypeScript interface with the pilot climate chart, coverage and evidence panel, honest unavailable state, and farm-input validation.
- Backend regression tests and frontend build checks in GitHub Actions.

## Not yet delivered / not yet validated

- Live NASA POWER data has **not** been acquired in the model's network-restricted development runtime. Run the documented command and inspect provider response before calling the demo data-ready.
- Crop catalog, soil profiles, rotation rules, three-season comparison engine and reviewed agronomic outputs.
- Direct satellite precipitation (IMERG), soil moisture (SMAP), full bilingual support, installable PWA, public hosted app.
- End-to-end demo, video and October submission.

## Acceptance for next milestone

An internet-connected developer validates one original NASA response, including units,
dates, geographic footprint, QA/fill conventions and nonzero data coverage. Tulip and
Iftekhar approve a small, locally relevant crop and soil evidence register. Only then
may a limited rotation engine produce user-visible comparisons.
