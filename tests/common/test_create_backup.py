import os
import re
from pathlib import Path

import pytest

from pymdtools.common import create_backup
import pymdtools.common as common


def test_create_backup_creates_file_in_same_dir(tmp_path):
    src = tmp_path / "a.txt"
    src.write_text("hello", encoding="utf-8")

    backup = Path(create_backup(str(src)))

    assert backup.exists()
    assert backup.is_file()
    assert backup.parent == src.parent
    assert backup.read_text(encoding="utf-8") == "hello"


def test_create_backup_name_format_contains_date_and_counter(tmp_path):
    src = tmp_path / "a.txt"
    src.write_text("x", encoding="utf-8")

    backup_path = str(create_backup(str(src)))
    # example: a.txt.2026-01-31-000.bak
    assert re.search(r"\.20\d{2}-\d{2}-\d{2}-\d{3}\.bak$", backup_path)


def test_create_backup_increments_counter_if_name_exists(tmp_path):
    src = tmp_path / "a.txt"
    src.write_text("x", encoding="utf-8")

    b1 = Path(create_backup(str(src)))
    b2 = Path(create_backup(str(src)))

    assert b1 != b2
    assert b1.exists() and b2.exists()


def test_create_backup_raises_if_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        create_backup(str(tmp_path / "missing.txt"))


def test_create_backup_raises_if_path_is_directory(tmp_path):
    with pytest.raises(IsADirectoryError):
        create_backup(str(tmp_path))


def test_create_backup_raises_when_no_slot_available(tmp_path, monkeypatch):
    src = tmp_path / "file.txt"
    src.write_text("x", encoding="utf-8")

    monkeypatch.setattr(common, "today_utc", lambda: "2026-02-01")

    for i in range(0, 100):
        (tmp_path / f"file.txt.2026-02-01-{i:03d}.bak").write_text("bak", encoding="utf-8")

    with pytest.raises(Exception):
        common.create_backup(src, backup_ext=".bak")
        

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------

def test_create_backup_raises_if_file_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        create_backup(tmp_path / "missing.txt")


def test_create_backup_raises_if_not_file(tmp_path: Path) -> None:
    folder = tmp_path / "dir"
    folder.mkdir()

    with pytest.raises(IsADirectoryError):
        create_backup(folder)


def test_create_backup_raises_if_ext_empty(tmp_path: Path) -> None:
    src = tmp_path / "file.txt"
    _write(src, "x")

    with pytest.raises(ValueError):
        create_backup(src, ext="")


def test_create_backup_raises_if_max_tries_invalid(tmp_path: Path) -> None:
    src = tmp_path / "file.txt"
    _write(src, "x")

    with pytest.raises(ValueError):
        create_backup(src, max_tries=0)


# ---------------------------------------------------------------------------
# Basic behavior
# ---------------------------------------------------------------------------

def test_create_backup_creates_backup_with_expected_name(tmp_path: Path) -> None:
    src = tmp_path / "report.md"
    _write(src, "content")

    backup = create_backup(
        src,
        date_prefix="2026-01-01",
        ext=".bak",
    )

    expected_name = "report.md.2026-01-01-001.bak"

    assert backup.name == expected_name
    assert backup.exists()
    assert _read(backup) == "content"


def test_create_backup_ext_without_dot(tmp_path: Path) -> None:
    src = tmp_path / "file.txt"
    _write(src, "data")

    backup = create_backup(
        src,
        date_prefix="2026-01-01",
        ext="backup",
    )

    assert backup.name.endswith(".backup")
    assert _read(backup) == "data"


def test_create_backup_increments_index(tmp_path: Path) -> None:
    src = tmp_path / "file.txt"
    _write(src, "data")

    # Pre-create first backup
    existing = tmp_path / "file.txt.2026-01-01-001.bak"
    _write(existing, "old")

    backup = create_backup(
        src,
        date_prefix="2026-01-01",
        ext=".bak",
    )

    assert backup.name == "file.txt.2026-01-01-002.bak"
    assert _read(backup) == "data"


def test_create_backup_preserves_original_filename(tmp_path: Path) -> None:
    src = tmp_path / "archive.tar.gz"
    _write(src, "x")

    backup = create_backup(
        src,
        date_prefix="2026-01-01",
    )

    # The entire original name must be preserved
    assert backup.name.startswith("archive.tar.gz.2026-01-01-")


# ---------------------------------------------------------------------------
# Max tries exhaustion
# ---------------------------------------------------------------------------

def test_create_backup_raises_when_no_name_available(tmp_path: Path) -> None:
    src = tmp_path / "file.txt"
    _write(src, "data")

    # Pre-create all possible candidates
    for i in range(1, 4):
        existing = tmp_path / f"file.txt.2026-01-01-{i:03d}.bak"
        _write(existing, "x")

    with pytest.raises(FileExistsError):
        create_backup(
            src,
            date_prefix="2026-01-01",
            max_tries=3,
        )