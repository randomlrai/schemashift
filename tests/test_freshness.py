"""Tests for schemashift.freshness."""

from __future__ import annotations

import os
import pytest

from schemashift.freshness import (
    FreshnessResult,
    check_freshness,
    check_freshness_many,
)


@pytest.fixture()
def tmp_file(tmp_path):
    p = tmp_path / "schema.csv"
    p.write_text("id,name\n1,alice\n")
    return str(p)


# ---------------------------------------------------------------------------
# check_freshness — basic behaviour
# ---------------------------------------------------------------------------

def test_fresh_file_not_stale(tmp_file):
    mtime = os.path.getmtime(tmp_file)
    result = check_freshness(tmp_file, threshold_seconds=3600, _now=mtime + 100)
    assert result.is_stale is False


def test_stale_file_detected(tmp_file):
    mtime = os.path.getmtime(tmp_file)
    result = check_freshness(tmp_file, threshold_seconds=3600, _now=mtime + 7200)
    assert result.is_stale is True


def test_age_computed_correctly(tmp_file):
    mtime = os.path.getmtime(tmp_file)
    result = check_freshness(tmp_file, threshold_seconds=3600, _now=mtime + 500)
    assert abs(result.age_seconds - 500) < 0.01


def test_last_modified_matches_mtime(tmp_file):
    mtime = os.path.getmtime(tmp_file)
    result = check_freshness(tmp_file, _now=mtime + 10)
    assert result.last_modified == pytest.approx(mtime)


def test_label_stored(tmp_file):
    result = check_freshness(tmp_file, label="users_v2", _now=os.path.getmtime(tmp_file) + 1)
    assert result.label == "users_v2"


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        check_freshness(str(tmp_path / "nonexistent.csv"))


# ---------------------------------------------------------------------------
# FreshnessResult helpers
# ---------------------------------------------------------------------------

def test_to_dict_keys(tmp_file):
    mtime = os.path.getmtime(tmp_file)
    result = check_freshness(tmp_file, threshold_seconds=600, _now=mtime + 60)
    d = result.to_dict()
    assert set(d.keys()) == {
        "path", "label", "age_seconds", "threshold_seconds", "is_stale", "last_modified"
    }


def test_to_dict_is_stale_false(tmp_file):
    mtime = os.path.getmtime(tmp_file)
    d = check_freshness(tmp_file, threshold_seconds=3600, _now=mtime + 10).to_dict()
    assert d["is_stale"] is False


def test_summary_contains_stale_label(tmp_file):
    mtime = os.path.getmtime(tmp_file)
    result = check_freshness(tmp_file, threshold_seconds=3600, _now=mtime + 7200)
    assert "STALE" in result.summary()


def test_summary_contains_fresh_label(tmp_file):
    mtime = os.path.getmtime(tmp_file)
    result = check_freshness(tmp_file, threshold_seconds=3600, _now=mtime + 60)
    assert "FRESH" in result.summary()


# ---------------------------------------------------------------------------
# check_freshness_many
# ---------------------------------------------------------------------------

def test_check_many_returns_all_results(tmp_path):
    files = []
    for i in range(3):
        p = tmp_path / f"schema_{i}.csv"
        p.write_text("a,b\n1,2\n")
        files.append(str(p))

    mtime = os.path.getmtime(files[0])
    results = check_freshness_many(files, threshold_seconds=3600, _now=mtime + 10)
    assert len(results) == 3
    assert all(isinstance(r, FreshnessResult) for r in results)


def test_check_many_mixed_staleness(tmp_path):
    fresh_file = tmp_path / "fresh.csv"
    fresh_file.write_text("x\n1\n")
    stale_file = tmp_path / "stale.csv"
    stale_file.write_text("x\n2\n")

    mtime = os.path.getmtime(str(fresh_file))
    results = check_freshness_many(
        [str(fresh_file), str(stale_file)],
        threshold_seconds=3600,
        _now=mtime + 7200,
    )
    assert all(r.is_stale for r in results)
