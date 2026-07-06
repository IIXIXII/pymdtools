from __future__ import annotations

from pathlib import Path

import pytest

import pymdtools.normalize as normalize


def test_md_beautifier_normalizes_markdown_text() -> None:
    assert normalize.md_beautifier("# Title\n\nBody\n\n") == "# Title\n\nBody"


def test_md_beautifier_rejects_non_string() -> None:
    with pytest.raises(TypeError, match="text must be a string"):
        normalize.md_beautifier(123)


def test_md_file_beautifier_updates_file_and_returns_checked_filename(tmp_path: Path) -> None:
    source = tmp_path / "doc.md"
    source.write_text("# Title\n\nBody\n\n", encoding="utf-8")

    returned = normalize.md_file_beautifier(source, backup_option=False)

    assert Path(returned) == source.resolve()
    assert source.read_text(encoding="utf-8") == "# Title\n\nBody"
    assert not list(tmp_path.glob("doc.md.*.bak"))


def test_md_file_beautifier_creates_backup(tmp_path: Path) -> None:
    source = tmp_path / "doc.md"
    source.write_text("# Title\n\nBody\n\n", encoding="utf-8")

    normalize.md_file_beautifier(source, backup_ext=".backup")

    backups = list(tmp_path.glob("doc.md.*.backup"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "# Title\n\nBody\n\n"
    assert source.read_text(encoding="utf-8") == "# Title\n\nBody"


def test_md_file_beautifier_uses_requested_extensions_and_encodings(tmp_path: Path) -> None:
    source = tmp_path / "doc.markdown"
    source.write_text("# Titre\n\nEte\n\n", encoding="latin-1")

    normalize.md_file_beautifier(
        source,
        backup_option=False,
        filename_ext=".markdown",
        read_encoding="latin-1",
        write_encoding="utf-8",
    )

    assert source.read_text(encoding="utf-8") == "# Titre\n\nEte"


def test_md_file_beautifier_rejects_empty_file(tmp_path: Path) -> None:
    source = tmp_path / "empty.md"
    source.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="seems empty"):
        normalize.md_file_beautifier(source, backup_option=False)


def test_md_file_beautifier_rejects_unexpected_extension(tmp_path: Path) -> None:
    source = tmp_path / "doc.txt"
    source.write_text("content", encoding="utf-8")

    with pytest.raises(ValueError, match="Unexpected file extension"):
        normalize.md_file_beautifier(source, backup_option=False)
