"""Tests for schemashift.profiler."""
import json
import textwrap
from pathlib import Path

import pytest

from schemashift.profiler import (
    DataProfile,
    FieldProfile,
    profile,
    profile_csv,
    profile_json,
)


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write_csv(path: Path, content: str) -> str:
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return str(path)


def _write_json(path: Path, data) -> str:
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


def test_profile_csv_row_count(tmp_dir):
    f = _write_csv(
        tmp_dir / "data.csv",
        """\
        id,name,age
        1,Alice,30
        2,Bob,
        3,Carol,25
        """,
    )
    dp = profile_csv(f)
    assert dp.row_count == 3


def test_profile_csv_field_names(tmp_dir):
    f = _write_csv(
        tmp_dir / "data.csv",
        """\
        id,name,age
        1,Alice,30
        """,
    )
    dp = profile_csv(f)
    names = [fp.name for fp in dp.fields]
    assert names == ["id", "name", "age"]


def test_profile_csv_null_count(tmp_dir):
    f = _write_csv(
        tmp_dir / "data.csv",
        """\
        id,name,age
        1,Alice,30
        2,,
        3,Carol,25
        """,
    )
    dp = profile_csv(f)
    name_fp = next(fp for fp in dp.fields if fp.name == "name")
    assert name_fp.null_count == 1
    assert name_fp.null_rate == pytest.approx(1 / 3)


def test_profile_csv_unique_count(tmp_dir):
    f = _write_csv(
        tmp_dir / "data.csv",
        """\
        status
        active
        inactive
        active
        """,
    )
    dp = profile_csv(f)
    assert dp.fields[0].unique_count == 2


def test_profile_json_row_count(tmp_dir):
    data = [{"id": 1, "val": "a"}, {"id": 2, "val": "b"}]
    f = _write_json(tmp_dir / "data.json", data)
    dp = profile_json(f)
    assert dp.row_count == 2


def test_profile_json_null_count(tmp_dir):
    data = [{"x": 1}, {"x": None}, {"x": 3}]
    f = _write_json(tmp_dir / "data.json", data)
    dp = profile_json(f)
    assert dp.fields[0].null_count == 1


def test_profile_auto_detect_csv(tmp_dir):
    f = _write_csv(tmp_dir / "d.csv", "a,b\n1,2\n")
    dp = profile(f)
    assert isinstance(dp, DataProfile)


def test_profile_auto_detect_json(tmp_dir):
    f = _write_json(tmp_dir / "d.json", [{"k": "v"}])
    dp = profile(f)
    assert isinstance(dp, DataProfile)


def test_profile_unsupported_extension(tmp_dir):
    bad = tmp_dir / "data.parquet"
    bad.write_text("")
    with pytest.raises(ValueError, match="Unsupported"):
        profile(str(bad))


def test_field_profile_to_dict():
    fp = FieldProfile(name="col", inferred_type="integer", null_count=1, total_count=4, unique_count=3, sample_values=[1, 2, 3])
    d = fp.to_dict()
    assert d["name"] == "col"
    assert d["null_rate"] == pytest.approx(0.25)


def test_data_profile_to_dict(tmp_dir):
    f = _write_csv(tmp_dir / "d.csv", "x\n1\n2\n")
    dp = profile_csv(f)
    d = dp.to_dict()
    assert "source" in d
    assert "row_count" in d
    assert isinstance(d["fields"], list)
