"""Schema tagging — attach and query user-defined tags on saved baselines."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from schemashift.baseline import _baseline_path, load_baseline, save_baseline

_TAG_INDEX_NAME = "_tag_index.json"


def _tag_index_path(store_dir: str) -> Path:
    return Path(store_dir) / _TAG_INDEX_NAME


def _load_index(store_dir: str) -> Dict[str, List[str]]:
    """Return mapping of baseline_name -> list[tag]."""
    p = _tag_index_path(store_dir)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_index(store_dir: str, index: Dict[str, List[str]]) -> None:
    p = _tag_index_path(store_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(index, indent=2))


def add_tag(name: str, tag: str, store_dir: str) -> None:
    """Add *tag* to baseline *name*.  Raises FileNotFoundError if missing."""
    load_baseline(name, store_dir=store_dir)  # validate existence
    index = _load_index(store_dir)
    tags = index.setdefault(name, [])
    if tag not in tags:
        tags.append(tag)
    _save_index(store_dir, index)


def remove_tag(name: str, tag: str, store_dir: str) -> bool:
    """Remove *tag* from baseline *name*.  Returns True if tag existed."""
    index = _load_index(store_dir)
    tags = index.get(name, [])
    if tag not in tags:
        return False
    tags.remove(tag)
    index[name] = tags
    _save_index(store_dir, index)
    return True


def get_tags(name: str, store_dir: str) -> List[str]:
    """Return all tags for baseline *name*."""
    return list(_load_index(store_dir).get(name, []))


def find_by_tag(tag: str, store_dir: str) -> List[str]:
    """Return baseline names that carry *tag*."""
    return [name for name, tags in _load_index(store_dir).items() if tag in tags]
