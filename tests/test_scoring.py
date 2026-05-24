"""Tests for schemashift.scoring and schemashift.scoring_cli."""
from __future__ import annotations

import io
import json
import textwrap
import types

import pytest

from schemashift.scoring import (
    ScoreBreakdown,
    _field_count_score,
    _naming_score,
    _type_coverage,
    score_schema,
)
from schemashift.scoring_cli import handle_score


# ---------------------------------------------------------------------------
# Unit tests for individual helpers
# ---------------------------------------------------------------------------

def test_type_coverage_all_known():
    schema = {"id": "integer", "name": "string", "active": "boolean"}
    assert _type_coverage(schema) == 1.0


def test_type_coverage_some_unknown():
    schema = {"id": "integer", "meta": "custom_type"}
    assert _type_coverage(schema) == pytest.approx(0.5)


def test_type_coverage_empty():
    assert _type_coverage({}) == 0.0


def test_naming_score_all_snake():
    schema = {"user_id": "integer", "first_name": "string"}
    assert _naming_score(schema) == 1.0


def test_naming_score_mixed():
    schema = {"userId": "integer", "first_name": "string"}
    assert _naming_score(schema) == pytest.approx(0.5)


def test_naming_score_empty():
    assert _naming_score({}) == 0.0


def test_field_count_score_small():
    schema = {f"f{i}": "string" for i in range(10)}
    assert _field_count_score(schema) == 1.0


def test_field_count_score_exactly_50():
    schema = {f"f{i}": "string" for i in range(50)}
    assert _field_count_score(schema) == 1.0


def test_field_count_score_large():
    schema = {f"f{i}": "string" for i in range(200)}
    assert _field_count_score(schema) == pytest.approx(0.0)


def test_field_count_score_zero_fields():
    assert _field_count_score({}) == 0.0


# ---------------------------------------------------------------------------
# score_schema integration
# ---------------------------------------------------------------------------

def test_perfect_schema_scores_one():
    schema = {"id": "integer", "name": "string", "is_active": "boolean"}
    result = score_schema(schema)
    assert result.overall == pytest.approx(1.0)
    assert result.notes == []


def test_empty_schema_scores_zero():
    result = score_schema({})
    assert result.overall == 0.0
    assert any("no fields" in n for n in result.notes)


def test_bad_naming_adds_note():
    schema = {"UserID": "integer", "FirstName": "string"}
    result = score_schema(schema)
    assert result.naming_convention == 0.0
    assert any("snake_case" in n for n in result.notes)


def test_custom_weights_applied():
    schema = {"id": "integer", "name": "string"}
    default = score_schema(schema)
    custom = score_schema(schema, weights={"type_coverage": 1.0, "naming_convention": 0.0, "field_count": 0.0})
    # With all weight on type_coverage (1.0) and perfect coverage, score == 1.0
    assert custom.overall == pytest.approx(1.0)
    assert default.overall == pytest.approx(1.0)


def test_to_dict_keys():
    result = score_schema({"age": "integer"})
    d = result.to_dict()
    assert set(d.keys()) == {"type_coverage", "naming_convention", "field_count_score", "overall", "notes"}


# ---------------------------------------------------------------------------
# CLI handler tests
# ---------------------------------------------------------------------------

def _ns(file, fmt="text", wt=0.5, wn=0.3, wf=0.2):
    return types.SimpleNamespace(file=file, fmt=fmt, weight_type=wt, weight_naming=wn, weight_fields=wf)


def _write_csv(path, rows):
    path.write_text("\n".join(rows))


def test_handle_score_text_output(tmp_path):
    csv_file = tmp_path / "data.csv"
    _write_csv(csv_file, ["id,name,active", "1,Alice,true"])
    buf = io.StringIO()
    rc = handle_score(_ns(str(csv_file)), out=buf)
    assert rc == 0
    output = buf.getvalue()
    assert "Overall score" in output
    assert "type_coverage" in output


def test_handle_score_json_output(tmp_path):
    csv_file = tmp_path / "data.csv"
    _write_csv(csv_file, ["id,name", "1,Alice"])
    buf = io.StringIO()
    rc = handle_score(_ns(str(csv_file), fmt="json"), out=buf)
    assert rc == 0
    data = json.loads(buf.getvalue())
    assert "overall" in data
    assert "notes" in data


def test_handle_score_returns_zero_on_success(tmp_path):
    csv_file = tmp_path / "ok.csv"
    _write_csv(csv_file, ["user_id,email", "1,a@b.com"])
    rc = handle_score(_ns(str(csv_file)), out=io.StringIO())
    assert rc == 0
