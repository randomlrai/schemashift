"""Tests for schemashift.exporter."""

from __future__ import annotations

import csv
import io
import json
import os
import textwrap

import pytest

from schemashift.exporter import (
    export_csv,
    export_json,
    export_markdown,
    write_export,
)

SAMPLE: dict[str, str] = {"id": "integer", "name": "string", "score": "float"}


def test_export_json_is_valid_json():
    raw = export_json(SAMPLE)
    parsed = json.loads(raw)
    assert parsed == SAMPLE


def test_export_json_indented():
    raw = export_json(SAMPLE, indent=4)
    assert "    " in raw  # 4-space indent present


def test_export_csv_has_header_and_rows():
    raw = export_csv(SAMPLE)
    reader = csv.DictReader(io.StringIO(raw))
    rows = list(reader)
    assert reader.fieldnames == ["field", "type"]
    fields_in_csv = {r["field"]: r["type"] for r in rows}
    assert fields_in_csv == SAMPLE


def test_export_markdown_contains_header_row():
    raw = export_markdown(SAMPLE)
    assert "| Field | Type |" in raw
    assert "|-------|------|" in raw


def test_export_markdown_contains_all_fields():
    raw = export_markdown(SAMPLE)
    for field, ftype in SAMPLE.items():
        assert field in raw
        assert ftype in raw


def test_write_export_json(tmp_path):
    dest = str(tmp_path / "schema.json")
    write_export(SAMPLE, dest, fmt="json")
    with open(dest, encoding="utf-8") as fh:
        parsed = json.load(fh)
    assert parsed == SAMPLE


def test_write_export_csv(tmp_path):
    dest = str(tmp_path / "schema.csv")
    write_export(SAMPLE, dest, fmt="csv")
    with open(dest, encoding="utf-8") as fh:
        content = fh.read()
    assert "field,type" in content


def test_write_export_markdown(tmp_path):
    dest = str(tmp_path / "schema.md")
    write_export(SAMPLE, dest, fmt="markdown")
    with open(dest, encoding="utf-8") as fh:
        content = fh.read()
    assert "| Field | Type |" in content


def test_write_export_unknown_format_raises():
    with pytest.raises(ValueError, match="Unknown export format"):
        write_export(SAMPLE, "/tmp/x.txt", fmt="xml")
