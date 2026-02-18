from __future__ import annotations

from pathlib import Path

import pytest

from pymdtools.instruction import get_refs_from_md_directory


def _write_text(p: Path, name: str, content: str) -> Path:
    f = p / name
    f.write_text(content, encoding="utf-8")
    return f


def test_get_refs_from_md_directory_depth_0_only_current_level(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "sub").mkdir()

    _write_text(root, "a.md", "<!-- begin-ref(a) -->A<!-- end-ref -->")
    _write_text(root / "sub", "b.md", "<!-- begin-ref(b) -->B<!-- end-ref -->")

    out = get_refs_from_md_directory(root, filename_ext=".md", depth=0)
    assert out == {"a": "A"}


def test_get_refs_from_md_directory_depth_1_includes_one_level(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "sub").mkdir()

    _write_text(root, "a.md", "<!-- begin-ref(a) -->A<!-- end-ref -->")
    _write_text(root / "sub", "b.md", "<!-- begin-ref(b) -->B<!-- end-ref -->")

    out = get_refs_from_md_directory(root, filename_ext=".md", depth=1)
    assert out == {"a": "A", "b": "B"}


def test_get_refs_from_md_directory_depth_unlimited(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "sub" / "deep").mkdir(parents=True)

    _write_text(root, "a.md", "<!-- begin-ref(a) -->A<!-- end-ref -->")
    _write_text(root / "sub", "b.md", "<!-- begin-ref(b) -->B<!-- end-ref -->")
    _write_text(root / "sub" / "deep", "c.md", "<!-- begin-ref(c) -->C<!-- end-ref -->")

    out = get_refs_from_md_directory(root, filename_ext=".md", depth=-1)
    assert out == {"a": "A", "b": "B", "c": "C"}


def test_get_refs_from_md_directory_respects_filename_ext_in_subfolders(tmp_path: Path):
    # Regression test: filename_ext must be propagated (not forced to ".md")
    root = tmp_path / "root"
    root.mkdir()
    (root / "sub").mkdir()

    _write_text(root, "a.txt", "<!-- begin-ref(a) -->A<!-- end-ref -->")
    _write_text(root / "sub", "b.txt", "<!-- begin-ref(b) -->B<!-- end-ref -->")

    out = get_refs_from_md_directory(root, filename_ext=".txt", depth=-1)
    assert out == {"a": "A", "b": "B"}


def test_get_refs_from_md_directory_raises_on_missing_folder(tmp_path: Path):
    missing = tmp_path / "missing"
    with pytest.raises(Exception):
        get_refs_from_md_directory(missing, filename_ext=".md", depth=0)
