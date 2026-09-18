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
        "customers": None,
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


def _project(cwd: str, buckets: set[int], marks: list | None = None) -> dict:
    return {"cwd": cwd, "active_minutes": len(buckets) * 5, "sessions": [{"_buckets": buckets, "_marks": marks or []}]}


_CONFIG = {
    "self": "ZunoSmart Labs",
    "customers": {
        "Spark": {"paths": ["spark-asset-iq"], "domains": ["spark.co.nz"]},
        "Thundergrid": {"paths": ["thundergrid149/"], "prompts": ["thundergrid"]},
        "SeenSafety": {"paths": ["tgmedia-customers/seensafety"], "prompts": ["seensafety"]},
        "ZunoSmart Labs": {"paths": ["zunosmartlabs/"]},
    },
}


def test_assign_customers_fails_the_prose_way():
    # The checkout path says zunosmartlabs, but the customer is Spark: a model
    # bucketing by the path's org segment gets this wrong. Entry order decides,
    # so the specific repo must be listed before the catch-all org.
    projects = [_project("/code/github.com/zunosmartlabs/spark-asset-iq", {1, 2})]
    ds.assign_customers(projects, _CONFIG)
    assert projects[0]["customer"] == "Spark"


def test_assign_customers_orders_unassigned_first_and_self_last():
    projects = [
        _project("/code/github.com/zunosmartlabs/workstation-setup", {1, 2, 3, 4, 5, 6}),
        _project("/code/github.com/thundergrid149/tg-ops-portal", {7}),
        _project("/code/gitlab.com/tgmedia-customers/seensafety-aws-architecture", {8, 9}),
        _project("/code/github.com/zunosmartlabs/spark-asset-iq", {1, 2, 3}),
    ]
    roll_up = ds.assign_customers(projects, _CONFIG)
    assert roll_up is not None
    # By minutes: Spark 15, SeenSafety 10, Thundergrid 5; self last regardless of its 30.
    assert [c["name"] for c in roll_up] == ["Spark", "SeenSafety", "Thundergrid", "ZunoSmart Labs"]
    assert projects[2]["customer"] == "SeenSafety"
    # Self has the most minutes but still sorts last; minutes are unioned per customer.
    assert roll_up[-1] == {"name": "ZunoSmart Labs", "active_minutes": 30}


def test_assign_customers_off_without_a_config():
    projects = [_project("/code/anything", {1})]
    assert ds.assign_customers(projects, None) is None
    assert projects[0]["customer"] is None
    assert projects[0]["blocks"][0]["minutes"] == 5 and projects[0]["blocks"][0]["customer"] is None


def test_strip_internal_labels_customers():
    d = _digest(270)
    d["customers"] = [{"name": "Spark", "active_minutes": 90}]
    out = ds.strip_internal(d)
    assert out["customers"][0]["duration_label"] == "1.5h"


def test_blocks_split_at_gaps_fails_the_prose_way():
    # One session's first and last events are nine hours apart, but the work sat
    # in two runs with an eight-hour hole. Reading started_at/ended_at as the
    # working window over-bills by eight hours; the blocks split at the gap.
    old_tz = os.environ.get("TZ")
    os.environ["TZ"] = "UTC"
    time.tzset()
    try:
        base = int(time.mktime((2026, 9, 16, 0, 0, 0, 0, 0, 0))) // 300  # 2026-09-16 00:00 UTC
        buckets = {base + i for i in range(0, 11)} | {base + 104, base + 105} | {base + 108}
        blocks = ds.blocks_from([(b, "SeenSafety") for b in sorted(buckets)])
    finally:
        if old_tz is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = old_tz
        time.tzset()
    assert [(b["start"][11:], b["end"][11:], b["minutes"]) for b in blocks] == [
        ("00:00", "00:55", 55),
        ("08:40", "09:05", 15),  # the 10-minute gap at 106-107 stays inside one block
    ]


def test_prompt_keywords_reattribute_time_fails_the_prose_way():
    # Ten minutes of Thundergrid work done from the SeenSafety checkout. Billing
    # by checkout path puts all 50 minutes on SeenSafety; the prompt that names
    # Thundergrid moves its minutes, and the next SeenSafety prompt moves back.
    marks = [(100, "clone the repo"), (105, "apply the same method to the Thundergrid accounts"), (107, "what about steampipe across the seensafety accounts?"), (108, "/init")]
    projects = [_project("/code/gitlab.com/tgmedia-customers/seensafety-aws-architecture", set(range(100, 110)), marks)]
    roll_up = ds.assign_customers(projects, _CONFIG)
    assert [(b["minutes"], b["customer"]) for b in projects[0]["blocks"]] == [(25, "SeenSafety"), (10, "Thundergrid"), (15, "SeenSafety")]
    assert roll_up is not None
    assert {c["name"]: c["active_minutes"] for c in roll_up} == {"SeenSafety": 40, "Thundergrid": 10}


def test_prompt_attribution_resets_after_a_gap():
    marks = [(100, "the Thundergrid routers")]
    projects = [_project("/code/gitlab.com/tgmedia-customers/seensafety-aws-architecture", {100, 101, 120, 121}, marks)]
    ds.assign_customers(projects, _CONFIG)
    assert [b["customer"] for b in projects[0]["blocks"]] == ["Thundergrid", "SeenSafety"]


def test_strip_internal_drops_private_session_keys():
    d = _digest(10)
    d["projects"][0]["sessions"] = [{"_buckets": {5_000_000}, "_marks": [(5_000_000, "hi")], "user_prompts": ["hi"]}]
    out = ds.strip_internal(d)
    assert out["projects"][0]["sessions"][0] == {"user_prompts": ["hi"]}


def test_pasted_output_never_switches_customer():
    # A directory listing pasted into the prompt mentions thundergrid149 among
    # 60 other paths. Keyword matching on it would bill the next 40 minutes to
    # Thundergrid; only short prompts, the user actually speaking, may switch.
    pasted = "» ssh lappy 'ls ~/.claude/projects'\n" + "\n".join(f"-Users-x-Code-github-com-org{i}-repo{i}" for i in range(60)) + "\n-Users-x-Code-github-com-thundergrid149-tg-ops-portal"
    assert len(pasted) > ds.PROMPT_KEYWORD_MAX_CHARS
    projects = [_project("/code/gitlab.com/tgmedia-customers/seensafety-aws-architecture", set(range(100, 108)), [(102, pasted)])]
    ds.assign_customers(projects, _CONFIG)
    assert [b["customer"] for b in projects[0]["blocks"]] == ["SeenSafety"]


def test_day_window_fails_the_prose_way():
    # "--hours 24" run at 10:40 spans 10:40 yesterday to 10:40 today; the day
    # the user asked about is midnight to midnight, local.
    import datetime as dt

    old_tz = os.environ.get("TZ")
    os.environ["TZ"] = "Pacific/Auckland"
    time.tzset()
    try:
        start, end, hours = ds.window_for(12.0, dt.date(2026, 9, 16))
    finally:
        if old_tz is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = old_tz
        time.tzset()
    assert start.isoformat() == "2026-09-15T12:00:00+00:00"  # NZST is UTC+12
    assert end.isoformat() == "2026-09-16T12:00:00+00:00"
    assert hours == 24.0
    assert ds.fmt_window_phrase(hours, "2026-09-16") == "16 September 2026"


def test_trailing_window_keeps_its_phrase():
    start, end, hours = ds.window_for(1.5, None)
    assert (end - start).total_seconds() == 5400 and hours == 1.5
    assert ds.fmt_window_phrase(hours, None) == "last 1.5 hours"
