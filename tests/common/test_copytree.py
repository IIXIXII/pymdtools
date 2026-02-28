# tests/test_copytree.py
from __future__ import annotations

import time
from pathlib import Path

import pytest

from pymdtools.common import copytree


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _supports_symlinks(tmp_path: Path) -> bool:
    """
    Detect whether the current environment supports creating symlinks.

    On Windows this may require admin rights or Developer Mode.
    """
    target = tmp_path / "target.txt"
    link = tmp_path / "link.txt"
    _write(target, "x")

    try:
        link.symlink_to(target)
        ok = link.is_symlink()
    except (OSError, NotImplementedError):
        ok = False
    finally:
        try:
            if link.exists() or link.is_symlink():
                link.unlink()
        except OSError:
            pass

    return ok


# ---------------------------------------------------------------------------
# Basic validation
# ---------------------------------------------------------------------------

def test_copytree_raises_when_src_missing(tmp_path: Path) -> None:
    src = tmp_path / "missing"
    dst = tmp_path / "dst"

    with pytest.raises(FileNotFoundError):
        copytree(src, dst)


def test_copytree_raises_when_src_not_directory(tmp_path: Path) -> None:
    src = tmp_path / "file.txt"
    dst = tmp_path / "dst"

    _write(src, "x")

    with pytest.raises(NotADirectoryError):
        copytree(src, dst)


# ---------------------------------------------------------------------------
# Basic recursive copy
# ---------------------------------------------------------------------------

def test_copytree_basic_recursive_copy(tmp_path: Path) -> None:
    src = tmp_path / "src"
    dst = tmp_path / "dst"

    _write(src / "a.txt", "A")
    _write(src / "sub" / "b.txt", "B")

    out = copytree(src, dst)

    assert out == dst
    assert (dst / "a.txt").is_file()
    assert (dst / "sub" / "b.txt").is_file()
    assert _read(dst / "a.txt") == "A"
    assert _read(dst / "sub" / "b.txt") == "B"


# ---------------------------------------------------------------------------
# Ignore callable
# ---------------------------------------------------------------------------

def test_copytree_ignore_callable(tmp_path: Path) -> None:
    src = tmp_path / "src"
    dst = tmp_path / "dst"

    _write(src / "keep.txt", "K")
    _write(src / "skip.txt", "S")
    _write(src / "sub" / "keep2.txt", "K2")
    _write(src / "sub" / "skip2.txt", "S2")

    def ignore(dirpath: str, names: list[str]):
        return [n for n in names if n.startswith("skip")]

    copytree(src, dst, ignore=ignore)

    assert (dst / "keep.txt").exists()
    assert not (dst / "skip.txt").exists()
    assert (dst / "sub" / "keep2.txt").exists()
    assert not (dst / "sub" / "skip2.txt").exists()


# ---------------------------------------------------------------------------
# Incremental logic
# ---------------------------------------------------------------------------

def test_copytree_does_not_overwrite_when_dest_newer(tmp_path: Path) -> None:
    src = tmp_path / "src"
    dst = tmp_path / "dst"

    _write(src / "a.txt", "SRC")
    copytree(src, dst)

    assert _read(dst / "a.txt") == "SRC"

    # Make destination newer
    time.sleep(1.1)
    _write(dst / "a.txt", "DST")  # same length

    copytree(src, dst)

    # Destination should remain unchanged
    assert _read(dst / "a.txt") == "DST"


def test_copytree_overwrites_when_source_newer(tmp_path: Path) -> None:
    src = tmp_path / "src"
    dst = tmp_path / "dst"

    _write(src / "a.txt", "OLD")
    copytree(src, dst)

    time.sleep(1.1)
    _write(src / "a.txt", "NEW")

    copytree(src, dst)

    assert _read(dst / "a.txt") == "NEW"


def test_copytree_overwrites_when_size_differs(tmp_path: Path) -> None:
    src = tmp_path / "src"
    dst = tmp_path / "dst"

    _write(src / "a.txt", "A")
    copytree(src, dst)

    # Change destination size
    _write(dst / "a.txt", "DEST-CHANGED-SIZE")

    copytree(src, dst)

    assert _read(dst / "a.txt") == "A"


# ---------------------------------------------------------------------------
# Symlink behavior (portable)
# ---------------------------------------------------------------------------

def test_copytree_symlinks_true_preserves_symlink_if_supported(tmp_path: Path) -> None:
    if not _supports_symlinks(tmp_path):
        pytest.skip("Symlinks not supported in this environment.")

    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()

    target = src / "target.txt"
    _write(target, "T")

    link = src / "link.txt"
    link.symlink_to(target)

    copytree(src, dst, symlinks=True)

    out_link = dst / "link.txt"
    assert out_link.is_symlink()
    assert _read(out_link) == "T"


def test_copytree_symlinks_false_follows_symlink_if_supported(tmp_path: Path) -> None:
    if not _supports_symlinks(tmp_path):
        pytest.skip("Symlinks not supported in this environment.")

    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()

    target = src / "target.txt"
    _write(target, "T")

    link = src / "link.txt"
    link.symlink_to(target)

    copytree(src, dst, symlinks=False)

    out_link = dst / "link.txt"
    assert out_link.exists()
    assert not out_link.is_symlink()
    assert _read(out_link) == "T"


def test_copytree_symlinks_true_overwrites_existing_dest_entry_if_supported(tmp_path: Path) -> None:
    if not _supports_symlinks(tmp_path):
        pytest.skip("Symlinks not supported in this environment.")

    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    dst.mkdir()

    target = src / "target.txt"
    _write(target, "T")

    link = src / "link.txt"
    link.symlink_to(target)

    # Pre-create regular file
    _write(dst / "link.txt", "OLD")

    copytree(src, dst, symlinks=True)

    out_link = dst / "link.txt"
    assert out_link.is_symlink()
    assert _read(out_link) == "T"