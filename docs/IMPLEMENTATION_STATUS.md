# Milestone 01 — repository and NASA POWER data foundation

**Started:** 23 September 2026. **Owner:** Team EARTH.exe / BoponX.

## Done in code

- Initial monorepo, documented backend setup and safe Git ignores.
- NASA POWER acquisition command with explicit request parameters, caching, raw checksum and validation.
- Deterministic historical summary with coverage and missing-data behavior.
- FastAPI health, pilot locations, and climate-read endpoints; no fabricated fallback data.
- Synthetic offline tests and automated backend CI.

## Pending before October prescreening

1. Run POWER acquisition from an internet-connected developer machine; inspect raw metadata and unit compatibility.
2. Approve exact pilot coordinates and the source-reviewed initial crop set.
3. Implement crop and soil inputs, rotation engine and documented comparison criteria.
4. Build React mobile-first screens and connect API endpoints.
5. Validate an end-to-end demonstration; record the 240-second prescreening video; test submission links.

**No React application, crop advice, direct GPM/SMAP integration, or public deployed demo is claimed in this milestone.**
