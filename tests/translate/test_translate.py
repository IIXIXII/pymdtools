from __future__ import annotations

import json
from typing import Any
from urllib.error import URLError
from urllib.parse import parse_qs, urlparse

import pytest

import pymdtools.translate as translate


class FakeResponse:
    def __init__(self, payload: object) -> None:
        self.payload = payload

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        del args

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_public_api_only_exposes_markdown_and_text_translation() -> None:
    assert translate.__all__ == ["translate_md", "translate_txt"]
    assert hasattr(translate, "translate_md")
    assert hasattr(translate, "translate_txt")


def test_build_mymemory_url_encodes_required_and_optional_parameters() -> None:
    url = translate._build_mymemory_url(
        "Bonjour le monde",
        "fr",
        "en",
        email="me@example.com",
        api_key="secret",
    )
    query = parse_qs(urlparse(url).query)

    assert url.startswith("https://api.mymemory.translated.net/get?")
    assert query == {
        "q": ["Bonjour le monde"],
        "langpair": ["fr|en"],
        "de": ["me@example.com"],
        "key": ["secret"],
    }


def test_build_mymemory_url_omits_empty_optional_parameters() -> None:
    url = translate._build_mymemory_url("", "fr", "en", email="", api_key=None)
    query = parse_qs(urlparse(url).query)

    assert query == {"langpair": ["fr|en"]}


def test_extract_mymemory_translation_returns_translated_text() -> None:
    assert translate._extract_mymemory_translation(
        {"responseStatus": 200, "responseData": {"translatedText": "Hello"}}
    ) == "Hello"


def test_extract_mymemory_translation_accepts_missing_status() -> None:
    assert translate._extract_mymemory_translation(
        {"responseData": {"translatedText": "Hello"}}
    ) == "Hello"


def test_extract_mymemory_translation_rejects_api_errors() -> None:
    with pytest.raises(RuntimeError, match="quota exceeded"):
        translate._extract_mymemory_translation(
            {"responseStatus": 429, "responseDetails": "quota exceeded"}
        )


def test_extract_mymemory_translation_rejects_missing_response_data() -> None:
    with pytest.raises(RuntimeError, match="responseData"):
        translate._extract_mymemory_translation({"responseStatus": 200})


def test_extract_mymemory_translation_rejects_missing_translated_text() -> None:
    with pytest.raises(RuntimeError, match="translatedText"):
        translate._extract_mymemory_translation({"responseData": {}})


def test_request_mymemory_translation_reads_json_response(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, float]] = []

    def fake_urlopen(url: str, *, timeout: float) -> FakeResponse:
        calls.append((url, timeout))
        return FakeResponse({"responseData": {"translatedText": "Hello"}})

    monkeypatch.setattr(translate, "urlopen", fake_urlopen)

    assert translate._request_mymemory_translation(
        "Bonjour",
        "fr",
        "en",
        email="me@example.com",
        api_key="secret",
        timeout=2.0,
    ) == "Hello"

    query = parse_qs(urlparse(calls[0][0]).query)
    assert calls[0][1] == 2.0
    assert query["q"] == ["Bonjour"]
    assert query["langpair"] == ["fr|en"]
    assert query["de"] == ["me@example.com"]
    assert query["key"] == ["secret"]


def test_request_mymemory_translation_rejects_non_mapping_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        translate,
        "urlopen",
        lambda *args, **kwargs: FakeResponse(["unexpected"]),
    )

    with pytest.raises(RuntimeError, match="JSON object"):
        translate._request_mymemory_translation(
            "Bonjour",
            "fr",
            "en",
            email=None,
            api_key=None,
            timeout=2.0,
        )


def test_split_text_for_mymemory_returns_no_chunks_for_empty_text() -> None:
    assert translate._split_text_for_mymemory("") == []


def test_split_text_for_mymemory_rejects_invalid_max_bytes() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        translate._split_text_for_mymemory("Bonjour", max_bytes=0)


def test_split_text_for_mymemory_keeps_chunks_under_limit() -> None:
    chunks = translate._split_text_for_mymemory("alpha beta gamma", max_bytes=10)

    assert chunks == ["alpha beta", " gamma"]
    assert all(len(chunk.encode("utf-8")) <= 10 for chunk in chunks)
    assert "".join(chunks) == "alpha beta gamma"


def test_split_text_for_mymemory_splits_oversized_words() -> None:
    chunks = translate._split_text_for_mymemory("\u00e9\u00e9\u00e9\u00e9\u00e9", max_bytes=4)

    assert chunks == ["\u00e9\u00e9", "\u00e9\u00e9", "\u00e9"]


def test_split_oversized_word_returns_no_chunk_for_empty_word() -> None:
    assert translate._split_oversized_word("", max_bytes=4) == []


def test_split_text_for_mymemory_flushes_current_before_oversized_word() -> None:
    chunks = translate._split_text_for_mymemory("abc defghijk", max_bytes=4)

    assert chunks == ["abc ", "defg", "hijk"]
    assert "".join(chunks) == "abc defghijk"


