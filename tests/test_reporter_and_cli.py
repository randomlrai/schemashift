"""Tests for schemashift.reporter and schemashift.cli."""

from __future__ import annotations

import io
import json
import os
import textwrap
from pathlib import Path

import pytest

from schemashift.drift_detector import DriftReport, detect_drift
from schemashift.reporter import format_text, format_json, write_report
from schemashift.cli import main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _report_with_drift() -> DriftReport:
    old = {"id": "integer", "name": "string", "age": "integer"}
    new = {"id": "integer", "name": "string", "email": "string", "age": "string"}
    return detect_drift(old, new)


def _report_no_drift() -> DriftReport:
    schema = {"id": "integer", "name": "string"}
    return detect_drift(schema, schema)


# ---------------------------------------------------------------------------
# reporter tests
# ---------------------------------------------------------------------------

def test_format_text_no_drift():
    text = format_text(_report_no_drift())
    assert "No schema drift" in text


def test_format_text_with_drift():
    text = format_text(_report_with_drift())
    assert "Schema drift detected" in text
    assert "email" in text
    assert "age" in text
    assert "integer" in text
    assert "string" in text


def test_format_json_no_drift():
    data = json.loads(format_json(_report_no_drift()))
    assert data["has_drift"] is False
    assert data["added_fields"] == []
    assert data["removed_fields"] == []
    assert data["type_changes"] == {}


def test_format_json_with_drift():
    data = json.loads(format_json(_report_with_drift()))
    assert data["has_drift"] is True
    assert "email" in data["added_fields"]
    assert data["type_changes"]["age"] == {"from": "integer", "to": "string"}


def test_write_report_text(capsys):
    write_report(_report_no_drift(), fmt="text")
    captured = capsys.readouterr()
    assert "No schema drift" in captured.out


def test_write_report_json_stream():
    buf = io.StringIO()
    write_report(_report_with_drift(), fmt="json", output=buf)
    data = json.loads(buf.getvalue())
    assert data["has_drift"] is True


def test_write_report_unknown_format():
    with pytest.raises(ValueError, match="Unknown format"):
        write_report(_report_no_drift(), fmt="xml")


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

def test_cli_no_drift(tmp_path):
    v1 = tmp_path / "v1.csv"
    v2 = tmp_path / "v2.csv"
    v1.write_text("id,name\n1,Alice\n")
    v2.write_text("id,name\n2,Bob\n")
    rc = main([str(v1), str(v2)])
    assert rc == 0


def test_cli_drift_exit_code(tmp_path):
    v1 = tmp_path / "v1.csv"
    v2 = tmp_path / "v2.csv"
    v1.write_text("id,name\n1,Alice\n")
    v2.write_text("id,email\n2,a@b.com\n")
    rc = main([str(v1), str(v2), "--exit-code"])
    assert rc == 1


def test_cli_json_output(tmp_path, capsys):
    v1 = tmp_path / "v1.csv"
    v2 = tmp_path / "v2.csv"
    v1.write_text("id,name\n1,Alice\n")
    v2.write_text("id,email\n2,a@b.com\n")
    main([str(v1), str(v2), "--format", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["has_drift"] is True


def test_cli_missing_file(tmp_path, capsys):
    rc = main([str(tmp_path / "missing.csv"), str(tmp_path / "also_missing.csv")])
    assert rc == 2
    captured = capsys.readouterr()
    assert "Error" in captured.err
