import pytest

from pymdtools.common.core import check_len


def test_check_len_ok_returns_same_object():
    data = [1]
    out = check_len(data, expected=1, name="data")
    assert out is data


def test_check_len_raises_on_wrong_length():
    with pytest.raises(ValueError, match=r"items must have length 2, got 1"):
        check_len([1], expected=2, name="items")


def test_check_len_negative_expected_raises():
    with pytest.raises(ValueError):
        check_len([1], expected=-1)


def test_check_len_non_sized_raises_typeerror():
    with pytest.raises(TypeError):
        check_len(123, expected=1)  # int has no len()
