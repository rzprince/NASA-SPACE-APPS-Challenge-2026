"""Statistics tests against scipy and hand-computed truths."""
import random

import pytest

from backend.app.compute.onset_stats import (
    bootstrap_shift_ci,
    find_onset,
    hodges_lehmann_shift,
    mann_kendall,
    normalized_doy,
    sen_slope,
)
from datetime import date


def test_find_onset_returns_evidence_and_respects_max_start():
    daily = [0.0] * 60
    daily[30:37] = [4, 4, 4, 4, 4, 4, 4]  # 28 mm window starting at 30
    daily[38] = 5.0
    hit = find_onset(daily)
    assert hit["index"] == 28 or hit["index"] == 29 or hit["index"] == 30
    assert hit["window_rain_mm"] >= 20
    assert find_onset(daily, max_start=10) is None


def test_hodges_lehmann_is_robust_to_one_outlier():
    early = [10, 11, 12, 13, 14]
    late = [20, 21, 22, 23, 90]
    assert hodges_lehmann_shift(early, late) == 10.0


def test_bootstrap_ci_is_reproducible_and_brackets_estimate():
    rng = random.Random(1)
    early = [160 + rng.randint(-4, 4) for _ in range(12)]
    late = [171 + rng.randint(-4, 4) for _ in range(14)]
    a = bootstrap_shift_ci(early, late, n_boot=500)
    b = bootstrap_shift_ci(early, late, n_boot=500)
    assert a == b
    est = hodges_lehmann_shift(early, late)
    assert a["low"] <= est <= a["high"]


def test_mann_kendall_matches_scipy_kendalltau_sign_and_significance():
    years = list(range(2001, 2027))
    rng = random.Random(4)
    values = [150 + 0.6 * i + rng.uniform(-3, 3) for i in range(len(years))]
    mk = mann_kendall(values)
    try:
        from scipy.stats import kendalltau

        tau, p = kendalltau(years, values)
        tau = float(tau)
        p = float(p)
    except ImportError:
        # Exact reference output of scipy.stats.kendalltau(years, values) for Random(4)
        tau = 0.7907692307692308
        p = 6.267372968210562e-11
    assert mk["s"] > 0 and tau > 0
    assert abs(mk["p_value"] - p) < 0.01


def test_sen_slope_recovers_a_known_slope():
    years = list(range(2001, 2021))
    values = [150 + 0.5 * (y - 2001) for y in years]
    assert sen_slope(years, values) == pytest.approx(0.5)


def test_normalized_doy_treats_leap_years_like_common_years():
    assert normalized_doy(date(2020, 3, 1)) == normalized_doy(date(2021, 3, 1))
    assert normalized_doy(date(2020, 1, 31)) == 31
