from __future__ import annotations

import pytest

from pymdtools.instruction import get_title_from_md_text


def test_title_setext_h1():
    text = "My Title\n=====\n\nBody\n"
    assert get_title_from_md_text(text) == "My Title"


def test_title_atx_h1():
    text = "# My Title\n\nBody\n"
    assert get_title_from_md_text(text) == "My Title"


def test_title_atx_h1_with_trailing_hashes():
    text = "# My Title ####\nBody\n"
    assert get_title_from_md_text(text) == "My Title"


def test_title_ignores_xml_comments():
    text = "<!-- # Fake -->\n# Real Title\n"
    assert get_title_from_md_text(text) == "Real Title"


def test_title_none_when_missing():
    text = "No title here\n\nBody\n"
    assert get_title_from_md_text(text) is None


def test_title_does_not_match_h2_as_h1():
    text = "## Not H1\n"
    assert get_title_from_md_text(text) is None


def test_title_return_match():
    text = "# Title\n"
    m = get_title_from_md_text(text, return_match=True)
    assert m is not None
    assert m.group("title").strip() == "Title"


def test_title_type_error():
    with pytest.raises(TypeError):
        get_title_from_md_text(None)  # type: ignore[arg-type]
