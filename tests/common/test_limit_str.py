import pytest

from pymdtools.common import limit_str


def test_limit_str_basic():
    assert limit_str("a b c d", limit=3, sep=" ", min_last_word=1) == "a b"
    assert limit_str("aa bb cc dd", limit=5, sep=" ") == "aa bb"


def test_limit_str_does_not_exceed_limit():
    out = limit_str("hello world", limit=7, sep=" ")
    assert out in {"hello"}  # "hello" (5) ok, "hello world" (11) no
    assert len(out) <= 7


def test_limit_str_respects_min_last_word():
    # 'a' ignored if min_last_word=2
    assert limit_str("a bb ccc", limit=10, sep=" ", min_last_word=2) == "bb ccc"


def test_limit_str_handles_consecutive_separators():
    assert limit_str("aa  bb   ccc", limit=20, sep=" ") == "aa bb ccc"


def test_limit_str_limit_zero_returns_empty():
    assert limit_str("aa bb", limit=0, sep=" ") == ""


def test_limit_str_invalid_sep_raises():
    with pytest.raises(ValueError):
        limit_str("aa bb", limit=5, sep="")


def test_limit_str_negative_limit_raises():
    with pytest.raises(ValueError):
        limit_str("aa bb", limit=-1, sep=" ")


def test_limit_str_negative_min_last_word_raises():
    with pytest.raises(ValueError):
        limit_str("aa bb", limit=5, sep=" ", min_last_word=-1)
