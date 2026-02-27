# tests/test_handle_exception.py
from __future__ import annotations

import pytest

from pymdtools.common import handle_exception


@handle_exception(
    "Error while converting file",
    filename="File",
    output="Output directory",
)
def _fail_convert(*, filename: str, output: str) -> None:
    raise ValueError("Invalid format")


@handle_exception(
    "Error while processing",
    filename="File",
)
def _fail_with_positional(filename: str) -> None:
    # positional arg is not included (current decorator behavior)
    raise RuntimeError("Boom")


@handle_exception(
    "Error while doing things",
    a="A",
    b="B",
)
def _fail_partial_kwargs(*, a: str, b: str, c: str) -> None:
    # c is not mapped; should not appear
    raise KeyError("oops")


def test_handle_exception_wraps_exception_type() -> None:
    with pytest.raises(RuntimeError) as ei:
        _fail_convert(filename="doc.md", output="/tmp")

    ex = ei.value
    assert isinstance(ex, RuntimeError)
    assert isinstance(ex.__cause__, ValueError)


def test_handle_exception_message_contains_action_func_and_kwargs() -> None:
    with pytest.raises(RuntimeError) as ei:
        _fail_convert(filename="doc.md", output="/tmp")

    msg = str(ei.value)

    # Original exception message is included
    assert "Invalid format" in msg

    # Context header
    assert "Error while converting file (_fail_convert)" in msg

    # Mapped keyword arguments included
    assert "File : doc.md" in msg
    assert "Output directory : /tmp" in msg


def test_handle_exception_only_includes_present_kwargs() -> None:
    with pytest.raises(RuntimeError) as ei:
        _fail_partial_kwargs(a="x", b="y", c="z")

    msg = str(ei.value)
    assert "Error while doing things (_fail_partial_kwargs)" in msg
    assert "A : x" in msg
    assert "B : y" in msg

    # c is not mapped and must not appear
    assert "c" not in msg
    assert "z" not in msg


def test_handle_exception_does_not_print_positional_args_current_behavior() -> None:
    with pytest.raises(RuntimeError) as ei:
        _fail_with_positional("doc.md")

    msg = str(ei.value)
    assert "Error while processing (_fail_with_positional)" in msg

    # Only keyword args are displayed; positional filename is not printed
    assert "File :" not in msg
    assert "doc.md" not in msg  # the only "doc.md" value should not appear