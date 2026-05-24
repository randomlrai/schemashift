"""Tests for schemashift.enrichment."""

import pytest
from schemashift.enrichment import (
    FieldMeta,
    EnrichedSchema,
    enrich,
    save_enrichment,
    load_enrichment,
    list_enrichments,
)


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path / "enrichments")


_SCHEMA = {"id": "integer", "name": "string", "email": "string"}

_ANNOTATIONS = {
    "id": {"description": "Primary key", "owner": "platform", "examples": [1, 2]},
    "name": {"description": "Full name", "tags": ["pii"]},
}


def test_enrich_creates_enriched_schema():
    es = enrich(_SCHEMA, source="users.csv", annotations=_ANNOTATIONS)
    assert es.source == "users.csv"
    assert es.fields == _SCHEMA
    assert es.meta["id"].description == "Primary key"
    assert es.meta["id"].owner == "platform"
    assert es.meta["id"].examples == [1, 2]
    assert es.meta["name"].tags == ["pii"]


def test_enrich_missing_annotation_defaults_empty():
    es = enrich(_SCHEMA, source="users.csv", annotations={})
    assert es.meta["email"].description == ""
    assert es.meta["email"].owner == ""
    assert es.meta["email"].examples == []
    assert es.meta["email"].tags == []


def test_enrich_no_annotations_arg():
    es = enrich(_SCHEMA, source="users.csv")
    for fname in _SCHEMA:
        assert es.meta[fname].description == ""


def test_coverage_fully_described():
    annotations = {f: {"description": "desc"} for f in _SCHEMA}
    es = enrich(_SCHEMA, source="x", annotations=annotations)
    assert es.coverage() == pytest.approx(1.0)


def test_coverage_partially_described():
    es = enrich(_SCHEMA, source="x", annotations=_ANNOTATIONS)
    # 'id' and 'name' have descriptions; 'email' does not => 2/3
    assert es.coverage() == pytest.approx(2 / 3)


def test_coverage_empty_schema():
    es = enrich({}, source="x")
    assert es.coverage() == 0.0


def test_to_dict_structure():
    es = enrich(_SCHEMA, source="users.csv", annotations=_ANNOTATIONS)
    d = es.to_dict()
    assert d["source"] == "users.csv"
    assert "id" in d["fields"]
    assert d["meta"]["id"]["description"] == "Primary key"


def test_save_and_load_roundtrip(store):
    es = enrich(_SCHEMA, source="users.csv", annotations=_ANNOTATIONS)
    save_enrichment(es, store, "users_v1")
    loaded = load_enrichment(store, "users_v1")
    assert loaded.source == es.source
    assert loaded.fields == es.fields
    assert loaded.meta["id"].description == "Primary key"
    assert loaded.meta["name"].tags == ["pii"]


def test_load_missing_raises(store):
    with pytest.raises(FileNotFoundError):
        load_enrichment(store, "nonexistent")


def test_list_enrichments_empty(store):
    assert list_enrichments(store) == []


def test_list_enrichments_returns_names(store):
    es = enrich(_SCHEMA, source="x")
    save_enrichment(es, store, "alpha")
    save_enrichment(es, store, "beta")
    names = sorted(list_enrichments(store))
    assert names == ["alpha", "beta"]


def test_field_meta_to_dict():
    fm = FieldMeta(description="d", owner="eng", examples=[1], tags=["pii"])
    d = fm.to_dict()
    assert d == {"description": "d", "owner": "eng", "examples": [1], "tags": ["pii"]}
