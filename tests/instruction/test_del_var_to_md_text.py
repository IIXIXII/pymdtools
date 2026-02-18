from __future__ import annotations

import pytest

from pymdtools.instruction import del_var_to_md_text


def test_del_var_removes_matching_var_only():
    text = '<!-- var(a)="1" --><!-- var(b)="2" -->'
    out = del_var_to_md_text(text, "a")
    assert '<!-- var(a)="' not in out
    assert '<!-- var(b)="2" -->' in out


def test_del_var_removes_all_occurrences():
    text = '<!-- var(a)="1" -->\nX\n<!-- var(a)="2" -->\n'
    out = del_var_to_md_text(text, "a")
    assert "var(a)" not in out
    assert "X" in out


def test_del_var_supports_slash_names():
    text = '<!-- var(a/b)="1" --><!-- var(c)="2" -->'
    out = del_var_to_md_text(text, "a/b")
    assert "var(a/b)" not in out
    assert 'var(c)="2"' in out


def test_del_var_no_match_returns_same_text():
    text = "Body\n"
    out = del_var_to_md_text(text, "a")
    assert out == text


def test_del_var_invalid_name_raises():
    with pytest.raises(ValueError):
        del_var_to_md_text("x", "bad name")


def test_del_var_type_errors():
    with pytest.raises(TypeError):
        del_var_to_md_text(None, "a")  # type: ignore[arg-type]
