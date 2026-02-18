from __future__ import annotations

import pytest

from pymdtools.instruction import include_refs_to_md_text


def test_include_replaces_inner_content_and_keeps_markers():
    text = "A\n<!-- begin-include(x) -->\nOLD\n<!-- end-include -->\nB\n"
    refs = {"x": "NEW\n"}

    out = include_refs_to_md_text(text, refs)

    assert "<!-- begin-include(x) -->" in out
    assert "<!-- end-include -->" in out
    assert "NEW\n" in out
    assert "OLD" not in out


def test_include_multiple_blocks():
    text = (
        "<!-- begin-include(a) -->A0<!-- end-include -->\n"
        "mid\n"
        "<!-- begin-include(b) -->B0<!-- end-include -->\n"
    )
    refs = {"a": "AA", "b": "BB"}

    out = include_refs_to_md_text(text, refs)

    assert "AA" in out
    assert "BB" in out
    assert "A0" not in out
    assert "B0" not in out


def test_include_unknown_key_raises_by_default():
    text = "<!-- begin-include(x) -->X<!-- end-include -->"
    with pytest.raises(KeyError):
        include_refs_to_md_text(text, {}, error_if_no_key=True)


def test_include_unknown_key_ignored_keeps_block_and_continues():
    text = (
        "<!-- begin-include(x) -->X<!-- end-include -->\n"
        "<!-- begin-include(y) -->Y<!-- end-include -->\n"
    )
    refs = {"y": "YY"}

    out = include_refs_to_md_text(text, refs, error_if_no_key=False)

    # x block unchanged
    assert "<!-- begin-include(x) -->" in out
    assert "X" in out
    assert "<!-- end-include -->" in out

    # y block replaced
    assert "YY" in out
    assert "Y" not in out  # original inner content removed


def test_include_missing_end_raises():
    text = "<!-- begin-include(x) -->no end"
    refs = {"x": "X"}
    with pytest.raises(ValueError):
        include_refs_to_md_text(text, refs)


def test_include_non_string_text_raises():
    with pytest.raises(TypeError):
        include_refs_to_md_text(None, {})  # type: ignore[arg-type]
