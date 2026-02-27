import pytest

from pymdtools.common import get_flat_filename


def test_get_flat_filename_basic():
    assert get_flat_filename("Hello World") == "hello_world"


def test_get_flat_filename_removes_punctuation():
    assert get_flat_filename("Hello, world! (test)") == "hello_world_test"


def test_get_flat_filename_unicode_transliteration():
    assert get_flat_filename("éàç été") == "eac_ete"


def test_get_flat_filename_custom_replacement():
    assert get_flat_filename("Hello World", replacement="-") == "hello-world"


def test_get_flat_filename_windows_reserved_name():
    assert get_flat_filename("CON") == "con_"


def test_get_flat_filename_only_invalid_chars_raises():
    with pytest.raises(ValueError):
        get_flat_filename("!!!")

