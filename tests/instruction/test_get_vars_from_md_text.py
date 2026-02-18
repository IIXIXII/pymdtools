from __future__ import annotations

import pytest

from pymdtools.instruction import get_vars_from_md_text, unescape_var_value

def test_get_vars_supports_slash_names():
    text = '<!-- var(a/b)="1" -->'
    assert get_vars_from_md_text(text) == {"a/b": "1"}

def test_unescape_var_value_basic():
    assert unescape_var_value(r"ab") == "ab"
    assert unescape_var_value(r"he said \"hi\"") == 'he said "hi"'
    assert unescape_var_value(r"it\'s ok") == "it's ok"
    assert unescape_var_value(r"c:\\tmp\\file") == r"c:\tmp\file"
    assert unescape_var_value(r"line1\nline2") == "line1\nline2"
    assert unescape_var_value(r"tab\tX") == "tab\tX"


def test_get_vars_from_md_text_interprets_escapes():
    text = r'<!-- var(a)= "he said \"hi\"\nline2" -->'
    out = get_vars_from_md_text(text)
    assert out["a"] == 'he said "hi"\nline2'


def test_get_vars_from_md_text_single_quotes_interprets():
    text = r"<!-- var(a)= 'it\'s ok' -->"
    out = get_vars_from_md_text(text)
    assert out["a"] == "it's ok"


def test_get_vars_from_md_text_multiple_vars():
    text = r'<!-- var(a)= "1" --><!-- var(b)= "2" -->'
    assert get_vars_from_md_text(text) == {"a": "1", "b": "2"}


def test_get_vars_from_md_text_duplicate_raises():
    text = r'<!-- var(a)= "1" --><!-- var(a)= "2" -->'
    with pytest.raises(ValueError, match=r"duplicate var\(a\)"):
        get_vars_from_md_text(text)
