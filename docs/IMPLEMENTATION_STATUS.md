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

- A **real NASA POWER 2024 snapshot** was acquired and verified in [GitHub Actions run 35860018103](https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026/actions/runs/35860018103) with complete 366-day T2M/PRECTOTCORR coverage and a matching raw SHA-256. The raw and processed data are distributed as a time-limited workflow artifact, not committed to Git; installation and app-level demo verification remain pending.
- Crop catalog, soil profiles, rotation rules, three-season comparison engine and reviewed agronomic outputs.
- Direct satellite precipitation (IMERG), soil moisture (SMAP), full bilingual support, installable PWA, public hosted app.
- End-to-end demo, video and October submission.

## Acceptance for next milestone

Inspect the verified NASA artifact's source metadata and geographic/time conventions,
extract it into a reproducible local demo, and confirm the frontend renders its evidence.
Tulip and Iftekhar must approve a small, locally relevant crop/soil evidence register;
only then may a limited rotation engine produce user-visible comparisons. A separate
direct-Earth-observation product remains required for the expanded release.
