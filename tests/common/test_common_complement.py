# tests/test_common_complement.py
from __future__ import annotations

import builtins
import sys
import os
import time
from pathlib import Path
from typing import Any, Optional

import pytest

import pymdtools.common as common


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _write_bytes(p: Path, data: bytes) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)


def _write_text(p: Path, text: str, encoding: str = "utf-8") -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding=encoding)


def _supports_symlinks(tmp_path: Path) -> bool:
    target = tmp_path / "target.txt"
    link = tmp_path / "link.txt"
    _write_text(target, "x")

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


def _block_import(monkeypatch: pytest.MonkeyPatch, blocked: str) -> None:
    """
    Force ImportError for a given top-level module name.
    Useful to cover optional dependency ImportError branches deterministically.
    """
    orig_import = builtins.__import__

    def custom_import(name: str, globals: Any = None, locals: Any = None, fromlist: Any = (), level: int = 0):
        if name == blocked or name.startswith(blocked + "."):
            raise ImportError(f"blocked import: {name}")
        return orig_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", custom_import)


# -----------------------------------------------------------------------------
# copytree: symlink branches (780-796)
# -----------------------------------------------------------------------------

def test_copytree_symlinks_true_overwrites_existing_dest_dir(tmp_path: Path) -> None:
    if not _supports_symlinks(tmp_path):
        pytest.skip("Symlinks not supported in this environment.")

    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    dst.mkdir()

    target = src / "target.txt"
    _write_text(target, "T")

    link = src / "link"
    link.symlink_to(target)

    # Destination already contains a directory with the same name -> triggers rmtree()
    (dst / "link").mkdir(parents=True, exist_ok=True)

    out = common.copytree(src, dst, symlinks=True)
    assert out == dst

    out_link = dst / "link"
    assert out_link.is_symlink()
    assert out_link.read_text(encoding="utf-8") == "T"


def test_copytree_symlinks_false_follows_symlink_file(tmp_path: Path) -> None:
    if not _supports_symlinks(tmp_path):
        pytest.skip("Symlinks not supported in this environment.")

    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()

    target = src / "target.txt"
    _write_text(target, "T")

    link = src / "link"
    link.symlink_to(target)

    common.copytree(src, dst, symlinks=False)

    out_link = dst / "link"
    assert out_link.exists()
    assert not out_link.is_symlink()
    assert out_link.read_text(encoding="utf-8") == "T"


# -----------------------------------------------------------------------------
# is_binary_file: UnicodeDecodeError branch (983-984)
# -----------------------------------------------------------------------------

def test_is_binary_file_invalid_utf8_no_null_no_bom(tmp_path: Path) -> None:
    p = tmp_path / "bad.bin"
    # invalid UTF-8 sequence, no null byte, no BOM prefix
    _write_bytes(p, b"\x80\x81\x82\x83")
    assert common.is_binary_file(p) is True


# -----------------------------------------------------------------------------
# detect_file_encoding: validation, BOM branches, ImportError, low confidence
# -----------------------------------------------------------------------------

def test_detect_file_encoding_min_confidence_validation(tmp_path: Path) -> None:
    p = tmp_path / "x.txt"
    _write_text(p, "hello")

    with pytest.raises(ValueError):
        common.detect_file_encoding(p, min_confidence=-0.1)

    with pytest.raises(ValueError):
        common.detect_file_encoding(p, min_confidence=1.1)


def test_detect_file_encoding_sample_size_validation(tmp_path: Path) -> None:
    p = tmp_path / "x.txt"
    _write_text(p, "hello")

    with pytest.raises(ValueError):
        common.detect_file_encoding(p, sample_size=0)


@pytest.mark.parametrize(
    "data, expected",
    [
        (b"\xff\xfe\x00\x00H\x00\x00\x00", "utf-32-le"),
        (b"\x00\x00\xfe\xff\x00\x00\x00H", "utf-32-be"),
        (b"\xff\xfeH\x00", "utf-16-le"),
        (b"\xfe\xff\x00H", "utf-16-be"),
        (b"\xef\xbb\xbfHello", "utf-8-sig"),
    ],
)
def test_detect_file_encoding_boms(tmp_path: Path, data: bytes, expected: str) -> None:
    p = tmp_path / "bom.txt"
    _write_bytes(p, data)
    assert common.detect_file_encoding(p) == expected


def test_detect_file_encoding_utf8_bom_prefer_flag(tmp_path: Path) -> None:
    p = tmp_path / "bom.txt"
    _write_bytes(p, b"\xef\xbb\xbfHello")

    assert common.detect_file_encoding(p, prefer_utf8_sig=True) == "utf-8-sig"
    assert common.detect_file_encoding(p, prefer_utf8_sig=False) == "utf-8"


