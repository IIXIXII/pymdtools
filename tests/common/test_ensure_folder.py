import os
import pytest

from pymdtools.common import ensure_folder


def test_ensure_folder_creates_missing_dir(tmp_path):
    target = tmp_path / "a" / "b" / "c"
    out = ensure_folder(str(target))

    assert os.path.isabs(out)
    assert os.path.isdir(out)


def test_ensure_folder_is_idempotent(tmp_path):
    out1 = ensure_folder(str(tmp_path))
    out2 = ensure_folder(str(tmp_path))
    assert out1 == out2


def test_ensure_folder_raises_if_path_is_file(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("data", encoding="utf-8")

    with pytest.raises(NotADirectoryError):
        ensure_folder(str(f))
