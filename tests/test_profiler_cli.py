"""Tests for schemashift.profiler_cli."""
import argparse
import json
import textwrap
from pathlib import Path

import pytest

from schemashift.profiler_cli import _add_profile_parser, handle_profile


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write_csv(path: Path, content: str) -> str:
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return str(path)


def _ns(file: str, fmt: str = "text", output=None) -> argparse.Namespace:
    return argparse.Namespace(file=file, fmt=fmt, output=output)


def test_handle_profile_text_stdout(tmp_dir, capsys):
    f = _write_csv(tmp_dir / "d.csv", "id,name\n1,Alice\n2,Bob\n")
    handle_profile(_ns(f))
    out = capsys.readouterr().out
    assert "Rows" in out
    assert "id" in out
    assert "name" in out


def test_handle_profile_json_stdout(tmp_dir, capsys):
    f = _write_csv(tmp_dir / "d.csv", "a,b\n1,2\n")
    handle_profile(_ns(f, fmt="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "row_count" in data
    assert "fields" in data


def test_handle_profile_writes_file(tmp_dir):
    f = _write_csv(tmp_dir / "d.csv", "x\n10\n20\n")
    out_path = str(tmp_dir / "profile.txt")
    handle_profile(_ns(f, output=out_path))
    content = Path(out_path).read_text()
    assert "Rows" in content


def test_handle_profile_json_to_file(tmp_dir):
    f = _write_csv(tmp_dir / "d.csv", "col\nval\n")
    out_path = str(tmp_dir / "profile.json")
    handle_profile(_ns(f, fmt="json", output=out_path))
    data = json.loads(Path(out_path).read_text())
    assert data["row_count"] == 1


def test_handle_profile_missing_file(tmp_dir, capsys):
    with pytest.raises(SystemExit) as exc_info:
        handle_profile(_ns(str(tmp_dir / "missing.csv")))
    assert exc_info.value.code == 1
    assert "Error" in capsys.readouterr().err


def test_add_profile_parser_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    _add_profile_parser(sub)
    args = parser.parse_args(["profile", "myfile.csv"])
    assert args.file == "myfile.csv"
    assert args.fmt == "text"


def test_add_profile_parser_json_format():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    _add_profile_parser(sub)
    args = parser.parse_args(["profile", "myfile.csv", "--format", "json"])
    assert args.fmt == "json"
