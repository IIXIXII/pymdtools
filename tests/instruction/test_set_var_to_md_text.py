from __future__ import annotations

import pytest

from pymdtools.instruction import set_var_to_md_text

def test_set_var_supports_slash_names():
    out = set_var_to_md_text("Body\n", "a/b", "1")
    assert '<!-- var(a/b)="1" -->' in out

def test_set_var_replaces_existing_var():
    text = '<!-- var(a)="1" -->\nBody\n'
    out = set_var_to_md_text(text, "a", "2")
    assert '<!-- var(a)="2" -->' in out
    assert '<!-- var(a)="1" -->' not in out
    assert "Body" in out


def test_set_var_adds_when_missing_at_top():
    text = "Body\n"
    out = set_var_to_md_text(text, "a", "1")
    assert out.startswith('<!-- var(a)="1" -->')
    assert "Body" in out


def test_set_var_adds_after_existing_vars():
    text = '<!-- var(a)="1" -->\n<!-- var(b)="2" -->\nBody\n'
    out = set_var_to_md_text(text, "c", "3")
    assert '<!-- var(c)="3" -->' in out
    assert out.index('<!-- var(b)="2" -->') < out.index('<!-- var(c)="3" -->')
    assert "Body" in out


def test_set_var_escapes_quotes_and_newlines():
    text = "Body\n"
    out = set_var_to_md_text(text, "a", 'he said "hi"\nline2')
    assert r'<!-- var(a)="he said \"hi\"\nline2" -->' in out


def test_set_var_added_after_include_file_directives():
    text = (
        '<!-- var(a)="1" -->\n'
        '<!-- include-file(tpl) some content -->\n'
        "Body\n"
    )
    out = set_var_to_md_text(text, "b", "2")

    # b should be inserted after include-file directive block
    pos_include = out.index("include-file(tpl)")
    pos_b = out.index('<!-- var(b)="2" -->')
    assert pos_include < pos_b
    assert "Body" in out


def test_set_var_rejects_invalid_name():
    with pytest.raises(ValueError):
        set_var_to_md_text("x", "bad name", "1")


def test_set_var_type_errors():
    with pytest.raises(TypeError):
        set_var_to_md_text(None, "a", "1")  # type: ignore[arg-type]
