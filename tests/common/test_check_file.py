import pytest

from pymdtools.common import check_file


def test_check_file_returns_absolute_path(tmp_path):
    f = tmp_path / "a.md"
    f.write_text("x", encoding="utf-8")

    out = check_file(str(f))
    assert out.endswith("a.md")


def test_check_file_raises_if_missing(tmp_path):
    missing = tmp_path / "missing.md"
    with pytest.raises(FileNotFoundError):
        check_file(str(missing))


def test_check_file_raises_if_directory(tmp_path):
    with pytest.raises(IsADirectoryError):
        check_file(str(tmp_path))


def test_check_file_accepts_expected_extension_case_insensitive(tmp_path):
    f = tmp_path / "a.MD"
    f.write_text("x", encoding="utf-8")

    assert check_file(str(f), expected_ext=".md").endswith("a.MD")


def test_check_file_raises_on_wrong_extension(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("x", encoding="utf-8")

    with pytest.raises(ValueError):
        check_file(str(f), expected_ext=".md")


def test_check_file_validates_expected_ext_format(tmp_path):
    f = tmp_path / "a.md"
    f.write_text("x", encoding="utf-8")

    with pytest.raises(ValueError):
        check_file(str(f), expected_ext="md")  # missing dot
