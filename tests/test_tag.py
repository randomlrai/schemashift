"""Tests for schemashift.tag — baseline tagging feature."""
import pytest

from schemashift.baseline import save_baseline
from schemashift.tag import add_tag, find_by_tag, get_tags, remove_tag

_SCHEMA = {"id": "integer", "name": "string"}


@pytest.fixture()
def store(tmp_path):
    d = str(tmp_path / "baselines")
    save_baseline("users_v1", _SCHEMA, store_dir=d)
    save_baseline("orders_v1", _SCHEMA, store_dir=d)
    return d


def test_add_tag_and_get_tags(store):
    add_tag("users_v1", "production", store_dir=store)
    assert "production" in get_tags("users_v1", store_dir=store)


def test_add_duplicate_tag_is_idempotent(store):
    add_tag("users_v1", "stable", store_dir=store)
    add_tag("users_v1", "stable", store_dir=store)
    assert get_tags("users_v1", store_dir=store).count("stable") == 1


def test_add_multiple_tags(store):
    add_tag("users_v1", "production", store_dir=store)
    add_tag("users_v1", "reviewed", store_dir=store)
    tags = get_tags("users_v1", store_dir=store)
    assert "production" in tags
    assert "reviewed" in tags


def test_remove_existing_tag_returns_true(store):
    add_tag("users_v1", "draft", store_dir=store)
    result = remove_tag("users_v1", "draft", store_dir=store)
    assert result is True
    assert "draft" not in get_tags("users_v1", store_dir=store)


def test_remove_nonexistent_tag_returns_false(store):
    result = remove_tag("users_v1", "nonexistent", store_dir=store)
    assert result is False


def test_get_tags_empty_for_untagged_baseline(store):
    assert get_tags("orders_v1", store_dir=store) == []


def test_find_by_tag_single_match(store):
    add_tag("users_v1", "production", store_dir=store)
    matches = find_by_tag("production", store_dir=store)
    assert matches == ["users_v1"]


def test_find_by_tag_multiple_matches(store):
    add_tag("users_v1", "approved", store_dir=store)
    add_tag("orders_v1", "approved", store_dir=store)
    matches = find_by_tag("approved", store_dir=store)
    assert set(matches) == {"users_v1", "orders_v1"}


def test_find_by_tag_no_match(store):
    assert find_by_tag("ghost", store_dir=store) == []


def test_add_tag_missing_baseline_raises(store):
    with pytest.raises(FileNotFoundError):
        add_tag("does_not_exist", "tag", store_dir=store)
