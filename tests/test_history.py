"""Tests for schemashift.history module."""

import pytest
from pathlib import Path

from schemashift.history import record_run, load_history, clear_history


@pytest.fixture
def tmp_dir(tmp_path):
    return tmp_path / "history"


def test_record_run_creates_file(tmp_dir):
    path = record_run("data.csv", "v1", False, "No drift", base_dir=tmp_dir)
    assert path.exists()
    assert path.suffix == ".json"


def test_record_run_content(tmp_dir):
    import json
    path = record_run("users.csv", "baseline_v1", True, "2 fields changed", base_dir=tmp_dir)
    data = json.loads(path.read_text())
    assert data["source"] == "users.csv"
    assert data["baseline"] == "baseline_v1"
    assert data["drift_detected"] is True
    assert data["summary"] == "2 fields changed"
    assert "timestamp" in data


def test_load_history_empty(tmp_dir):
    entries = load_history(base_dir=tmp_dir)
    assert entries == []


def test_load_history_returns_all(tmp_dir):
    record_run("a.csv", "v1", False, "ok", base_dir=tmp_dir)
    record_run("b.csv", "v2", True, "drift", base_dir=tmp_dir)
    entries = load_history(base_dir=tmp_dir)
    assert len(entries) == 2


def test_load_history_newest_first(tmp_dir):
    import time
    record_run("first.csv", "v1", False, "first", base_dir=tmp_dir)
    time.sleep(0.01)
    record_run("second.csv", "v1", True, "second", base_dir=tmp_dir)
    entries = load_history(base_dir=tmp_dir)
    assert entries[0]["summary"] == "second"
    assert entries[1]["summary"] == "first"


def test_load_history_with_limit(tmp_dir):
    for i in range(5):
        record_run(f"file{i}.csv", "v1", False, f"run{i}", base_dir=tmp_dir)
    entries = load_history(base_dir=tmp_dir, limit=3)
    assert len(entries) == 3


def test_load_history_filter_by_baseline(tmp_dir):
    record_run("a.csv", "baseline_a", False, "ok", base_dir=tmp_dir)
    record_run("b.csv", "baseline_b", True, "drift", base_dir=tmp_dir)
    record_run("c.csv", "baseline_a", False, "ok2", base_dir=tmp_dir)
    entries = load_history(base_dir=tmp_dir, baseline_name="baseline_a")
    assert len(entries) == 2
    assert all(e["baseline"] == "baseline_a" for e in entries)


def test_clear_history_removes_entries(tmp_dir):
    record_run("a.csv", "v1", False, "ok", base_dir=tmp_dir)
    record_run("b.csv", "v1", True, "drift", base_dir=tmp_dir)
    removed = clear_history(base_dir=tmp_dir)
    assert removed == 2
    assert load_history(base_dir=tmp_dir) == []


def test_clear_history_empty_dir(tmp_dir):
    removed = clear_history(base_dir=tmp_dir)
    assert removed == 0
