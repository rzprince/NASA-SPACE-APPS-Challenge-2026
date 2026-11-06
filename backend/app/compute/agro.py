"""Planting-window shift engine built on real NASA POWER daily data (2001 to present).

For one POWER grid cell the engine:
1. finds the usable-rain onset of every year with the stated definition (`rain_onset`),
2. compares 2001-2012 with 2013-latest (Mann-Whitney U, Hodges-Lehmann shift, bootstrap CI),
3. tests the whole record for a trend (Mann-Kendall, Sen slope),
4. checks sensitivity to threshold, window length, dry-spell length and search start,
5. computes crop GDD and seasonal water balance (P - ET0) from real PRECTOTCORR / T2M_MAX / T2M_MIN,
6. turns the result into an English/Bangla advisory and an SMS, and only moves the BAMIS planting
   window when the shift is statistically reliable and the crop is monsoon-linked.

If no real data can be obtained the engine returns status "UNAVAILABLE". It never invents data.
"""
from __future__ import annotations

from datetime import date, timedelta
import math
from typing import Any, Sequence

from backend.app.compute.bangladesh_districts import (
    DISTRICTS,
    lookup_bangladesh_area,
    nearest_bangladesh_district,
)
from backend.app.compute.onset_stats import (
    bootstrap_shift_ci,
    find_onset,
    hodges_lehmann_shift,
    mann_kendall,
    normalized_doy,
    sen_slope,
)
from backend.app.services.power_history import grid_cell, load_history
from backend.app.services.power_live import _hargreaves_et0_mm_day

ONSET_DEFINITION_EN = (
    "First day (scanning from 01 May) of a 7-day window with 20 mm or more of cumulative rainfall "
    "that is not followed by a dry spell longer than 7 days (at least one day > 1.0 mm in the next 7 days); "
    "candidate windows containing any missing day are skipped, never imputed."
)
ONSET_DEFINITION_BN = (
    "১ মে থেকে গণনা করে টানা ৭ দিনে কমপক্ষে ২০ মিমি বা তার বেশি বৃষ্টিপাতের প্রথম দিন, যার পরবর্তী ৭ দিনের মধ্যে "
    "টানা শুষ্ক বিরতি থাকে না (পরবর্তী ৭ দিনে অন্তত ১ দিন >১.০ মিমি বৃষ্টি থাকে); "
    "কোনো দিনে তথ্য অনুপস্থিত থাকলে সেই উইন্ডোটি বাদ দেওয়া হয়, কখনো অনুমান করা হয় না।"
)

CROP_SPECS: dict[str, dict[str, Any]] = {
    "rice": {
        "id": "rice",
        "name_en": "Aman Rice (T. Aman)",
        "name_bn": "আমন ধান (রোপা আমন)",
        "short_en": "Aman rice",
        "short_bn": "আমন ধান",
        "gdd_base_c": 10.0,
        "gdd_target_c_days": 1680,
        "action_word_en": "transplanting",
        "action_word_bn": "চারা রোপণ",
        "baseline_window_en": "05 Jul – 25 Jul",
        "baseline_window_bn": "৫ জুলাই – ২৫ জুলাই",
        "base_doy_start": 186,
        "base_doy_end": 206,
    },
    "wheat": {
        "id": "wheat",
        "name_en": "Rabi Wheat",
        "name_bn": "রবি গম",
        "short_en": "Wheat",
        "short_bn": "গম",
        "gdd_base_c": 5.0,
        "gdd_target_c_days": 1450,
        "action_word_en": "sowing",
        "action_word_bn": "বীজ বপন",
        "baseline_window_en": "15 Nov – 30 Nov",
        "baseline_window_bn": "১৫ নভেম্বর – ৩০ নভেম্বর",
        "base_doy_start": 319,
        "base_doy_end": 334,
    },
    "maize": {
        "id": "maize",
        "name_en": "Maize (Rabi / Kharif-1)",
        "name_bn": "ভুট্টা (রবি / খরিফ-১)",
        "short_en": "Maize",
        "short_bn": "ভুট্টা",
        "gdd_base_c": 10.0,
        "gdd_target_c_days": 1600,
        "action_word_en": "sowing",
        "action_word_bn": "বীজ বপন",
        "baseline_window_en": "10 Nov – 05 Dec",
        "baseline_window_bn": "১০ নভেম্বর – ৫ ডিসেম্বর",
        "base_doy_start": 314,
        "base_doy_end": 339,
    },
    "mustard": {
        "id": "mustard",
        "name_en": "Short-Duration Mustard",
        "name_bn": "স্বল্পমেয়াদি সরিষা",
        "short_en": "Mustard",
        "short_bn": "সরিষা",
        "gdd_base_c": 5.0,
        "gdd_target_c_days": 1150,
        "action_word_en": "sowing",
        "action_word_bn": "বীজ বপন",
        "baseline_window_en": "20 Oct – 15 Nov",
        "baseline_window_bn": "২০ অক্টোবর – ১৫ নভেম্বর",
        "base_doy_start": 293,
        "base_doy_end": 319,
    },
    "pulse": {
        "id": "pulse",
        "name_en": "Pulse (Lentil / Mungbean)",
        "name_bn": "ডাল (মসুর / মুগ)",
        "short_en": "Pulse",
        "short_bn": "ডাল",
        "gdd_base_c": 8.0,
        "gdd_target_c_days": 1200,
        "action_word_en": "sowing",
        "action_word_bn": "বীজ বপন",
        "baseline_window_en": "25 Oct – 20 Nov",
        "baseline_window_bn": "২৫ অক্টোবর – ২০ নভেম্বর",
        "base_doy_start": 298,
        "base_doy_end": 324,
    },
    "jute": {
        "id": "jute",
        "name_en": "Kharif-1 Jute",
        "name_bn": "খরিফ-১ পাট",
        "short_en": "Jute",
        "short_bn": "পাট",
        "gdd_base_c": 12.0,
        "gdd_target_c_days": 1550,
        "action_word_en": "sowing",
        "action_word_bn": "বীজ বপন",
        "baseline_window_en": "20 Mar – 20 Apr",
        "baseline_window_bn": "২০ মার্চ – ২০ এপ্রিল",
        "base_doy_start": 79,
        "base_doy_end": 110,
    },
    "vegetables": {
        "id": "vegetables",
        "name_en": "Seasonal Vegetables",
        "name_bn": "মৌসুমি সবজি",
        "short_en": "Vegetables",
        "short_bn": "সবজি",
        "gdd_base_c": 10.0,
        "gdd_target_c_days": 1250,
        "action_word_en": "planting",
        "action_word_bn": "রোপণ/বপন",
        "baseline_window_en": "15 Oct – 15 Nov",
        "baseline_window_bn": "১৫ অক্টোবর – ১৫ নভেম্বর",
        "base_doy_start": 288,
        "base_doy_end": 319,
    },
    "other": {
        "id": "other",
        "name_en": "Seasonal Field Crop",
        "name_bn": "মৌসুমি মাঠ ফসল",
        "short_en": "Field crop",
        "short_bn": "ফসল",
        "gdd_base_c": 10.0,
        "gdd_target_c_days": 1400,
        "action_word_en": "planting",
        "action_word_bn": "বপন/রোপণ",
        "baseline_window_en": "01 Jul – 25 Jul",
        "baseline_window_bn": "১ জুলাই – ২৫ জুলাই",
        "base_doy_start": 182,
        "base_doy_end": 206,
    },
}


