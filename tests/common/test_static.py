import pytest

from pymdtools.common import static


def test_static_sets_attributes_on_function():
    @static(a=1, b="x", c=None)
    def f():
        return 0

    assert f.a == 1
    assert f.b == "x"
    assert f.c is None


def test_static_attributes_can_be_mutated_by_function_logic():
    @static(counter=0)
    def f():
        f.counter += 1
        return f.counter

    assert f() == 1
    assert f() == 2
    assert f.counter == 2


def test_static_does_not_wrap_function_identity():
    def original():
        """doc"""
        return 1

    decorated = static(x=1)(original)

    # same callable object (no wrapper)
    assert decorated is original
    assert decorated.__name__ == "original"
    assert decorated.__doc__ == "doc"
    assert decorated.x == 1


def test_static_overwrites_existing_attribute():
    @static(x=1)
    def f():
        return 0

    assert f.x == 1

    # apply again with different value
    f2 = static(x=2)(f)
    assert f2 is f
    assert f.x == 2
