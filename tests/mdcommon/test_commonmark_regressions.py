from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st
from markdown_it import MarkdownIt

from pymdtools._markdown import parse_document
from pymdtools.common import encode_path_url
from pymdtools.instruction import get_vars_from_md_text, include_files_to_md_text
from pymdtools.mdcommon import (
    markdown_code_ranges,
    move_base_path_in_md_text,
    search_link_in_md_text,
    update_link_from_old_link,
)
from pymdtools.normalize import md_beautifier


@pytest.mark.parametrize(
    "source",
    [
        r"\[label](file.md)",
        r"\*literal\*",
        "    indented code\n",
        "```\ncode\n\n",
        "| A | B |\n|---|---|\n| x | y |\n",
        '<!-- var(x)="y" -->\n',
        "> ~~~md\n> <!-- include-file(secret.md) -->\n> ~~~\n",
    ],
)
def test_normalization_preserves_rendering_and_is_idempotent(source):
    normalized = md_beautifier(source)
    assert MarkdownIt().render(normalized) == MarkdownIt().render(source)
    assert md_beautifier(normalized) == normalized


@given(st.text(alphabet="abc XYZ[]()*_`~\\\n\t<>!é", max_size=120))
def test_normalization_semantics(source):
    normalized = md_beautifier(source)
    assert MarkdownIt().render(normalized) == MarkdownIt().render(source)
    assert md_beautifier(normalized) == normalized


@pytest.mark.parametrize("container", ["> ", "> > ", "  "])
@pytest.mark.parametrize("fence", ["~~~", "````"])
def test_code_examples_never_read_includes(container, fence, monkeypatch):
    def unexpected(*args, **kwargs):
        pytest.fail("An example attempted to read a file")

    monkeypatch.setattr("pymdtools._directives.includes.get_file_content_to_include", unexpected)
    source = "\n".join(
        container + line
        for line in [fence, "<!-- include-file(secret.md) -->", '<!-- var(x)="y" -->', fence]
    )
    assert include_files_to_md_text(source) == source
    assert get_vars_from_md_text(source) == {}


def test_links_preserve_occurrences_and_reference_case():
    links = search_link_in_md_text("[one][ID] [two][id]\n\n[id]: file(v2).md\n")
    assert [link["name"] for link in links] == ["one", "two"]
    assert all(link["url"] == "file(v2).md" for link in links)
    assert search_link_in_md_text(r"\[literal](file.md)") == []
    assert search_link_in_md_text("[doc](file(v2).md)")[0]["url"] == "file(v2).md"


def test_updates_preserve_unrelated_references_and_images():
    source = "[one][id] [two][id] ![image][id]\n\n[id]: old.md\n"
    out = update_link_from_old_link(
        source, {"name": "one", "url": "old.md"}, {"name": "new", "url": "new.md"}
    )
    assert out == "[new](new.md) [two][id] ![image][id]\n\n[id]: old.md\n"


def test_definition_inside_multiline_inline_code_is_not_a_reference():
    source = "`example\n[id]: secret.md\nend`\n\n[doc][id]\n"
    assert search_link_in_md_text(source) == []
    assert move_base_path_in_md_text(source, "docs") == source


@pytest.mark.parametrize("prefix", ["- ", "1. ", "> - "])
def test_reference_rewrite_preserves_container(prefix):
    source = f"{prefix}[id]: old.md\n\n[doc][id]\n"
    assert move_base_path_in_md_text(source, "docs") == (
        f"{prefix}[id]: docs/old.md\n\n[doc][id]\n"
    )


def test_nested_links_and_crlf_offsets():
    source = "> [doc](file(v2).md)\r\n\r\ntext\r\n"
    assert (
        update_link_from_old_link(
            source, {"name": "doc", "url": "file(v2).md"}, {"name": "new", "url": "next.md"}
        )
        == "> [new](next.md)\r\n\r\ntext\r\n"
    )
    assert parse_document("[collapsed][]\n\n[collapsed]: target.md\n").links[0].url == "target.md"


def test_paths_preserve_spelling_and_offer_legacy_mode():
    assert encode_path_url(Path("Été/My Docs")) == "%C3%89t%C3%A9/My%20Docs"
    assert move_base_path_in_md_text("[doc](file.md)", "My Docs") == "[doc](My%20Docs/file.md)"
    assert (
        move_base_path_in_md_text("[doc](file.md)", "My Docs", legacy_slug=True)
        == "[doc](my-docs/file.md)"
    )


@pytest.mark.parametrize("reference", [False, True])
def test_rebased_links_preserve_escaped_title_quotes(reference):
    definition = r'file.md "a \"quote\" and \\slash"'
    source = f"[doc][id]\n\n[id]: {definition}\n" if reference else f"[doc]({definition})"
    original = search_link_in_md_text(source)[0]
    updated = search_link_in_md_text(move_base_path_in_md_text(source, "docs"))[0]
    assert updated["url"] == "docs/file.md"
    assert updated["title"] == original["title"]


def test_many_code_blocks_are_indexed():
    source = ("```\ncode\n```\n" + "paragraph words " * 5 + "\n\n") * 2000
    assert len(markdown_code_ranges(source)) == 2000


def test_malformed_definitions_and_unicode_line_separators():
    assert search_link_in_md_text("[id]: <unterminated\n") == []
    source = "before\x85text [doc](doc.md)"
    assert parse_document(source).links[0].span == (12, len(source))


def test_unknown_source_mapping_protects_directives(monkeypatch):
    from markdown_it.token import Token

    from pymdtools import _markdown

    token = Token("inline", "", 0, map=[0, 2], content="expanded text")
    assert _markdown._inline_offsets(token, ["prefix\n", "expanded text\n"], [0, 7, 21])
    # A parser adapter mismatch must protect the block instead of editing wrong bytes.
    monkeypatch.setattr(_markdown.MarkdownIt, "parse", lambda *args: [token])
    source = "<!-- include-file(secret) -->\nsecond line\n"
    assert markdown_code_ranges(source) == [(0, len(source))]
