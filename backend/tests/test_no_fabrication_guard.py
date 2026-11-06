"""Guard: the advisory code path must never contain generated onsets or rainfall again."""
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app"
FORBIDDEN = (
    "_synthesize_daily_rainfall",
    "_district_shift_profile",
    "early_base = [",
    "Calibrated so",
    "calibrated so",
    "shift * 9.5",
)


def test_no_synthetic_onset_or_rainfall_generators_in_production_code():
    offenders = []
    for path in APP.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN:
            if token in text:
                offenders.append(f"{path.relative_to(APP)}: {token}")
    assert not offenders, offenders


def test_production_code_never_imports_test_fixtures():
    for path in APP.rglob("*.py"):
        assert "power_fixture" not in path.read_text(encoding="utf-8"), path
