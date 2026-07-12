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


def test_search_link_in_md_text_ignores_markdown_images() -> None:
    text = "![Logo](img/logo.png)\n![Logo ref][logo]\n[logo]: img/logo-ref.png\n[Doc](doc.md)"

    assert mdcommon.search_link_in_md_text(text) == [
        {"name": "Doc", "url": "doc.md", "title": None, "line": 4}
    ]


def test_search_link_in_md_text_ignores_code_spans_and_fences() -> None:
    text = (
        "`[Inline](inline.md)`\n"
        "```markdown\n[Fenced](fenced.md)\n```\n"
        "~~~\n[Ref][hidden]\n[hidden]: hidden.md\n~~~\n"
        "[Real](real.md)\n"
    )

    assert mdcommon.search_link_in_md_text(text) == [
        {"name": "Real", "url": "real.md", "title": None, "line": 9}
    ]


def test_markdown_code_range_edge_cases() -> None:
    assert mdcommon.merge_ranges([(1, 1), (0, 2), (1, 3)]) == [(0, 3)]
    assert mdcommon.markdown_code_ranges("```\nunclosed\n") == [
        (0, len("```\nunclosed\n"))
    ]
    assert mdcommon.markdown_code_ranges("``code``") == [(0, 8)]
    assert mdcommon.markdown_code_ranges("`") == []
    assert mdcommon.markdown_code_ranges("`unclosed") == []
    assert mdcommon.markdown_code_ranges("`a``b`") == [(0, 6)]
    assert mdcommon.markdown_code_ranges(r"\`literal") == []
    assert mdcommon.markdown_code_ranges(r"\\`code`") == [(2, 8)]

    spanning_fence = "`open\n```\ninside\n```\n`"
    ranges = mdcommon.markdown_code_ranges(spanning_fence)
    assert ranges == [(0, len(spanning_fence))]
    assert not mdcommon.position_in_ranges(0, [(2, 3)])


def test_apply_replacements_skips_overlapping_source_ranges() -> None:
    assert mdcommon._apply_replacements(
        "abcd",
        [(0, 2, "X"), (1, 3, "Y")],
    ) == "Xcd"


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


def test_update_links_in_md_text_does_not_update_images() -> None:
    text = "![old](old-image.png) [old](old-doc.md)\n![old][img]\n[img]: old-ref.png\n"

    out = mdcommon.update_links_in_md_text(
        text,
        {"name": "new", "name_to_replace": "old", "url": "new.md"},
    )

    assert out == "![old](old-image.png) [new](new.md)\n![old][img]\n[img]: old-ref.png\n"


def test_update_links_in_md_text_updates_reference_links_without_mutating_input() -> None:
    new_link = {"name": "Ref", "url": "new.md", "title": "new title"}
    text = "before [Ref][id1]\n[id1]: old.md\n"

    out = mdcommon.update_links_in_md_text(text, new_link)

    assert out == 'before [Ref][id1]\n[id1]: new.md "new title"\n'
    assert "id_link" not in new_link


def test_update_link_in_md_text_leaves_other_reference_labels_unchanged() -> None:
    text = "[Other][id]\n[id]: old.md\n"

    assert mdcommon.update_link_in_md_text(
        text,
        "Missing",
        {"name": "New", "url": "new.md"},
    ) == text


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


def test_update_link_from_old_link_does_not_update_images() -> None:
    text = "![Old](old.md) [Old](old.md)\n![Old][img]\n[img]: old.md\n"

    out = mdcommon.update_link_from_old_link(
        text,
        {"name": "Old", "url": "old.md"},
        {"name": "New", "url": "new.md"},
    )

    assert out == "![Old](old.md) [New](new.md)\n![Old][img]\n[img]: old.md\n"


def test_update_link_from_old_link_matches_exact_url_and_reference() -> None:
    text = (
        "[Old](old.md-extra) [Old](old.md#part) [Old](old.md)\n"
        "[Old][a] [Old][b]\n"
        "[a]: other.md\n"
        "[b]: old.md\n"
    )

    out = mdcommon.update_link_from_old_link(
        text,
        {"name": "Old", "url": "old.md"},
        {"name": "New", "url": "new.md"},
    )

    assert out == (
        "[Old](old.md-extra) [Old](old.md#part) [New](new.md)\n"
        "[Old][a] [New][b]\n"
        "[a]: other.md\n"
        "[b]: new.md\n"
    )


def test_link_updates_ignore_code_spans_and_fences() -> None:
    text = (
        "`[Old](old.md)` [Old](old.md)\n"
        "```\n[Old][code]\n[code]: old.md\n```\n"
    )

    out = mdcommon.update_link_from_old_link(
        text,
        {"name": "Old", "url": "old.md"},
        {"name": "New", "url": "new.md"},
    )

    assert out == (
        "`[Old](old.md)` [New](new.md)\n"
        "```\n[Old][code]\n[code]: old.md\n```\n"
    )


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


def test_move_base_path_preserves_anchors_queries_and_root_links() -> None:
    text = (
        "[Anchor](#part) [Doc](page.md#part) "
        "[Query](page.md?mode=full#part) [Root](/root.md#part)"
    )

    out = mdcommon.move_base_path_in_md_text(text, "base")

    assert out == (
        "[Anchor](#part) [Doc](base/page.md#part) "
        "[Query](base/page.md?mode=full#part) [Root](/root.md#part)"
    )


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
