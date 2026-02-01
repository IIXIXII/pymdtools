from pathlib import Path
import pytest

from pymdtools.filetools import FileName


def test_filename_initial_none():
    f = FileName()
    assert f.full_filename is None
    assert f.filename is None
    assert f.filename_path is None
    assert f.filename_ext is None


def test_full_filename_normalization(tmp_path):
    p = tmp_path / "a.txt"
    f = FileName(str(p))
    assert Path(f.full_filename).name == "a.txt"


def test_set_filename_when_full_is_none():
    f = FileName()
    f.filename = "a.txt"
    assert Path(f.full_filename).name == "a.txt"


def test_set_filename_replaces_name(tmp_path):
    p = tmp_path / "a.txt"
    f = FileName(str(p))
    f.filename = "b.txt"
    assert Path(f.full_filename).name == "b.txt"
    assert Path(f.full_filename).parent == tmp_path


def test_set_filename_path_requires_existing_full_filename(tmp_path):
    f = FileName()
    with pytest.raises(ValueError):
        f.filename_path = tmp_path


def test_set_filename_path_moves_file(tmp_path):
    src_dir = tmp_path / "src"
    dst_dir = tmp_path / "dst"
    src_dir.mkdir()
    dst_dir.mkdir()

    f = FileName(str(src_dir / "a.txt"))
    f.filename_path = dst_dir
    assert Path(f.full_filename) == (dst_dir / "a.txt")


def test_set_filename_ext_validation(tmp_path):
    f = FileName(str(tmp_path / "a.txt"))
    with pytest.raises(ValueError):
        f.filename_ext = "md"  # missing dot
    f.filename_ext = ".md"
    assert Path(f.full_filename).name == "a.md"


def test_is_file_and_is_dir(tmp_path):
    file_path = tmp_path / "a.txt"
    dir_path = tmp_path / "d"
    dir_path.mkdir()
    file_path.write_text("x", encoding="utf-8")

    f1 = FileName(str(file_path))
    assert f1.is_file() is True
    assert f1.is_dir() is False

    f2 = FileName(str(dir_path))
    assert f2.is_dir() is True
    assert f2.is_file() is False

