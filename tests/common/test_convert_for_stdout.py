# tests/test_convert_for_stdout.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pytest

from pymdtools.common import convert_for_stdout


@dataclass
class DummyStream:
    """Minimal TextIO-like object for tests."""
    encoding: Optional[str] = None


def test_convert_for_stdout_uses_stream_encoding_utf8_ok() -> None:
    s = DummyStream(encoding="utf-8")
    text = "é€— ✅"
    out = convert_for_stdout(text, stream=s, errors="strict")
    assert out == text


def test_convert_for_stdout_replaces_unrepresentable_chars_cp1252() -> None:
    # CP1252 cannot represent "€" is representable, but "—" yes, "✅" not.
    s = DummyStream(encoding="cp1252")
    text = "OK ✅"
    out = convert_for_stdout(text, stream=s, errors="replace")
    assert out != text
    assert "OK " in out
    assert "✅" not in out  # replaced


def test_convert_for_stdout_uses_fallback_when_stream_has_no_encoding() -> None:
    s = DummyStream(encoding=None)
    text = "hello"
    out = convert_for_stdout(text, stream=s, fallback_encoding="utf-8")
    assert out == "hello"


def test_convert_for_stdout_fallback_when_encoding_unknown() -> None:
    s = DummyStream(encoding="x-unknown-encoding")
    text = "hello"
    out = convert_for_stdout(text, stream=s, fallback_encoding="utf-8")
    assert out == "hello"


def test_convert_for_stdout_strict_raises_when_not_encodable() -> None:
    s = DummyStream(encoding="ascii")
    text = "é"  # not ASCII
    with pytest.raises(UnicodeEncodeError):
        convert_for_stdout(text, stream=s, errors="strict")