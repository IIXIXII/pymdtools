from __future__ import annotations

from pathlib import Path

import pytest

import pymdtools.filetools as filetools


def test_get_template_files_in_folder_lists_files(tmp_path: Path):
    # Create template folder structure: <module_dir>/template/emails
    template_dir = tmp_path / "template" / "emails"
    template_dir.mkdir(parents=True)

    (template_dir / "a.html").write_text("a", encoding="utf-8")
    (template_dir / "b.html").write_text("b", encoding="utf-8")
    (template_dir / "subdir").mkdir()  # should be ignored

    out = filetools.get_template_files_in_folder("emails", start_folder=tmp_path)

    # Sorted and POSIX-style
    assert out == ["emails/a.html", "emails/b.html"]


def test_get_template_files_in_folder_raises_if_missing(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        filetools.get_template_files_in_folder("emails", start_folder=tmp_path)


def test_get_template_files_in_folder_rejects_parent_traversal(tmp_path: Path):
    (tmp_path / "template").mkdir()

    with pytest.raises(ValueError, match="path traversal"):
        filetools.get_template_files_in_folder("../secret", start_folder=tmp_path)


def test_get_template_files_in_folder_rejects_empty_folder(tmp_path: Path):
    (tmp_path / "template").mkdir()

    with pytest.raises(ValueError, match="non-empty"):
        filetools.get_template_files_in_folder("", start_folder=tmp_path)


def test_get_template_files_in_folder_uses_filetools_module_as_default_base(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(filetools, "__file__", str(tmp_path / "filetools.py"))
    folder = tmp_path / "template" / "emails"
    folder.mkdir(parents=True)
    (folder / "a.html").write_text("a", encoding="utf-8")

    assert filetools.get_template_files_in_folder("emails") == ["emails/a.html"]


def test_get_template_files_in_folder_rejects_resolved_folder_escape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    template_dir = tmp_path / "template"
    folder = template_dir / "emails"
    folder.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    original_resolve = Path.resolve

    def fake_resolve(self: Path, *args, **kwargs) -> Path:
        if self == folder:
            return outside
        return original_resolve(self, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", fake_resolve)

    with pytest.raises(ValueError, match="template folder escapes"):
        filetools.get_template_files_in_folder("emails", start_folder=tmp_path)


def test_get_template_files_in_folder_rejects_resolved_file_escape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    folder = tmp_path / "template" / "emails"
    folder.mkdir(parents=True)
    file = folder / "outside.html"
    file.write_text("placeholder", encoding="utf-8")
    outside = tmp_path / "outside.html"
    outside.write_text("outside", encoding="utf-8")
    original_resolve = Path.resolve

    def fake_resolve(self: Path, *args, **kwargs) -> Path:
        if self == file:
            return outside
        return original_resolve(self, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", fake_resolve)

    with pytest.raises(ValueError, match="template file escapes"):
        filetools.get_template_files_in_folder("emails", start_folder=tmp_path)
