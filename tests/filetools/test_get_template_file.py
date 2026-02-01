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
