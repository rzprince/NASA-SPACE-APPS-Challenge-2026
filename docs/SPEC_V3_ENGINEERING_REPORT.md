# BoponX — Final Spec V3.1 Scientific Validation & NASA Data Reliability Engineering Report

**Project:** BoponX (Team EARTH.exe — NASA Space Apps Challenge 2026)  
**Release:** Final Spec V3.1 (`boponx.rotation_science.v3.1` / `boponx.onset_results.v2`)  
**Report Date:** 2026-11-06  

## Deliverable A: Complete List of Modified & Created Files (Spec V3 & V3.1)

| File Path | Action | Problem Addressed | Implemented Solution & Technical Approach | Validation Method |
| :--- | :--- | :--- | :--- | :--- |
| `backend/app/services/imerg_check.py` | Modified (V3 & V3.1) | V3: Basic list comparison stub. V3.1: `convert_half_hourly_rates_to_daily_mm()` scaled 44 valid intervals across 48 slots (`24.0 / len(valid)`), silently imputing missing rainfall intervals with the observed mean rate. | Added `aggregate_half_hourly_imerg_to_daily()` and updated `convert_half_hourly_rates_to_daily_mm()`. Removed all scaling/imputation (`imputation_applied: False`). `observed_accumulation_mm = sum(r * 0.5 for r in valid)` is computed transparently; `daily_total_mm` is returned **only** when `48/48` intervals are valid (`coverage_status == "complete"`). Incomplete days are classified as `partial_incomplete` (`44/48–47/48`), `insufficient_coverage` (`1/48–43/48`), or `missing` (`0/48`) with `missing_intervals` and `coverage_pct`. | Verified against manually calculated fixtures in `test_imerg_half_hourly_48_of_48_complete_coverage`, `test_imerg_half_hourly_44_of_48_partial_incomplete_never_imputes`, `test_imerg_half_hourly_43_of_48_insufficient_coverage_never_imputes`, and `test_imerg_half_hourly_0_of_48_completely_missing`. |
| `backend/app/compute/rotation_science.py` | Created & Upgraded (V3.1) | V3: When `soil_test != "yes"`, `local_suitability` was assigned a synthetic numeric score (`68.0 - warnings * 8.0`) and blended into `weighted_composite_score_0_100`. | Strictly separated four orthogonal dimensions: (1) `scientific_performance` (biophysical score over known/calculated criteria only), (2) `evidence_completeness` (`completeness_pct`, `known_dimensions`, `unknown_dimensions`), (3) `local_suitability` (`score_0_100 = None` / `"UNKNOWN"` whenever `soil_test != "yes"`), and (4) `critical_constraints` (`critical_constraint_violated`, `constraint_flags`). Missing measurements never improve a strategy's score or ranking. | Verified in `test_rotation_scoring_separates_performance_completeness_suitability_and_constraints` and `test_e2e_coastal_bangladesh_farmer_scenario_patuakhali`. |
| `backend/app/services/power_history.py` | Modified | Lacked explicit meteorological range/continuity validation statuses (`complete`, `partial`, `unavailable`, `failed_validation`), HTTP 429/5xx backoff retries, and full 40-cell inventory across all 64 districts. | Added `validate_snapshot_record()` enforcing geographic bounds, ISO date continuity, parameter completeness (`PRECTOTCORR`, `T2M_MAX`, `T2M_MIN`), physical range checks (`0–1500 mm/day`, `-40–60 °C`, `T2M_MAX >= T2M_MIN`), and coverage thresholds (`>=95%` complete, `50–95%` partial). Added retry/backoff in `fetch_live()` and `all_bangladesh_grid_cells()` (40 unique cells). | Verified via `test_power_history.py` and `test_snapshot_validation_distinguishes_complete_partial_and_failed`. |
| `scripts/build_onset_results.py` & `scripts/build_snapshot.py` | Modified (V3 & V3.1) | Previously lacked a 40-cell inventory and 4-tier district coverage classification, and `build_onset_results.py` attempted live network calls per district when snapshots were absent. | Upgraded to schema `boponx.onset_results.v2` reading committed snapshots directly from disk, exporting the 40-cell native `0.5° × 0.625°` [NASA POWER Daily API](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) inventory, and classifying all 64 districts into `verified_complete`, `partial_evidence`, `insufficient_spatial_coverage`, or `unavailable`. Added `--timeout` to `build_snapshot.py`. | Executed `python3 -m scripts.build_onset_results` and verified via `test_all_64_districts_have_explicit_coverage_classification_across_40_cells`. |
| `backend/app/compute/soil_evidence.py` | Created | District profiles contained narrative soil summaries without structured soil property records, survey years, units, or formal evidence classifications. | Built a structured soil evidence model integrating published Agro-Ecological Zone (AEZ) ranges from [SRDI](https://srdi.gov.bd/), [BARC Fertilizer Recommendation Guide (FRG-2024)](https://apps.barc.gov.bd/fertilizer_recommendation/FRG%20English%2030.10.2024.pdf), [BARC Crop Zoning](https://apps.barc.gov.bd/cropzoning/), [BARI](https://bari.gov.bd/), and [BRRI](https://brri.gov.bd/) with 5 strict classifications (`VERIFIED`, `REFERENCE`, `ESTIMATED`, `FARMER_REPORTED`, `UNKNOWN`) and `evaluate_crop_soil_suitability()`. | Verified via `test_soil_evidence_classifications_and_false_precision_guard` and `test_soil_suitability_flags_waterlogging_and_farmer_ph`. |
| `backend/app/services/provenance.py` | Created | Freshness metadata was scattered across endpoints without product-specific latency rules. | Created centralized provenance registry (`build_centralized_provenance_registry()`) and product-specific freshness classifiers (`Fresh`, `Recently updated`, `Delayed`, `Cached`, `Partial`, `Unavailable`, `Validation failed`) across [NASA POWER Daily](https://power.larc.nasa.gov/docs/services/api/temporal/daily/), [NASA POWER Climatology](https://power.larc.nasa.gov/docs/services/api/temporal/climatology/), [NASA EONET v3](https://eonet.gsfc.nasa.gov/docs/v3), [NASA GIBS](https://worldview.earthdata.nasa.gov/), and [GPM IMERG](https://gpm.nasa.gov/data/imerg). | Verified via `test_freshness_classifications_use_product_specific_latency`. |
| `backend/app/compute/agro.py` & `onset_stats.py` | Modified | Discrete boundary ties at `01 May` (`DOY 121`) could round `-0.5` to `0` under Python banker's rounding while `p < 0.05`, producing `"0 days later"`, and `mann_kendall()` omitted `significant_at_0_05`. | Replaced banker's rounding with half-away-from-zero rounding, fell back to rounded mean difference when boundary ties collapse Hodges-Lehmann median to `0`, prevented `shift_days == 0` from being marked `significant = True`, and added `significant_at_0_05` to `mann_kendall()`. | Verified across all shifts and crops in `test_agro_advisory.py`, `test_onset_stats.py`, and `test_statistical_edge_cases_constant_series_and_ties`. |
| `backend/app/compute/context.py`, `plan.py` & `main.py` | Modified | Context and plan responses did not expose the soil evidence model, centralized provenance registry, 8-criterion rotation evaluation, or dedicated validation endpoints. | Integrated `soil_evidence`, `nasa_provenance`, `scientific_evaluation`, and `intended_crop_suitability` into `/api/v1/context` and `/api/v1/plans/preview`, and added `/api/v1/validation/imerg`, `/api/v1/soil/evidence`, and `/api/v1/provenance`. | Verified via `test_api.py`, `test_spec_v2_upgrades.py`, and `test_spec_v3_scientific_validation.py`. |
| `frontend/src/api.ts` & `frontend/src/App.tsx` | Modified (V3 & V3.1) | Defaulted `intendedCrop` to `mustard`, lacked a Stage 02 district switcher, and did not display soil evidence classifications, evidence completeness %, or `UNKNOWN (No Lab Test)` for unmeasured local soil gates. | Defaulted `intendedCrop` to `rice` (Aman Rice), updated `.onset-shift-badge`, added a 64-district switcher on Stage 02, and displayed `Scientific Performance`, `Evidence Completeness %`, `Local Soil Gate: UNKNOWN (No Lab Test)`, and SRDI/BARC soil evidence classifications. | Verified TypeScript/JSX structural integrity and API contract alignment. |
| `README.md`, `docs/LIMITATIONS.md`, `docs/IMPLEMENTATION_STATUS.md`, `docs/VALIDATION.md`, `scripts/run.ps1`, `data/processed/onset_results.json` | Modified (V3.1) | Contained legacy references to `29` grid cells and outdated review dates (`28 September 2026`). | Standardized all spatial grid documentation to **40 unique `0.5° × 0.625°` NASA POWER grid cells** covering all 64 Bangladesh districts and updated review dates to `6 November 2026`. | Verified via `grep` audit and `test_all_64_districts_have_explicit_coverage_classification_across_40_cells`. |

## Deliverable B: Historical NASA POWER Data Acquisition & IMERG Report

### 1. Execution of `scripts.build_snapshot` & `scripts.build_onset_results`
- **Commands Executed:**
  ```bash
  python3 -m scripts.build_snapshot --districts rajshahi --retries 1 --pause 0.1 --timeout 2.0
  python3 -m scripts.build_onset_results
  ```
- **Exact Execution Result in This Build Container:**
  - `scripts.build_snapshot` failed with:
    `[1/1] 24.25_88.4375: failed: URLError: <urlopen error [Errno -3] Temporary failure in name resolution>`
  - **Root Cause:** Outbound internet access and DNS resolution are disabled inside this isolated sandbox container (`<sandbox_internet_access>`).
  - **Resulting `data/processed/onset_results.json` State:**
    - `status`: `"snapshots_not_built"`
    - `cells_total`: `40` (`complete_cells: 0`, `partial_cells: 0`, `unavailable_cells: 40`)
    - `districts_total`: `64` (`verified_complete: 0`, `partial_evidence: 0`, `insufficient_spatial_coverage: 0`, `unavailable: 64`)
    - Zero fabricated or fixture-substituted historical files were written to `data/processed/power_history/`.
- **Reproducible Workflow on Any Internet-Connected Machine:**
  ```powershell
  Remove-Item Env:OFFLINE -ErrorAction SilentlyContinue
  .\.venv\Scripts\python.exe -m scripts.build_snapshot
  .\.venv\Scripts\python.exe -m scripts.build_onset_results
  ```
  Each of the **40 unique `0.5° × 0.625°` [NASA POWER Daily](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) cells** is fetched from `https://power.larc.nasa.gov/api/temporal/daily/point` (`2001-01-01` to `today - 7 days`), validated via `validate_snapshot_record()`, stored in `data/processed/power_history/<cell_id>.json` with its SHA-256 digest in `index.json`, and `onset_results.json` is automatically updated.

### 2. IMERG Half-Hourly Missing-Data Correction (Spec V3.1 Fix 1)
In `backend/app/services/imerg_check.py`, `aggregate_half_hourly_imerg_to_daily()` and `convert_half_hourly_rates_to_daily_mm()` were corrected so missing 30-minute intervals are **never** silently imputed with the mean rainfall rate of observed intervals:

| Test Case | Valid / Expected Intervals | Input Rate (`mm/hr`) | `observed_accumulation_mm` (`sum(r * 0.5)`) | `daily_total_mm` (Full-Day Total) | `coverage_pct` | `coverage_status` | `imputation_applied` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Full Day (`48/48`)** | `48 / 48` (`0` missing) | `2.0` | `48.0 mm` | `48.0 mm` | `100.0%` | `complete` | `False` |
| **Partial Day (`44/48`)** | `44 / 48` (`4` missing) | `2.0` | `44.0 mm` *(never scaled to 48.0)* | `None` *(withheld)* | `91.67%` | `partial_incomplete` | `False` |
| **Insufficient (`43/48`)** | `43 / 48` (`5` missing) | `2.0` | `43.0 mm` | `None` *(withheld)* | `89.58%` | `insufficient_coverage` | `False` |
| **Missing (`0/48`)** | `0 / 48` (`48` missing) | `None` | `None` | `None` *(withheld)* | `0.0%` | `missing` | `False` |

## Deliverable C: Soil Evidence Report

- **Integrated Sources:** [SRDI](https://srdi.gov.bd/) (*Saline Soils of Bangladesh 2010/2022* & *Thana Nirdeshika*), [BARC Fertilizer Recommendation Guide (FRG-2024)](https://apps.barc.gov.bd/fertilizer_recommendation/FRG%20English%2030.10.2024.pdf), [BARC Crop Zoning](https://apps.barc.gov.bd/cropzoning/), [BARI](https://bari.gov.bd/), and [BRRI](https://brri.gov.bd/).
- **Evidence Classifications:** Every soil property record (`soil_ph`, `organic_matter_pct`, `salinity_ec_ds_m`, `soil_texture_and_classification`, `drainage_class`, `parcel_npk_nutrients`) carries an explicit `evidence_classification` in `{"VERIFIED", "REFERENCE", "ESTIMATED", "FARMER_REPORTED", "UNKNOWN"}`. Regional AEZ values are classified as `REFERENCE`, farmer-entered lab pH (`soil_test == "yes"`) as `FARMER_REPORTED`, and unmeasured parcel NPK/ECe as `UNKNOWN`.

## Deliverable D: Rotation Scoring Uncertainty & Methodology Report (Spec V3.1 Fix 3)

In `backend/app/compute/rotation_science.py`, every strategy evaluation (`scientific_evaluation`) strictly separates four orthogonal blocks:
1. **`scientific_performance`**: Biophysical performance score (`score_0_100`) computed **only** over evaluated biophysical criteria (`water_demand`, `nitrogen_contribution`, `soil_coverage`, `pest_break_potential`, `climate_resilience`, `planting_window_compatibility`, `farmer_priority_compatibility`), normalized by `known_criteria_weight_sum` (`0.90` when `soil_test != "yes"`, `1.00` when `soil_test == "yes"`).
2. **`evidence_completeness`**: Tracks 8 explicit evidence dimensions (`regional_bamis_crop_calendar`, `srdi_barc_aez_soil_reference`, `nasa_power_recent_or_seasonal_water_balance`, `nasa_power_historical_onset_series`, `field_water_source_specified`, `field_post_rain_drainage_specified`, `parcel_laboratory_soil_ph_verified`, `parcel_laboratory_npk_and_salinity_ec_verified`), reporting `completeness_pct`, `known_dimensions`, and `unknown_dimensions`.
3. **`local_suitability_summary` & `criteria.local_suitability`**: When `soil_test != "yes"`, `local_suitability.score_0_100` is **`None` (`"UNKNOWN"`)** and `status` is `"UNVERIFIED_MISSING_SOIL_TEST"`—never a synthetic average score like `50.0` or `68.0`.
4. **`critical_constraints`**: Non-overridable constraint flags (`critical_constraint_violated`, `constraint_flags`) for waterlogging (`water_after_heavy_rain == "stays"` on pulses/mustard), dry-season irrigation incompatibility (`water_source == "rainfed"` on Boro rice), or out-of-range soil pH.

## Deliverable E: Final Test & Verification Report

### 1. Backend & Statistical Test Suite (`PYTHONPATH=/tmp/pyshim:. OFFLINE=1 python3 -m pytest -q backend/tests`)
- **Total Tests Executed:** `114`
- **Passed:** `114`
- **Failed:** `0`
- **Skipped:** `0`
- **Blocked:** `0`

| Test Suite | Passed | Key Verifications |
| :--- | :--- | :--- |
| `test_spec_v3_scientific_validation.py` | **14 / 14** | Snapshot validation (`complete`, `partial`, `failed_validation`, `unavailable`), `-999 -> None` non-zeroing, 40-cell / 64-district coverage, IMERG `48/48`, `44/48`, `43/48`, `0/48` non-imputing aggregation, RMSE/Pearson `r`, SRDI/BARC soil classifications, freshness rules, statistical tie/constant edge cases, rotation uncertainty separation (`local_suitability.score_0_100 is None` when `soil_test != "yes"`), and Coastal Bangladesh (`Patuakhali`) E2E farmer scenario. |
| `test_no_fabrication_guard.py`, `test_power_history.py`, `test_onset_stats.py`, `test_agro_advisory.py`, `test_spec_v2_upgrades.py`, and 12 core API/compute suites | **100 / 100** | Zero synthetic generators, `scipy.stats` agreement for Mann-Whitney $U$ and Mann-Kendall $\tau$, `422 SOIL_TEST_REQUIRED`, `409 AGRONOMIC_RULES_NOT_APPROVED`, and Rajshahi pilot SHA-256 integrity. |

### 2. Frontend TypeScript & Production Build Report
- **Source Structural & Security Verification:** `frontend/src/App.tsx` (2,226 lines), `frontend/src/api.ts` (858 lines), `frontend/src/DecisionReport.tsx` (396 lines), and `frontend/src/LocationMap.tsx` (668 lines) passed syntax and zero-secret scanning (`PASS`).
- **Vite Production Bundle (`npm run build`):** `BLOCKED` inside this sandbox VM because the Node.js / `npm` binary and `node_modules` are not pre-installed in the Python container (`which npm node` returns empty, and outbound package installation is disabled). On your local machine where `node_modules` is installed, run `cd frontend && npm run build` (or `.\scripts\run.ps1 test`) to compile `frontend/dist`.

## Deliverable F: Final Readiness & Outstanding Limitations

| Capability | Status | Notes & Outstanding Limitations |
| :--- | :--- | :--- |
| **1. IMERG Half-Hourly Missing-Data Handling** | **PASS** | Zero silent scaling/imputation; `48/48`, `44/48`, `43/48`, and `0/48` verified against manual fixtures (`114/114` backend tests pass). |
| **2. Rotation Scoring Uncertainty Separation** | **PASS** | `scientific_performance`, `evidence_completeness`, `local_suitability` (`None` when unmeasured), and `critical_constraints` are strictly separated. |
| **3. 40-Cell Spatial Inventory & Documentation Consistency** | **PASS** | All references across `README.md`, `docs/*.md`, `scripts/*`, `power_history.py`, and `onset_results.json` consistently report **40 unique `0.5° × 0.625°` NASA POWER grid cells** across 64 districts. |
| **4. Pre-Built 40-Cell Historical Snapshots on Disk** | **BLOCKED (Sandbox Network)** | Blocked in this build container by disabled outbound DNS/HTTPS (`URLError: [Errno -3] Temporary failure in name resolution`). Run `.\.venv\Scripts\python.exe -m scripts.build_snapshot` on your internet-connected machine to populate all 40 cell snapshots. |
| **5. Live GES DISC Numerical IMERG Queries** | **PARTIAL (Token Gated)** | Code and tests are complete; live GES DISC OPeNDAP queries require setting `NASA_EARTHDATA_TOKEN` in the environment (otherwise cleanly reports `skipped_no_token` while keeping GIBS visual tiles active). |
| **6. Frontend Production Build (`npm run build`)** | **BLOCKED (Sandbox Binary)** | Blocked in this container because `node`/`npm` is not installed in the sandbox image; verified via static TypeScript structure checks and ready to build on your local machine via `cd frontend && npm run build`. |
