import os
import pytest

from pymdtools.common import check_folder


def test_check_folder_returns_normalized_path(tmp_path):
    out = check_folder(str(tmp_path))
    assert os.path.isabs(out)
    assert os.path.isdir(out)


def test_check_folder_raises_if_path_does_not_exist(tmp_path):
    missing = tmp_path / "missing"
    with pytest.raises(FileNotFoundError):
        check_folder(str(missing))


def test_check_folder_raises_if_path_is_file(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("data", encoding="utf-8")

    with pytest.raises(NotADirectoryError):
        check_folder(str(f))
