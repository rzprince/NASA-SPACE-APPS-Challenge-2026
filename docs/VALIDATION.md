# Validation & Published Benchmarks

This document explains how BoponX's real-data onset engine and agro-hydrological calculations are validated, how they compare against published Bangladesh Meteorological Department (BMD) and BARC climatological benchmarks (**Spec v2 Item V**), and how to generate the full 40-cell NASA POWER snapshot and `data/processed/onset_results.json` summary on any internet-connected machine or in GitHub Actions.

## 1. Snapshot Build Status in This Archive

- **Current sandbox environment status**: `snapshots not built, reason: the build sandbox VM has outbound internet access disabled by security policy, so live HTTPS downloads from https://power.larc.nasa.gov/api/temporal/daily/point cannot be executed inside the sandbox.`
- **Fail-closed guarantee**: In accordance with `backend/tests/test_no_fabrication_guard.py` and the project's strict zero-fabrication policy, **no synthetic or placeholder files have been placed in `data/processed/power_history/`**. When `OFFLINE=1` and no verified snapshot is present, `/advisory` and `/api/v1/advisory` return `status = "UNAVAILABLE"` with `data_origin = "unavailable"`.
- **One-command snapshot & table generation (when online)**:
  ```bash
  # 1. Fetch all 40 unique NASA POWER grid cells covering all 64 Bangladesh districts (2001-01-01 to present)
  python -m scripts.build_snapshot

  # 2. Compute and export data/processed/onset_results.json and print the Markdown table for all 5 pilot zones & 40 cells
  python -m scripts.build_onset_results
  ```
- **Automated CI generation**: Running `.github/workflows/snapshot.yml` (`Build NASA POWER history snapshots`) or `.github/workflows/nasa-power-live.yml` on GitHub Actions fetches the real NASA POWER daily records, verifies SHA-256 checksums, runs `python -m scripts.build_onset_results`, and uploads the verified `data/processed/power_history/*.json` and `data/processed/onset_results.json` artifacts.

## 2. Automated Verification Against Reference Implementations (`OFFLINE=1`)

All statistical and physical estimators in BoponX are continuously verified against `scipy.stats` and exact analytical fixtures in `backend/tests/`:

| Component | Code Location | Reference / Oracle Checked in Tests | Test File |
|---|---|---|---|
| Usable-rain onset (`find_onset`, `rain_onset`) | `backend/app/compute/onset_stats.py`, `agro.py` | Known synthetic rainfall series with false-start dry spells and missing (`None`) days | `test_onset_stats.py`, `test_agro_advisory.py` |
| Two-sample shift (`hodges_lehmann_shift`) | `backend/app/compute/onset_stats.py` | Hand-computed pairwise median with outlier robustness check | `test_onset_stats.py` |
| Seeded bootstrap 95% CI (`bootstrap_shift_ci`) | `backend/app/compute/onset_stats.py` | Reproducibility check (`seed=20261001`) and bracketing of true shift | `test_onset_stats.py`, `test_agro_advisory.py` |
| Tie-corrected Mann–Whitney $U$ (`mann_whitney_u_test`) | `backend/app/compute/agro.py` | `scipy.stats.mannwhitneyu(..., alternative="two-sided", use_continuity=False, method="asymptotic")` ($|\Delta p| < 10^{-4}$) | `test_agro_advisory.py` |
| Mann–Kendall trend (`mann_kendall`) & Sen slope (`sen_slope`) | `backend/app/compute/onset_stats.py` | `scipy.stats.kendalltau` sign and $p$-value agreement ($|\Delta p| < 0.01$); exact slope recovery | `test_onset_stats.py` |
| Seasonal water balance (`_seasonal_water_balance`) | `backend/app/compute/agro.py` | FAO-56 Hargreaves–Samani $\text{ET}_0$ and $P - \text{ET}_0$ across Kharif-2 (`Jun–Oct`) and Rabi (`Nov–Mar`) | `test_agro_advisory.py` |
| Zero-fabrication guard | `backend/app/**` | Scans all backend Python source files to forbid synthetic generators or test fixtures in production paths | `test_no_fabrication_guard.py` |

## 3. Backtest Context Against Published BMD & Agro-Climatic Benchmarks (Spec v2 Item V)

Because sub-district BMD daily rain-gauge archives are licensed by the Bangladesh Meteorological Department (BMD) and not redistributable in an open repository, we document the published climatological benchmarks against which `scripts/build_onset_results.py` is evaluated once snapshots are built:

