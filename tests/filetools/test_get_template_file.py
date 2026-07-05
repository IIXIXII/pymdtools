from __future__ import annotations

from pathlib import Path

import pytest

import pymdtools.filetools as filetools


def test_get_template_file_reads_content_from_start_folder(tmp_path: Path):
    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "a.txt").write_text("hello", encoding="utf-8")

    content = filetools.get_template_file("a.txt", start_folder=tmp_path)
    assert content == "hello"


def test_get_template_file_raises_if_template_folder_missing(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        filetools.get_template_file("a.txt", start_folder=tmp_path)


def test_get_template_file_raises_on_empty_filename(tmp_path: Path):
    (tmp_path / "template").mkdir()
    with pytest.raises(ValueError):
        filetools.get_template_file("", start_folder=tmp_path)


def test_get_template_file_supports_subpaths(tmp_path: Path):
    template_dir = tmp_path / "template" / "sub"
    template_dir.mkdir(parents=True)
    (template_dir / "a.txt").write_text("ok", encoding="utf-8")

    content = filetools.get_template_file("sub/a.txt", start_folder=tmp_path)
    assert content == "ok"


def test_get_template_file_rejects_absolute_filename(tmp_path: Path):
    (tmp_path / "template").mkdir()
    absolute = tmp_path / "template" / "a.txt"

    with pytest.raises(ValueError, match="relative path"):
        filetools.get_template_file(absolute, start_folder=tmp_path)


def test_get_template_file_rejects_parent_traversal(tmp_path: Path):
    (tmp_path / "template").mkdir()

    with pytest.raises(ValueError, match="path traversal"):
        filetools.get_template_file("../secret.txt", start_folder=tmp_path)


def test_get_template_file_accepts_file_start_folder(tmp_path: Path):
    module_file = tmp_path / "module.py"
    module_file.write_text("#", encoding="utf-8")
    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "a.txt").write_text("ok", encoding="utf-8")

    assert filetools.get_template_file("a.txt", start_folder=module_file) == "ok"


def test_get_template_file_rejects_empty_path_object(tmp_path: Path):
    (tmp_path / "template").mkdir()

    class EmptyPath:
        def __fspath__(self) -> str:
            return ""

        def __str__(self) -> str:
            return ""

    with pytest.raises(ValueError, match="non-empty path"):
        filetools.get_template_file(EmptyPath(), start_folder=tmp_path)


def test_get_template_file_missing_file_raises(tmp_path: Path):
    (tmp_path / "template").mkdir()

    with pytest.raises(FileNotFoundError):
        filetools.get_template_file("missing.txt", start_folder=tmp_path)


def test_get_template_file_detects_resolved_escape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "a.txt").write_text("ok", encoding="utf-8")

    real_resolve = Path.resolve

    def fake_resolve(self: Path, *args, **kwargs) -> Path:
        if self == template_dir / "a.txt":
            return tmp_path / "outside.txt"
        return real_resolve(self, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", fake_resolve)

    with pytest.raises(ValueError, match="escapes template directory"):
        filetools.get_template_file("a.txt", start_folder=tmp_path)


def test_get_template_file_start_folder_missing_with_suffix_uses_parent(tmp_path: Path):
    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "a.txt").write_text("ok", encoding="utf-8")

    assert filetools.get_template_file("a.txt", start_folder=tmp_path / "missing.py") == "ok"


def test_get_template_file_start_folder_directory_without_suffix(tmp_path: Path):
    template_dir = tmp_path / "folder" / "template"
    template_dir.mkdir(parents=True)
    (template_dir / "a.txt").write_text("ok", encoding="utf-8")

    assert filetools.get_template_file("a.txt", start_folder=tmp_path / "folder") == "ok"


def test_get_template_file_start_folder_missing_without_suffix_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        filetools.get_template_file("a.txt", start_folder=tmp_path / "missing_folder")
