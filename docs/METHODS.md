# Methods

This document states the exact definitions and equations implemented in code (`backend/app/compute/onset_stats.py`, `backend/app/compute/agro.py`, and `backend/app/services/power_live.py`). Every equation can be checked against `backend/tests/test_onset_stats.py` and `backend/tests/test_agro_advisory.py`.

## 1. Input data

- **Provider**: NASA POWER Agroclimatology Daily Point API (`community=AG`, `time-standard=LST`, `format=JSON`).
  - Official API documentation: <https://power.larc.nasa.gov/docs/services/api/temporal/daily/>
- **Variables**:
  - `PRECTOTCORR` — bias-corrected daily precipitation (`mm/day`).
  - `T2M_MAX`, `T2M_MIN` — daily maximum and minimum air temperature at 2 m (`°C`).
  - Recent 14-day and monthly climatology endpoints additionally read `T2M`, `T2MDEW`, `RH2M`, `WS2M`, `ALLSKY_SFC_SW_DWN`, `GWETTOP` (0–5 cm surface soil wetness fraction), and `GWETROOT` (0–100 cm root-zone soil wetness fraction).
- **Spatial resolution**: `0.5°` latitude × `0.625°` longitude (MERRA-2 native grid). Coordinates are snapped to the cell centre (`backend/app/services/power_history.py:grid_cell`); districts that fall in the same cell share the same climate series, and the API reports this in `shared_with`.
- **Period**: `2001-01-01` to `today − 7 days` (7-day latency margin so incomplete near-real-time days are not mixed into historical series).
- **Missing values**: NASA POWER's `-999.0` fill value, any non-finite number, and any negative precipitation (`PRECTOTCORR < 0.0`) are stored as `None`. **Missing days are never interpolated or filled.**

## 2. Usable-rain onset (`find_onset`) & Agronomic Literature Basis

For each year $y$, let $R_0, R_1, \dots, R_{M}$ be the daily rainfall series from the search start date $s_0$ (default **01 May**, `(5, 1)`) through **31 August** (`(8, 31)`), plus `dry_spell_max` extra days (to **14 September**) so the follow-up check is complete.

- A year is used only if at least `95%` of days in `[01 May .. 31 Aug]` are non-missing (`MIN_VALID_FRACTION = 0.95`).
- A candidate start index $i$ ($0 \le i \le M - w$) is **valid** iff:
  1. none of $R_i, \dots, R_{i+w-1}$ is `None`,
  2. $\sum_{k=0}^{w-1} R_{i+k} \ge T$ (default $w = 7\text{ days}$, $T = 20.0\text{ mm}$),
  3. none of $R_{i+w}, \dots, R_{i+w+d-1}$ is `None`, and
  4. $\max_{0 \le k < d} R_{i+w+k} > 1.0\text{ mm}$ (no dry spell of $d = 7$ consecutive days with $\le 1.0\text{ mm/day}$ immediately after the onset window).
- The year's onset is the **first** valid $i$. If no $i$ qualifies, the year is recorded as `no_onset_found` and excluded from the shift test (not replaced by a fallback).

### Literature Citations for the Onset Definition (Spec v2 Item O)
The two-part agronomic onset rule — requiring a cumulative rainfall threshold over a multi-day sowing window ($20\text{ mm}$ over $7\text{ days}$, sufficient to wet the top $5\text{–}10\text{ cm}$ seedbed layer above wilting point) coupled with a post-onset dry-spell screen (no $\ge 7\text{-day}$ dry spell immediately following) to reject "false starts" from isolated pre-monsoon convective storms — follows standard tropical agro-meteorological onset methodology:
1. **Stern, R. D., Dennett, M. D., & Garbutt, D. J. (1981).** *The start of the rains in West Africa.* Journal of Climatology, 1(1), 59–68; and **Stern, R. D., Dennett, M. D., & Dale, I. C. (1982).** *Analysing daily rainfall measurements to give agronomically useful results.* Experimental Agriculture, 18(3), 223–236.
2. **Sivakumar, M. V. K. (1988).** *Predicting rainy season potential from the onset of rains in Southern Sahelian and Sudanian climatic zones of West Africa.* Agricultural and Forest Meteorology, 42(4), 295–305.
3. **Marteau, R., Moron, V., & Philippon, N. (2009).** *Spatial coherence of monsoon onset over Western and Central Sahel (1950–2000).* Journal of Climate, 22(5), 1313–1324.
4. **Bangladesh Meteorological Department (BMD) & BAMIS / FAO TCP/BGD/3501:** Agro-meteorological framing for Bangladesh distinguishing pre-monsoon *Kalbaishakhi* convective showers (April–May) from sustained Kharif-2 monsoon establishment (late May–June) by requiring post-onset moisture persistence.

### Why the `1 May` Search Start and `dry_spell_max = 7` Screen Pre-Monsoon Showers
In Bangladesh, isolated April–May *Kalbaishakhi* thunderstorms can drop $20\text{–}35\text{ mm}$ in 1–2 days followed by 7–12 hot, dry days that desiccate newly broadcast seedbeds. Starting the scan on **01 May** and requiring at least one wet day ($> 1.0\text{ mm}$) within the subsequent 7 days rejects isolated pre-monsoon spikes while still detecting genuine early monsoon arrivals in late May (such as in the Sylhet/Sunamganj Haor basin and southeastern Chattogram coast). Furthermore, the sensitivity grid (`_sensitivity` in `backend/app/compute/agro.py`) automatically re-evaluates alternative search starts (`15 April` and `01 June`), window lengths ($w \in \{5, 7, 10\}$), dry-spell tolerances ($d \in \{5, 7, 10\}$), and rainfall thresholds ($T \in \{15, 20, 25\}\text{ mm}$) on the exact same daily series.

