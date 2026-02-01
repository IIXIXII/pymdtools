import sys
import pytest

from pymdtools.common import convert_for_stdout


def test_convert_for_stdout_respects_explicit_coding_out():
    assert convert_for_stdout("é", coding_in="utf-8", coding_out="latin-1") == "Ã©"


def test_convert_for_stdout_fallbacks_to_utf8_when_stdout_encoding_is_none(monkeypatch):
    class DummyStdout:
        encoding = None

    monkeypatch.setattr(sys, "stdout", DummyStdout(), raising=False)
    assert convert_for_stdout("hello", coding_in="utf-8", coding_out=None) == "hello"


def test_convert_for_stdout_uses_stdout_encoding_when_available(monkeypatch):
    class DummyStdout:
        encoding = "latin-1"

    monkeypatch.setattr(sys, "stdout", DummyStdout(), raising=False)
    assert convert_for_stdout("é", coding_in="utf-8", coding_out=None) == "Ã©"
