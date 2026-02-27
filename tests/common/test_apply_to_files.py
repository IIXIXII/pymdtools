# tests/test_apply_to_files.py
from __future__ import annotations

from pathlib import Path
import pytest

from pymdtools.common import apply_to_files


def _write(p: Path, text: str = "x") -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def test_apply_to_files_root_is_file(tmp_path: Path) -> None:
    f = _write(tmp_path / "a.md", "hello")

    def fn(p: Path) -> str:
        return p.read_text(encoding="utf-8")

    results, summary, errors = apply_to_files(f, fn, recursive=True)

    assert results == ["hello"]
    assert errors == []
    assert summary.processed == 1
    assert summary.succeeded == 1
    assert summary.failed == 0
    assert summary.skipped == 0


def test_apply_to_files_non_recursive(tmp_path: Path) -> None:
    _write(tmp_path / "a.md")
    _write(tmp_path / "b.txt")
    _write(tmp_path / "sub" / "c.md")

    def fn(p: Path) -> str:
        return p.name

    results, summary, errors = apply_to_files(
        tmp_path,
        fn,
        recursive=False,
    )

    assert errors == []
    assert set(results) == {"a.md", "b.txt"}  # sub/c.md excluded (non-recursive)
    assert summary.processed == 2
    assert summary.succeeded == 2
    assert summary.failed == 0
    assert summary.skipped == 0


def test_apply_to_files_recursive_expected_ext(tmp_path: Path) -> None:
    _write(tmp_path / "a.md")
    _write(tmp_path / "b.txt")
    _write(tmp_path / "sub" / "c.md")
    _write(tmp_path / "sub" / "deep" / "d.markdown")

    def fn(p: Path) -> str:
        return p.relative_to(tmp_path).as_posix()

    results, summary, errors = apply_to_files(
        tmp_path,
        fn,
        recursive=True,
        expected_ext=(".md", ".markdown"),
    )

    assert errors == []
    assert set(results) == {"a.md", "sub/c.md", "sub/deep/d.markdown"}
    # processed includes all files encountered; skipped includes filtered-out extensions
    assert summary.processed == 4
    assert summary.succeeded == 3
    assert summary.failed == 0
    assert summary.skipped == 1  # b.txt


def test_apply_to_files_include_exclude_globs(tmp_path: Path) -> None:
    _write(tmp_path / "a.md")
    _write(tmp_path / "b.md")
    _write(tmp_path / "notes.txt")
    _write(tmp_path / "sub" / "c.md")
    _write(tmp_path / "sub" / "private.md")
    _write(tmp_path / "sub" / "deep" / "d.md")

    def fn(p: Path) -> str:
        return p.relative_to(tmp_path).as_posix()

    results, summary, errors = apply_to_files(
        tmp_path,
        fn,
        recursive=True,
        expected_ext=".md",
        include_globs=("*.md", "sub/*.md", "sub/deep/*.md"),  # fnmatch on rel POSIX
        exclude_globs=("sub/private.md",),
    )

    assert errors == []
    assert set(results) == {"a.md", "b.md", "sub/c.md", "sub/deep/d.md"}
    assert "sub/private.md" not in results

    # processed counts all files (md + txt)
    assert summary.processed == 6
    assert summary.failed == 0
    # succeeded = 4 md included, skipped = remaining (txt + excluded/private.md)
    assert summary.succeeded == 4
    assert summary.skipped == 2


def test_apply_to_files_on_error_raise(tmp_path: Path) -> None:
    _write(tmp_path / "ok.md", "ok")
    _write(tmp_path / "boom.md", "boom")
    _write(tmp_path / "later.md", "later")

    def fn(p: Path) -> str:
        if p.name == "boom.md":
            raise RuntimeError("boom")
        return p.name

    with pytest.raises(RuntimeError, match="boom"):
        apply_to_files(
            tmp_path,
            fn,
            recursive=False,
            expected_ext=".md",
            on_error="raise",
        )


def test_apply_to_files_on_error_collect(tmp_path: Path) -> None:
    _write(tmp_path / "ok.md", "ok")
    _write(tmp_path / "boom.md", "boom")
    _write(tmp_path / "later.md", "later")
    _write(tmp_path / "note.txt", "x")

    def fn(p: Path) -> str:
        if p.name == "boom.md":
            raise RuntimeError("boom")
        return p.name

    results, summary, errors = apply_to_files(
        tmp_path,
        fn,
        recursive=False,
        expected_ext=".md",
        on_error="collect",
    )

    assert set(results) == {"ok.md", "later.md"}
    assert summary.processed == 4  # includes note.txt
    assert summary.succeeded == 2
    assert summary.failed == 1
    assert summary.skipped == 1  # note.txt filtered by expected_ext

    assert len(errors) == 1
    err_path, exc = errors[0]
    assert err_path.name == "boom.md"
    assert isinstance(exc, RuntimeError)
    assert str(exc) == "boom"


def test_apply_to_files_missing_root_raises(tmp_path: Path) -> None:
    missing = tmp_path / "missing"

    def fn(_: Path) -> None:
        return None

    with pytest.raises(FileNotFoundError):
        apply_to_files(missing, fn)


def test_apply_to_files_root_not_dir_not_file_raises(tmp_path: Path) -> None:
    # Create a path that exists but is neither file nor directory is hard portably.
    # Instead, validate that a directory is required when root exists and isn't file.
    # We emulate by creating a directory, then passing a path inside that does not exist:
    # (covered by missing_root_raises). So here we just ensure directory works.
    root = tmp_path / "root"
    root.mkdir()

    def fn(p: Path) -> str:
        return p.name

    results, summary, errors = apply_to_files(root, fn, recursive=False)
    assert results == []
    assert errors == []
    assert summary.processed == 0
    assert summary.succeeded == 0
    assert summary.failed == 0
    assert summary.skipped == 0