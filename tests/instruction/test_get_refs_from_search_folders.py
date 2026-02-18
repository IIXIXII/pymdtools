from __future__ import annotations

from pathlib import Path

from pymdtools.instruction import get_refs_from_search_folders


def _write_text(p: Path, name: str, content: str) -> Path:
    f = p / name
    f.write_text(content, encoding="utf-8")
    return f


def test_get_refs_from_search_folders_single_folder(tmp_path: Path):
    f1 = tmp_path / "f1"
    f1.mkdir()

    _write_text(f1, "a.md", "<!-- begin-ref(a) -->A<!-- end-ref -->")

    out = get_refs_from_search_folders([f1], filename_ext=".md", depth=-1)
    assert out == {"a": "A"}


def test_get_refs_from_search_folders_multiple_folders(tmp_path: Path):
    f1 = tmp_path / "f1"
    f2 = tmp_path / "f2"
    f1.mkdir()
    f2.mkdir()

    _write_text(f1, "a.md", "<!-- begin-ref(a) -->A<!-- end-ref -->")
    _write_text(f2, "b.md", "<!-- begin-ref(b) -->B<!-- end-ref -->")

    out = get_refs_from_search_folders([f1, f2], filename_ext=".md", depth=-1)
    assert out == {"a": "A", "b": "B"}


def test_get_refs_from_search_folders_extends_existing_refs(tmp_path: Path):
    f1 = tmp_path / "f1"
    f1.mkdir()

    _write_text(f1, "b.md", "<!-- begin-ref(b) -->B<!-- end-ref -->")

    out = get_refs_from_search_folders([f1], refs={"a": "A"}, filename_ext=".md", depth=-1)
    assert out == {"a": "A", "b": "B"}


def test_get_refs_from_search_folders_respects_depth(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "sub").mkdir()

    _write_text(root, "a.md", "<!-- begin-ref(a) -->A<!-- end-ref -->")
    _write_text(root / "sub", "b.md", "<!-- begin-ref(b) -->B<!-- end-ref -->")

    # depth=0: only current directory
    out0 = get_refs_from_search_folders([root], filename_ext=".md", depth=0)
    assert out0 == {"a": "A"}

    # depth=1: include one level
    out1 = get_refs_from_search_folders([root], filename_ext=".md", depth=1)
    assert out1 == {"a": "A", "b": "B"}


def test_get_refs_from_search_folders_respects_filename_ext(tmp_path: Path):
    f1 = tmp_path / "f1"
    f1.mkdir()

    _write_text(f1, "a.txt", "<!-- begin-ref(a) -->A<!-- end-ref -->")

    out = get_refs_from_search_folders([f1], filename_ext=".txt", depth=-1)
    assert out == {"a": "A"}
