"""Optional paragraph translation with validated, protected Markdown markers."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from typing import Any

from mistune.core import BlockState

from ..mistune_integration import MdRenderer


class TranslationStructureError(RuntimeError):
    """A translation changed or removed protected Markdown markers."""


def translate_inline(
    token: dict[str, Any],
    state: BlockState,
    *,
    translate: Callable[[str], str],
    escape: Callable[[str], str],
    fallback: Callable[[], str],
    on_error: str,
    max_bytes: int,
) -> str:
    """Send one inline block while retaining all markup locally.

    Longer blocks use the established token translator to respect the provider's
    byte limit. Invalid markers never become Markdown syntax in the output.
    """
    # Choose a namespace absent from both source text and attributes.
    prefix = "PMD"
    while prefix in repr(token):
        prefix += "X"
    texts: list[str] = []

    class Collect(MdRenderer):
        def text(self, token: Mapping[str, object], state: BlockState) -> str:
            texts.append(str(token.get("raw", "")))
            return f"\u27e6{prefix}T{len(texts) - 1}\u27e7"

    template = Collect().render_children(token, state)
    pattern = rf"\u27e6{prefix}T(\d+)\u27e7"
    parts: list[str] = []
    markup: dict[str, str] = {}
    cursor = 0

    def protect(value: str) -> None:
        if value:
            key = f"\u27e6{prefix}M{len(markup)}\u27e7"
            markup[key] = value
            parts.append(key)

    for match in re.finditer(pattern, template):
        protect(template[cursor : match.start()])
        parts.append(texts[int(match[1])])
        cursor = match.end()
    protect(template[cursor:])
    query = "".join(parts)
    if not texts or len(query.encode("utf-8")) > max_bytes:
        return fallback()

    translated = translate(query)
    marker_pattern = rf"\u27e6{prefix}M\d+\u27e7"
    if re.findall(marker_pattern, translated) != list(markup):
        if on_error == "raise":
            raise TranslationStructureError("Translation changed protected Markdown markers")
        if on_error == "empty":
            return ""
        # Reinsert original text, escaped, without making another API request.
        return re.sub(pattern, lambda match: escape(texts[int(match[1])]), template)
    result: list[str] = []
    cursor = 0
    for match in re.finditer(marker_pattern, translated):
        result.append(escape(translated[cursor : match.start()]))
        result.append(markup[match[0]])
        cursor = match.end()
    result.append(escape(translated[cursor:]))
    return "".join(result)
