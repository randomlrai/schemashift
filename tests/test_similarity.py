"""Tests for schemashift.similarity and schemashift.similarity_cli."""

from __future__ import annotations

import argparse
import json
import os

import pytest

from schemashift.similarity import SimilarityResult, compute_similarity
from schemashift.similarity_cli import handle_similarity


# ---------------------------------------------------------------------------
# compute_similarity unit tests
# ---------------------------------------------------------------------------

def test_identical_schemas_score_one():
    schema = {"id": "integer", "name": "string"}
    result = compute_similarity(schema, schema)
    assert result.overall_score == 1.0
    assert result.field_overlap == 1.0
    assert result.type_match_rate == 1.0


def test_completely_disjoint_schemas_score_zero():
    a = {"id": "integer"}
    b = {"email": "string"}
    result = compute_similarity(a, b)
    assert result.field_overlap == 0.0
    assert result.common_fields == 0
    assert result.overall_score == 0.0


def test_partial_overlap():
    a = {"id": "integer", "name": "string", "age": "integer"}
    b = {"id": "integer", "name": "string", "email": "string"}
    result = compute_similarity(a, b)
    # union = 4, common = 2 => jaccard = 0.5
    assert result.field_overlap == 0.5
    assert result.common_fields == 2
    assert result.type_matched_fields == 2
    assert result.type_match_rate == 1.0


def test_type_mismatch_reduces_type_match_rate():
    a = {"id": "integer", "value": "string"}
    b = {"id": "integer", "value": "float"}
    result = compute_similarity(a, b)
    assert result.type_matched_fields == 1
    assert result.type_match_rate == 0.5


def test_field_scores_present_for_all_fields():
    a = {"id": "integer", "only_a": "string"}
    b = {"id": "integer", "only_b": "string"}
    result = compute_similarity(a, b)
    assert "id" in result.field_scores
    assert "only_a" in result.field_scores
    assert "only_b" in result.field_scores
    assert result.field_scores["id"] == 1.0
    assert result.field_scores["only_a"] == 0.0
    assert result.field_scores["only_b"] == 0.0


def test_to_dict_keys():
    result = compute_similarity({"x": "string"}, {"x": "string"})
    d = result.to_dict()
    for key in ("overall_score", "field_overlap", "type_match_rate", "field_scores"):
        assert key in d


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_dir(tmp_path):
    return tmp_path


def _write_csv(path, rows):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(rows) + "\n")


def _ns(file_a, file_b, output_format="text", output=None):
    return argparse.Namespace(
        file_a=str(file_a),
        file_b=str(file_b),
        output_format=output_format,
        output=str(output) if output else None,
    )


def test_handle_similarity_text_stdout(tmp_dir, capsys):
    a = tmp_dir / "a.csv"
    b = tmp_dir / "b.csv"
    _write_csv(a, ["id,name", "1,Alice"])
    _write_csv(b, ["id,name", "2,Bob"])
    handle_similarity(_ns(a, b, "text"))
    out = capsys.readouterr().out
    assert "Overall score" in out
    assert "Field overlap" in out


def test_handle_similarity_json_stdout(tmp_dir, capsys):
    a = tmp_dir / "a.csv"
    b = tmp_dir / "b.csv"
    _write_csv(a, ["id,email", "1,a@b.com"])
    _write_csv(b, ["id,phone", "1,555"])
    handle_similarity(_ns(a, b, "json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "overall_score" in data
    assert data["common_fields"] == 1


def test_handle_similarity_writes_file(tmp_dir):
    a = tmp_dir / "a.csv"
    b = tmp_dir / "b.csv"
    out_file = tmp_dir / "result.json"
    _write_csv(a, ["id", "1"])
    _write_csv(b, ["id", "2"])
    handle_similarity(_ns(a, b, "json", output=out_file))
    assert out_file.exists()
    data = json.loads(out_file.read_text())
    assert "overall_score" in data
