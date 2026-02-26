# tests/test_to_path.py
from __future__ import annotations

import os
from pathlib import Path

import pytest

from pymdtools.common import to_path


class DummyPathLike:
    """Minimal os.PathLike[str] implementation for tests."""

    def __init__(self, value: str) -> None:
        self._value = value

    def __fspath__(self) -> str:  # noqa: D401
        return self._value


def _set_fake_home(monkeypatch: pytest.MonkeyPatch, fake_home: Path) -> None:
    """
    Try to make Path.expanduser() deterministic across platforms.

    On POSIX, HOME is enough.
    On Windows, expanduser may rely on USERPROFILE / HOMEDRIVE+HOMEPATH.
    We set USERPROFILE and clear HOMEDRIVE/HOMEPATH to reduce ambiguity.
    """
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("USERPROFILE", str(fake_home))
    monkeypatch.delenv("HOMEDRIVE", raising=False)
    monkeypatch.delenv("HOMEPATH", raising=False)


@pytest.mark.parametrize(
    "value_factory",
    [
        lambda p: str(p),
        lambda p: p,
        lambda p: DummyPathLike(str(p)),
    ],
)
def test_to_path_accepts_str_path_and_pathlike(value_factory, tmp_path: Path) -> None:
    p_in = tmp_path / "a" / "b.txt"
    out = to_path(value_factory(p_in))
    assert isinstance(out, Path)
    assert out == p_in


def test_to_path_expand_user_default_true(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    _set_fake_home(monkeypatch, fake_home)

    out = to_path("~/documents/report.md")
    assert isinstance(out, Path)
    assert str(out).startswith(str(fake_home))
    assert out == fake_home / "documents" / "report.md"


def test_to_path_expand_user_false(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    _set_fake_home(monkeypatch, fake_home)

    out = to_path("~/x.txt", expand_user=False)
    # Should keep "~" unexpanded
    assert out.parts[0] == "~"
    assert out.as_posix().endswith("x.txt")


def test_to_path_does_not_resolve_by_default(tmp_path: Path) -> None:
    # By default, do not collapse ".." / "." via resolve()
    inp = tmp_path / "a" / ".." / "b" / "." / "c.txt"
    out = to_path(inp)
    assert out == inp
    # But it should still be a Path object
    assert isinstance(out, Path)


def test_to_path_resolve_false_strict_ignored(tmp_path: Path) -> None:
    missing = tmp_path / "missing" / "file.txt"
    # strict has no effect when resolve=False
    out = to_path(missing, resolve=False, strict=True)
    assert out == missing


def test_to_path_resolve_true_non_strict_missing_ok(tmp_path: Path) -> None:
    missing = tmp_path / "missing" / "file.txt"
    out = to_path(missing, resolve=True, strict=False)
    assert isinstance(out, Path)
    # resolve() should return an absolute (or at least normalized) path
    assert out.is_absolute()
    assert out.name == "file.txt"


def test_to_path_resolve_true_strict_missing_raises(tmp_path: Path) -> None:
    missing = tmp_path / "missing" / "file.txt"
    with pytest.raises(FileNotFoundError):
        to_path(missing, resolve=True, strict=True)


def test_to_path_resolve_true_existing_file(tmp_path: Path) -> None:
    f = tmp_path / "folder" / "file.txt"
    f.parent.mkdir(parents=True)
    f.write_text("ok", encoding="utf-8")

    out = to_path(f, resolve=True, strict=True)
    assert out.is_absolute()
    assert out.exists()
    assert out.samefile(f)


def test_to_path_path_object_passthrough(tmp_path: Path) -> None:
    p = tmp_path / "x" / "y"
    out = to_path(p)
    assert out is p  # preserve identity for Path inputs