# tests/test_with_suffix.py
from __future__ import annotations

from pathlib import Path
import pytest

from pymdtools.common import with_suffix


def test_with_suffix_replaces_existing_suffix_str_input(tmp_path: Path) -> None:
    p = tmp_path / "file.md"
    result = with_suffix(str(p), ".html")

    assert isinstance(result, Path)
    assert result.name == "file.html"
    assert result.parent == tmp_path


def test_with_suffix_replaces_existing_suffix_without_dot(tmp_path: Path) -> None:
    p = tmp_path / "file.md"
    result = with_suffix(p, "html")

    assert result.name == "file.html"


def test_with_suffix_adds_suffix_if_none(tmp_path: Path) -> None:
    p = tmp_path / "file"
    result = with_suffix(p, ".txt")

    assert result.name == "file.txt"


def test_with_suffix_multiple_suffixes(tmp_path: Path) -> None:
    p = tmp_path / "archive.tar.gz"
    result = with_suffix(p, ".zip")

    # Path.with_suffix replaces only the last suffix
    assert result.name == "archive.tar.zip"


def test_with_suffix_preserves_parent(tmp_path: Path) -> None:
    p = tmp_path / "subdir" / "file.md"
    result = with_suffix(p, ".html")

    assert result.parent == tmp_path / "subdir"


def test_with_suffix_empty_suffix_raises(tmp_path: Path) -> None:
    p = tmp_path / "file.md"

    with pytest.raises(ValueError, match="Suffix must not be empty"):
        with_suffix(p, "")


def test_with_suffix_path_like_str(tmp_path: Path) -> None:
    p = tmp_path / "example.md"
    result = with_suffix(str(p), "pdf")

    assert result == tmp_path / "example.pdf"