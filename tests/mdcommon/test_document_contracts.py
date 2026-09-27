"""The same source corpus exercises inspection, editing, formatting and translation."""

from pathlib import Path

import pytest
from markdown_it import MarkdownIt

from pymdtools import mdcommon
from pymdtools.normalize import md_beautifier
from pymdtools.translate import translate_md
from pymdtools.translation_client import TranslationClient

CORPUS = Path(__file__).resolve().parents[1] / "fixtures" / "markdown"


@pytest.mark.parametrize("source_path", sorted(CORPUS.glob("*.md")), ids=lambda path: path.stem)
def test_document_transformations_preserve_links(source_path):
    source = source_path.read_text(encoding="utf-8")
    links = mdcommon.search_link_in_md_text(source)
    assert links
    rebased = mdcommon.search_link_in_md_text(mdcommon.move_base_path_in_md_text(source, "docs"))
    assert [(link["name"], link["url"], link["title"]) for link in rebased] == [
        (link["name"], "docs/" + link["url"], link["title"]) for link in links
    ]
    renderer = MarkdownIt()
    client = TranslationClient(lambda text, *args, **kwargs: text)
    for result in (
        md_beautifier(source),
        translate_md(source, client=client),
        translate_md(source, client=client, segmentation="paragraph"),
    ):
        assert renderer.render(result) == renderer.render(source)
    assert md_beautifier(md_beautifier(source)) == md_beautifier(source)


def test_batch_updates_preserve_sequential_renames_and_reference_isolation(monkeypatch):
    source = "[A][id] [untouched][id] [B](b.md)\n\n[id]: a.md\n"
    calls = []
    parse = mdcommon.parse_document

    def counted(text):
        calls.append(text)
        return parse(text)

    monkeypatch.setattr(mdcommon, "parse_document", counted)
    output = mdcommon.update_links_in_md_text(
        source,
        [
            {"name_to_replace": "A", "name": "B", "url": "first.md"},
            {"name_to_replace": "B", "name": "C", "url": "last.md"},
        ],
    )
    assert len(calls) == 1
    assert output == "[C](last.md) [untouched][id] [C](last.md)\n\n[id]: a.md\n"


def test_batch_shared_reference_is_written_once():
    source = "[A][id] [A][id]\n\n[id]: old.md\n"
    output = mdcommon.update_links_in_md_text(source, {"name": "A", "url": "file(.md"})
    assert output == "[A][id] [A][id]\n\n[id]: <file(.md>\n"


@pytest.mark.parametrize(
    "url", ["", "file).md", "two words.md", "file.md?x=&copy;", "back\\slash.md"]
)
def test_generated_destinations_remain_links(url):
    output = mdcommon.sub_string_link_md(None, {"name": "doc", "url": url})
    assert len(mdcommon.search_link_in_md_text(output)) == 1