def rain_onset(
    daily_mm: Sequence[float | None],
    window: int = 7,
    threshold_mm: float = 20.0,
    dry_spell_max: int = 7,
) -> int | None:
    """First day of a 7-day window with 20 mm or more that is not followed by a
    dry spell longer than 7 days. State this definition in the interface.
    Missing days (None) are skipped, never guessed.
    """
    found = find_onset(daily_mm, window=window, threshold_mm=threshold_mm, dry_spell_max=dry_spell_max)
    return None if found is None else int(found["index"])


def growing_degree_days(
    t_max_c: Sequence[float],
    t_min_c: Sequence[float],
    base_temp_c: float = 10.0,
    cap_temp_c: float = 35.0,
) -> dict[str, Any]:
    """Compute daily and cumulative Growing Degree Days (GDD) with a crop-specific base temperature."""
    n = min(len(t_max_c), len(t_min_c))
    daily_gdd: list[float] = []
    for idx in range(n):
        mean_t = (float(t_max_c[idx]) + float(t_min_c[idx])) / 2.0
        gdd = max(0.0, min(mean_t, float(cap_temp_c)) - float(base_temp_c))
        daily_gdd.append(round(gdd, 2))
    total = round(sum(daily_gdd), 1)
    mean_daily = round(total / n, 2) if n > 0 else 0.0
    return {
        "days": n,
        "base_temp_c": float(base_temp_c),
        "cap_temp_c": float(cap_temp_c),
        "total_gdd_c_days": total,
        "mean_daily_gdd_c_days": mean_daily,
        "daily_gdd": daily_gdd,
    }


def mann_whitney_u_test(period_a: Sequence[float], period_b: Sequence[float]) -> dict[str, Any]:
    """Two-sided Mann-Whitney U test (tie-corrected normal approximation) for two onset samples."""
    a = [float(x) for x in period_a]
    b = [float(x) for x in period_b]
    n1, n2 = len(a), len(b)
    if n1 == 0 or n2 == 0:
        raise ValueError("Both distributions must be non-empty for Mann-Whitney U test")

    combined = [(val, 0) for val in a] + [(val, 1) for val in b]
    combined.sort(key=lambda item: item[0])

    n = n1 + n2
    ranks = [0.0] * n
    tie_sum = 0.0
    i = 0
    while i < n:
        j = i
        while j < n and combined[j][0] == combined[i][0]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[k] = avg_rank
        t = j - i
        if t > 1:
            tie_sum += t**3 - t
        i = j

    r1 = sum(ranks[k] for k in range(n) if combined[k][1] == 0)
    u1 = r1 - (n1 * (n1 + 1)) / 2.0
    u2 = (n1 * n2) - u1
    u_stat = min(u1, u2)

    mean_u = (n1 * n2) / 2.0
    tie_correction = tie_sum / (n * (n - 1)) if n > 1 else 0.0
    var_u = (n1 * n2 / 12.0) * ((n + 1) - tie_correction)
    if var_u <= 0:
        z_score = 0.0
        p_value = 1.0
    else:
        z_score = (u2 - mean_u) / math.sqrt(var_u)
        p_value = math.erfc(abs(z_score) / math.sqrt(2.0))

    return {
        "u_statistic": round(float(u_stat), 2),
        "u_later_period": round(float(u2), 2),
        "z_score": round(float(z_score), 3),
        "p_value": round(float(p_value), 5),
        "significant_at_0_05": bool(p_value < 0.05),
        "n_early": n1,
        "n_late": n2,
        "n_2001_2012": n1,
        "n_2013_2025": n2,
        "method": "two-sided Mann-Whitney U, tie-corrected normal approximation",
    }


def _doy_to_label(doy: int, lang: str = "en") -> str:
    base = date(2026, 1, 1) + timedelta(days=max(0, min(364, int(doy) - 1)))
    months_en = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    months_bn = ["জানু", "ফেব্রু", "মার্চ", "এপ্রিল", "মে", "জুন", "জুলাই", "আগস্ট", "সেপ্টে", "অক্টো", "নভে", "ডিসে"]
    if lang == "bn":
        return f"{_bn(base.day)} {months_bn[base.month - 1]}"
    return f"{base.day:02d} {months_en[base.month - 1]}"


_BN_DIGITS = str.maketrans("0123456789-+", "০১২৩৪৫৬৭৮৯−+")


def _bn(value: Any) -> str:
    return str(value).translate(_BN_DIGITS)


def _window_label(start_doy: int, end_doy: int, lang: str, *, ascii_only: bool = False) -> str:
    sep = "-" if ascii_only else "–"
    return f"{_doy_to_label(start_doy, lang)}{sep}{_doy_to_label(end_doy, lang)}" if ascii_only else (
        f"{_doy_to_label(start_doy, lang)} – {_doy_to_label(end_doy, lang)}"
    )


# ------------------------------------------------------------------ SMS length rules
_GSM7_BASIC = set(
    "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà"
)
_GSM7_EXT = set("^{}\\[~]|€\f")


def sms_segments(text: str) -> dict[str, Any]:
    """Encoding, length units and SMS segments for a message (GSM-7: 160/153, UCS-2: 70/67)."""
    if all(ch in _GSM7_BASIC or ch in _GSM7_EXT for ch in text):
        units = sum(2 if ch in _GSM7_EXT else 1 for ch in text)
        single, multi, encoding = 160, 153, "GSM-7"
    else:
        units = sum(2 if ord(ch) > 0xFFFF else 1 for ch in text)
        single, multi, encoding = 70, 67, "UCS-2"
    segments = 1 if units <= single else math.ceil(units / multi)
    return {"encoding": encoding, "length": units, "segments": segments, "single_segment_limit": single}


def _pick_sms(candidates: Sequence[str]) -> str:
    """Longest-informative candidate that fits one segment; otherwise the shortest candidate."""
    for text in candidates:
        if sms_segments(text)["segments"] == 1:
            return text
    return min(candidates, key=lambda t: sms_segments(t)["length"])


