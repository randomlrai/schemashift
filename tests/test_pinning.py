"""Tests for schemashift.pinning and schemashift.pinning_cli."""

from __future__ import annotations

import argparse
import csv
import json
import os

import pytest

from schemashift.pinning import (
    PinResult,
    delete_pin,
    list_pins,
    load_pin,
    save_pin,
    validate_against_pin,
)
from schemashift.pinning_cli import handle_pin


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path / "store")


def _write_csv(path: str, rows: list[dict]) -> None:
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


# ── unit tests ────────────────────────────────────────────────────────────────

def test_save_and_load_pin(store):
    schema = {"id": "integer", "name": "string"}
    save_pin(store, "v1", schema)
    loaded = load_pin(store, "v1")
    assert loaded == schema


def test_load_missing_pin_raises(store):
    with pytest.raises(FileNotFoundError):
        load_pin(store, "nonexistent")


def test_list_pins_empty(store):
    assert list_pins(store) == []


def test_list_pins_returns_names(store):
    save_pin(store, "alpha", {"x": "string"})
    save_pin(store, "beta", {"y": "integer"})
    assert list_pins(store) == ["alpha", "beta"]


def test_delete_pin_returns_true(store):
    save_pin(store, "tmp", {"a": "string"})
    assert delete_pin(store, "tmp") is True
    assert "tmp" not in list_pins(store)


def test_delete_missing_pin_returns_false(store):
    assert delete_pin(store, "ghost") is False


def test_validate_identical_schema_passes(store):
    schema = {"id": "integer", "email": "string"}
    save_pin(store, "v1", schema)
    result = validate_against_pin(store, "v1", schema)
    assert result.passed is True
    assert result.violations == []


def test_validate_removed_field_fails(store):
    save_pin(store, "v1", {"id": "integer", "email": "string"})
    result = validate_against_pin(store, "v1", {"id": "integer"})
    assert result.passed is False
    fields = [v.field for v in result.violations]
    assert "email" in fields


def test_validate_type_change_fails(store):
    save_pin(store, "v1", {"id": "integer"})
    result = validate_against_pin(store, "v1", {"id": "string"})
    assert result.passed is False
    assert result.violations[0].field == "id"


def test_validate_added_field_passes_non_strict(store):
    save_pin(store, "v1", {"id": "integer"})
    result = validate_against_pin(store, "v1", {"id": "integer", "new_col": "string"})
    assert result.passed is True


def test_validate_added_field_fails_strict(store):
    save_pin(store, "v1", {"id": "integer"})
    result = validate_against_pin(store, "v1", {"id": "integer", "new_col": "string"}, strict=True)
    assert result.passed is False


def test_pin_result_to_dict(store):
    save_pin(store, "v1", {"id": "integer"})
    result = validate_against_pin(store, "v1", {"id": "string"})
    d = result.to_dict()
    assert d["pin_name"] == "v1"
    assert d["passed"] is False
    assert isinstance(d["violations"], list)


# ── CLI tests ─────────────────────────────────────────────────────────────────

def _ns(**kwargs):
    defaults = {"store": None, "strict": False, "format": "text"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cli_save_and_list(tmp_path, store):
    csv_path = str(tmp_path / "data.csv")
    _write_csv(csv_path, [{"id": "1", "name": "Alice"}])
    rc = handle_pin(_ns(pin_cmd="save", file=csv_path, name="v1", store=store))
    assert rc == 0
    rc = handle_pin(_ns(pin_cmd="list", store=store))
    assert rc == 0


def test_cli_validate_pass(tmp_path, store, capsys):
    csv_path = str(tmp_path / "data.csv")
    _write_csv(csv_path, [{"id": "1"}])
    handle_pin(_ns(pin_cmd="save", file=csv_path, name="v1", store=store))
    rc = handle_pin(_ns(pin_cmd="validate", file=csv_path, name="v1", store=store, strict=False, format="text"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "PASSED" in out


def test_cli_validate_fail_json(tmp_path, store, capsys):
    csv_path = str(tmp_path / "v1.csv")
    _write_csv(csv_path, [{"id": "1", "name": "Alice"}])
    handle_pin(_ns(pin_cmd="save", file=csv_path, name="v1", store=store))
    csv_path2 = str(tmp_path / "v2.csv")
    _write_csv(csv_path2, [{"id": "1"}])  # name removed
    rc = handle_pin(_ns(pin_cmd="validate", file=csv_path2, name="v1", store=store, strict=False, format="json"))
    assert rc == 1
    data = json.loads(capsys.readouterr().out)
    assert data["passed"] is False


def test_cli_delete(tmp_path, store):
    csv_path = str(tmp_path / "data.csv")
    _write_csv(csv_path, [{"x": "1"}])
    handle_pin(_ns(pin_cmd="save", file=csv_path, name="to_del", store=store))
    rc = handle_pin(_ns(pin_cmd="delete", name="to_del", store=store))
    assert rc == 0
    assert list_pins(store) == []
