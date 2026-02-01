import os
from pathlib import Path

from pymdtools.common import make_temp_dir


def test_make_temp_dir_creates_directory(tmp_path):
    d = make_temp_dir(prefix="test_", dir=tmp_path)
    p = Path(d)

    assert p.exists()
    assert p.is_dir()
    assert str(p).startswith(str(tmp_path))


def test_make_temp_dir_is_unique(tmp_path):
    d1 = make_temp_dir(prefix="test_", dir=tmp_path)
    d2 = make_temp_dir(prefix="test_", dir=tmp_path)

    assert d1 != d2
    assert Path(d1).is_dir()
    assert Path(d2).is_dir()
