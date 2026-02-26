import os
from pathlib import Path

from pymdtools.common import normpath


def test_normpath_returns_absolute_path(tmp_path):
    p = tmp_path / "a" / "b"
    out = normpath(str(p))
    assert os.path.isabs(out)


def test_normpath_normalizes_dot_and_dotdot(tmp_path):
    base = tmp_path / "base"
    raw = str(base / "x" / ".." / "y" / "." / "z")
    out = normpath(raw)
    expected = (base / "y" / "z").resolve()
    assert out == expected


def test_normpath_does_not_require_existing_path(tmp_path):
    raw = str(tmp_path / "does_not_exist" / "file.txt")
    out = str(normpath(raw))
    assert os.path.isabs(out)
    assert out.endswith(os.path.join("does_not_exist", "file.txt"))


def test_normpath_equivalent_to_pathlib_resolve(tmp_path):
    raw = str(tmp_path / "a" / ".." / "b" / "c.txt")
    assert str(normpath(raw)) == str(Path(raw).resolve())
