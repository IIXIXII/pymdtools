from __future__ import annotations

import pytest

import pymdtools.markdownify as legacy
import pymdtools.markdownify_integration as mi


def test_backend_metadata_and_public_api() -> None:
    assert mi.get_backend_name() == "markdownify"
    assert mi.get_backend_version() == mi.__version__
    assert mi.get_backend_version() != "unknown"

    for name in (
        "ATX",
        "ATX_CLOSED",
        "MarkdownConverter",
        "SETEXT",
        "UNDERLINED",
        "get_backend_name",
        "get_backend_version",
        "markdownify",
    ):
        assert name in mi.__all__


def test_markdownify_converts_html_to_markdown() -> None:
    out = mi.markdownify("<h1>Title</h1><p>Hello <strong>world</strong></p>")

    assert "Title" in out
    assert "=====" in out
    assert "Hello **world**" in out


def test_markdown_converter_and_options_are_reexported() -> None:
    converter = mi.MarkdownConverter(heading_style=mi.ATX)

    assert converter.convert("<h2>Subtitle</h2>").strip() == "## Subtitle"
    assert mi.SETEXT == mi.UNDERLINED
    assert mi.ATX_CLOSED != mi.ATX


def test_legacy_markdownify_module_reexports_integration_api() -> None:
    assert legacy.markdownify is mi.markdownify
    assert legacy.MarkdownConverter is mi.MarkdownConverter
    assert legacy.get_backend_name() == "markdownify"
    assert legacy.__all__ == mi.__all__


def test_require_markdownify_rejects_missing_api(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delattr(mi._markdownify, "markdownify")

    with pytest.raises(ImportError, match="missing markdownify"):
        mi._require_markdownify()


def test_backend_version_prefers_module_dunder_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(mi._markdownify, "__version__", "1.2.3", raising=False)

    assert mi.get_backend_version() == "1.2.3"


def test_backend_version_returns_unknown_without_package_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delattr(mi._markdownify, "__version__", raising=False)

    def missing_version(_package: str) -> str:
        raise mi.PackageNotFoundError

    monkeypatch.setattr(mi, "version", missing_version)

    assert mi.get_backend_version() == "unknown"
