from __future__ import annotations

from pathlib import Path

import pytest

import pymdtools.filetools as filetools


def test_get_template_files_in_folder_lists_files(tmp_path: Path, monkeypatch):
    # Fake module location
    fake_module = tmp_path / "filetools.py"
    fake_module.write_text("#", encoding="utf-8")

    monkeypatch.setattr(filetools, "_get_this_filename", lambda: str(fake_module))

    # Create template folder structure: <module_dir>/template/emails
    template_dir = tmp_path / "template" / "emails"
    template_dir.mkdir(parents=True)

    (template_dir / "a.html").write_text("a", encoding="utf-8")
    (template_dir / "b.html").write_text("b", encoding="utf-8")
    (template_dir / "subdir").mkdir()  # should be ignored

    out = filetools.get_template_files_in_folder("emails")

    # Sorted and POSIX-style
    assert out == ["emails/a.html", "emails/b.html"]


def test_get_template_files_in_folder_raises_if_missing(tmp_path: Path, monkeypatch):
    fake_module = tmp_path / "filetools.py"
    fake_module.write_text("#", encoding="utf-8")

    monkeypatch.setattr(filetools, "_get_this_filename", lambda: str(fake_module))

    with pytest.raises(FileNotFoundError):
        filetools.get_template_files_in_folder("emails")