# ------------------------------------------------------------------ real-data onset analysis
SEARCH_END_MD = (8, 31)  # latest start day considered for an onset
TAIL_END_MD = (9, 14)  # extra days so the dry-spell check can look past the search end
MIN_VALID_FRACTION = 0.95
MIN_YEARS_PER_PERIOD = 8
EARLY_YEARS = (2001, 2012)
GDD_WINDOW_DAYS = 90
BASE_CONFIG = {"window": 7, "threshold_mm": 20.0, "dry_spell_max": 7, "search_start": (5, 1)}
MONSOON_LINKED_CROPS = ("rice", "other")  # crops whose planting date is tied to the rainy-season start
MAX_APPLIED_SHIFT_DAYS = 21


def _day_index(record: dict[str, Any], d: date) -> int:
    return (d - date.fromisoformat(record["start"])).days


def _year_rain_slice(record: dict[str, Any], year: int, search_start: tuple[int, int]) -> dict[str, Any]:
    """Daily rain for [search_start .. Sep 14] of one year and quality flags."""
    start_d = date(year, *search_start)
    search_end_d = date(year, *SEARCH_END_MD)
    tail_end_d = date(year, *TAIL_END_MD)
    rec_start = date.fromisoformat(record["start"])
    rec_end = date.fromisoformat(record["end"])
    if start_d < rec_start or tail_end_d > rec_end:
        return {"year": year, "status": "incomplete_season"}
    i0, i1 = _day_index(record, start_d), _day_index(record, tail_end_d)
    rain = record["series"]["PRECTOTCORR"][i0 : i1 + 1]
    search_len = (search_end_d - start_d).days + 1
    valid = sum(1 for v in rain[:search_len] if v is not None)
    fraction = valid / search_len
    if fraction < MIN_VALID_FRACTION:
        return {"year": year, "status": "insufficient_data", "valid_fraction": round(fraction, 3)}
    return {
        "year": year,
        "status": "ok",
        "start_date": start_d,
        "rain": rain,
        "max_start": search_len - 1,
        "valid_fraction": round(fraction, 3),
    }


def _year_onsets(record: dict[str, Any], years: Sequence[int], cfg: dict[str, Any]) -> dict[int, dict[str, Any]]:
    out: dict[int, dict[str, Any]] = {}
    for year in years:
        sl = _year_rain_slice(record, year, cfg["search_start"])
        if sl["status"] != "ok":
            out[year] = {"year": year, "status": sl["status"], **({"valid_fraction": sl["valid_fraction"]} if "valid_fraction" in sl else {})}
            continue
        found = find_onset(
            sl["rain"],
            window=cfg["window"],
            threshold_mm=cfg["threshold_mm"],
            dry_spell_max=cfg["dry_spell_max"],
            max_start=sl["max_start"],
        )
        if found is None:
            out[year] = {"year": year, "status": "no_onset_found", "valid_fraction": sl["valid_fraction"]}
            continue
        onset_date = sl["start_date"] + timedelta(days=found["index"])
        out[year] = {
            "year": year,
            "status": "ok",
            "onset_date": onset_date,
            "onset_doy": normalized_doy(onset_date),
            "window_rain_mm": found["window_rain_mm"],
            "next_span_max_mm": found["next_span_max_mm"],
            "valid_fraction": sl["valid_fraction"],
        }
    return out


def _split_periods(onsets: dict[int, dict[str, Any]], last_year: int) -> tuple[list[dict], list[dict]]:
    early = [onsets[y] for y in range(EARLY_YEARS[0], EARLY_YEARS[1] + 1) if onsets.get(y, {}).get("status") == "ok"]
    late = [onsets[y] for y in range(EARLY_YEARS[1] + 1, last_year + 1) if onsets.get(y, {}).get("status") == "ok"]
    return early, late


def _shift_from_onsets(onsets: dict[int, dict[str, Any]], last_year: int) -> dict[str, Any]:
    early, late = _split_periods(onsets, last_year)
    if len(early) < 3 or len(late) < 3:
        return {"shift_days": None, "n_early": len(early), "n_late": len(late)}
    e = [x["onset_doy"] for x in early]
    l_ = [x["onset_doy"] for x in late]
    return {
        "shift_days": round(hodges_lehmann_shift(e, l_), 1),
        "mean_early_doy": round(sum(e) / len(e), 1),
        "mean_late_doy": round(sum(l_) / len(l_), 1),
        "n_early": len(early),
        "n_late": len(late),
    }


def _last_complete_year(record: dict[str, Any]) -> int:
    end = date.fromisoformat(record["end"])
    tail_end = date(end.year, *TAIL_END_MD)
    return end.year if end >= tail_end else end.year - 1


