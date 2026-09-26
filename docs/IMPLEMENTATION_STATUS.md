# BoponX implementation status
**Reviewed:** 26 September 2026 · **Owner:** Team EARTH.exe

## Working in the current redesign branch
- Location-first farmer flow with browser geolocation, Bangladesh place search (village/upazila/district/place), regional evidence-hub fallback, and map-pin selection.
- MapLibre interface with an OpenStreetMap basemap and a dated NASA GIBS IMERG near-real-time rainfall overlay.
- Location-context API separating environmental availability, local evidence availability, and crop-rotation support.
- Regional reference coverage for Dhaka, Mymensingh, Cumilla, Chattogram, Sylhet, Rangpur, Dinajpur, Bogura, Rajshahi, Jashore, Faridpur, Khulna, Barishal, and Rangamati. These are reference hubs, not administrative-boundary polygons.
- Selected-location recent NASA POWER point context plus a 2001–2020 planning-month climatology baseline, with explicit failure states and no fabricated fallback numbers.
- Existing integrity-gated 2024 Rajshahi NASA POWER/MERRA-2 historical pipeline retained.
- Official BAMIS crop-weather-calendar presence is indexed by regional evidence hub and shown as source evidence, not as suitability or recommendation.
- Farmer intake rewritten around observable facts. Soil pH is conditional on an existing soil-test report and is rejected otherwise.
- Bangla-first interface with English toggle, large controls, unknown/not-sure options, mobile layouts, reduced-motion support, and print styling.
- Stage-aware 90-day plan with distinct Month 1, Month 2, and Month 3 objectives.
- Printable bilingual field brief with area, farmer context, recent environmental context when available, evidence links, and the rotation-evidence gate.
- Deterministic backend tests for location resolution, pH gating, stage-aware planning, and POWER completeness behavior.

## Deliberately not represented as complete
- Nationwide agronomic decision coverage.
- A reviewed crop catalog or crop-specific three-season rotation engine.
- Planting/transplanting dates.
- Soil pH inferred from Earth observations.
- SMAP numeric integration into a farmer decision.
- IMERG values as a computed decision input; the current IMERG integration is a dated map/evidence layer.
- Yield, soil-health, water-saving, fertilizer, pesticide, or profit predictions.
- Weather forecasts.
- Field-level measurements from regional NASA products.
- NASA endorsement.

## Scientific next gates
1. Verify and implement the IMERG data adapter needed for quantitative selected-location precipitation evidence, retaining timestamps/quality/provenance.
2. Implement SMAP SPL3SMP_E retrieval only after Earthdata authentication, QA handling, and the 2026 geolocation advisory are explicitly handled.
3. Build a Bangladesh agricultural source register with reuse terms for BAMIS/BARC/BRRI/BARI/SRDI materials.
4. Translate only approved, geographically appropriate crop calendars/requirements/sequence constraints into deterministic rule packs.
5. Add at least two evidence-backed three-season rotation alternatives in a supported region, with uncertainty and trade-offs visible.
6. Add multi-year historical baselines appropriate to the final challenge statement instead of treating one historical year as climate change evidence.

## Human QA still required
Automated CI can verify tests and builds, but it does not verify visual quality. Before presenting the redesign:
- inspect the location map and NASA layer on desktop
- test browser GPS permission granted/denied
- test multiple Bangladesh locations
- verify the map pin and regional context change together
- test Samsung-size mobile layout
- verify Bangla readability
- verify reduced-motion mode
- print/save the report on desktop and Android
- confirm no crop recommendation is exposed accidentally
- confirm IMERG/GIBS tile attribution and map date are visible
- rehearse offline/degraded behavior