@pytest.mark.parametrize(
    "text",
    ["  leading", "trailing  ", "a   b", "line one\n\nline two\t"],
)
def test_split_text_for_mymemory_preserves_all_whitespace(text: str) -> None:
    chunks = translate._split_text_for_mymemory(text, max_bytes=5)

    assert "".join(chunks) == text
    assert all(len(chunk.encode("utf-8")) <= 5 for chunk in chunks)


def test_translate_txt_returns_blank_without_api_call(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        translate,
        "_request_mymemory_translation",
        lambda text, src, dest, *, email, api_key, timeout: calls.append(text) or "x",
    )

    assert translate.translate_txt("") == ""
    assert translate.translate_txt("   ") == "   "
    assert calls == []


def test_translate_txt_translates_each_chunk(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str, str, str | None, str | None, float]] = []

    def fake_request(
        text: str,
        src: str,
        dest: str,
        *,
        email: str | None,
        api_key: str | None,
        timeout: float,
    ) -> str:
        calls.append((text, src, dest, email, api_key, timeout))
        return f"[{text}]"

    monkeypatch.setattr(translate, "_request_mymemory_translation", fake_request)
    long_text = ("a" * 500) + " b"

    out = translate.translate_txt(
        long_text,
        src="fr",
        dest="en",
        email="me@example.com",
        api_key="secret",
        timeout=3.0,
    )

    assert out == f"[{'a' * 500}][ b]"
    assert calls == [
        ("a" * 500, "fr", "en", "me@example.com", "secret", 3.0),
        (" b", "fr", "en", "me@example.com", "secret", 3.0),
    ]


def test_translate_txt_keeps_original_text_when_api_fails_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_request(*args: Any, **kwargs: Any) -> str:
        del args, kwargs
        raise URLError("offline")

    monkeypatch.setattr(translate, "_request_mymemory_translation", fake_request)

    assert translate.translate_txt("Bonjour") == "Bonjour"


def test_translate_txt_does_not_log_source_text(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    secret = "private customer text"
    monkeypatch.setattr(
        translate,
        "_request_mymemory_translation",
        lambda *args, **kwargs: (_ for _ in ()).throw(URLError("offline")),
    )

    assert translate.translate_txt(secret) == secret
    assert secret not in caplog.text


def test_translate_txt_can_return_empty_string_when_api_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_request(*args: Any, **kwargs: Any) -> str:
        del args, kwargs
        raise URLError("offline")

    monkeypatch.setattr(translate, "_request_mymemory_translation", fake_request)

    assert translate.translate_txt("Bonjour", on_error="empty") == ""


def test_translate_txt_can_raise_when_api_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request(*args: Any, **kwargs: Any) -> str:
        del args, kwargs
        raise URLError("offline")

    monkeypatch.setattr(translate, "_request_mymemory_translation", fake_request)

    with pytest.raises(URLError):
        translate.translate_txt("Bonjour", on_error="raise")


def test_translate_txt_rejects_unknown_error_mode() -> None:
    with pytest.raises(ValueError, match="invalid on_error"):
        translate.translate_txt("Bonjour", on_error="missing")  # type: ignore[arg-type]


def test_translate_md_translates_text_tokens_and_preserves_markdown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str, str, str | None, str | None, float]] = []

    def fake_request(
        text: str,
        src: str,
        dest: str,
        *,
        email: str | None,
        api_key: str | None,
        timeout: float,
    ) -> str:
        calls.append((text, src, dest, email, api_key, timeout))
        return f"tr:{text}"

    monkeypatch.setattr(translate, "_request_mymemory_translation", fake_request)

    out = translate.translate_md(
        "# Bonjour\n\nUn **texte**.",
        src="fr",
        dest="en",
        email="me@example.com",
        api_key="secret",
        timeout=4.0,
    )

    assert "# tr:Bonjour" in out
    assert "tr:Un **tr:texte**" in out
    assert calls == [
        ("Bonjour", "fr", "en", "me@example.com", "secret", 4.0),
        ("Un ", "fr", "en", "me@example.com", "secret", 4.0),
        ("texte", "fr", "en", "me@example.com", "secret", 4.0),
        (".", "fr", "en", "me@example.com", "secret", 4.0),
    ]


def test_translate_md_escapes_markdown_returned_by_remote_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        translate,
        "_request_mymemory_translation",
        lambda *args, **kwargs: "[click](javascript:alert(1)) <script>",
    )

    out = translate.translate_md("Bonjour")

    assert r"\[click\]\(javascript:alert\(1\)\) \<script\>" in out


def test_translate_md_keeps_original_text_for_failed_tokens_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_request(*args: Any, **kwargs: Any) -> str:
        del args, kwargs
        raise RuntimeError("boom")

    monkeypatch.setattr(translate, "_request_mymemory_translation", fake_request)

    assert translate.translate_md("Bonjour").strip() == "Bonjour"


def test_translate_md_can_return_empty_text_for_failed_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_request(*args: Any, **kwargs: Any) -> str:
        del args, kwargs
        raise RuntimeError("boom")

    monkeypatch.setattr(translate, "_request_mymemory_translation", fake_request)

    assert translate.translate_md("Bonjour", on_error="empty").strip() == ""