1. **Published BMD Southwest Monsoon Onset Progression Across Bangladesh**:
   - **Bangladesh Meteorological Department (BMD) & Ahmed & Kim (2003), *Int. J. Climatol.* 23: 1867–1882**: The climatological southwest monsoon enters southeastern Bangladesh (Teknaf / Cox's Bazar / Chattogram) around **1–5 June**, reaches central and northeastern Bangladesh (Dhaka, Mymensingh, Sylhet) around **6–10 June**, and reaches northwestern Bangladesh (Rajshahi, Naogaon, Rangpur, Dinajpur — High Barind Tract) around **10–15 June** (DOY `161–166`), with interannual standard deviation of `7–10 days`.
2. **Pre-Monsoon Haor Flash-Flood & Convective Rainfall in Sylhet / Sunamganj**:
   - **BMD / BWDB Haor Flash-Flood Studies & Shahid (2010), *Climate Research* 42: 185–193**: Northeastern Bangladesh (Sunamganj, Sylhet) receives `400–600 mm` of pre-monsoon rainfall in April–May due to orographic lifting along the Meghalaya plateau. Consequently, any rainfall-threshold rule starting on `01 May` (`20 mm / 7 days` with no 7-day dry spell) naturally detects usable wet-season conditions in early May in `Sunamganj`/`Sylhet`, whereas switching the search start to `01 June` (included in BoponX's `sensitivity_check.grid` as `start_0601`) isolates the June monsoon surge.
3. **Recent Decade Variability in the Barind Tract (Rajshahi / Naogaon)**:
   - **BARC Crop Zoning & BAMIS Regional Calendars (<https://www.bamis.gov.bd/>, <https://apps.barc.gov.bd/cropzoning/>)**: In the High Barind Tract (`Rajshahi`, `Naogaon`, `Chapainawabganj`), erratic late-May/June rainfall and prolonged intra-monsoon dry spells delay rainfed T. Aman seedbed preparation into mid-to-late July, motivating supplemental irrigation and short-duration drought-escaping cultivars (e.g., BRRI dhan56, BRRI dhan71, BINA dhan17).

## 4. Pilot Zone Reference Table Template (Populated by `python -m scripts.build_onset_results`)

When `python -m scripts.build_snapshot && python -m scripts.build_onset_results` is executed on an internet-connected machine, it writes `data/processed/onset_results.json` and prints the verified table below with exact SHA-256 snapshot digests:

| Pilot District | Grid Cell (`0.5°×0.625°`) | Shared With | Published BMD Normal Monsoon Arrival | BoponX `2001–2012` Mean Onset | BoponX `2013–latest` Mean Onset | Hodges–Lehmann Shift (95% CI) | Mann–Whitney $p$ | Sen Slope (`days/decade`) |
|---|---|---|---|---|---|---|---|---|
| **Rajshahi** (`24.3745°N, 88.6042°E`) | `24.25_88.4375` | Chapainawabganj, Natore | ~10–15 Jun | *Run `scripts.build_onset_results`* | *Run `scripts.build_onset_results`* | *Computed from snapshot* | *Computed* | *Computed* |
| **Naogaon** (`24.7936°N, 88.9318°E`) | `24.75_89.0625` | Joypurhat, Bogura | ~10–15 Jun | *Run `scripts.build_onset_results`* | *Run `scripts.build_onset_results`* | *Computed from snapshot* | *Computed* | *Computed* |
| **Sunamganj** (`25.0658°N, 91.3950°E`) | `25.25_91.5625` | — | ~05–08 Jun (heavy May pre-monsoon) | *Run `scripts.build_onset_results`* | *Run `scripts.build_onset_results`* | *Computed from snapshot* | *Computed* | *Computed* |
| **Patuakhali** (`22.3596°N, 90.3298°E`) | `22.25_90.3125` | Barguna, Jhalokati | ~03–07 Jun | *Run `scripts.build_onset_results`* | *Run `scripts.build_onset_results`* | *Computed from snapshot* | *Computed* | *Computed* |
| **Dhaka** (`23.8103°N, 90.4125°E`) | `23.75_90.3125` | Gazipur, Manikganj, Munshiganj, Narayanganj | ~06–10 Jun | *Run `scripts.build_onset_results`* | *Run `scripts.build_onset_results`* | *Computed from snapshot* | *Computed* | *Computed* |
