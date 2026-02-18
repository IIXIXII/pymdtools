import pytest

from pymdtools.instruction import get_refs_from_md_text

def test_get_refs_from_md_text_no_refs():
    assert get_refs_from_md_text("hello") == {}


def test_get_refs_from_md_text_single_ref():
    md = (
        "before\n"
        "<!-- begin-ref(foo) -->\n"
        "content\n"
        "<!-- end-ref -->\n"
        "after\n"
    )
    out = get_refs_from_md_text(md)
    assert out == {"foo": "\ncontent\n"}


def test_get_refs_from_md_text_multiple_refs_sequential():
    md = (
        "<!-- begin-ref(a) -->A<!-- end-ref -->\n"
        "mid\n"
        "<!-- begin-ref(b) -->B\nB2<!-- end-ref -->"
    )
    out = get_refs_from_md_text(md)
    assert out["a"] == "A"
    assert out["b"] == "B\nB2"


def test_get_refs_from_md_text_duplicate_key_raises():
    md = (
        "<!-- begin-ref(x) -->one<!-- end-ref -->\n"
        "<!-- begin-ref(x) -->two<!-- end-ref -->"
    )
    with pytest.raises(ValueError, match=r"duplicate begin-ref\(x\)"):
        get_refs_from_md_text(md)


def test_get_refs_from_md_text_missing_end_raises():
    md = "<!-- begin-ref(x) -->no end"
    with pytest.raises(ValueError, match=r"begin-ref\(x\) without end-ref"):
        get_refs_from_md_text(md)


def test_get_refs_from_md_text_whitespace_variants():
    md = (
        "<!--   begin-ref(my_ref-1)   -->X"
        "<!--  end-ref  -->"
    )
    out = get_refs_from_md_text(md)
    assert out == {"my_ref-1": "X"}


def test_get_refs_from_md_text_previous_refs_are_copied():
    prev = {"a": "A"}
    md = "<!-- begin-ref(b) -->B<!-- end-ref -->"
    out = get_refs_from_md_text(md, previous_refs=prev)

    assert out == {"a": "A", "b": "B"}
    assert prev == {"a": "A"}  # no side effect
