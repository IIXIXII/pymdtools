from __future__ import annotations

from pathlib import Path
import pytest

from pymdtools.instruction import get_vars_around_md_file


def test_get_vars_around_md_file_collects_from_parent_and_subdirs(tmp_path: Path):
    # structure:
    # root/
    #   vars.md          defines a
    #   sub/
    #     more.md        defines b
    #     target.md      (file under test)
    root = tmp_path / "root"
    sub = root / "sub"
    sub.mkdir(parents=True)

    (root / "vars.md").write_text(r'<!-- var(a)="1" -->', encoding="utf-8")
    (sub / "more.md").write_text(r'<!-- var(b)="2" -->', encoding="utf-8")
    target = sub / "target.md"
    target.write_text("body\n", encoding="utf-8")

    out = get_vars_around_md_file(
        target,
        filename_ext=".md",
        depth_up=1,
        depth_down=1,
        encoding="utf-8",
    )
    assert out == {"a": "1", "b": "2"}


def test_get_vars_around_md_file_depth_down_0_only_current_dir(tmp_path: Path):
    root = tmp_path / "root"
    sub = root / "sub"
    sub.mkdir(parents=True)

    (root / "vars.md").write_text(r'<!-- var(a)="1" -->', encoding="utf-8")
    (sub / "more.md").write_text(r'<!-- var(b)="2" -->', encoding="utf-8")
    target = sub / "target.md"
    target.write_text("body\n", encoding="utf-8")

    out = get_vars_around_md_file(
        target,
        depth_up=0,     # stay in sub/
        depth_down=0,   # only sub/
        encoding="utf-8",
    )
    assert out == {"b": "2"}


def test_get_vars_around_md_file_duplicate_raises(tmp_path: Path):
    root = tmp_path / "root"
    sub = root / "sub"
    sub.mkdir(parents=True)

    (root / "vars.md").write_text(r'<!-- var(a)="1" -->', encoding="utf-8")
    (sub / "more.md").write_text(r'<!-- var(a)="2" -->', encoding="utf-8")
    target = sub / "target.md"
    target.write_text("body\n", encoding="utf-8")

    with pytest.raises(ValueError):
        get_vars_around_md_file(target, depth_up=1, depth_down=1, encoding="utf-8")


def test_get_vars_around_md_file_invalid_depth_raises(tmp_path: Path):
    f = tmp_path / "a.md"
    f.write_text("x", encoding="utf-8")

    with pytest.raises(ValueError):
        get_vars_around_md_file(f, depth_up=-1)

    with pytest.raises(ValueError):
        get_vars_around_md_file(f, depth_down=-2)
