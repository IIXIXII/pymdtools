from __future__ import annotations

from pathlib import Path
import pytest

from pymdtools.filetools import FileContent


def test_filecontent_init_with_content_sets_save_needed(tmp_path: Path):
    fc = FileContent(tmp_path / "a.txt", content="hello", backup=True)
    assert fc.content == "hello"
    assert fc.save_needed is True


def test_filecontent_read_requires_filename():
    fc = FileContent()
    with pytest.raises(ValueError):
        fc.read()


def test_filecontent_write_requires_filename():
    fc = FileContent(content="x")
    with pytest.raises(ValueError):
        fc.write()


def test_filecontent_write_requires_content(tmp_path: Path):
    fc = FileContent(tmp_path / "a.txt")
    fc.content = None
    with pytest.raises(ValueError):
        fc.write()


def test_filecontent_read_existing_file(tmp_path: Path):
    p = tmp_path / "a.txt"
    p.write_text("abc", encoding="utf-8")

    fc = FileContent(p, backup=False)
    assert fc.content == "abc"
    assert fc.save_needed is False


def test_filecontent_write_creates_file(tmp_path: Path):
    p = tmp_path / "a.txt"
    fc = FileContent(p, content="hello", backup=False)
    fc.write()
    assert p.read_text(encoding="utf-8").lstrip("\ufeff") == "hello"
    assert fc.save_needed is False


def test_filecontent_write_creates_backup_when_overwriting(tmp_path: Path, monkeypatch):
    import pymdtools.common as common

    p = tmp_path / "a.txt"
    p.write_text("old", encoding="utf-8")

    fc = FileContent(p, content="new", backup=True)

    # Make backup deterministic by freezing "today" if create_backup uses it.

    fc.write(backup_ext=".bak")

    backups = list(tmp_path.glob("a.txt."+common.today_utc()+"-*.bak"))
    assert len(backups) == 1
    assert p.read_text(encoding="utf-8").lstrip("\ufeff") == "new"
