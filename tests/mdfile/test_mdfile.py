from __future__ import annotations

from pathlib import Path

import pymdtools.mdfile as mdfile


def test_markdown_content_reads_existing_file_with_default_encoding(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text("# Titre\n\nEte\n", encoding="utf-8")

    content = mdfile.MarkdownContent(source)

    assert content.content == "# Titre\n\nEte\n"
    assert content.title == "Titre"


def test_markdown_content_empty_buffer_behaves_like_empty_text() -> None:
    content = mdfile.MarkdownContent()

    assert list(content.keys()) == []
    assert content.title is None
    assert content.toc == ""


def test_markdown_content_variable_mapping_api() -> None:
    content = mdfile.MarkdownContent(
        content='<!-- var(author)="Ada" -->\n<!-- var(lang)="en" -->\n# Doc\n'
    )

    assert content["author"] == "Ada"
    assert content.has_key("author")
    assert "lang" in content
    assert list(content.values()) == ["Ada", "en"]
    assert list(content.items()) == [("author", "Ada"), ("lang", "en")]
    assert list(iter(content)) == ["author", "lang"]

    content["author"] = "Grace"
    assert content["author"] == "Grace"
    assert '<!-- var(author)="Grace" -->' in content.content

    del content["lang"]
    assert "lang" not in content
    assert list(content.keys()) == ["author"]


def test_title_setter_updates_content() -> None:
    content = mdfile.MarkdownContent(content="Body\n")

    content.title = "New Title"

    assert content.title == "New Title"
    assert content.content.startswith("New Title\n")


def test_set_include_file_uses_current_instruction_api() -> None:
    content = mdfile.MarkdownContent(content="Body\n")

    content.set_include_file("snippet.md")
    content.set_include_file("snippet.md")

    assert content.content.count("include-file(snippet.md)") == 1
    assert content.content.endswith("Body\n")


def test_del_include_file_removes_matching_directive() -> None:
    content = mdfile.MarkdownContent(
        content="<!-- include-file(snippet.md) -->\n\nBody\n"
    )

    content.del_include_file("snippet.md")

    assert "include-file(snippet.md)" not in content.content
    assert content.content.endswith("Body\n")


def test_beautify_updates_and_returns_content() -> None:
    content = mdfile.MarkdownContent(content="# Title\n\nBody\n\n")

    out = content.beautify()

    assert out == "# Title\n\nBody"
    assert content.content == out


def test_process_tags_includes_refs_from_current_file_folder(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    ref = tmp_path / "ref.md"

    source.write_text(
        "# Source\n\n"
        "<!-- begin-include(section) -->OLD<!-- end-include -->\n",
        encoding="utf-8",
    )
    ref.write_text(
        "<!-- begin-ref(section) -->\n"
        "NEW\n"
        "<!-- end-ref -->\n",
        encoding="utf-8",
    )

    content = mdfile.MarkdownContent(source)
    out = content.process_tags()

    assert "NEW" in out
    assert "OLD" not in out


def test_process_tags_can_extend_refs_from_search_folders(tmp_path: Path) -> None:
    source_dir = tmp_path / "src"
    refs_dir = tmp_path / "refs"
    source_dir.mkdir()
    refs_dir.mkdir()

    source = source_dir / "source.md"
    source.write_text(
        "<!-- begin-include(external) -->OLD<!-- end-include -->\n",
        encoding="utf-8",
    )
    (refs_dir / "external.md").write_text(
        "<!-- begin-ref(external) -->EXTERNAL<!-- end-ref -->\n",
        encoding="utf-8",
    )

    content = mdfile.MarkdownContent(source, search_folders=[refs_dir])
    out = content.process_tags()

    assert "EXTERNAL" in out
    assert "OLD" not in out


def test_process_tags_without_filename_uses_empty_ref_set() -> None:
    content = mdfile.MarkdownContent(
        content='<!-- var(name)="Ada" -->\n'
        "<!-- begin-var(name) -->OLD<!-- end-var -->\n"
    )

    out = content.process_tags()

    assert "Ada" in out
    assert "OLD" not in out


def test_process_tags_resolves_include_relative_to_document(
    tmp_path: Path,
    monkeypatch,
) -> None:
    document_folder = tmp_path / "document"
    other_folder = tmp_path / "other"
    document_folder.mkdir()
    other_folder.mkdir()
    source = document_folder / "source.md"
    source.write_text(
        "Before\n<!-- include-file(snippet.txt) -->\nAfter\n",
        encoding="utf-8",
    )
    (document_folder / "snippet.txt").write_text("LOCAL", encoding="utf-8")
    (other_folder / "snippet.txt").write_text("WRONG", encoding="utf-8")
    monkeypatch.chdir(other_folder)

    content = mdfile.MarkdownContent(source, render_mode="raw")
    out = content.process_tags()

    assert out == "Before\nLOCAL\nAfter\n"
