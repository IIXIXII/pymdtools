from __future__ import annotations

import pytest

from pymdtools.instruction import include_vars_to_md_text


def test_include_vars_replaces_block_content():
    text = "A\n<!-- begin-var(x) -->OLD<!-- end-var -->\nB\n"
    out = include_vars_to_md_text(text, {"x": "NEW"})
    assert "NEW" in out
    assert "OLD" not in out
    assert "begin-var(x)" in out
    assert "end-var" in out


def test_include_vars_unknown_var_raises_by_default():
    text = "<!-- begin-var(x) -->OLD<!-- end-var -->"
    with pytest.raises(KeyError):
        include_vars_to_md_text(text, {}, error_if_var_not_found=True)


def test_include_vars_unknown_var_can_be_ignored():
    text = (
        "<!-- begin-var(x) -->X<!-- end-var -->\n"
        "<!-- begin-var(y) -->Y<!-- end-var -->\n"
    )
    out = include_vars_to_md_text(text, {"y": "YY"}, error_if_var_not_found=False)
    assert "X" in out       # bloc x inchangé
    assert "YY" in out      # bloc y remplacé
    assert "Y" not in out   # contenu original de y supprimé


def test_include_vars_supports_slash_names():
    text = "<!-- begin-var(a/b) -->X<!-- end-var -->"
    out = include_vars_to_md_text(text, {"a/b": "Y"})
    assert "Y" in out
    assert "X" not in out