def _seasonal_water_balance(record: dict[str, Any], last_year: int) -> dict[str, Any]:
    """Compute Kharif-2 (Jun-Oct) and Rabi (Nov-Mar) rainfall, FAO-56 Hargreaves ET0, and P-ET0
    comparing 2001-2012 vs 2013-latest from the real NASA POWER daily series."""
    rec_start = date.fromisoformat(record["start"])
    rec_end = date.fromisoformat(record["end"])
    lat_deg = float(record.get("cell", {}).get("center_latitude", 24.0))
    rain_all = record["series"]["PRECTOTCORR"]
    tmax_all = record["series"]["T2M_MAX"]
    tmin_all = record["series"]["T2M_MIN"]

    def _span_metrics(s_date: date, e_date: date) -> dict[str, float] | None:
        if s_date < rec_start or e_date > rec_end:
            return None
        i0, i1 = _day_index(record, s_date), _day_index(record, e_date)
        n_days = i1 - i0 + 1
        if n_days <= 0:
            return None
        p_vals: list[float] = []
        et0_vals: list[float] = []
        for idx in range(i0, i1 + 1):
            p = rain_all[idx]
            hi = tmax_all[idx]
            lo = tmin_all[idx]
            if p is None or hi is None or lo is None:
                continue
            d = s_date + timedelta(days=idx - i0)
            t_mean = (hi + lo) / 2.0
            et0 = _hargreaves_et0_mm_day(t_mean, hi, lo, lat_deg=lat_deg, day_of_year=d.timetuple().tm_yday)
            if et0 is None:
                continue
            p_vals.append(float(p))
            et0_vals.append(float(et0))
        if len(p_vals) / n_days < MIN_VALID_FRACTION:
            return None
        p_daily = sum(p_vals) / len(p_vals)
        et0_daily = sum(et0_vals) / len(et0_vals)
        wb_daily = p_daily - et0_daily
        return {
            "rain_daily_mm": round(p_daily, 2),
            "et0_daily_mm": round(et0_daily, 2),
            "wb_daily_mm": round(wb_daily, 2),
            "rain_total_mm": round(p_daily * n_days, 1),
            "et0_total_mm": round(et0_daily * n_days, 1),
            "wb_total_mm": round(wb_daily * n_days, 1),
        }

    def _summarize_season(season_key: str, label_en: str, label_bn: str, is_rabi: bool) -> dict[str, Any]:
        early_rows: list[dict[str, float]] = []
        late_rows: list[dict[str, float]] = []
        for y in range(EARLY_YEARS[0], last_year + 1):
            if is_rabi:
                # Rabi spans Nov 1 of year y to Mar 31 of year y+1
                if y + 1 > rec_end.year:
                    continue
                s_d, e_d = date(y, 11, 1), date(y + 1, 3, 31)
            else:
                # Kharif-2 (Aman) spans Jun 1 to Oct 31 of year y
                s_d, e_d = date(y, 6, 1), date(y, 10, 31)
            m = _span_metrics(s_d, e_d)
            if m is None:
                continue
            if y <= EARLY_YEARS[1]:
                early_rows.append(m)
            else:
                late_rows.append(m)

        if len(early_rows) < 3 or len(late_rows) < 3:
            return {"season": season_key, "label_en": label_en, "label_bn": label_bn, "status": "insufficient_data"}

        def _avg(rows: list[dict[str, float]], k: str) -> float:
            return round(sum(r[k] for r in rows) / len(rows), 2)

        e_wb = [r["wb_daily_mm"] for r in early_rows]
        l_wb = [r["wb_daily_mm"] for r in late_rows]
        hl_wb = round(hodges_lehmann_shift(e_wb, l_wb), 2)
        ci_wb = bootstrap_shift_ci(e_wb, l_wb, n_boot=500)
        return {
            "season": season_key,
            "label_en": label_en,
            "label_bn": label_bn,
            "status": "ok",
            "period_2001_2012": {
                "n_years": len(early_rows),
                "rain_daily_mm": _avg(early_rows, "rain_daily_mm"),
                "et0_daily_mm": _avg(early_rows, "et0_daily_mm"),
                "water_balance_daily_mm": _avg(early_rows, "wb_daily_mm"),
                "water_balance_total_mm": round(_avg(early_rows, "wb_total_mm"), 1),
            },
            "period_2013_latest": {
                "n_years": len(late_rows),
                "rain_daily_mm": _avg(late_rows, "rain_daily_mm"),
                "et0_daily_mm": _avg(late_rows, "et0_daily_mm"),
                "water_balance_daily_mm": _avg(late_rows, "wb_daily_mm"),
                "water_balance_total_mm": round(_avg(late_rows, "wb_total_mm"), 1),
            },
            "shift_daily_mm": hl_wb,
            "ci_95_daily_mm": {"low": round(ci_wb["low"], 2), "high": round(ci_wb["high"], 2)},
        }

    return {
        "method": "FAO-56 Hargreaves-Samani ET0 and NASA POWER PRECTOTCORR daily water balance (P - ET0)",
        "kharif2_aman": _summarize_season("kharif2_aman", "Kharif-2 / Aman (Jun–Oct)", "খরিফ-২ / আমন (জুন–অক্টোবর)", is_rabi=False),
        "rabi": _summarize_season("rabi", "Rabi Dry Season (Nov–Mar)", "রবি মৌসুম (নভেম্বর–মার্চ)", is_rabi=True),
    }


_ONSET_CACHE: dict[tuple[str, str, str], dict[str, Any]] = {}


def analyze_record(record: dict[str, Any]) -> dict[str, Any]:
    """Crop-independent onset analysis of one POWER grid-cell record (cached)."""
    rain_vals = [v for v in record["series"]["PRECTOTCORR"] if v is not None]
    key = (record["cell"]["id"], record["retrieved_at"], f'{record["end"]}|{len(rain_vals)}|{round(sum(rain_vals), 2)}')
    if key in _ONSET_CACHE:
        return _ONSET_CACHE[key]

    last_year = _last_complete_year(record)
    years = list(range(EARLY_YEARS[0], last_year + 1))
    base_onsets = _year_onsets(record, years, BASE_CONFIG)
    early, late = _split_periods(base_onsets, last_year)

    result: dict[str, Any] = {
        "last_year": last_year,
        "onsets": base_onsets,
        "early": early,
        "late": late,
        "ok": len(early) >= MIN_YEARS_PER_PERIOD and len(late) >= MIN_YEARS_PER_PERIOD,
    }
    if result["ok"]:
        e = [x["onset_doy"] for x in early]
        l_ = [x["onset_doy"] for x in late]
        mw = mann_whitney_u_test(e, l_)
        hl = hodges_lehmann_shift(e, l_)
        ci = bootstrap_shift_ci(e, l_)
        ok_years = [y for y in years if base_onsets[y]["status"] == "ok"]
        doys = [base_onsets[y]["onset_doy"] for y in ok_years]
        mk = mann_kendall(doys) if len(doys) >= 4 else None
        slope = sen_slope(ok_years, doys) if len(doys) >= 4 else None
        result.update(
            {
                "mw": mw,
                "hl_shift": hl,
                "mean_diff": sum(l_) / len(l_) - sum(e) / len(e),
                "mean_early": sum(e) / len(e),
                "mean_late": sum(l_) / len(l_),
                "ci": ci,
                "trend": {
                    "years_used": len(ok_years),
                    "mann_kendall": mk,
                    "sen_slope_days_per_decade": None if slope is None else round(slope * 10.0, 2),
                },
                "sensitivity": _sensitivity(record, years, last_year),
                "seasonal_water_balance": _seasonal_water_balance(record, last_year),
            }
        )
    _ONSET_CACHE[key] = result
    if len(_ONSET_CACHE) > 128:
        _ONSET_CACHE.clear()
        _ONSET_CACHE[key] = result
    return result


def _sensitivity(record: dict[str, Any], years: Sequence[int], last_year: int) -> dict[str, Any]:
    """Re-run the whole onset analysis with perturbed definitions on the real series."""
    def run(label: str, **over: Any) -> dict[str, Any]:
        cfg = {**BASE_CONFIG, **over}
        s = _shift_from_onsets(_year_onsets(record, years, cfg), last_year)
        return {"key": label, "threshold_mm": cfg["threshold_mm"], "window_days": cfg["window"],
                "dry_spell_max_days": cfg["dry_spell_max"], "search_start": f"{cfg['search_start'][0]:02d}-{cfg['search_start'][1]:02d}", **s}

    thresholds = [run("minus_5mm", threshold_mm=15.0), run("base_20mm"), run("plus_5mm", threshold_mm=25.0)]
    grid: list[dict[str, Any]] = []
    for w in (5, 7, 10):
        for d in (5, 7, 10):
            grid.append(run(f"w{w}_d{d}", window=w, dry_spell_max=d))
    for start in ((4, 15), (6, 1)):
        grid.append(run(f"start_{start[0]:02d}{start[1]:02d}", search_start=start))
    return {"thresholds": thresholds, "grid": grid}


