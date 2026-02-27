import pytest

from pymdtools.common import to_ascii


def test_to_ascii_basic_latin():
    assert to_ascii("éàç") == "eac"


def test_to_ascii_preserves_ascii():
    assert to_ascii("abc-XYZ_123") == "abc-XYZ_123"

