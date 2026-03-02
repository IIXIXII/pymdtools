# tests/test_common_core.py
# -*- coding: utf-8 -*-

import pytest

from pymdtools.common.core import Constant, check_len, handle_exception, static


# =============================================================================
# handle_exception
# =============================================================================

def test_handle_exception_wraps_and_enriches_message_and_preserves_cause():
    @handle_exception("Error while converting file", filename="File", output_dir="Output")
    def convert(*, filename: str, output_dir: str) -> None:
        raise ValueError("Invalid format")

    with pytest.raises(RuntimeError) as excinfo:
        convert(filename="doc.md", output_dir="/tmp")

    # Original exception should be chained as __cause__
    assert isinstance(excinfo.value.__cause__, ValueError)
    assert str(excinfo.value.__cause__) == "Invalid format"

    msg = str(excinfo.value)
    # Must contain original message then enriched context (stable formatting)
    assert "Invalid format" in msg
    assert "Error while converting file (convert)" in msg
    assert "File : doc.md" in msg
    assert "Output : /tmp" in msg


def test_handle_exception_only_prints_present_kwargs():
    @handle_exception("Action", filename="File", missing="Missing")
    def f(*, filename: str) -> None:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError) as excinfo:
        f(filename="a.md")

    msg = str(excinfo.value)
    assert "File : a.md" in msg
    # 'missing' label must not appear because kw arg was not passed
    assert "Missing :" not in msg


def test_handle_exception_preserves_return_value_when_no_error():
    @handle_exception("Action", x="X")
    def add(*, x: int, y: int) -> int:
        return x + y

    assert add(x=2, y=3) == 5


# =============================================================================
# Constant
# =============================================================================

def test_constant_descriptor_readable_from_class_and_instance():
    class C:
        A = Constant("v")

    assert C.A == "v"
    assert C().A == "v"
    # .value property
    assert C.A == "v"


def test_constant_descriptor_blocks_instance_assignment_and_delete():
    class C:
        A = Constant("v")

    c = C()

    with pytest.raises(ValueError, match=r"can't change a constant value"):
        c.A = "x"

    with pytest.raises(ValueError, match=r"Cannot delete a constant value"):
        del c.A


def test_constant_allows_class_level_rebinding_by_design():
    class C:
        A = Constant("v")

    # Rebinding at class level replaces the descriptor (documented behavior)
    C.A = "x"
    assert C.A == "x"
    assert C().A == "x"


# =============================================================================
# static
# =============================================================================

def test_static_attaches_attributes_to_function():
    @static(counter=0, label="ok")
    def f() -> int:
        f.counter += 1
        return f.counter

    assert getattr(f, "counter") == 0
    assert getattr(f, "label") == "ok"

    assert f() == 1
    assert f() == 2
    assert f.counter == 2


def test_static_overwrites_existing_attribute():
    @static(x=1)
    def f() -> None:
        return None

    assert f.x == 1

    # Reapply: should overwrite
    f2 = static(x=2)(f)
    assert f2 is f
    assert f.x == 2


# =============================================================================
# check_len
# =============================================================================

def test_check_len_ok_returns_same_object():
    obj = [1]
    out = check_len(obj, expected=1, name="items")
    assert out is obj


def test_check_len_raises_on_negative_expected():
    with pytest.raises(ValueError, match=r"expected length must be >= 0"):
        check_len([1], expected=-1)


def test_check_len_raises_when_len_mismatch():
    with pytest.raises(ValueError, match=r"items must have length 2, got 1"):
        check_len([1], expected=2, name="items")


def test_check_len_raises_typeerror_when_no_len():
    class NoLen:
        pass

    with pytest.raises(TypeError, match=r"thing does not support len"):
        check_len(NoLen(), expected=1, name="thing")