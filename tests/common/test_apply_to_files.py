from pathlib import Path

import pytest

from pymdtools.common import apply_to_files


def test_apply_to_files_processes_matching_extension(tmp_path):
    (tmp_path / "a.md").write_text("x", encoding="utf-8")
    (tmp_path / "b.txt").write_text("y", encoding="utf-8")
    (tmp_path / "c.MD").write_text("z", encoding="utf-8")

    seen = []

    def process(p: str) -> None:
        seen.append(Path(p).name)

    n = apply_to_files(tmp_path, process, ext=".md", recursive=False, case_sensitive=False, sort=True)

    assert n == 2
    assert seen == ["a.md", "c.MD"]


def test_apply_to_files_recursive(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "a.md").write_text("x", encoding="utf-8")

    seen = []
    n = apply_to_files(tmp_path, lambda p: seen.append(p), ext=".md", recursive=True)

    assert n == 1
    assert Path(seen[0]).name == "a.md"


def test_apply_to_files_non_recursive(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "a.md").write_text("x", encoding="utf-8")

    n = apply_to_files(tmp_path, lambda _p: None, ext=".md", recursive=False)
    assert n == 0


def test_apply_to_files_invalid_ext_raises(tmp_path):
    with pytest.raises(ValueError):
        apply_to_files(tmp_path, lambda _p: None, ext="md")


def test_apply_to_files_missing_folder_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        apply_to_files(tmp_path / "missing", lambda _p: None)
