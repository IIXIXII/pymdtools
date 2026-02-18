from __future__ import annotations

from pathlib import Path
import pytest

from pymdtools.instruction import search_include_vars_to_md_file


def test_search_include_vars_to_md_file_applies_vars_from_around(tmp_path: Path):
    # root/
    #   vars.md        defines x
    #   sub/
    #     target.md    uses begin-var(x)
    root = tmp_path / "root"
    sub = root / "sub"
    sub.mkdir(parents=True)

    (root / "vars.md").write_text(r'<!-- var(x)="VALUE" -->', encoding="utf-8")

    target = sub / "target.md"
    target.write_text(
        "A\n<!-- begin-var(x) -->OLD<!-- end-var -->\nB\n",
        encoding="utf-8",
    )

    search_include_vars_to_md_file(
        target,
        backup_option=False,
        depth_up=1,
        depth_down=1,
        encoding="utf-8",
    )

    out = target.read_text(encoding="utf-8").lstrip("\ufeff")
    assert "VALUE" in out
    assert "OLD" not in out


def test_search_include_vars_to_md_file_creates_backup(tmp_path: Path, monkeypatch):
    root = tmp_path / "root"
    sub = root / "sub"
    sub.mkdir(parents=True)

    (root / "vars.md").write_text(r'<!-- var(x)="VALUE" -->', encoding="utf-8")

    target = sub / "target.md"
    target.write_text(
        "<!-- begin-var(x) -->OLD<!-- end-var -->",
        encoding="utf-8",
    )

    import pymdtools.common as common
    monkeypatch.setattr(common, "get_today", lambda: "2026-02-01")

    search_include_vars_to_md_file(
        target,
        backup_option=True,
        backup_ext=".bak",
        depth_up=1,
        depth_down=1,
        encoding="utf-8",
    )

    backups = list(sub.glob("target.md.2026-02-01-*.bak"))
    assert len(backups) >= 1
