import os
import time
import shutil
import pytest

from pymdtools.common import copytree


def _write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def test_copytree_copies_files_and_directories(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    _write(str(src / "a.txt"), "hello")
    _write(str(src / "sub" / "b.txt"), "world")

    copytree(str(src), str(dst))

    assert (dst / "a.txt").read_text(encoding="utf-8") == "hello"
    assert (dst / "sub" / "b.txt").read_text(encoding="utf-8") == "world"


def test_copytree_incremental_does_not_overwrite_newer_destination(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"

    _write(str(src / "a.txt"), "src_v1")
    copytree(str(src), str(dst))
    assert (dst / "a.txt").read_text(encoding="utf-8") == "src_v1"

    # Make destination newer than source
    _write(str(dst / "a.txt"), "dst_newer")
    time.sleep(0.05)
    os.utime(str(dst / "a.txt"), None)  # update mtime

    # Source unchanged => should NOT overwrite newer destination
    copytree(str(src), str(dst))
    assert (dst / "a.txt").read_text(encoding="utf-8") == "dst_newer"


def test_copytree_overwrites_when_source_newer(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"

    _write(str(src / "a.txt"), "v1")
    copytree(str(src), str(dst))

    time.sleep(0.05)
    _write(str(src / "a.txt"), "v2")  # updates mtime

    copytree(str(src), str(dst))
    assert (dst / "a.txt").read_text(encoding="utf-8") == "v2"


def test_copytree_respects_ignore(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"

    _write(str(src / "keep.txt"), "ok")
    _write(str(src / "skip.log"), "no")

    def ignore_func(dirpath, names):
        return {"skip.log"}

    copytree(str(src), str(dst), ignore=ignore_func)

    assert (dst / "keep.txt").exists()
    assert not (dst / "skip.log").exists()


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlink not supported on this platform")
def test_copytree_symlinks_true_copies_link_itself(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    os.makedirs(src, exist_ok=True)

    target = src / "target.txt"
    target.write_text("data", encoding="utf-8")

    link = src / "link.txt"
    os.symlink(str(target), str(link))

    copytree(str(src), str(dst), symlinks=True)

    dst_link = dst / "link.txt"
    assert dst_link.is_symlink()
    # the link should exist, target content not necessarily duplicated
    assert os.path.islink(dst_link)


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlink not supported on this platform")
def test_copytree_symlinks_false_follows_link(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    os.makedirs(src, exist_ok=True)

    target = src / "target.txt"
    target.write_text("data", encoding="utf-8")

    link = src / "link.txt"
    os.symlink(str(target), str(link))

    copytree(str(src), str(dst), symlinks=False)

    dst_link = dst / "link.txt"
    assert not dst_link.is_symlink()
    assert dst_link.read_text(encoding="utf-8") == "data"
