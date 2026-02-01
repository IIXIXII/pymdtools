import pytest

from pymdtools.common import get_valid_filename


def test_replaces_invalid_characters():
    assert get_valid_filename('a:b*c?.txt') == 'a_b_c_.txt'


def test_removes_trailing_dot_and_space():
    assert get_valid_filename("test. ") == "test"


def test_strips_whitespace_by_default():
    assert get_valid_filename("  test  ") == "test"


def test_reserved_windows_names_are_modified():
    assert get_valid_filename("CON") == "CON_"
    assert get_valid_filename("nul.txt") == "nul_.txt"


def test_control_characters_are_removed():
    assert get_valid_filename("a\x00b\x1fc") == "a_b_c"


def test_custom_replacement():
    assert get_valid_filename("a:b", replacement="-") == "a-b"


def test_empty_filename_raises():
    with pytest.raises(ValueError):
        get_valid_filename("   ")


def test_non_string_filename_raises():
    with pytest.raises(ValueError):
        get_valid_filename(123)  # type: ignore[arg-type]