def test_detect_file_encoding_importerror_when_chardet_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    p = tmp_path / "x.txt"
    _write_text(p, "hello")

    _block_import(monkeypatch, "chardet")

    with pytest.raises(ImportError, match="chardet is required"):
        common.detect_file_encoding(p)


def test_detect_file_encoding_low_confidence_falls_back_to_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    p = tmp_path / "x.txt"
    _write_bytes(p, b"plain ascii bytes")

    class FakeChardet:
        @staticmethod
        def detect(_: bytes) -> dict[str, object]:
            return {"encoding": "latin-1", "confidence": 0.10}

    monkeypatch.setitem(sys.modules, "chardet", FakeChardet)  # type: ignore[name-defined]

    assert common.detect_file_encoding(p, default="utf-8", min_confidence=0.50) == "utf-8"


# -----------------------------------------------------------------------------
# get_file_content: reject_binary branch (1124) + encoding auto-detect path (1128)
# -----------------------------------------------------------------------------

def test_get_file_content_rejects_binary(tmp_path: Path) -> None:
    p = tmp_path / "bin.dat"
    _write_bytes(p, b"abc\x00def")
    with pytest.raises(ValueError, match="Binary file detected"):
        common.get_file_content(p, reject_binary=True)


def test_get_file_content_calls_detect_encoding_when_encoding_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    p = tmp_path / "t.txt"
    _write_text(p, "hello")

    monkeypatch.setattr(common, "is_binary_file", lambda _: False)
    monkeypatch.setattr(common, "detect_file_encoding", lambda *_args, **_kw: "utf-8")

    assert common.get_file_content(p, encoding=None, strip_bom=False) == "hello"


# -----------------------------------------------------------------------------
# set_file_content: create_parents branch (1164->1167) + cleanup OSError (1196)
# -----------------------------------------------------------------------------

def test_set_file_content_creates_parents(tmp_path: Path) -> None:
    p = tmp_path / "a" / "b" / "c.txt"
    out = common.set_file_content(p, "x", create_parents=True, atomic=False)
    assert out.exists()
    assert out.parent == (tmp_path / "a" / "b").resolve()
    assert out.read_text(encoding="utf-8") == "x"


