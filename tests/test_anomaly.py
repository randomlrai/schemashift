"""Tests for schemashift.anomaly and schemashift.anomaly_cli."""
from __future__ import annotations

import argparse
import json
import os
from io import StringIO
from unittest import mock

import pytest

from schemashift.anomaly import detect_anomalies, AnomalyResult
from schemashift.anomaly_cli import handle_anomaly
from schemashift.history import record_run


@pytest.fixture()
def tmp_dir(tmp_path):
    return str(tmp_path)


def _populate(history_dir: str, dataset: str, pattern: list[bool]) -> None:
    """Write synthetic run records for *dataset*."""
    for has_drift in pattern:
        record_run(
            history_dir=history_dir,
            dataset=dataset,
            has_drift=has_drift,
            added=[],
            removed=[],
            changed=[],
        )


def _ns(**kwargs) -> argparse.Namespace:
    defaults = dict(
        dataset="users",
        history_dir=".schemashift/history",
        threshold=0.5,
        min_runs=3,
        format="text",
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# anomaly.detect_anomalies
# ---------------------------------------------------------------------------

def test_insufficient_history_flagged(tmp_dir):
    _populate(tmp_dir, "users", [True, False])  # only 2 runs
    result = detect_anomalies("users", tmp_dir, threshold=0.5, min_runs=3)
    assert result.has_anomalies
    assert any("Insufficient" in a for a in result.anomalies)


def test_high_drift_rate_flagged(tmp_dir):
    _populate(tmp_dir, "users", [True, True, True, False])  # 75 % drift
    result = detect_anomalies("users", tmp_dir, threshold=0.5, min_runs=3)
    assert result.has_anomalies
    assert any("High drift" in a for a in result.anomalies)


def test_no_anomaly_clean_history(tmp_dir):
    _populate(tmp_dir, "users", [False, False, False, False])
    result = detect_anomalies("users", tmp_dir, threshold=0.5, min_runs=3)
    assert not result.has_anomalies
    assert result.drift_rate == 0.0


def test_sudden_spike_detected(tmp_dir):
    _populate(tmp_dir, "users", [False, False, False, True])  # spike at end
    result = detect_anomalies("users", tmp_dir, threshold=0.9, min_runs=3)
    assert result.has_anomalies
    assert any("spike" in a for a in result.anomalies)


def test_to_dict_keys(tmp_dir):
    _populate(tmp_dir, "orders", [False, False, False])
    result = detect_anomalies("orders", tmp_dir)
    d = result.to_dict()
    for key in ("dataset", "total_runs", "drift_rate", "threshold", "anomalies", "has_anomalies"):
        assert key in d


def test_dataset_isolation(tmp_dir):
    _populate(tmp_dir, "users", [False, False, False])
    _populate(tmp_dir, "orders", [True, True, True])
    users = detect_anomalies("users", tmp_dir)
    orders = detect_anomalies("orders", tmp_dir)
    assert not users.has_anomalies
    assert orders.has_anomalies


# ---------------------------------------------------------------------------
# anomaly_cli.handle_anomaly
# ---------------------------------------------------------------------------

def test_handle_anomaly_text_no_anomaly(tmp_dir, capsys):
    _populate(tmp_dir, "users", [False, False, False])
    handle_anomaly(_ns(history_dir=tmp_dir))
    out = capsys.readouterr().out
    assert "No anomalies" in out


def test_handle_anomaly_json_output(tmp_dir, capsys):
    _populate(tmp_dir, "users", [False, False, False])
    handle_anomaly(_ns(history_dir=tmp_dir, format="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["dataset"] == "users"
    assert "has_anomalies" in data


def test_handle_anomaly_exits_1_on_anomaly(tmp_dir):
    _populate(tmp_dir, "users", [True, True, True])
    with pytest.raises(SystemExit) as exc_info:
        handle_anomaly(_ns(history_dir=tmp_dir))
    assert exc_info.value.code == 1
