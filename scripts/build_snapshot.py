"""Download real NASA POWER daily history (2001 to present) for every grid cell used by the
64 Bangladesh districts (40 unique 0.5 x 0.625 deg cells), validate each snapshot, store verified
snapshots in data/processed/power_history/, and regenerate data/processed/onset_results.json.

Usage (needs internet, resumable):
    python -m scripts.build_snapshot                 # all 40 cells covering 64 districts
    python -m scripts.build_snapshot --districts rajshahi,naogaon
    python -m scripts.build_snapshot --force         # re-download existing cells

The script never writes synthetic values. A cell that fails is reported and skipped without
discarding already acquired cells.
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import date

from backend.app.compute.bangladesh_districts import DISTRICTS
from backend.app.services import power_history as ph
from scripts.build_onset_results import build_onset_results


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--districts", default="", help="comma separated district ids (default: all 64)")
    ap.add_argument("--force", action="store_true", help="re-download cells that already have a validated snapshot")
    ap.add_argument("--pause", type=float, default=1.5, help="seconds to wait between requests")
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--timeout", type=float, default=30.0, help="HTTP timeout in seconds per attempt")
    args = ap.parse_args()

    wanted = {x.strip().lower() for x in args.districts.split(",") if x.strip()}
    chosen = [d for d in DISTRICTS if not wanted or d.id in wanted]
    if not chosen:
        print("No matching districts.", file=sys.stderr)
        return 2

    cells: dict[str, dict] = {}
    for d in chosen:
        cell = ph.grid_cell(d.latitude, d.longitude)
        cells.setdefault(cell["id"], {"cell": cell, "districts": []})["districts"].append(d.name_en)

    print(f"{len(chosen)} districts -> {len(cells)} NASA POWER grid cells")
    end = ph.history_end()
    failed: list[str] = []
    for n, (cell_id, info) in enumerate(sorted(cells.items()), start=1):
        existing = ph.read_snapshot(cell_id)
        if not args.force and existing is not None:
            val = ph.validate_snapshot_record(existing)
            print(
                f"[{n}/{len(cells)}] {cell_id}: validated snapshot exists ({val['validation_status']}, "
                f"min_cov={val.get('min_coverage_fraction')}), skipped"
            )
            continue
        c = info["cell"]
        try:
            record = ph.fetch_live(
                c["center_latitude"],
                c["center_longitude"],
                date(ph.START_YEAR, 1, 1),
                end,
                timeout=args.timeout,
                max_retries=args.retries,
                backoff_sec=args.pause,
            )
            val = ph.validate_snapshot_record(record)
            digest = ph.write_snapshot(record)
            valid = sum(1 for v in record["series"]["PRECTOTCORR"] if v is not None)
            total = len(record["series"]["PRECTOTCORR"])
            print(
                f"[{n}/{len(cells)}] {cell_id}: {val['validation_status']}, rain coverage {valid}/{total}, "
                f"sha256 {digest[:12]}  ({', '.join(info['districts'])})"
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[{n}/{len(cells)}] {cell_id}: failed: {type(exc).__name__}: {exc}", file=sys.stderr)
            failed.append(cell_id)
        time.sleep(args.pause)

    health = ph.snapshot_health()
    print(f"snapshot health: {health}")
    onset_summary = build_onset_results()
    print(
        f"Regenerated onset_results.json: status={onset_summary['status']}, "
        f"ready={onset_summary['districts_ready']}/{onset_summary['districts_total']}, "
        f"coverage={onset_summary['district_coverage_summary']}"
    )
    if failed:
        print(f"FAILED cells: {failed}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
