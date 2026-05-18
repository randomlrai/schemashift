"""Tests for schemashift.baseline — save/load/list/delete baselines."""

import os
import pytest

from schemashift.baseline import (
    save_baseline,
    load_baseline,
    list_baselines,
    delete_baseline,
)

SAMPLE_SCHEMA = {"id": "integer", "name": "string", "email": "string"}


@pytest.fixture()
def tmp_dir(tmp_path):
    return str(tmp_path / "baselines")


def test_save_and_load_roundtrip(tmp_dir):
    path = save_baseline("users_v1", SAMPLE_SCHEMA, directory=tmp_dir)
    assert os.path.exists(path)
    payload = load_baseline("users_v1", directory=tmp_dir)
    assert payload["schema"] == SAMPLE_SCHEMA
    assert payload["name"] == "users_v1"
    assert "saved_at" in payload


def test_save_stores_metadata(tmp_dir):
    meta = {"source": "users.csv", "version": "1.0"}
    save_baseline("users_v2", SAMPLE_SCHEMA, directory=tmp_dir, metadata=meta)
    payload = load_baseline("users_v2", directory=tmp_dir)
    assert payload["metadata"] == meta


def test_load_missing_raises(tmp_dir):
    with pytest.raises(FileNotFoundError, match="no_such"):
        load_baseline("no_such", directory=tmp_dir)


def test_list_baselines_empty(tmp_dir):
    assert list_baselines(tmp_dir) == []


def test_list_baselines_returns_names(tmp_dir):
    save_baseline("alpha", SAMPLE_SCHEMA, directory=tmp_dir)
    save_baseline("beta", SAMPLE_SCHEMA, directory=tmp_dir)
    names = list_baselines(tmp_dir)
    assert names == ["alpha", "beta"]


def test_list_baselines_nonexistent_dir():
    assert list_baselines("/nonexistent/path/xyz") == []


def test_delete_existing_baseline(tmp_dir):
    save_baseline("to_delete", SAMPLE_SCHEMA, directory=tmp_dir)
    result = delete_baseline("to_delete", directory=tmp_dir)
    assert result is True
    assert "to_delete" not in list_baselines(tmp_dir)


def test_delete_missing_baseline(tmp_dir):
    result = delete_baseline("ghost", directory=tmp_dir)
    assert result is False


def test_overwrite_baseline(tmp_dir):
    save_baseline("users", SAMPLE_SCHEMA, directory=tmp_dir)
    new_schema = {"id": "integer", "username": "string"}
    save_baseline("users", new_schema, directory=tmp_dir)
    payload = load_baseline("users", directory=tmp_dir)
    assert payload["schema"] == new_schema


def test_name_with_spaces_saved_safely(tmp_dir):
    save_baseline("my dataset v1", SAMPLE_SCHEMA, directory=tmp_dir)
    payload = load_baseline("my dataset v1", directory=tmp_dir)
    assert payload["schema"] == SAMPLE_SCHEMA