### Leap-year convention (`normalized_doy`)
To keep calendar dates comparable between leap and common years, day-of-year is computed on a 365-day reference calendar (`2001`): `29 Feb` is mapped to the same position as `28 Feb`, so `01 Jun` is always day `152`.

## 3. Two-period comparison (`2001–2012` vs `2013–latest`)

Let $A = \{x_1, \dots, x_{n_1}\}$ be the valid onset DOYs in `2001–2012` and $B = \{y_1, \dots, y_{n_2}\}$ those in `2013–latest` (where `latest` is the last year whose `14 September` is on or before `data_through`). Both periods must have at least `8` valid years (`MIN_YEARS_PER_PERIOD = 8`); otherwise the advisory returns `status = "INSUFFICIENT_DATA"`.

- **Shift estimator (Hodges–Lehmann)**:
  $$\hat\Delta = \operatorname{median}\{\, y_j - x_i \mid 1 \le i \le n_1,\; 1 \le j \le n_2 \,\}.$$
  Positive $\hat\Delta$ means the later period had a **later** onset. The mean difference $\bar B - \bar A$ is also reported in `shift.mean_difference_days`.
- **95% confidence interval (`bootstrap_shift_ci`)**: percentile bootstrap of $\hat\Delta$ with `n_boot = 2000` resamples and fixed seed `20261001` so the interval is reproducible.
- **Hypothesis test (`mann_whitney_u_test`)**: two-sided Mann–Whitney $U$ test with tie correction on the variance:
  $$\operatorname{Var}(U) = \frac{n_1 n_2}{12}\left(n + 1 - \frac{\sum (t_k^3 - t_k)}{n(n-1)}\right), \qquad n = n_1 + n_2,$$
  normal approximation $z = (U_2 - n_1 n_2 / 2)/\sqrt{\operatorname{Var}(U)}$, $p = \operatorname{erfc}(|z|/\sqrt{2})$.

## 4. Whole-record trend (`mann_kendall`, `sen_slope`)

Across all valid years $(t_1, d_1), \dots, (t_m, d_m)$ with $t_1 < \dots < t_m$:
- **Mann–Kendall** statistic $S = \sum_{i<j} \operatorname{sgn}(d_j - d_i)$, tie-corrected variance, two-sided normal $p$-value with continuity correction.
- **Theil–Sen slope**: $\beta = \operatorname{median}_{i<j} \frac{d_j - d_i}{t_j - t_i}$ (`days/year`), reported as `10 * β` (`days/decade`).

## 5. Sensitivity check (`_sensitivity`)

Every call re-runs the full onset detection and Hodges–Lehmann shift on the **same real series** across:
- thresholds $T \in \{15, 20, 25\}\text{ mm}$ (with $w=7, d=7$),
- the $3 \times 3$ grid $w \in \{5, 7, 10\} \times d \in \{5, 7, 10\}$ at $T = 20\text{ mm}$,
- search-start dates `15 April` and `01 June`.

The response reports the whole grid, the range of shifts across it, and whether all variants agree in sign (`grid_sign_consistent`).

## 6. Growing degree days (`_gdd_for_crop`)

For each year with $\ge 95\%$ valid temperature days in the 90-day window starting on the crop's BAMIS baseline start date:
$$\text{GDD}_t = \max\!\left(0,\; \min\!\left(\frac{T_{\max,t} + T_{\min,t}}{2},\; 35^\circ\text{C}\right) - T_{\text{base}}\right).$$
Both the 90-day sum and the number of days needed to reach the crop's target GDD (`preliminary_estimate`) are averaged over `2001–2012` and `2013–latest`.

## 7. Seasonal Water Balance (`_seasonal_water_balance`, Spec v2 Item W)

Using daily `PRECTOTCORR`, `T2M_MAX`, and `T2M_MIN` from the same historical NASA POWER record:
- Daily reference evapotranspiration $\text{ET}_0$ (`mm/day`) is estimated with the FAO-56 Hargreaves–Samani equation:
  $$\text{ET}_0 = 0.0023 \, (T_{\text{mean}} + 17.8)\,\sqrt{\max(0, T_{\max} - T_{\min})}\, R_a(\varphi, \text{DOY}),$$
  where $R_a$ is extraterrestrial radiation (`mm/day` equivalent evaporation) at grid-cell latitude $\varphi$.
- Daily net water balance is $P - \text{ET}_0$ (`mm/day`).
- Two agricultural seasons are summarized for `2001–2012` vs `2013–latest` with Hodges–Lehmann shift and 95% bootstrap CI:
  1. **Kharif-2 / Aman (`Jun–Oct`, 1 June to 31 October)**
  2. **Rabi (`Nov–Mar`, 1 November of year $y$ to 31 March of year $y+1$)**

## 8. When the planting window is — and is not — shifted

- The BAMIS baseline window is shifted **only** when `mann_whitney_test.significant_at_0_05` is `True` **and** the crop is monsoon-linked (`rice`, `other`). Even then, the applied shift is capped at `±21` days (`MAX_APPLIED_SHIFT_DAYS`) and labelled `rule_based`.
- If $p \ge 0.05$, `advisory_kind = "no_reliable_shift"`, `applied_shift_days = 0`, and `recommended_window == baseline_window`.
- For Rabi/winter crops (`wheat`, `mustard`, `pulse`, `maize`, `vegetables`) and `jute`, the monsoon onset shift is reported as `context_only` and the BAMIS window is left unchanged.
