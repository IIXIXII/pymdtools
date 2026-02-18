from __future__ import annotations

import pytest

from pymdtools.instruction import search_include_vars_to_md_text


def test_search_include_vars_to_md_text_replaces_using_local_vars():
    text = (
        '<!-- var(x)="VALUE" -->\n'
        'A\n'
        '<!-- begin-var(x) -->OLD<!-- end-var -->\n'
        'B\n'
    )
    out = search_include_vars_to_md_text(text)
    assert "VALUE" in out
    assert "OLD" not in out


def test_search_include_vars_to_md_text_unknown_var_raises():
    text = "A\n<!-- begin-var(x) -->OLD<!-- end-var -->\nB\n"
    with pytest.raises(KeyError):
        search_include_vars_to_md_text(text, error_if_var_not_found=True)


def test_search_include_vars_to_md_text_unknown_var_can_be_ignored():
    text = (
        '<!-- var(y)="YY" -->\n'
        '<!-- begin-var(x) -->X<!-- end-var -->\n'
        '<!-- begin-var(y) -->Y<!-- end-var -->\n'
    )
    out = search_include_vars_to_md_text(text, error_if_var_not_found=False)
    assert "X" in out          # bloc x inchangé
    assert "YY" in out         # bloc y remplacé
    assert "Y" not in out      # contenu original de y supprimé
