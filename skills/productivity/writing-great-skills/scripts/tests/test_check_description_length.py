"""Tests for check-description-length.py — the hard 1024-char description gate.

Invokes the script as a subprocess (the way the skill calls it) and asserts exit
codes + output, including a 1190-char description that "looks like two sentences"
and so passes a model's eyeball the old prose way.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "check-description-length.py"


def run(*args: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        input=stdin,
        capture_output=True,
        text=True,
    )


def test_golden_short_description_passes():
    r = run("Extract text from PDFs. Use when working with PDF files.")
    assert r.returncode == 0
    assert "PASS" in r.stdout


def test_boundary_exactly_1024_passes():
    r = run("x" * 1024)
    assert r.returncode == 0


def test_boundary_1025_fails():
    r = run("x" * 1025)
    assert r.returncode == 1
    assert "1025 chars" in r.stdout


def test_fails_the_prose_way_1190_chars():
    # A plausible-looking two-sentence description that's actually over the cap.
    desc = (
        "Extract, transform, and validate structured data from spreadsheets, "
        "CSVs, and database exports, then reconcile the results against a "
        "canonical schema and emit a normalized report. " + ("Use when " + "x" * 1000)
    )
    assert len(desc) > 1024  # sanity: this is genuinely over
    r = run(desc)
    assert r.returncode == 1
    assert "FAIL" in r.stdout
    assert f"{len(desc)} chars" in r.stdout


def test_reads_stdin():
    r = run(stdin="short via stdin")
    assert r.returncode == 0
    assert "PASS" in r.stdout


def test_reads_file(tmp_path: Path):
    p = tmp_path / "desc.txt"
    p.write_text("x" * 2000, encoding="utf-8")
    r = run("--file", str(p))
    assert r.returncode == 1
    assert "2000 chars" in r.stdout


def test_trailing_newline_not_counted():
    # 1024 chars + a trailing newline should still PASS (newline is input artifact).
    r = run(stdin="x" * 1024 + "\n")
    assert r.returncode == 0
