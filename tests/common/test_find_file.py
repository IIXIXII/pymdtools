from pathlib import Path
import pytest

from pymdtools.common import find_file


def test_find_file_finds_in_relative_path(tmp_path):
    # structure: tmp/a/b/target.txt
    base = tmp_path / "a" / "b"
    base.mkdir(parents=True)
    target = base / "target.txt"
    target.write_text("x", encoding="utf-8")

    found = find_file(
        "target.txt",
        start_points=[base],
        relative_paths=["."],
        max_up=0,
    )
    assert Path(found) == target.resolve()


def test_find_file_walks_up_parents(tmp_path):
    # tmp/root/rel/target.txt and start at tmp/root/sub
    root = tmp_path / "root"
    (root / "rel").mkdir(parents=True)
    (root / "sub").mkdir(parents=True)

    target = root / "rel" / "target.txt"
    target.write_text("x", encoding="utf-8")

    found = find_file(
        "target.txt",
        start_points=[root / "sub"],
        relative_paths=["rel"],
        max_up=2,
    )
    assert Path(found) == target.resolve()


def test_find_file_tries_multiple_start_points(tmp_path):
    p1 = tmp_path / "p1"
    p2 = tmp_path / "p2"
    p1.mkdir()
    p2.mkdir()

    target = p2 / "target.txt"
    target.write_text("x", encoding="utf-8")

    found = find_file(
        "target.txt",
        start_points=[p1, p2],
        relative_paths=["."],
        max_up=0,
    )
    assert Path(found) == target.resolve()


def test_find_file_raises_with_details(tmp_path):
    with pytest.raises(FileNotFoundError) as exc:
        find_file("missing.txt", start_points=[tmp_path], relative_paths=["."], max_up=1)
    assert "missing.txt" in str(exc.value)


def test_find_file_invalid_max_up_raises(tmp_path):
    with pytest.raises(ValueError):
        find_file("x.txt", start_points=[tmp_path], relative_paths=["."], max_up=-1)
