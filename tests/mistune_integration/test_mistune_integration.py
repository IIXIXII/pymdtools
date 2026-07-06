from __future__ import annotations

import pytest

import pymdtools.mistune_integration as mi


def test_backend_metadata_and_public_api() -> None:
    assert mi.get_backend_name() == "mistune"
    assert mi.get_backend_version() == mi.__version__
    assert mi.get_backend_version().startswith("3.")

    for name in (
        "BaseRenderer",
        "ClosingHTMLRenderer",
        "ClosingMarkdownRenderer",
        "HTMLRenderer",
        "Markdown",
        "MarkdownRenderer",
        "MdRenderer",
        "create_markdown",
        "create_markdown_with_close",
        "escape",
        "get_backend_name",
        "get_backend_version",
        "html",
    ):
        assert name in mi.__all__


def test_version_tuple_extracts_leading_numeric_parts() -> None:
    assert mi._version_tuple("3.2.1") == (3, 2, 1)
    assert mi._version_tuple("3.2.1rc1") == (3, 2, 1)
    assert mi._version_tuple("3.dev0") == (3,)
    assert mi._version_tuple("dev") == ()


def test_require_mistune3_rejects_old_version(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mi.mistune, "__version__", "2.9.9")

    with pytest.raises(ImportError, match="requires mistune>=3.0"):
        mi._require_mistune3()


def test_require_mistune3_rejects_missing_modern_api(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mi.mistune, "__version__", "3.0.0")
    monkeypatch.delattr(mi.mistune, "html")

    with pytest.raises(ImportError, match="missing html"):
        mi._require_mistune3()


def test_closing_html_renderer_appends_close_output() -> None:
    class Renderer(mi.ClosingHTMLRenderer):
        def close(self) -> str:
            return "<footer>closed</footer>"

    markdown = mi.create_markdown_with_close(renderer=Renderer())
    rendered = markdown("# Title")

    assert "<h1>Title</h1>" in rendered
    assert rendered.endswith("<footer>closed</footer>")


def test_closing_markdown_renderer_appends_close_output() -> None:
    class Renderer(mi.MdRenderer):
        def close(self) -> str:
            return "\n<!-- closed -->"

    markdown = mi.create_markdown_with_close(renderer=Renderer())
    rendered = markdown("# Title\n\nBody")

    assert rendered.startswith("# Title")
    assert "Body" in rendered
    assert rendered.endswith("<!-- closed -->")


def test_create_markdown_with_close_accepts_renderer_names() -> None:
    html_markdown = mi.create_markdown_with_close(renderer="html")
    md_markdown = mi.create_markdown_with_close(renderer="markdown")

    assert "<p>Hello</p>" in html_markdown("Hello")
    assert md_markdown("Hello").strip() == "Hello"


def test_append_close_output_ignores_renderers_without_close() -> None:
    renderer = mi.ClosingMarkdownRenderer()

    assert mi._append_close_output(renderer, "content") == "content"


def test_append_close_output_calls_close_hook() -> None:
    class Renderer(mi.ClosingMarkdownRenderer):
        def close(self) -> str:
            return " done"

    assert mi._append_close_output(Renderer(), "content") == "content done"

