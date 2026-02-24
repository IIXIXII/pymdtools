from __future__ import annotations

from pathlib import Path
import pytest

import pymdtools.instruction as instruction


def test_include_files_to_md_file_rewrites_file(tmp_path: Path, monkeypatch):
    # patch include resolution
    monkeypatch.setattr(instruction, "get_file_content_to_include", lambda name, **kw: "INC\n")

    f = tmp_path / "doc.md"
    f.write_text("A\n<!-- include-file(x.md) -->\nB\n", encoding="utf-8")

    instruction.include_files_to_md_file(
        f,
        backup_option=False,
        filename_ext=".md",
        read_encoding="utf-8",
        render_mode="raw",
    )

    out = f.read_text(encoding="utf-8").lstrip("\ufeff")
    assert "INC\n" in out
    assert "include-file(x.md)" not in out


def test_include_files_to_md_file_backup_created(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(instruction, "get_file_content_to_include", lambda name, **kw: "INC\n")

    f = tmp_path / "doc.md"
    f.write_text("<!-- include-file(x.md) -->", encoding="utf-8")

    import pymdtools.common as common
    monkeypatch.setattr(common, "get_today", lambda: "2026-02-01")

    instruction.include_files_to_md_file(
        f,
        backup_option=True,
        backup_ext=".bak",
        filename_ext=".md",
        read_encoding="utf-8",
        render_mode="raw",
    )

    backups = list(tmp_path.glob("doc.md.2026-02-01-*.bak"))
    assert len(backups) >= 1


def test_include_files_to_md_file_missing_include_can_be_ignored(tmp_path: Path, monkeypatch):
    def _raise(*args, **kwargs):
        raise FileNotFoundError("nope")

    monkeypatch.setattr(instruction, "get_file_content_to_include", _raise)

    f = tmp_path / "doc.md"
    original = "A\n<!-- include-file(x.md) -->\nB\n"
    f.write_text(original, encoding="utf-8")

    instruction.include_files_to_md_file(
        f,
        backup_option=False,
        filename_ext=".md",
        read_encoding="utf-8",
        error_if_no_file=False,
    )

    out = f.read_text(encoding="utf-8").lstrip("\ufeff")
    assert "<!-- include-file(x.md) -->" in out