def _gdd_for_crop(record: dict[str, Any], crop: dict[str, Any], last_year: int) -> dict[str, Any]:
    """Real GDD per year from T2M_MAX/T2M_MIN: sum over 90 days from the crop's baseline start, and
    days needed to reach the crop's GDD target."""
    base = float(crop["gdd_base_c"])
    target = float(crop["gdd_target_c_days"])
    start_md = date(2026, 1, 1) + timedelta(days=int(crop["base_doy_start"]) - 1)
    rec_start = date.fromisoformat(record["start"])
    rec_end = date.fromisoformat(record["end"])
    tmax_all, tmin_all = record["series"]["T2M_MAX"], record["series"]["T2M_MIN"]

    def daily_gdd(idx: int) -> float | None:
        hi, lo = tmax_all[idx], tmin_all[idx]
        if hi is None or lo is None:
            return None
        return max(0.0, min((hi + lo) / 2.0, 35.0) - base)

    per_year: dict[int, dict[str, Any]] = {}
    for year in range(EARLY_YEARS[0], last_year + 1):
        s = date(year, start_md.month, start_md.day)
        if s < rec_start:
            continue
        i0 = _day_index(record, s)
        window_end = i0 + GDD_WINDOW_DAYS
        if s + timedelta(days=GDD_WINDOW_DAYS) > rec_end:
            continue
        vals = [daily_gdd(i) for i in range(i0, window_end)]
        valid = [v for v in vals if v is not None]
        if len(valid) / GDD_WINDOW_DAYS < MIN_VALID_FRACTION:
            continue
        entry: dict[str, Any] = {"gdd_90d": round(sum(valid) / len(valid) * GDD_WINDOW_DAYS, 1)}
        cum, days_to = 0.0, None
        for k in range(0, 300):
            idx = i0 + k
            if idx >= len(tmax_all):
                break
            g = daily_gdd(idx)
            cum += g if g is not None else 0.0
            if cum >= target:
                days_to = k + 1
                break
        entry["days_to_target"] = days_to
        per_year[year] = entry

    def mean_of(years: range, key: str) -> float | None:
        vals = [per_year[y][key] for y in years if y in per_year and per_year[y][key] is not None]
        return round(sum(vals) / len(vals), 1) if len(vals) >= 3 else None

    early_years = range(EARLY_YEARS[0], EARLY_YEARS[1] + 1)
    late_years = range(EARLY_YEARS[1] + 1, last_year + 1)
    return {
        "per_year": per_year,
        "gdd_90d_early": mean_of(early_years, "gdd_90d"),
        "gdd_90d_late": mean_of(late_years, "gdd_90d"),
        "days_to_target_early": mean_of(early_years, "days_to_target"),
        "days_to_target_late": mean_of(late_years, "days_to_target"),
    }


# ------------------------------------------------------------------ advisory builder
def _resolve_district(district_query: str | None, lat: float | None, lon: float | None):
    district_obj = None
    if district_query:
        match = lookup_bangladesh_area(district_query)
        if match and isinstance(match.get("district_profile"), dict):
            dp = match["district_profile"]
            for d in DISTRICTS:
                if d.id == dp.get("id"):
                    district_obj = d
                    break
    if district_obj is None and lat is not None and lon is not None:
        district_obj, _ = nearest_bangladesh_district(lat, lon)
    if district_obj is None:
        district_obj = next(d for d in DISTRICTS if d.id == "rajshahi")  # documented default demo district
    return district_obj


def _resolve_crop(crop_query: str | None) -> str:
    raw_crop = (crop_query or "rice").strip().lower()
    if raw_crop in ("aman", "boro", "aus", "paddy", "ধান", "আমন"):
        return "rice"
    return raw_crop if raw_crop in CROP_SPECS else "rice"


def _shared_districts(cell_id: str, own_id: str) -> list[str]:
    names: list[str] = []
    for d in DISTRICTS:
        if d.id != own_id and grid_cell(d.latitude, d.longitude)["id"] == cell_id:
            names.append(d.name_en)
    return names


_EVIDENCE_TYPES = {
    "onset_dates": "derived_from_nasa",
    "shift_statistics": "derived_from_nasa",
    "gdd": "derived_from_nasa",
    "seasonal_water_balance": "derived_from_nasa",
    "baseline_window": "official_local_reference",
    "recommended_window": "rule_based",
    "crop_gdd_targets": "preliminary_estimate",
}

_LIMITATIONS_EN = [
    "NASA POWER precipitation is gridded (0.5° × 0.625°, roughly 50 km); neighbouring districts can share one cell and a field gauge may differ.",
    "The record is short (about 25 seasons); a two-period comparison of 12 and 14 years has limited statistical power.",
    "The onset definition is one of many; results are reported for several definitions, not only this one.",
    "A one-for-one carry-over of the onset shift to transplanting dates is a planning assumption, not a measured response. Confirm with DAE (16123).",
    "NASA POWER data lag real time by about a week. This is near-real-time context, not a forecast.",
]


def _unavailable(district_obj, crop, history: dict[str, Any], cell: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "UNAVAILABLE",
        "data_origin": "unavailable",
        "reason": history.get("reason", "no_data"),
        "message": history.get("message", "Real NASA POWER data could not be loaded."),
        "district": _district_block(district_obj),
        "crop": _crop_block(crop),
        "grid_cell": cell,
        "limitations": _LIMITATIONS_EN,
        "provenance": {"datasets": [], "note": "No numbers are shown because no verified NASA POWER data was available."},
    }


def _district_block(d) -> dict[str, Any]:
    return {
        "id": d.id, "name_en": d.name_en, "name_bn": d.name_bn,
        "division_en": d.division_en, "division_bn": d.division_bn,
        "latitude": d.latitude, "longitude": d.longitude,
        "landform_en": d.landform_en, "landform_bn": d.landform_bn,
    }


def _crop_block(crop: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": crop["id"], "name_en": crop["name_en"], "name_bn": crop["name_bn"],
        "action_word_en": crop["action_word_en"], "action_word_bn": crop["action_word_bn"],
        "gdd_base_temp_c": crop["gdd_base_c"], "gdd_target_c_days": crop["gdd_target_c_days"],
    }


