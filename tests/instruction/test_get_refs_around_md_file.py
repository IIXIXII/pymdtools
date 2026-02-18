from __future__ import annotations

from pathlib import Path

from pymdtools.instruction import get_refs_around_md_file


def _write(p: Path, name: str, content: str) -> None:
    (p / name).write_text(content, encoding="utf-8")


def test_get_refs_around_md_file_depth_up_0_scans_file_dir(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    _write(root, "a.md", "<!-- begin-ref(a) -->A<!-- end-ref -->")

    file_path = root / "x.md"
    file_path.write_text("dummy", encoding="utf-8")

    out = get_refs_around_md_file(file_path, depth_up=0, depth_down=0)
    assert out == {"a": "A"}


def test_get_refs_around_md_file_depth_up_1_and_depth_down_adjustment(tmp_path: Path):
    # Structure:
    # root/
    #   a.md (ref a)
    #   sub/
    #     b.md (ref b)
    #     file.md (target file)
    root = tmp_path / "root"
    sub = root / "sub"
    sub.mkdir(parents=True)

    _write(root, "a.md", "<!-- begin-ref(a) -->A<!-- end-ref -->")
    _write(sub, "b.md", "<!-- begin-ref(b) -->B<!-- end-ref -->")

    file_path = sub / "file.md"
    file_path.write_text("dummy", encoding="utf-8")

    # depth_up=1 moves to root; depth_down=1 becomes effective 2, so it reaches sub/
    out = get_refs_around_md_file(file_path, depth_up=1, depth_down=1)
    assert out == {"a": "A", "b": "B"}


def test_get_refs_around_md_file_depth_down_unlimited(tmp_path: Path):
    root = tmp_path / "root"
    deep = root / "a" / "b"
    deep.mkdir(parents=True)

    _write(deep, "x.md", "<!-- begin-ref(x) -->X<!-- end-ref -->")
    file_path = deep / "file.md"
    file_path.write_text("dummy", encoding="utf-8")

    out = get_refs_around_md_file(file_path, depth_up=2, depth_down=-1)
    assert out == {"x": "X"}


def test_get_refs_around_md_file_respects_filename_ext(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    _write(root, "a.txt", "<!-- begin-ref(a) -->A<!-- end-ref -->")

    file_path = root / "file.md"
    file_path.write_text("dummy", encoding="utf-8")

    out = get_refs_around_md_file(file_path, filename_ext=".txt", depth_up=0, depth_down=0)
    assert out == {"a": "A"}
