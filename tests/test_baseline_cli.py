"""Tests for schemashift.baseline_cli sub-commands."""

import argparse
import json
import os
import pytest

from schemashift.baseline_cli import handle_baseline
from schemashift.baseline import save_baseline

SAMPLE_SCHEMA = {"id": "integer", "name": "string"}


@pytest.fixture()
def tmp_dir(tmp_path):
    return str(tmp_path / "bl")


def _ns(**kwargs):
    defaults = {"baseline_cmd": None, "directory": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_save_baseline_cmd(tmp_dir, tmp_path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("id,name\n1,Alice\n")
    ns = _ns(baseline_cmd="save", file=str(csv_file), name="v1", directory=tmp_dir)
    rc = handle_baseline(ns)
    assert rc == 0
    from schemashift.baseline import load_baseline
    payload = load_baseline("v1", directory=tmp_dir)
    assert "id" in payload["schema"]


def test_list_empty(tmp_dir, capsys):
    ns = _ns(baseline_cmd="list", directory=tmp_dir)
    rc = handle_baseline(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No baselines" in out


def test_list_with_entries(tmp_dir, capsys):
    save_baseline("alpha", SAMPLE_SCHEMA, directory=tmp_dir)
    save_baseline("beta", SAMPLE_SCHEMA, directory=tmp_dir)
    ns = _ns(baseline_cmd="list", directory=tmp_dir)
    handle_baseline(ns)
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta" in out


def test_show_existing(tmp_dir, capsys):
    save_baseline("mybl", SAMPLE_SCHEMA, directory=tmp_dir)
    ns = _ns(baseline_cmd="show", name="mybl", directory=tmp_dir)
    rc = handle_baseline(ns)
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["schema"] == SAMPLE_SCHEMA


def test_show_missing_returns_error(tmp_dir, capsys):
    ns = _ns(baseline_cmd="show", name="ghost", directory=tmp_dir)
    rc = handle_baseline(ns)
    assert rc == 1
    err = capsys.readouterr().err
    assert "ghost" in err


def test_delete_existing(tmp_dir):
    save_baseline("old", SAMPLE_SCHEMA, directory=tmp_dir)
    ns = _ns(baseline_cmd="delete", name="old", directory=tmp_dir)
    rc = handle_baseline(ns)
    assert rc == 0
    from schemashift.baseline import list_baselines
    assert "old" not in list_baselines(tmp_dir)


def test_delete_missing_returns_error(tmp_dir, capsys):
    ns = _ns(baseline_cmd="delete", name="nope", directory=tmp_dir)
    rc = handle_baseline(ns)
    assert rc == 1
