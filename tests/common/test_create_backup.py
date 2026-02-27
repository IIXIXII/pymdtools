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
        
