from urllib.error import HTTPError, URLError

import pytest
from markdown_it import MarkdownIt

import pymdtools._translation.client as _translation_client_impl
from pymdtools._translation_blocks import TranslationStructureError as LegacyStructureError
from pymdtools.translate import (
    TranslationClient,
    TranslationStructureError,
    translate_md,
    translate_txt,
)


@pytest.mark.parametrize(
    "options",
    [
        {"cache_size": -1},
        {"max_retries": -1},
        {"max_retries": 6},
        {"retry_delay": -1},
        {"retry_delay": float("nan")},
        {"retry_delay": 11},
    ],
)
def test_invalid_client_options(options):
    with pytest.raises(ValueError):
        TranslationClient(**options)


def test_legacy_exception_import_catches_the_public_error():
    with pytest.raises(LegacyStructureError):
        raise TranslationStructureError("formatting markers changed")


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf")])
def test_invalid_transport_timeout(timeout):
    client = TranslationClient(lambda *a, **kw: pytest.fail("no network expected"))
    with pytest.raises(ValueError, match="timeout"):
        translate_txt("hello", client=client, timeout=timeout, on_error="raise")


def test_default_transport_and_cache(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "pymdtools._translation.mymemory.request_mymemory_translation",
        lambda text, *a, **kw: calls.append(text) or text.upper(),
    )
    client = TranslationClient(cache_size=2)
    assert translate_txt("one", client=client) == "ONE"
    translate_txt("two", client=client)
    translate_txt("one", client=client)  # refresh least-recently-used position
    translate_txt("three", client=client)
    translate_txt("two", client=client)
    assert calls == ["one", "two", "three", "two"]
    client.clear_cache()
    translate_txt("two", client=client)
    assert len(calls) == 5


def test_cache_keys_include_languages_and_credentials():
    calls = []
    client = TranslationClient(lambda text, *a, **kw: calls.append((a, kw)) or text)
    for options in ({}, {"src": "de"}, {"dest": "es"}, {"email": "x@y"}, {"api_key": "key"}):
        translate_txt("hello", client=client, **options)
        translate_txt("hello", client=client, **options)
    assert len(calls) == 5


def test_cache_can_be_disabled():
    calls = []
    client = TranslationClient(lambda text, *a, **kw: calls.append(text) or text, cache_size=0)
    translate_txt("hello", client=client)
    translate_txt("hello", client=client)
    assert calls == ["hello", "hello"]


@pytest.mark.parametrize(
    "error", [URLError("offline"), TimeoutError(), HTTPError("", 503, "", {}, None)]
)
def test_transient_errors_retry_with_bounded_backoff(monkeypatch, error):
    attempts = []
    delays = []
    monkeypatch.setattr(_translation_client_impl.time, "sleep", delays.append)

    def transport(text, *args, **kwargs):
        attempts.append(text)
        if len(attempts) < 3:
            raise error
        return "translated"

    client = TranslationClient(transport)
    assert translate_txt("hello", client=client, on_error="raise") == "translated"
    assert delays == [0.25, 0.5]


@pytest.mark.parametrize("status,attempts", [(400, 1), (429, 3)])
def test_permanent_errors_and_exhausted_retries_are_not_cached(monkeypatch, status, attempts):
    calls = []
    monkeypatch.setattr(_translation_client_impl.time, "sleep", lambda _: None)

    def transport(*args, **kwargs):
        calls.append(None)
        raise HTTPError("", status, "failed", {}, None)

    client = TranslationClient(transport)
    assert translate_txt("hello", client=client) == "hello"
    assert translate_txt("hello", client=client) == "hello"
    assert len(calls) == 2 * attempts


def test_paragraph_translation_keeps_context_and_markup_local():
    calls = []

    def transport(text, *args, **kwargs):
        calls.append(text)
        return text.replace("Un ", "A ").replace("texte", "text").replace("lien", "link")

    source = "Un **texte** avec un [lien](private.md) et `code`."
    result = translate_md(source, client=TranslationClient(transport), segmentation="paragraph")
    assert result.strip() == r"A **text** avec un [link](private.md) et `code`\."
    assert len(calls) == 1
    assert "Un " in calls[0] and "texte" in calls[0] and "lien" in calls[0]
    assert "private.md" not in calls[0] and "code" not in calls[0]


@pytest.mark.parametrize(
    "source",
    [
        "# A *heading*",
        "- list **item**",
        "![alt](image.png)",
        "[PMD](page.md)",
        "**only emphasis**",
        "**first** **second**",
        "`only code`",
        "word " * 200,
        "before\nnext",
        "before  \nnext",
        "a <span>text</span>",
    ],
)
def test_identity_paragraph_translation_preserves_rendered_structure(source):
    result = translate_md(
        source, client=TranslationClient(lambda text, *a, **kw: text), segmentation="paragraph"
    )
    assert MarkdownIt().render(result) == MarkdownIt().render(source)


@pytest.mark.parametrize("mode", ["keep_original", "empty", "raise"])
def test_changed_markers_follow_error_policy_without_second_request(mode):
    calls = []
    client = TranslationClient(lambda text, *a, **kw: calls.append(text) or "altered")
    if mode == "raise":
        with pytest.raises(TranslationStructureError):
            translate_md("a **bold** word", client=client, segmentation="paragraph", on_error=mode)
    else:
        result = translate_md(
            "a **bold** word", client=client, segmentation="paragraph", on_error=mode
        )
        assert result.strip() == ("a **bold** word" if mode == "keep_original" else "")
    assert len(calls) == 1


def test_paragraph_translation_escapes_untrusted_text():
    result = translate_md(
        "hello",
        client=TranslationClient(lambda *a, **kw: "[bad](javascript:x)"),
        segmentation="paragraph",
    )
    assert "<a " not in MarkdownIt().render(result)


@pytest.mark.parametrize("options", [{"segmentation": "other"}, {"on_error": "other"}])
def test_markdown_options_validated_even_for_empty_input(options):
    with pytest.raises(ValueError):
        translate_md("", **options)
