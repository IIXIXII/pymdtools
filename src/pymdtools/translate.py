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

import logging
from collections.abc import Mapping
from typing import Any, Final, Literal
from urllib.error import HTTPError, URLError

from mistune.core import BlockState

from . import mistune_integration as mistune
from ._translation.blocks import TranslationStructureError as TranslationStructureError
from ._translation.blocks import translate_inline as translate_inline
from ._translation.client import TranslationClient as TranslationClient
from ._translation.mymemory import MYMEMORY_MAX_QUERY_BYTES as _MYMEMORY_MAX_QUERY_BYTES
from ._translation.mymemory import request_mymemory_translation as _request_mymemory_translation
from ._translation.mymemory import split_text_for_mymemory as _split_text_for_mymemory

logger: logging.Logger = logging.getLogger(__name__)


__all__ = ["translate_md", "translate_txt", "TranslationClient", "TranslationStructureError"]

_DEFAULT_TIMEOUT = 10.0
TranslationErrorMode = Literal["keep_original", "empty", "raise"]
_MARKDOWN_TEXT_ESCAPES: Final[frozenset[str]] = frozenset("\\`*_{}[]<>()#+-.!|=~&")


# -----------------------------------------------------------------------------
def _escape_markdown_text(text: str) -> str:
    """Escape translated plain text before reinserting it into Markdown."""
    return "".join(f"\\{char}" if char in _MARKDOWN_TEXT_ESCAPES else char for char in text)


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
    client: TranslationClient | None = None,
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
        client: Optional reusable client for transport injection, retries and caching.

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
        request = client.translate if client is not None else _request_mymemory_translation
        return "".join(
            request(
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
        logger.error("MyMemory translation failed: %s", type(err).__name__)
        if on_error == "raise":
            raise
        if isinstance(err, HTTPError):
            err.close()
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
    client: TranslationClient | None = None,
    segmentation: Literal["token", "paragraph"] = "token",
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
        client: Optional reusable client for transport injection, retries and caching.
        segmentation: ``"paragraph"`` groups inline text with protected markup.
            Changed markers preserve original text or follow ``on_error``.
            Blocks exceeding the provider's byte limit use token segmentation.

    Returns:
        Translated Markdown text.
    """

    if segmentation not in {"token", "paragraph"}:
        raise ValueError("segmentation must be token or paragraph")
    if on_error not in {"keep_original", "empty", "raise"}:
        raise ValueError(f"invalid on_error mode: {on_error!r}")

    def translate_segment(text: str) -> str:
        return translate_txt(
            text,
            src=src,
            dest=dest,
            email=email,
            api_key=api_key,
            timeout=timeout,
            on_error=on_error,
            client=client,
        )

    class LocalRender(mistune.MdRenderer):
        """Markdown renderer translating plain text tokens with MyMemory."""

        def text(self, token: Mapping[str, object], state: BlockState) -> str:
            """Translate one Mistune text token."""
            del state
            raw_text = str(token.get("raw", ""))
            translated = translate_segment(raw_text)
            return _escape_markdown_text(translated)

        def render_children(self, token: dict[str, Any], state: BlockState) -> str:
            if segmentation == "paragraph" and token["type"] in {
                "paragraph",
                "heading",
                "block_text",
            }:
                return translate_inline(
                    token,
                    state,
                    translate=translate_segment,
                    escape=_escape_markdown_text,
                    fallback=lambda: super(LocalRender, self).render_children(token, state),
                    on_error=on_error,
                    max_bytes=_MYMEMORY_MAX_QUERY_BYTES,
                )
            return super().render_children(token, state)

    markdown = mistune.create_markdown_with_close(renderer=LocalRender())
    return str(markdown(md_text))


# =============================================================================