def test_set_file_content_cleanup_unlink_oserror_is_ignored(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Force an exception after tmp file is created so the finally block runs,
    and make tmp_path.unlink raise OSError to cover the except OSError branch.
    """
    target = tmp_path / "out.txt"

    # Make replace fail to trigger finally cleanup path
    orig_replace = Path.replace

    def bad_replace(self: Path, _target: Path) -> Path:
        raise OSError("replace failed")

    monkeypatch.setattr(Path, "replace", bad_replace)

    # Make unlink fail; should be swallowed
    orig_unlink = Path.unlink

    def bad_unlink(self: Path, *args: Any, **kwargs: Any) -> None:
        raise OSError("unlink failed")

    monkeypatch.setattr(Path, "unlink", bad_unlink)

    with pytest.raises(OSError, match="replace failed"):
        common.set_file_content(target, "content", atomic=True)

    # restore methods for safety (monkeypatch will also undo automatically)
    monkeypatch.setattr(Path, "replace", orig_replace)
    monkeypatch.setattr(Path, "unlink", orig_unlink)


# -----------------------------------------------------------------------------
# apply_to_files: include_globs false path (1315), NotADirectoryError (1328),
# symlinked dir skipped (1340), non-file skipped (1345), relative_to ValueError (1367-1369)
# -----------------------------------------------------------------------------

def test_apply_to_files_include_globs_no_match_counts_skipped(tmp_path: Path) -> None:
    _write_text(tmp_path / "a.txt", "x")

    def fn(_: Path) -> str:
        return "OK"

    results, summary, errors = common.apply_to_files(
        tmp_path,
        fn,
        recursive=False,
        include_globs=("*.md",),  # won't match a.txt
    )
    assert results == []
    assert errors == []
    assert summary.processed == 1
    assert summary.skipped == 1
    assert summary.succeeded == 0


def test_apply_to_files_not_a_directory_branch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Force the NotADirectoryError branch by making a directory report exists=True,
    is_file=False, is_dir=False.
    """
    base = tmp_path / "dir"
    base.mkdir()

    orig_is_dir = Path.is_dir

    def fake_is_dir(self: Path) -> bool:
        if self == base:
            return False
        return orig_is_dir(self)

    monkeypatch.setattr(Path, "is_dir", fake_is_dir)

    def fn(_: Path) -> None:
        return None

    with pytest.raises(NotADirectoryError):
        common.apply_to_files(base, fn, recursive=True)


def test_apply_to_files_skips_symlinked_dir_when_follow_symlinks_false(tmp_path: Path) -> None:
    if not _supports_symlinks(tmp_path):
        pytest.skip("Symlinks not supported in this environment.")

    root = tmp_path / "root"
    root.mkdir()
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    _write_text(real_dir / "a.txt", "x")

    link_dir = root / "linkdir"
    link_dir.symlink_to(real_dir, target_is_directory=True)

    def fn(_: Path) -> str:
        return "OK"

    results, summary, errors = common.apply_to_files(root, fn, recursive=True, follow_symlinks=False)
    # linkdir is a directory symlink; should be skipped entirely => no files processed
    assert results == []
    assert errors == []
    assert summary.processed == 0


def test_apply_to_files_skips_non_file_entries(tmp_path: Path) -> None:
    if not _supports_symlinks(tmp_path):
        pytest.skip("Symlinks not supported in this environment.")

    root = tmp_path / "root"
    root.mkdir()

    # Broken symlink: is_dir False, is_file False, exists False on many platforms,
    # but it is yielded by glob/rglob and should be skipped by "not p.is_file()".
    broken = root / "broken"
    broken.symlink_to(root / "missing-target")

    def fn(_: Path) -> str:
        return "OK"

    results, summary, errors = common.apply_to_files(root, fn, recursive=False)
    assert results == []
    assert errors == []
    assert summary.processed == 0  # broken symlink should not be treated as file


def test_apply_to_files_relative_to_valueerror_falls_back_to_name(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_text(tmp_path / "a.txt", "x")

    # Force Path.relative_to to raise ValueError for this test
    orig_relative_to = Path.relative_to

    def bad_relative_to(self: Path, *args: Any, **kwargs: Any) -> Path:
        raise ValueError("boom")

    monkeypatch.setattr(Path, "relative_to", bad_relative_to)

    seen: list[str] = []

    def fn(p: Path) -> str:
        seen.append(p.name)
        return p.name

    results, summary, errors = common.apply_to_files(tmp_path, fn, recursive=False, include_globs=("a.txt",))
    assert results == ["a.txt"]
    assert summary.succeeded == 1
    assert errors == []

    monkeypatch.setattr(Path, "relative_to", orig_relative_to)


# -----------------------------------------------------------------------------
# find_file: filename empty (1481) + absolute relative_paths (1490)
# -----------------------------------------------------------------------------

def test_find_file_rejects_empty_filename(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="filename must be a non-empty string"):
        common.find_file("", [tmp_path], ["."], max_up=0)


def test_find_file_rejects_absolute_relative_paths(tmp_path: Path) -> None:
    abs_rel = tmp_path.resolve()
    with pytest.raises(ValueError, match="relative_paths must be relative"):
        common.find_file("x.txt", [tmp_path], [abs_rel], max_up=0)


# -----------------------------------------------------------------------------
# to_ascii: ImportError branch (1577-1578)
# -----------------------------------------------------------------------------

def test_to_ascii_importerror_when_unidecode_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    _block_import(monkeypatch, "unidecode")
    with pytest.raises(ImportError, match="Unidecode is required"):
        common.to_ascii("été")


# -----------------------------------------------------------------------------
# slugify: allow_unicode True branch (1608)
# -----------------------------------------------------------------------------

def test_slugify_allow_unicode_true_path() -> None:
    # Just ensure allow_unicode=True executes and returns a normalized slug.
    # (This covers the NFKC branch.)
    out = common.slugify("Été 2026", allow_unicode=True)
    assert out == "été-2026"


# -----------------------------------------------------------------------------
# get_valid_filename: strip branch (1660->1664) + sanitization and reserved names
# -----------------------------------------------------------------------------

def test_get_valid_filename_strip_and_invalid_chars_and_reserved_name() -> None:
    # Leading/trailing spaces stripped, invalid chars replaced
    out = common.get_valid_filename('  CON:<bad>|name>.txt  ', replacement="_", strip=True)
    # "CON" is reserved on Windows -> should be modified (stem gets "_")
    assert out.upper().startswith("CON_")
    assert "<" not in out and ">" not in out and "|" not in out and ":" not in out
    assert out.endswith(".txt")


# -----------------------------------------------------------------------------
# parse_timestamp: ImportError branch (1854-1855)
# -----------------------------------------------------------------------------

def test_parse_timestamp_importerror_when_dateutil_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    _block_import(monkeypatch, "dateutil")
    with pytest.raises(ImportError, match="python-dateutil is required"):
        common.parse_timestamp("2026-02-28 12:00:00")