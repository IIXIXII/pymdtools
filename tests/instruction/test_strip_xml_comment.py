import pytest

from pymdtools.instruction import strip_xml_comment


def test_strip_xml_comment_removes_simple_comment():
    text = "Hello <!-- comment --> world"
    assert strip_xml_comment(text) == "Hello  world"


def test_strip_xml_comment_removes_multiline_comment():
    text = "A\n<!-- line1\nline2 -->\nB"
    assert strip_xml_comment(text) == "A\n\nB"


def test_strip_xml_comment_removes_multiple_comments():
    text = "a <!-- c1 --> b <!-- c2 --> c"
    assert strip_xml_comment(text) == "a  b  c"


def test_strip_xml_comment_no_comment_is_noop():
    text = "No comment here"
    assert strip_xml_comment(text) == "No comment here"


def test_strip_xml_comment_empty_string():
    assert strip_xml_comment("") == ""


def test_strip_xml_comment_raises_on_non_string():
    with pytest.raises(TypeError):
        strip_xml_comment(None)  # type: ignore[arg-type]
