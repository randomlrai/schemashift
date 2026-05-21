"""Tests for schemashift.exporter_cli (handle_export)."""

from __future__ import annotations

import argparse
import json
import os

import pytest

from schemashift.exporter_cli import handle_export, _add_export_parser


@pytest.fixture()
def tmp_dir(tmp_path):
    return tmp_path


def _write_csv(path: str, rows: list[str]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(rows) + "\n")


def _ns(**kwargs) -> argparse.Namespace:
    defaults = {"file": "", "fmt": "json", "output": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_export_to_stdout_json(tmp_dir, capsys):
    src = str(tmp_dir / "data.csv")
    _write_csv(src, ["id,name", "1,Alice", "2,Bob"])
    rc = handle_export(_ns(file=src, fmt="json", output=None))
    assert rc == 0
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert "id" in parsed
    assert "name" in parsed


def test_export_to_stdout_csv(tmp_dir, capsys):
    src = str(tmp_dir / "data.csv")
    _write_csv(src, ["id,name", "1,Alice"])
    rc = handle_export(_ns(file=src, fmt="csv", output=None))
    assert rc == 0
    out = capsys.readouterr().out
    assert "field,type" in out


def test_export_to_stdout_markdown(tmp_dir, capsys):
    src = str(tmp_dir / "data.csv")
    _write_csv(src, ["id,name", "1,Alice"])
    rc = handle_export(_ns(file=src, fmt="markdown", output=None))
    assert rc == 0
    out = capsys.readouterr().out
    assert "| Field | Type |" in out


def test_export_to_file(tmp_dir):
    src = str(tmp_dir / "data.csv")
    dest = str(tmp_dir / "out.json")
    _write_csv(src, ["id,value", "1,99"])
    rc = handle_export(_ns(file=src, fmt="json", output=dest))
    assert rc == 0
    assert os.path.exists(dest)
    with open(dest) as fh:
        parsed = json.load(fh)
    assert "id" in parsed


def test_export_missing_file_returns_error(capsys):
    rc = handle_export(_ns(file="/nonexistent/data.csv", fmt="json", output=None))
    assert rc == 1
    err = capsys.readouterr().err
    assert "error" in err.lower()


def test_add_export_parser_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    _add_export_parser(sub)
    ns = parser.parse_args(["export", "myfile.csv", "--format", "csv"])
    assert ns.fmt == "csv"
    assert ns.file == "myfile.csv"