def build_planting_window_advisory(
    district_query: str | None = None,
    crop_query: str | None = None,
    *,
    lat: float | None = None,
    lon: float | None = None,
    history: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Planting-window advisory computed from real NASA POWER history.

    `history` lets tests inject a loader result; production code leaves it None.
    """
    district_obj = _resolve_district(district_query, lat, lon)
    crop_key = _resolve_crop(crop_query)
    crop = CROP_SPECS[crop_key]

    point_lat = lat if lat is not None else district_obj.latitude
    point_lon = lon if lon is not None else district_obj.longitude
    cell = grid_cell(point_lat, point_lon)
    if history is None:
        history = load_history(point_lat, point_lon)
    if history.get("status") != "available":
        return _unavailable(district_obj, crop, history, cell)

    record = history["record"]
    analysis = analyze_record(record)
    if not analysis["ok"]:
        out = _unavailable(district_obj, crop, {
            "reason": "insufficient_valid_years",
            "message": (f"Only {len(analysis['early'])} early and {len(analysis['late'])} late seasons had complete rainfall "
                        f"and a detectable onset; at least {MIN_YEARS_PER_PERIOD} are required in each period."),
        }, cell)
        out["status"] = "INSUFFICIENT_DATA"
        out["data_origin"] = history.get("data_origin", "nasa_power_snapshot")
        return out

    last_year = analysis["last_year"]
    early, late = analysis["early"], analysis["late"]
    mw, hl, ci = analysis["mw"], analysis["hl_shift"], analysis["ci"]
    mean_early, mean_late = round(analysis["mean_early"], 1), round(analysis["mean_late"], 1)
    mean_diff = float(analysis["mean_diff"])
    hl_rounded = int(math.floor(hl + 0.5)) if hl >= 0 else -int(math.floor(-hl + 0.5))
    mean_rounded = int(math.floor(mean_diff + 0.5)) if mean_diff >= 0 else -int(math.floor(-mean_diff + 0.5))
    shift_days = hl_rounded if hl_rounded != 0 else mean_rounded
    significant = bool(mw["significant_at_0_05"]) and shift_days != 0
    applies = crop_key in MONSOON_LINKED_CROPS
    applied_shift = 0
    if significant and applies:
        applied_shift = max(-MAX_APPLIED_SHIFT_DAYS, min(MAX_APPLIED_SHIFT_DAYS, shift_days))

    rev_start = crop["base_doy_start"] + applied_shift
    rev_end = crop["base_doy_end"] + applied_shift
    baseline_en = _window_label(crop["base_doy_start"], crop["base_doy_end"], "en")
    baseline_bn = _window_label(crop["base_doy_start"], crop["base_doy_end"], "bn")
    revised_en = _window_label(rev_start, rev_end, "en")
    revised_bn = _window_label(rev_start, rev_end, "bn")

    ci_lo, ci_hi = int(math.floor(ci["low"])), int(math.ceil(ci["high"]))
    p_en = f"p = {mw['p_value']:.4f}" if mw["p_value"] >= 0.0001 else "p < 0.0001"
    p_bn = _bn(p_en).replace("p =", "p =")
    direction_en = "later" if shift_days >= 0 else "earlier"
    direction_bn = "দেরিতে" if shift_days >= 0 else "আগে"
    name_en, name_bn = district_obj.name_en, district_obj.name_bn
    crop_en, crop_bn = crop["name_en"], crop["name_bn"]
    act_en, act_bn = crop["action_word_en"], crop["action_word_bn"]

    if significant and applies:
        kind = "shift_applied"
        sentence_en = (
            f"In {name_en}, usable-rain onset in 2013–{last_year} came about {abs(shift_days)} days {direction_en} than in 2001–2012 "
            f"(95% CI {ci_lo:+d} to {ci_hi:+d} days; Mann-Whitney {p_en}). Suggested {crop_en} {act_en} window: "
            f"{revised_en} (BAMIS baseline {baseline_en}). Verify with DAE 16123."
        )
        sentence_bn = (
            f"{name_bn} জেলায় ২০০১–২০১২ সালের তুলনায় ২০১৩–{_bn(last_year)} সালে কার্যকর বৃষ্টির শুরু প্রায় {_bn(abs(shift_days))} দিন {direction_bn} হয়েছে "
            f"(৯৫% আস্থা-ব্যবধান {_bn(f'{ci_lo:+d}')} থেকে {_bn(f'{ci_hi:+d}')} দিন; {p_bn})। {crop_bn} {act_bn}ের প্রস্তাবিত সময় "
            f"{revised_bn} (BAMIS ভিত্তি: {baseline_bn})। ১৬১২৩ নম্বরে যাচাই করুন।"
        )
    elif significant and not applies:
        kind = "context_only"
        sentence_en = (
            f"In {name_en}, usable-rain onset in 2013–{last_year} came about {abs(shift_days)} days {direction_en} than in 2001–2012 "
            f"(95% CI {ci_lo:+d} to {ci_hi:+d} days; {p_en}). This is shown as context only: {crop_en} {act_en} stays on the BAMIS window {baseline_en}."
        )
        sentence_bn = (
            f"{name_bn} জেলায় ২০০১–২০১২ সালের তুলনায় ২০১৩–{_bn(last_year)} সালে কার্যকর বৃষ্টির শুরু প্রায় {_bn(abs(shift_days))} দিন {direction_bn} হয়েছে "
            f"(৯৫% আস্থা-ব্যবধান {_bn(f'{ci_lo:+d}')} থেকে {_bn(f'{ci_hi:+d}')} দিন; {p_bn})। এটি শুধু প্রসঙ্গ হিসেবে দেওয়া হলো; "
            f"{crop_bn} {act_bn}ের সময় BAMIS-এর {baseline_bn}-ই থাকছে।"
        )
    else:
        kind = "no_reliable_shift"
        sentence_en = (
            f"In {name_en}, no reliable shift in usable-rain onset was detected between 2001–2012 and 2013–{last_year} "
            f"(estimate {shift_days:+d} days, 95% CI {ci_lo:+d} to {ci_hi:+d}; Mann-Whitney {p_en}). "
            f"Keep the BAMIS {crop_en} {act_en} window {baseline_en}."
        )
        sentence_bn = (
            f"{name_bn} জেলায় ২০০১–২০১২ ও ২০১৩–{_bn(last_year)} সময়ের মধ্যে কার্যকর বৃষ্টির শুরুতে নির্ভরযোগ্য কোনো পরিবর্তন পাওয়া যায়নি "
            f"(আনুমানিক {_bn(f'{shift_days:+d}')} দিন, ৯৫% আস্থা-ব্যবধান {_bn(f'{ci_lo:+d}')} থেকে {_bn(f'{ci_hi:+d}')}; {p_bn})। "
            f"{crop_bn} {act_bn}ের জন্য BAMIS-এর সময় {baseline_bn} অনুসরণ করুন।"
        )

    # SMS: ASCII hyphens keep English in GSM-7; Bangla is UCS-2 (70 per segment), so it is kept short.
    ws_en = _window_label(rev_start, rev_end, "en", ascii_only=True)
    ws_bn = _window_label(rev_start, rev_end, "bn", ascii_only=True)
    if kind == "shift_applied":
        sms_en_c = [
            f"BoponX {name_en}: usable rain {shift_days:+d}d vs 2001-12. {crop['short_en']} {act_en}: {ws_en}. Verify: DAE 16123",
            f"{name_en}: rain onset {shift_days:+d}d. {crop['short_en']} {act_en}: {ws_en}. DAE 16123",
        ]
        sms_bn_c = [
            f"{name_bn}: বৃষ্টি {_bn(abs(shift_days))} দিন {direction_bn}। {crop['short_bn']} {act_bn}: {ws_bn}। ১৬১২৩",
            f"{name_bn}: বৃষ্টি {_bn(abs(shift_days))} দিন {direction_bn}। {crop['short_bn']} {ws_bn}। ১৬১২৩",
            f"{name_bn}: {crop['short_bn']} {act_bn} {ws_bn}। ১৬১২৩",
        ]
    elif kind == "context_only":
        sms_en_c = [
            f"BoponX {name_en}: rain onset {shift_days:+d}d vs 2001-12 (context). {crop['short_en']} {act_en} stays {ws_en}. DAE 16123",
            f"{name_en}: {crop['short_en']} {act_en} stays {ws_en}. DAE 16123",
        ]
        sms_bn_c = [
            f"{name_bn}: {crop['short_bn']} {act_bn} {ws_bn}। ১৬১২৩",
            f"{name_bn}: {crop['short_bn']} {ws_bn}। ১৬১২৩",
        ]
    else:
        sms_en_c = [
            f"BoponX {name_en}: no reliable rain-onset shift found. Keep {crop['short_en']} {act_en}: {ws_en}. Verify: DAE 16123",
            f"{name_en}: no reliable shift. Keep {crop['short_en']} {act_en}: {ws_en}. DAE 16123",
        ]
        sms_bn_c = [
            f"{name_bn}: বৃষ্টির শুরুতে নির্ভরযোগ্য পরিবর্তন নেই। {crop['short_bn']} {act_bn}: {ws_bn}। ১৬১২৩",
            f"{name_bn}: পরিবর্তন নেই। {crop['short_bn']} {ws_bn}। ১৬১২৩",
        ]
    sms_en, sms_bn = _pick_sms(sms_en_c), _pick_sms(sms_bn_c)
    seg_en, seg_bn = sms_segments(sms_en), sms_segments(sms_bn)

    # GDD from real temperatures
    gdd = _gdd_for_crop(record, crop, last_year)
    g_e, g_l = gdd["gdd_90d_early"], gdd["gdd_90d_late"]
    d_e, d_l = gdd["days_to_target_early"], gdd["days_to_target_late"]
    if g_e is not None and g_l is not None:
        gdd_delta = round(g_l - g_e, 1)
        gdd_note_en = (
            f"Real NASA POWER temperatures, base {crop['gdd_base_c']:.0f}°C: {GDD_WINDOW_DAYS}-day GDD from the baseline planting start averaged "
            f"{g_e:.0f} °C·days in 2001–2012 and {g_l:.0f} in 2013–{last_year} ({gdd_delta:+.0f})."
            + (f" Days to reach the preliminary crop target: {d_e:.0f} vs {d_l:.0f}." if d_e is not None and d_l is not None else "")
        )
        gdd_note_bn = (
            f"NASA POWER-এর প্রকৃত তাপমাত্রা (ভিত্তি {crop['gdd_base_c']:.0f}°C): বপন/রোপণের ভিত্তি তারিখ থেকে {_bn(GDD_WINDOW_DAYS)} দিনের GDD গড়ে "
            f"২০০১–২০১২ সালে {_bn(round(g_e))} এবং ২০১৩–{_bn(last_year)} সালে {_bn(round(g_l))} °C·দিন ({_bn(f'{gdd_delta:+.0f}')})।"
        )
    else:
        gdd_delta = None
        gdd_note_en = "GDD could not be computed: too few years with complete temperature data."
        gdd_note_bn = "GDD হিসাব করা যায়নি: পর্যাপ্ত বছরের সম্পূর্ণ তাপমাত্রার তথ্য নেই।"

    # sensitivity block (keeps old keys; adds grid)
    sens = analysis["sensitivity"]
    thr = sens["thresholds"]
    thr_shifts = [t["shift_days"] for t in thr if t["shift_days"] is not None]
    all_shifts = [t["shift_days"] for t in sens["grid"] + thr if t["shift_days"] is not None]
    thr_rounded = [int(round(x)) for x in thr_shifts]
    thr_var = (max(thr_rounded) - min(thr_rounded)) if len(thr_rounded) == 3 else None
    is_stable = thr_var is not None and thr_var <= 2
    for t in thr:
        t["shift_days"] = None if t["shift_days"] is None else int(round(t["shift_days"]))
    sign_consistent = bool(all_shifts) and (all(s > 0 for s in all_shifts) or all(s < 0 for s in all_shifts))
    sensitivity = {
        "window_days": 7,
        "dry_spell_max_days": 7,
        "thresholds": thr,
        "max_shift_variation_days": thr_var,
        "is_stable": bool(is_stable),
        "grid": sens["grid"],
        "grid_shift_range_days": [min(all_shifts), max(all_shifts)] if all_shifts else None,
        "grid_sign_consistent": sign_consistent,
        "stability_note_en": (
            f"Shift across 15/20/25 mm thresholds: {min(thr_rounded):+d} to {max(thr_rounded):+d} days; across {len(sens['grid'])} further "
            f"definition variants (window, dry-spell, search start): {min(all_shifts):+.0f} to {max(all_shifts):+.0f} days."
            if thr_rounded and all_shifts else "Sensitivity could not be computed for this record."
        ),
        "stability_note_bn": (
            f"১৫/২০/২৫ মিমি সীমায় পরিবর্তন {_bn(f'{min(thr_rounded):+d}')} থেকে {_bn(f'{max(thr_rounded):+d}')} দিন; আরও {_bn(len(sens['grid']))}টি সংজ্ঞা-বৈচিত্র্যে "
            f"{_bn(f'{min(all_shifts):+.0f}')} থেকে {_bn(f'{max(all_shifts):+.0f}')} দিন।"
            if thr_rounded and all_shifts else "এই তথ্যের জন্য সংবেদনশীলতা পরীক্ষা করা যায়নি।"
        ),
    }

    onsets = analysis["onsets"]
    ok_years = [y for y in sorted(onsets) if onsets[y]["status"] == "ok"]
    excluded = [{"year": y, "reason": onsets[y]["status"]} for y in sorted(onsets) if onsets[y]["status"] != "ok"]

    def period_block(label: str, rows: list[dict[str, Any]], mean_doy: float) -> dict[str, Any]:
        doys = [r["onset_doy"] for r in rows]
        return {
            "label": label,
            "years": [r["year"] for r in rows],
            "onset_doy_values": doys,
            "mean_onset_doy": round(mean_doy, 1),
            "mean_onset_label_en": _doy_to_label(int(round(mean_doy)), "en"),
            "mean_onset_label_bn": _doy_to_label(int(round(mean_doy)), "bn"),
            "min_onset_doy": min(doys),
            "max_onset_doy": max(doys),
            "records": [{"year": r["year"], "onset_doy": r["onset_doy"], "onset_date_label": _doy_to_label(r["onset_doy"], "en")} for r in rows],
        }

    yearly_evidence = [
        {"year": y, "onset_date": onsets[y]["onset_date"].isoformat(), "onset_doy": onsets[y]["onset_doy"],
         "window_rain_mm": onsets[y]["window_rain_mm"], "max_day_in_next_7_mm": onsets[y]["next_span_max_mm"]}
        for y in ok_years
    ]

    return {
        "status": "ADVISORY_READY",
        "data_origin": history.get("data_origin", "nasa_power_snapshot"),
        "advisory_kind": kind,
        "district": _district_block(district_obj),
        "crop": _crop_block(crop),
        "grid_cell": cell,
        "shared_with": _shared_districts(cell["id"], district_obj.id),
        "data_through": record["end"],
        "retrieved_at": record["retrieved_at"],
        "lag_days": (date.today() - date.fromisoformat(record["end"])).days,
        "shift_days": shift_days,
        "shift": {
            "estimate_days": round(hl, 1),
            "estimator": "Hodges-Lehmann median of pairwise differences (robust)",
            "mean_difference_days": round(analysis["mean_diff"], 1),
            "ci_95_days": {"low": round(ci["low"], 1), "high": round(ci["high"], 1), "n_boot": ci["n_boot"], "seed": ci["seed"]},
            "reliable": significant,
            "applied_shift_days": applied_shift,
            "window_adjustment_applies_to_crop": applies,
            "max_applied_shift_days": MAX_APPLIED_SHIFT_DAYS,
        },
        "baseline_window": {"en": baseline_en, "bn": baseline_bn},
        "recommended_window": {"en": revised_en, "bn": revised_bn},
        "advisory_sentence": {"en": sentence_en, "bn": sentence_bn},
        "sms_advisory": {
            "en": sms_en,
            "bn": sms_bn,
            "char_count_en": seg_en["length"],
            "char_count_bn": seg_bn["length"],
            "max_chars": 160,
            "max_chars_en": seg_en["single_segment_limit"],
            "max_chars_bn": seg_bn["single_segment_limit"],
            "encoding_en": seg_en["encoding"],
            "encoding_bn": seg_bn["encoding"],
            "segments_en": seg_en["segments"],
            "segments_bn": seg_bn["segments"],
        },
        "distributions": {
            "period_2001_2012": period_block("2001–2012", early, mean_early),
            "period_2013_2025": period_block(f"2013–{last_year}", late, mean_late),
        },
        "mann_whitney_test": mw,
        "trend": analysis["trend"],
        "gdd_summary": {
            "base_temp_c": crop["gdd_base_c"],
            "window_days": GDD_WINDOW_DAYS,
            "period_2001_2012_seasonal_gdd": g_e,
            "period_2013_2025_seasonal_gdd": g_l,
            "gdd_delta_c_days": gdd_delta,
            "days_to_target_2001_2012": d_e,
            "days_to_target_2013_latest": d_l,
            "note_en": gdd_note_en,
            "note_bn": gdd_note_bn,
        },
        "seasonal_water_balance": analysis.get("seasonal_water_balance"),
        "sensitivity_check": sensitivity,
        "data_quality": {
            "min_valid_fraction_required": MIN_VALID_FRACTION,
            "years_used": len(ok_years),
            "years_excluded": excluded,
            "season_search_window": "from 01 May to 31 Aug (start varied in sensitivity grid)",
            "missing_values_policy": "never imputed; candidate windows containing a missing day are skipped",
        },
        "yearly_evidence": yearly_evidence,
        "how_computed": {
            "en": (
                "For each year, daily NASA POWER PRECTOTCORR is scanned from 01 May. The onset is the first start day whose 7-day total is at least 20 mm "
                "and that is followed by at least one day above 1.0 mm in the next 7 days (candidate windows with any missing day are skipped, never imputed). "
                "2001–2012 and 2013–latest onsets are compared with a Mann-Whitney U test; the shift is the Hodges-Lehmann median difference with a seeded "
                "bootstrap 95% interval. A Mann-Kendall test and Sen slope on all years check the trend."
            ),
            "bn": (
                "প্রতি বছর ১ মে থেকে NASA POWER-এর দৈনিক বৃষ্টি (PRECTOTCORR) দেখা হয়। টানা ৭ দিনে অন্তত ২০ মিমি এবং পরের ৭ দিনে অন্তত একদিন ১ মিমির বেশি বৃষ্টি হলে "
                "প্রথম দিনটিই কার্যকর বৃষ্টির শুরু (কোনো দিনে তথ্য না থাকলে সেই উইন্ডো বাদ দেওয়া হয়, কখনো অনুমান করা হয় না)। ২০০১–২০১২ ও ২০১৩–সর্বশেষ বছরের শুরুর তারিখ "
                "Mann-Whitney U পরীক্ষায় তুলনা করা হয়; পরিবর্তনের পরিমাণ Hodges-Lehmann মধ্যমা ও ৯৫% bootstrap ব্যবধানে দেওয়া হয়।"
            ),
        },
        "assumptions": {
            "onset_definition_en": ONSET_DEFINITION_EN,
            "onset_definition_bn": ONSET_DEFINITION_BN,
            "window_days": 7,
            "threshold_mm": 20.0,
            "dry_spell_max_days": 7,
            "gdd_base_temp_c": crop["gdd_base_c"],
            "statistical_test": f"Two-sided Mann-Whitney U test (2001–2012 vs. 2013–{last_year}); trend: Mann-Kendall + Sen slope",
            "transplanting_follows_onset": "Planning assumption: transplanting dates move one-for-one with the onset shift, only when significant (p < 0.05), capped at ±21 days.",
        },
        "evidence_types": _EVIDENCE_TYPES,
        "limitations": _LIMITATIONS_EN,
        "provenance": {
            "datasets": [
                {
                    "name": "NASA POWER Agroclimatology Daily (PRECTOTCORR, T2M_MAX, T2M_MIN), community AG",
                    "url": "https://power.larc.nasa.gov/docs/services/api/temporal/daily/",
                    "role": "computed: onset dates, shift statistics, GDD, seasonal P-ET0 water balance",
                    "request_url": record.get("source_request_url"),
                    "retrieved_at": record["retrieved_at"],
                },
                {
                    "name": "BAMIS regional crop calendar (baseline planting windows)",
                    "url": "https://www.bamis.gov.bd/",
                    "role": "official local reference: baseline window only",
                },
            ],
            "map_layers_not_used_in_this_calculation": ["GPM IMERG", "SMAP", "MODIS (visual GIBS layers)"],
        },
    }
