"""Pytest configuration and Windows Python 3.14 temp-junction cleanup compatibility.

On Windows with Python 3.14, `pathlib.Path.unlink()` inside `_pytest.pathlib.cleanup_dead_symlinks`
raises `PermissionError: [WinError 5] Access is denied` when removing the `pytest-current`
directory junction at session teardown (`os.rmdir` is required for Windows directory junctions).
This hook catches `PermissionError` during temp-dir teardown and removes the junction cleanly.
"""
from __future__ import annotations

import os
import pathlib
import shutil


def pytest_configure(config) -> None:  # type: ignore[no-untyped-def]
    try:
        import _pytest.pathlib as pytest_pathlib

        orig_cleanup = getattr(pytest_pathlib, "cleanup_dead_symlinks", None)
        if callable(orig_cleanup):

            def _safe_cleanup_dead_symlinks(root: pathlib.Path) -> None:
                try:
                    orig_cleanup(root)
                except PermissionError:
                    for left_dir in root.iterdir():
                        try:
                            if left_dir.is_symlink() and not left_dir.resolve().exists():
                                try:
                                    os.rmdir(left_dir)
                                except OSError:
                                    shutil.rmtree(left_dir, ignore_errors=True)
                        except OSError:
                            pass

            pytest_pathlib.cleanup_dead_symlinks = _safe_cleanup_dead_symlinks
    except Exception:
        pass
