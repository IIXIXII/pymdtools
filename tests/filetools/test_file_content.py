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


def test_filecontent_content_rejects_non_text(tmp_path: Path):
    fc = FileContent(tmp_path / "a.txt")
    with pytest.raises(TypeError, match="content must be a str or None"):
        fc.content = b"nope"  # type: ignore[assignment]


def test_filecontent_read_existing_file(tmp_path: Path):
    p = tmp_path / "a.txt"
    p.write_text("abc", encoding="utf-8")

    fc = FileContent(p, backup=False)
    assert fc.content == "abc"
    assert fc.save_needed is False


def test_filecontent_read_with_new_filename(tmp_path: Path):
    p = tmp_path / "a.txt"
    p.write_text("abc", encoding="utf-8")

    fc = FileContent()
    fc.read(p)

    assert fc.full_filename == str(p.resolve())
    assert fc.content == "abc"
    assert fc.save_needed is False


def test_filecontent_write_creates_file(tmp_path: Path):
    p = tmp_path / "a.txt"
    fc = FileContent(p, content="hello", backup=False)
    fc.write()
    assert p.read_text(encoding="utf-8").lstrip("\ufeff") == "hello"
    assert fc.save_needed is False


def test_filecontent_write_with_new_filename(tmp_path: Path):
    p = tmp_path / "a.txt"
    fc = FileContent(content="hello", backup=False)

    fc.write(p)

    assert fc.full_filename == str(p.resolve())
    assert p.read_text(encoding="utf-8").lstrip("\ufeff") == "hello"
    assert fc.save_needed is False


def test_filecontent_write_no_backup_when_disabled(tmp_path: Path):
    p = tmp_path / "a.txt"
    p.write_text("old", encoding="utf-8")

    fc = FileContent(p, content="new", backup=False)
    fc.write()

    assert not list(tmp_path.glob("a.txt.*.bak"))
    assert p.read_text(encoding="utf-8").lstrip("\ufeff") == "new"


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


def test_filecontent_backup_and_save_needed_setters() -> None:
    fc = FileContent(content="x")
    fc.backup = 0  # type: ignore[assignment]
    fc.save_needed = 0  # type: ignore[assignment]

    assert fc.backup is False
    assert fc.save_needed is False


def test_filecontent_repr_and_str_with_none_content(tmp_path: Path):
    fc = FileContent(tmp_path / "a.txt", backup=False)

    assert "content_len=None" in repr(fc)
    rendered = str(fc)
    assert "backup option=False" in rendered
    assert "save needed=False" in rendered
    assert "Content is None" in rendered


def test_filecontent_repr_and_str_with_text_content(tmp_path: Path):
    fc = FileContent(tmp_path / "a.txt", content="hello", backup=True)

    assert "content_len=5" in repr(fc)
    rendered = str(fc)
    assert "backup option=True" in rendered
    assert "save needed=True" in rendered
    assert "Content char number=     5" in rendered


def test_filecontent_failed_read_preserves_path_content_and_dirty_state(tmp_path: Path) -> None:
    original = tmp_path / "original.txt"
    original.write_text("old", encoding="utf-8")
    missing = tmp_path / "missing.txt"
    fc = FileContent(original, backup=False)
    fc.content = "edited"

    with pytest.raises(FileNotFoundError):
        fc.read(missing)

    assert fc.full_filename == str(original.resolve())
    assert fc.content == "edited"
    assert fc.save_needed is True


def test_filecontent_failed_read_of_current_file_preserves_buffer(tmp_path: Path) -> None:
    path = tmp_path / "current.txt"
    path.write_text("old", encoding="utf-8")
    fc = FileContent(path, backup=False)
    fc.content = "edited"
    path.unlink()

    with pytest.raises(FileNotFoundError):
        fc.read()

    assert fc.full_filename == str(path.resolve())
    assert fc.content == "edited"
    assert fc.save_needed is True


def test_filecontent_failed_write_preserves_path_and_dirty_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = tmp_path / "original.txt"
    destination = tmp_path / "destination.txt"
    fc = FileContent(original, content="edited", backup=False)

    def fail_write(*args, **kwargs):
        raise OSError("write failed")

    monkeypatch.setattr("pymdtools.filetools.common.set_file_content", fail_write)

    with pytest.raises(OSError, match="write failed"):
        fc.write(destination)

    assert fc.full_filename == str(original.resolve())
    assert fc.content == "edited"
    assert fc.save_needed is True
    assert not destination.exists()


def test_filecontent_none_content_write_keeps_original_path(tmp_path: Path) -> None:
    original = tmp_path / "original.txt"
    destination = tmp_path / "destination.txt"
    fc = FileContent(original, backup=False)
    fc.content = None

    with pytest.raises(ValueError, match="content is None"):
        fc.write(destination)

    assert fc.full_filename == str(original.resolve())
    assert not destination.exists()
