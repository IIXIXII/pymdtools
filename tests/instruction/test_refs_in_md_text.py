import pytest

from pymdtools.instruction import refs_in_md_text
from pymdtools.instruction import _BEGIN_INCLUDE_RE

def test_include_regex_variants():
    text = """
    <!--begin-include(header)-->
    <!-- begin-include(menu-bar) -->
    <!--   begin-include( footer )   -->
    """
    assert _BEGIN_INCLUDE_RE.findall(text) == ["header", "menu-bar", "footer"]

def test_refs_in_md_text_single_include():
    text = "<!-- begin-include(header) -->"
    assert refs_in_md_text(text) == ["header"]


def test_refs_in_md_text_multiple_includes():
    text = """
    <!-- begin-include(header) -->
    Some content
    <!-- begin-include(footer) -->
    """
    assert refs_in_md_text(text) == ["header", "footer"]


def test_refs_in_md_text_no_include():
    text = "No includes here"
    assert refs_in_md_text(text) == []


def test_refs_in_md_text_with_extra_spaces():
    text = "<!--    begin-include(menu-bar)    -->"
    assert refs_in_md_text(text) == ["menu-bar"]


def test_refs_in_md_text_invalid_name_not_matched():
    # contains illegal char '!'
    text = "<!-- begin-include(header!) -->"
    assert refs_in_md_text(text) == []


def test_refs_in_md_text_type_error():
    with pytest.raises(TypeError):
        refs_in_md_text(None)  # type: ignore
