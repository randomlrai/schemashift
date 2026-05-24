"""Tests for schemashift.snapshot and schemashift.snapshot_cli."""

from __future__ import annotations

import json
import textwrap
from argparse import Namespace
from pathlib import Path

import pytest

from schemashift.snapshot import (
    capture_snapshot,
    compare_snapshots,
    delete_snapshot,
    list_snapshots,
    load_snapshot,
)
from schemashift.snapshot_cli import handle_snapshot


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write_csv(path: Path, content: str) -> str:
    path.write_text(textwrap.dedent(content))
    return str(path)


# ---------------------------------------------------------------------------
# snapshot module tests
# ---------------------------------------------------------------------------

def test_capture_creates_file(tmp_dir):
    csv = _write_csv(tmp_dir / "data.csv", "id,name\n1,Alice\n")
    snap = capture_snapshot(csv, "v1", base_dir=str(tmp_dir))
    assert snap["tag"] == "v1"
    assert "schema" in snap
    assert (tmp_dir / ".schemashift" / "snapshots" / "v1.json").exists()


def test_capture_schema_fields(tmp_dir):
    csv = _write_csv(tmp_dir / "data.csv", "id,age\n1,30\n")
    snap = capture_snapshot(csv, "fields", base_dir=str(tmp_dir))
    assert "id" in snap["schema"]
    assert "age" in snap["schema"]


def test_load_snapshot_roundtrip(tmp_dir):
    csv = _write_csv(tmp_dir / "data.csv", "x,y\n1,2\n")
    capture_snapshot(csv, "rt", base_dir=str(tmp_dir))
    loaded = load_snapshot("rt", base_dir=str(tmp_dir))
    assert loaded["tag"] == "rt"
    assert "schema" in loaded


def test_load_missing_raises(tmp_dir):
    with pytest.raises(FileNotFoundError):
        load_snapshot("ghost", base_dir=str(tmp_dir))


def test_list_snapshots_empty(tmp_dir):
    assert list_snapshots(base_dir=str(tmp_dir)) == []


def test_list_snapshots_returns_entries(tmp_dir):
    csv = _write_csv(tmp_dir / "data.csv", "a,b\n1,2\n")
    capture_snapshot(csv, "snap1", base_dir=str(tmp_dir))
    capture_snapshot(csv, "snap2", base_dir=str(tmp_dir))
    entries = list_snapshots(base_dir=str(tmp_dir))
    tags = [e["tag"] for e in entries]
    assert "snap1" in tags and "snap2" in tags


def test_delete_snapshot(tmp_dir):
    csv = _write_csv(tmp_dir / "data.csv", "a\n1\n")
    capture_snapshot(csv, "del_me", base_dir=str(tmp_dir))
    assert delete_snapshot("del_me", base_dir=str(tmp_dir)) is True
    assert list_snapshots(base_dir=str(tmp_dir)) == []


def test_delete_missing_returns_false(tmp_dir):
    assert delete_snapshot("nope", base_dir=str(tmp_dir)) is False


def test_compare_snapshots(tmp_dir):
    csv_v1 = _write_csv(tmp_dir / "v1.csv", "id,name\n1,Alice\n")
    csv_v2 = _write_csv(tmp_dir / "v2.csv", "id,name,email\n1,Alice,a@b.com\n")
    capture_snapshot(csv_v1, "cmp_v1", base_dir=str(tmp_dir))
    capture_snapshot(csv_v2, "cmp_v2", base_dir=str(tmp_dir))
    result = compare_snapshots("cmp_v1", "cmp_v2", base_dir=str(tmp_dir))
    assert result["from_tag"] == "cmp_v1"
    assert result["to_tag"] == "cmp_v2"
    assert "diff" in result


# ---------------------------------------------------------------------------
# snapshot_cli tests
# ---------------------------------------------------------------------------

def _ns(**kwargs) -> Namespace:
    defaults = {"snapshot_cmd": "list"}
    defaults.update(kwargs)
    return Namespace(**defaults)


def test_cli_capture(tmp_dir, capsys):
    csv = _write_csv(tmp_dir / "data.csv", "id\n1\n")
    handle_snapshot(_ns(snapshot_cmd="capture", file=csv, tag="cli_v1"), base_dir=str(tmp_dir))
    out = capsys.readouterr().out
    assert "cli_v1" in out


def test_cli_list_empty(tmp_dir, capsys):
    handle_snapshot(_ns(snapshot_cmd="list"), base_dir=str(tmp_dir))
    assert "No snapshots" in capsys.readouterr().out


def test_cli_list_with_entries(tmp_dir, capsys):
    csv = _write_csv(tmp_dir / "data.csv", "a\n1\n")
    capture_snapshot(csv, "listed", base_dir=str(tmp_dir))
    handle_snapshot(_ns(snapshot_cmd="list"), base_dir=str(tmp_dir))
    assert "listed" in capsys.readouterr().out


def test_cli_show(tmp_dir, capsys):
    csv = _write_csv(tmp_dir / "data.csv", "x\n1\n")
    capture_snapshot(csv, "show_me", base_dir=str(tmp_dir))
    handle_snapshot(_ns(snapshot_cmd="show", tag="show_me"), base_dir=str(tmp_dir))
    output = capsys.readouterr().out
    data = json.loads(output)
    assert data["tag"] == "show_me"


def test_cli_delete(tmp_dir, capsys):
    csv = _write_csv(tmp_dir / "data.csv", "x\n1\n")
    capture_snapshot(csv, "bye", base_dir=str(tmp_dir))
    handle_snapshot(_ns(snapshot_cmd="delete", tag="bye"), base_dir=str(tmp_dir))
    assert "deleted" in capsys.readouterr().out
