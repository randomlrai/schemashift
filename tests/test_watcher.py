"""Tests for schemashift.watcher and schemashift.watcher_cli."""

from __future__ import annotations

import csv
import json
import os
import tempfile
import types
from pathlib import Path
from unittest.mock import patch

import pytest

from schemashift.baseline import save_baseline
from schemashift.watcher import WatchEvent, watch
from schemashift.watcher_cli import handle_watch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_csv(path: str, rows: list[dict]) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


@pytest.fixture()
def tmp_dir(tmp_path: Path):
    return str(tmp_path)


# ---------------------------------------------------------------------------
# WatchEvent
# ---------------------------------------------------------------------------

def test_watch_event_has_drift_property():
    drift = types.SimpleNamespace(has_drift=True)
    event = WatchEvent(path="f.csv", baseline_name="b", drift_report=drift, comparison=None)
    assert event.has_drift is True


def test_watch_event_no_drift_property():
    drift = types.SimpleNamespace(has_drift=False)
    event = WatchEvent(path="f.csv", baseline_name="b", drift_report=drift, comparison=None)
    assert event.has_drift is False


# ---------------------------------------------------------------------------
# watch() — no drift
# ---------------------------------------------------------------------------

def test_watch_no_drift_calls_on_no_change(tmp_dir):
    csv_path = os.path.join(tmp_dir, "data.csv")
    _write_csv(csv_path, [{"id": "1", "name": "Alice"}])
    save_baseline("snap", csv_path, baseline_dir=tmp_dir)

    received: list[str] = []
    watch(
        path=csv_path,
        baseline_name="snap",
        baseline_dir=tmp_dir,
        interval=0.0,
        max_checks=1,
        on_no_change=received.append,
    )
    assert received == [csv_path]


# ---------------------------------------------------------------------------
# watch() — drift detected
# ---------------------------------------------------------------------------

def test_watch_drift_calls_on_change(tmp_dir):
    csv_path = os.path.join(tmp_dir, "data.csv")
    _write_csv(csv_path, [{"id": "1", "name": "Alice"}])
    save_baseline("snap", csv_path, baseline_dir=tmp_dir)

    # Overwrite with a different schema (new column, removed column)
    _write_csv(csv_path, [{"id": "1", "email": "a@b.com"}])

    events: list[WatchEvent] = []
    watch(
        path=csv_path,
        baseline_name="snap",
        baseline_dir=tmp_dir,
        interval=0.0,
        max_checks=1,
        on_change=events.append,
    )
    assert len(events) == 1
    assert events[0].has_drift
    assert events[0].path == csv_path


# ---------------------------------------------------------------------------
# handle_watch() CLI handler
# ---------------------------------------------------------------------------

def test_handle_watch_text_output(tmp_dir, capsys):
    csv_path = os.path.join(tmp_dir, "data.csv")
    _write_csv(csv_path, [{"id": "1", "name": "Alice"}])
    save_baseline("snap", csv_path, baseline_dir=tmp_dir)
    _write_csv(csv_path, [{"id": "1", "score": "99"}])

    import types as _t
    args = _t.SimpleNamespace(
        file=csv_path,
        baseline="snap",
        baseline_dir=tmp_dir,
        interval=0.0,
        max_checks=1,
        fmt="text",
    )
    rc = handle_watch(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "DRIFT" in out or "drift" in out.lower()


def test_handle_watch_json_output(tmp_dir, capsys):
    csv_path = os.path.join(tmp_dir, "data.csv")
    _write_csv(csv_path, [{"id": "1", "name": "Alice"}])
    save_baseline("snap", csv_path, baseline_dir=tmp_dir)
    _write_csv(csv_path, [{"uid": "1", "name": "Alice"}])

    import types as _t
    args = _t.SimpleNamespace(
        file=csv_path,
        baseline="snap",
        baseline_dir=tmp_dir,
        interval=0.0,
        max_checks=1,
        fmt="json",
    )
    handle_watch(args)
    out = capsys.readouterr().out
    parsed = json.loads(out.strip().splitlines()[-1])
    assert "has_drift" in parsed
