#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                    Author: Florent TOURNOIS | License: MIT
# =============================================================================
"""
Translate plain text and Markdown with the MyMemory web API.

The module exposes two public helpers:

- :func:`translate_txt` translates plain text;
- :func:`translate_md` translates Markdown while keeping the Markdown structure.

MyMemory translates short segments through its REST ``/get`` endpoint. The API
requires a ``q`` text parameter and a ``langpair`` parameter formatted as
``source|destination``. A contact email can be sent with the ``de`` parameter to
raise the daily free quota.

References:
    https://mymemory.translated.net/doc/spec.php
    https://mymemory.translated.net/doc/usagelimits.php
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Mapping
from typing import Any, Final, Literal, cast
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from mistune.core import BlockState

from . import mistune_integration as mistune


__all__ = ["translate_md", "translate_txt"]

_MYMEMORY_ENDPOINT = "https://api.mymemory.translated.net/get"
_MYMEMORY_MAX_QUERY_BYTES = 500
_DEFAULT_TIMEOUT = 10.0
TranslationErrorMode = Literal["keep_original", "empty", "raise"]
_MARKDOWN_TEXT_ESCAPES: Final[frozenset[str]] = frozenset(
    "\\`*_{}[]<>()#+-.!|=~&"
)


# -----------------------------------------------------------------------------
def _utf8_len(text: str) -> int:
    """
    Return the UTF-8 byte length of a string.

    Args:
        text: Text to measure.

    Returns:
        Number of bytes used by the UTF-8 representation.
    """
    return len(text.encode("utf-8"))


# -----------------------------------------------------------------------------
def _split_oversized_word(word: str, max_bytes: int) -> list[str]:
    """
    Split one word into chunks accepted by MyMemory.

    Args:
        word: Word that may exceed ``max_bytes`` once UTF-8 encoded.
        max_bytes: Maximum UTF-8 byte length per chunk.

    Returns:
        Chunks whose UTF-8 byte length is at most ``max_bytes``.
    """
    chunks: list[str] = []
    current = ""
    for char in word:
        candidate = current + char
        if current and _utf8_len(candidate) > max_bytes:
            chunks.append(current)
            current = char
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


# -----------------------------------------------------------------------------
def _split_text_for_mymemory(text: str, max_bytes: int = _MYMEMORY_MAX_QUERY_BYTES) -> list[str]:
    """
    Split text into UTF-8 chunks compatible with MyMemory.

    The function keeps whitespace in the emitted chunks so joining translated
    chunks does not silently remove source spacing.

    Args:
        text: Source text to split.
        max_bytes: Maximum UTF-8 byte length per chunk.

    Returns:
        Ordered chunks to send to MyMemory.

    Raises:
        ValueError: If ``max_bytes`` is smaller than one byte.
    """
    if max_bytes < 1:
        raise ValueError("max_bytes must be greater than zero")
    if text == "":
        return []

    chunks: list[str] = []
    current = ""

    for part in re.findall(r"\s+|\S+", text):
        candidate = current + part
        if _utf8_len(candidate) <= max_bytes:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = ""

        if _utf8_len(part) <= max_bytes:
            current = part
            continue

        split_part = _split_oversized_word(part, max_bytes)
        chunks.extend(split_part[:-1])
        current = split_part[-1]

    chunks.append(current)
    return chunks


# -----------------------------------------------------------------------------
def _escape_markdown_text(text: str) -> str:
    """Escape translated plain text before reinserting it into Markdown."""
    return "".join(
        f"\\{char}" if char in _MARKDOWN_TEXT_ESCAPES else char
        for char in text
    )


# -----------------------------------------------------------------------------
def _build_mymemory_url(
    text: str,
    src: str,
    dest: str,
    *,
    email: str | None,
    api_key: str | None,
) -> str:
    """
    Build a MyMemory ``/get`` request URL.

    Args:
        text: Source text segment.
        src: Source language code.
        dest: Destination language code.
        email: Optional contact email sent as ``de``.
        api_key: Optional MyMemory private key.

    Returns:
        Fully encoded MyMemory URL.
    """
    parameters = {
        "q": text,
        "langpair": f"{src}|{dest}",
    }
    if email:
        parameters["de"] = email
    if api_key:
        parameters["key"] = api_key
    return f"{_MYMEMORY_ENDPOINT}?{urlencode(parameters)}"


# -----------------------------------------------------------------------------
def _extract_mymemory_translation(payload: Mapping[str, Any]) -> str:
    """
    Extract translated text from a MyMemory JSON payload.

    Args:
        payload: Decoded MyMemory response.

    Returns:
        Translated text.

    Raises:
        RuntimeError: If MyMemory reports an error or the response shape is
            incomplete.
    """
    status = payload.get("responseStatus")
    if isinstance(status, int) and status >= 400:
        detail = payload.get("responseDetails", "unknown MyMemory error")
        raise RuntimeError(str(detail))

    response_data_obj = payload.get("responseData")
    if not isinstance(response_data_obj, Mapping):
        raise RuntimeError("Missing MyMemory responseData")
    response_data = cast(Mapping[str, object], response_data_obj)

    translated_text = response_data.get("translatedText")
    if not isinstance(translated_text, str):
        raise RuntimeError("Missing MyMemory translatedText")
    return translated_text


# -----------------------------------------------------------------------------
def _request_mymemory_translation(
    text: str,
    src: str,
    dest: str,
    *,
    email: str | None,
    api_key: str | None,
    timeout: float,
) -> str:
    """
    Request one translation segment from MyMemory.

    Args:
        text: Source text segment. Must fit MyMemory's request size limit.
        src: Source language code.
        dest: Destination language code.
        email: Optional contact email sent as ``de``.
        api_key: Optional MyMemory private key.
        timeout: Network timeout in seconds.

    Returns:
        Translated text segment.
    """
    url = _build_mymemory_url(text, src, dest, email=email, api_key=api_key)
    with urlopen(url, timeout=timeout) as response:  # noqa: S310 - URL is fixed to MyMemory.
        payload: object = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, Mapping):
        raise RuntimeError("Invalid MyMemory response: expected a JSON object")
    return _extract_mymemory_translation(cast(Mapping[str, Any], payload))


# -----------------------------------------------------------------------------
def translate_txt(
    text: str,
    src: str = "fr",
    dest: str = "en",
    *,
    email: str | None = None,
    api_key: str | None = None,
    timeout: float = _DEFAULT_TIMEOUT,
    on_error: TranslationErrorMode = "keep_original",
) -> str:
    """
    Translate plain text with MyMemory.

    Blank strings are returned unchanged. Long text is split into chunks of at
    most 500 UTF-8 bytes, which matches the MyMemory ``q`` parameter limit.

    Args:
        text: Source text.
        src: Source language code, for example ``"fr"``.
        dest: Destination language code, for example ``"en"``.
        email: Optional contact email sent to MyMemory as the ``de`` parameter.
        api_key: Optional MyMemory private key.
        timeout: Network timeout in seconds.
        on_error: Behavior when the API call fails:
            ``"keep_original"`` returns the source text, ``"empty"`` returns
            ``""`` for backward compatibility, and ``"raise"`` propagates the
            exception.

    Returns:
        Translated text, unchanged blank text, or the configured fallback when
        the API call fails.
    """
    if on_error not in ("keep_original", "empty", "raise"):
        raise ValueError(f"invalid on_error mode: {on_error!r}")

    if not text or text.isspace():
        return text

    try:
        chunks = _split_text_for_mymemory(text)
        return "".join(
            _request_mymemory_translation(
                chunk,
                src,
                dest,
                email=email,
                api_key=api_key,
                timeout=timeout,
            )
            for chunk in chunks
        )
    except (HTTPError, URLError, TimeoutError, OSError, RuntimeError, ValueError) as err:
        logging.error("MyMemory translation failed: %s", type(err).__name__)
        if on_error == "raise":
            raise
        if on_error == "empty":
            return ""
        return text


# -----------------------------------------------------------------------------
def translate_md(
    md_text: str,
    src: str = "fr",
    dest: str = "en",
    *,
    email: str | None = None,
    api_key: str | None = None,
    timeout: float = _DEFAULT_TIMEOUT,
    on_error: TranslationErrorMode = "keep_original",
) -> str:
    """
    Translate Markdown text with MyMemory while preserving Markdown structure.

    Mistune parses the Markdown and the renderer sends only plain text tokens to
    :func:`translate_txt`. Markdown syntax such as headings, emphasis, lists and
    links is therefore emitted by the renderer instead of being translated as raw
    markup.

    Args:
        md_text: Source Markdown text.
        src: Source language code, for example ``"fr"``.
        dest: Destination language code, for example ``"en"``.
        email: Optional contact email sent to MyMemory as the ``de`` parameter.
        api_key: Optional MyMemory private key.
        timeout: Network timeout in seconds.
        on_error: Forwarded to :func:`translate_txt`.

    Returns:
        Translated Markdown text.
    """

    class LocalRender(mistune.MdRenderer):
        """Markdown renderer translating plain text tokens with MyMemory."""

        def text(self, token: Mapping[str, object], state: BlockState) -> str:
            """Translate one Mistune text token."""
            del state
            raw_text = str(token.get("raw", ""))
            translated = translate_txt(
                raw_text,
                src=src,
                dest=dest,
                email=email,
                api_key=api_key,
                timeout=timeout,
                on_error=on_error,
            )
            return _escape_markdown_text(translated)

    markdown = mistune.create_markdown_with_close(renderer=LocalRender())
    return str(markdown(md_text))


# =============================================================================
