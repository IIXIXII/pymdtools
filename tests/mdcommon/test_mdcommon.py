from __future__ import annotations

import json
from pathlib import Path

import pytest

import pymdtools.mdcommon as mdcommon


def test_is_external_link_and_domain_name() -> None:
    assert mdcommon.is_external_link("https://example.com/page")
    assert mdcommon.is_external_link("mailto:contact@example.com")
    assert not mdcommon.is_external_link("www.example.com")
    assert not mdcommon.is_external_link("http://")
    assert not mdcommon.is_external_link("http://[invalid")

    assert mdcommon.get_domain_name("https://example.com/page") == "example.com"
    assert mdcommon.get_domain_name("mailto:contact@example.com") == "contact@example.com"
    assert mdcommon.get_domain_name("docs/page.md") == "docs/page.md"


def test_link_properties_and_string_representation() -> None:
    link = mdcommon.Link()

    assert link.name is None
    assert link.label is None
    assert link.url is None
    assert link.title is None

    link.name = "Name"
    link.label = "Label"
    link.url = "target.md"
    link.title = "Title"

    assert link["name"] == "Label"
    assert link.name == "Label"
    assert link.label == "Label"
    assert link.url == "target.md"
    assert link.title == "Title"
    assert str(link) == "Link name='Label' title='Title'\n      url=target.md\n"

    link.name = None
    link.url = None
    link.title = None

    assert "name" not in link
    assert "url" not in link
    assert "title" not in link

    link["name"] = 3
    link["url"] = 4
    link["title"] = 5

    assert link.name is None
    assert link.url is None
    assert link.title is None


def test_search_link_in_md_text_finds_inline_and_reference_links_without_mutating_previous() -> None:
    previous = [{"name": "old", "url": "old.md", "title": None, "line": 1}]
    text = (
        "before\n"
        '[Label](docs/page.md "Title")\n'
        "[Ref][id1]\n"
        '[id1]: https://example.com/ref "Ref title"\n'
        "[Missing][missing]\n"
        '[other]: ignored.md "Ignored"\n'
    )

    links = mdcommon.search_link_in_md_text(text, previous_links=previous)

    assert previous == [{"name": "old", "url": "old.md", "title": None, "line": 1}]
    assert links == [
        {"name": "old", "url": "old.md", "title": None, "line": 1},
        {"name": "Label", "url": "docs/page.md", "title": "Title", "line": 2},
        {"name": "Ref", "url": "https://example.com/ref", "title": "Ref title", "line": 4},
    ]


def test_search_link_in_md_text_json_is_deterministic() -> None:
    out = mdcommon.search_link_in_md_text_json("[A](a.md)")

    assert json.loads(out) == [{"line": 1, "name": "A", "title": None, "url": "a.md"}]
    assert out.startswith("[\n  {")


def test_search_link_in_md_file_reads_checked_file(tmp_path: Path) -> None:
    source = tmp_path / "doc.md"
    source.write_text("[A](a.md)", encoding="utf-8")

    assert mdcommon.search_link_in_md_file(source, encoding="utf-8") == [
        {"line": 1, "name": "A", "title": None, "url": "a.md"}
    ]


def test_update_links_in_md_text_updates_single_and_multiple_inline_links() -> None:
    text = 'A [old](old.md "old title") B [google](old-google.md)'

    out = mdcommon.update_links_in_md_text(
        text,
        {"name_to_replace": "old", "name": "new", "url": "new.md", "title": "New title"},
    )

    assert out == 'A [new](new.md "New title") B [google](old-google.md)'

    out = mdcommon.update_links_in_md_text(
        out,
        [{"name": "google", "url": "https://google.example"}],
    )

    assert out == 'A [new](new.md "New title") B [google](https://google.example)'


def test_update_links_in_md_text_updates_reference_links_without_mutating_input() -> None:
    new_link = {"name": "Ref", "url": "new.md", "title": "new title"}
    text = "before [Ref][id1]\n[id1]: old.md\n"

    out = mdcommon.update_links_in_md_text(text, new_link)

    assert out == 'before [Ref][id1]\n[id1]: new.md "new title"\n'
    assert "id_link" not in new_link


def test_update_link_in_md_text_returns_unchanged_when_no_reference_match() -> None:
    assert (
        mdcommon.update_link_in_md_text(
            "No target here",
            "missing",
            {"name": "missing", "url": "new.md"},
        )
        == "No target here"
    )


def test_update_link_from_old_link_inline_reference_and_no_match() -> None:
    old_link = {"name": "Old", "url": "old.md"}
    new_link = {"name": "New", "url": "new.md"}

    assert mdcommon.update_link_from_old_link("[Old](old.md)", old_link, new_link) == "[New](new.md)"
    assert mdcommon.update_link_from_old_link("[Old](other.md)", old_link, new_link) == "[Old](other.md)"

    reference_text = "[Old][id1]\n[id1]: old.md\n"
    out = mdcommon.update_link_from_old_link(reference_text, old_link, new_link)

    assert out == "[New][id1]\n[id1]: new.md\n"
    assert "id_link" not in new_link


def test_update_links_from_old_link_applies_multiple_replacements() -> None:
    out = mdcommon.update_links_from_old_link(
        "[A](a.md) [B](b.md)",
        [
            ({"name": "A", "url": "a.md"}, {"name": "AA", "url": "aa.md"}),
            ({"name": "B", "url": "b.md"}, {"name": "BB", "url": "bb.md"}),
        ],
    )

    assert out == "[AA](aa.md) [BB](bb.md)"


def test_move_base_path_in_md_text_only_updates_relative_links() -> None:
    text = "[Local](docs/page.md) [External](https://example.com/page)"

    out = mdcommon.move_base_path_in_md_text(text, "base folder")

    assert out == "[Local](base-folder/docs/page.md) [External](https://example.com/page)"


def test_sub_string_helpers() -> None:
    assert mdcommon.sub_string_link_md("", {"name": "A", "url": "a.md"}) == "[A](a.md)"
    assert (
        mdcommon.sub_string_link_md("", {"name": "A", "url": "a.md", "title": "Title"})
        == '[A](a.md "Title")'
    )
    assert mdcommon.sub_string_link_by_ref_md("", {"url": "a.md"}) == "[]: a.md\n"
    assert (
        mdcommon.sub_string_link_by_ref_md(
            "",
            {"id_link": "id1", "url": "a.md", "title": "Title"},
        )
        == '[id1]: a.md "Title"\n'
    )
    assert mdcommon.sub_string_name_by_ref_md("", {"name": "A", "id_link": "id1"}) == "[A][id1]"


def test_missing_required_link_fields_raise_type_error() -> None:
    with pytest.raises(TypeError, match="url"):
        mdcommon.sub_string_link_md("", {"name": "A"})

    with pytest.raises(TypeError, match="name"):
        mdcommon.sub_string_name_by_ref_md("", {"id_link": "id1"})
