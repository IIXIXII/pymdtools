from __future__ import annotations

import pytest

from pymdtools.instruction import set_title_in_md_text


def test_preserve_replaces_setext_as_setext():
    text = "Old\n===\n\nBody\n"
    out = set_title_in_md_text(text, "New Title", style="preserve")
    assert out.startswith("New Title\n" + ("=" * len("New Title")) + "\n")
    assert "Old\n" not in out
    assert "Body\n" in out


def test_preserve_replaces_atx_as_atx():
    text = "# Old Title\n\nBody\n"
    out = set_title_in_md_text(text, "New Title", style="preserve")
    assert out.startswith("# New Title\n")
    assert "# Old Title\n" not in out
    assert "Body\n" in out


def test_force_setext_on_atx_title():
    text = "# Old\n\nBody\n"
    out = set_title_in_md_text(text, "New", style="setext")
    assert out.startswith("New\n===\n")
    assert "# Old\n" not in out


def test_force_atx_on_setext_title():
    text = "Old\n===\n\nBody\n"
    out = set_title_in_md_text(text, "New", style="atx")
    assert out.startswith("# New\n")
    assert "Old\n===\n" not in out


def test_insert_when_missing_default_preserve_inserts_setext():
    text = "Body\n"
    out = set_title_in_md_text(text, "Title", style="preserve")
    assert out.startswith("Title\n=====\n\n")
    assert out.endswith("Body\n")


def test_insert_when_missing_force_atx():
    text = "Body\n"
    out = set_title_in_md_text(text, "Title", style="atx")
    assert out.startswith("# Title\n\n")
    assert out.endswith("Body\n")


def test_does_not_replace_other_occurrences_of_old_title():
    text = "# Old\n\nOld appears in body.\n"
    out = set_title_in_md_text(text, "New", style="preserve")
    assert out.startswith("# New\n")
    assert "Old appears in body.\n" in out


def test_reject_blank_title():
    with pytest.raises(ValueError):
        set_title_in_md_text("x", "   ", style="preserve")


def test_reject_invalid_style():
    with pytest.raises(ValueError):
        set_title_in_md_text("x", "Title", style="bad")  # type: ignore[arg-type]


def test_type_errors():
    with pytest.raises(TypeError):
        set_title_in_md_text(None, "T")  # type: ignore[arg-type]
