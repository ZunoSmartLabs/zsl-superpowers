"""Tests for the deterministic render fields surfaced into the timesheet digest.

The skill's prose used to ask Claude to re-derive the per-project duration label
(`Xh`/`X.Yh`/`Xm`) and the window/timezone header line by hand. Those are
single-answer renders, so digest_sessions.py now emits them and the model copies
them verbatim. These tests pin the one correct answer — including inputs an
eyeballing model gets wrong the old prose way.
"""

from __future__ import annotations

import importlib.util
import os
import time
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parent.parent / "digest_sessions.py"
_spec = importlib.util.spec_from_file_location("digest_sessions", _SCRIPT)
assert _spec and _spec.loader
ds = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ds)


def test_fmt_duration_golden():
    assert ds.fmt_duration(180) == "3h"
    assert ds.fmt_duration(45) == "45m"


def test_fmt_duration_fails_the_prose_way():
    # 270 min: an eyeballing model writes "4h" or "4.5 hrs"; the contract is "4.5h".
    assert ds.fmt_duration(270) == "4.5h"
    # 90 min: a model often writes "90m"; the contract crosses to "1.5h".
    assert ds.fmt_duration(90) == "1.5h"


def test_fmt_window_phrase_pluralization():
    # "last 1 hours" is the classic prose mistake — pluralization is deterministic.
    assert ds.fmt_window_phrase(1) == "last 1 hour"
    assert ds.fmt_window_phrase(12) == "last 12 hours"
    assert ds.fmt_window_phrase(1.5) == "last 1.5 hours"


def _digest(active_minutes: int, hours: float = 12.0) -> dict:
    return {
        "window_start": "2026-05-09T12:00:00+00:00",
        "window_end": "2026-05-10T00:00:00+00:00",
        "hours": hours,
        "projects": [
            {"cwd": "/code/spark-asset-iq", "active_minutes": active_minutes, "sessions": []}
        ],
    }


def test_strip_internal_surfaces_render_fields():
    # Force a known tz so the header render is a deterministic golden value.
    old_tz = os.environ.get("TZ")
    os.environ["TZ"] = "UTC"
    time.tzset()
    try:
        out = ds.strip_internal(_digest(270))
    finally:
        if old_tz is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = old_tz
        time.tzset()

    assert out["window_header"] == "_2026-05-09 12:00 → 00:00 UTC_"
    assert out["window_phrase"] == "last 12 hours"
    assert out["projects"][0]["duration_label"] == "4.5h"


def test_strip_internal_single_hour_header():
    out = ds.strip_internal(_digest(60, hours=1))
    assert out["window_phrase"] == "last 1 hour"
    assert out["projects"][0]["duration_label"] == "1h"
