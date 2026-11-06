"""Pure, dependency-free statistics used by the planting-window onset engine.

Everything here works on plain Python lists so it is easy to test against scipy.
No function in this module generates or imputes data.
"""
from __future__ import annotations

import math
import random
from datetime import date
from statistics import median
from typing import Any, Sequence


# ------------------------------------------------------------------ onset detection
def find_onset(
    daily_mm: Sequence[float | None],
    *,
    window: int = 7,
    threshold_mm: float = 20.0,
    dry_spell_max: int = 7,
    max_start: int | None = None,
) -> dict[str, Any] | None:
    """First start index of a `window`-day span with >= threshold_mm that is not followed by a
    dry spell (at least one day > 1.0 mm in the next `dry_spell_max` days).

    Missing days (None) are never counted as rain and never as a dry day: any candidate whose
    window or follow-up span contains a missing day is skipped, not guessed.
    Returns evidence dict or None when no onset is found.
    """
    r = list(daily_mm)
    last_start = len(r) - window - dry_spell_max  # exclusive upper bound, same convention as before
    if last_start <= 0:
        return None
    if max_start is not None:
        last_start = min(last_start, max_start + 1)
    for i in range(last_start):
        win = r[i : i + window]
        after = r[i + window : i + window + dry_spell_max]
        if any(v is None for v in win) or any(v is None for v in after):
            continue
        total = float(sum(win))  # type: ignore[arg-type]
        if total >= float(threshold_mm) and any(float(v) > 1.0 for v in after):  # type: ignore[arg-type]
            return {
                "index": i,
                "window_rain_mm": round(total, 1),
                "next_span_max_mm": round(max(float(v) for v in after), 1),  # type: ignore[arg-type]
            }
    return None


def normalized_doy(d: date) -> int:
    """Day of year on a non-leap calendar (29 Feb ignored) so years are comparable."""
    doy = d.timetuple().tm_yday
    leap = (d.year % 4 == 0 and d.year % 100 != 0) or d.year % 400 == 0
    return doy - 1 if leap and d.month > 2 else doy


# ------------------------------------------------------------------ two-sample statistics
def pairwise_differences(early: Sequence[float], late: Sequence[float]) -> list[float]:
    return [float(b) - float(a) for a in early for b in late]


def hodges_lehmann_shift(early: Sequence[float], late: Sequence[float]) -> float:
    """Median of all pairwise (late - early) differences: a robust shift estimate."""
    if not early or not late:
        raise ValueError("Both samples must be non-empty")
    return float(median(pairwise_differences(early, late)))


def bootstrap_shift_ci(
    early: Sequence[float],
    late: Sequence[float],
    *,
    n_boot: int = 2000,
    confidence: float = 0.95,
    seed: int = 2026,
) -> dict[str, float]:
    """Percentile bootstrap CI for the Hodges-Lehmann shift (seeded, so reproducible)."""
    if len(early) < 2 or len(late) < 2:
        raise ValueError("Need at least 2 values per sample")
    rng = random.Random(seed)
    e, l_ = list(early), list(late)
    shifts: list[float] = []
    for _ in range(n_boot):
        be = [e[rng.randrange(len(e))] for _ in e]
        bl = [l_[rng.randrange(len(l_))] for _ in l_]
        shifts.append(hodges_lehmann_shift(be, bl))
    shifts.sort()
    alpha = (1.0 - confidence) / 2.0
    lo = shifts[int(math.floor(alpha * (n_boot - 1)))]
    hi = shifts[int(math.ceil((1.0 - alpha) * (n_boot - 1)))]
    return {"low": float(lo), "high": float(hi), "confidence": confidence, "n_boot": n_boot, "seed": seed}


# ------------------------------------------------------------------ trend statistics
def _norm_two_sided_p(z: float) -> float:
    return math.erfc(abs(z) / math.sqrt(2.0))


def mann_kendall(values: Sequence[float]) -> dict[str, Any]:
    """Mann-Kendall trend test (tie-corrected normal approximation, continuity corrected)."""
    x = [float(v) for v in values]
    n = len(x)
    if n < 4:
        raise ValueError("Mann-Kendall needs at least 4 values")
    s = 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            diff = x[j] - x[i]
            s += (diff > 0) - (diff < 0)
    counts: dict[float, int] = {}
    for v in x:
        counts[v] = counts.get(v, 0) + 1
    tie_term = sum(t * (t - 1) * (2 * t + 5) for t in counts.values() if t > 1)
    var_s = (n * (n - 1) * (2 * n + 5) - tie_term) / 18.0
    if var_s <= 0:
        z = 0.0
    elif s > 0:
        z = (s - 1) / math.sqrt(var_s)
    elif s < 0:
        z = (s + 1) / math.sqrt(var_s)
    else:
        z = 0.0
    p_val = round(_norm_two_sided_p(z), 5)
    return {"s": s, "z": round(z, 3), "p_value": p_val, "significant_at_0_05": bool(p_val < 0.05), "n": n}


def sen_slope(years: Sequence[float], values: Sequence[float]) -> float:
    """Median of pairwise slopes (value change per year)."""
    slopes: list[float] = []
    for i in range(len(years) - 1):
        for j in range(i + 1, len(years)):
            dy = float(years[j]) - float(years[i])
            if dy != 0:
                slopes.append((float(values[j]) - float(values[i])) / dy)
    if not slopes:
        raise ValueError("Not enough distinct years")
    return float(median(slopes))
