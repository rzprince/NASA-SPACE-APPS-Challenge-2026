"""TEST-ONLY synthetic POWER-shaped records. These are labelled origin="test_fixture" and are
never importable from backend/app. They exist so the statistics can be tested with a known truth."""
from __future__ import annotations

import random
from datetime import date, timedelta

from backend.app.services.power_history import grid_cell, make_record


def make_fixture_record(
    lat: float = 24.37,
    lon: float = 88.60,
    *,
    early_onset_md=(6, 9),
    shift_days: int = 0,
    jitter: int = 4,
    seed: int = 7,
    end: date = date(2026, 10, 15),
    missing_rate: float = 0.0,
) -> dict:
    rng = random.Random(seed)
    start = date(2001, 1, 1)
    n = (end - start).days + 1
    rain = [0.0] * n
    tmax = [0.0] * n
    tmin = [0.0] * n
    for i in range(n):
        d = start + timedelta(days=i)
        season = 1.0 if 5 <= d.month <= 9 else 0.0
        tmax[i] = round(26 + 7 * (1 if 4 <= d.month <= 9 else 0) + rng.uniform(-1, 1), 2)
        tmin[i] = round(tmax[i] - 8 + rng.uniform(-1, 1), 2)
        rain[i] = round(rng.uniform(0, 0.8) * (1 - season), 2)  # dry-ish outside the monsoon
    for year in range(2001, end.year + 1):
        shift = shift_days if year >= 2013 else 0
        onset = date(year, *early_onset_md) + timedelta(days=shift + rng.randint(-jitter, jitter))
        for k in range(0, 100):
            d = onset + timedelta(days=k)
            if d > end:
                break
            idx = (d - start).days
            if k < 7:
                rain[idx] = round(rng.uniform(3.5, 8.0), 2)  # a clear >= 20 mm window
            else:
                rain[idx] = round(rng.choice([0.0, 0.5, 2.0, 6.0, 14.0]), 2)
        # no usable rain before onset (keeps the true onset well defined)
        for k in range(1, 40):
            d = onset - timedelta(days=k)
            idx = (d - start).days
            if 0 <= idx < n:
                rain[idx] = round(rng.uniform(0, 0.6), 2)
    series = {"PRECTOTCORR": rain, "T2M_MAX": tmax, "T2M_MIN": tmin}
    if missing_rate:
        for key in series:
            for i in range(n):
                if rng.random() < missing_rate:
                    series[key][i] = None
    cell = grid_cell(lat, lon)
    return make_record(cell=cell, start=start, end=end, series=series, url="fixture://none", origin="nasa_power_https",
                       retrieved_at="2026-11-01T00:00:00Z")


def as_history(record: dict) -> dict:
    return {"status": "available", "record": record, "data_origin": "test_fixture"}
