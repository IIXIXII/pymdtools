"""Directives: headings."""

from __future__ import annotations

import logging
from typing import (
    Match,
    Union,
)

from ..mdcommon import markdown_code_ranges, merge_ranges
from ._shared import (
    ATX_H1_RE,
    SETEXT_H1_RE,
    XML_COMMENT_RE,
    TitleStyle,
    all_str,
    finditer_outside_ranges,
    require_str,
)

logger: logging.Logger = logging.getLogger(__name__)


def strip_xml_comment(text: str) -> str:
    """
    Remove XML / HTML comments from a text.

    XML comments are defined as any content between ``<!--`` and ``-->``,
    including multi-line comments.

    Args:
        text: Input markdown (or text) content.

    Returns:
        The input text with all XML comments removed.
    """
    return XML_COMMENT_RE.sub("", text)


def first_title_match(text: str) -> tuple[Match[str], TitleStyle] | None:
    """Return the first real H1 and its source style."""
    protected_ranges = merge_ranges(
        [
            *markdown_code_ranges(text),
            *(match.span() for match in XML_COMMENT_RE.finditer(text)),
        ]
    )
    candidates: list[tuple[Match[str], TitleStyle]] = []
    candidates.extend(
        (match, "setext") for match in finditer_outside_ranges(SETEXT_H1_RE, text, protected_ranges)
    )
    candidates.extend(
        (match, "atx") for match in finditer_outside_ranges(ATX_H1_RE, text, protected_ranges)
    )
    return min(candidates, key=lambda item: item[0].start()) if candidates else None


def get_title_from_md_text(text: str, return_match: bool = False) -> Union[None, str, Match[str]]:
    """
    Extract the first level-1 Markdown title from text.

    Supported syntaxes are Setext H1 (``Title`` followed by ``=====``) and
    ATX H1 (``# Title``).

    Comments and Markdown code regions are ignored while searching.

    Args:
        text: Markdown text.
        return_match: If True, return the `re.Match` object on the source text.

    Returns:
        The title string (stripped), or None if not found.
        If return_match is True, returns the match object instead.

    Raises:
        TypeError: If text is not a string.
    """
    text = require_str(text, "text")

    title_match = first_title_match(text)
    if title_match is None:
        return None
    m, _ = title_match

    if return_match:
        return m

    return m.group("title").strip()


def set_title_in_md_text(text: str, new_title: str, *, style: TitleStyle = "preserve") -> str:
    """
    Set or insert the first level-1 Markdown title in `text`.

    Supported syntaxes are Setext H1 (``Title`` followed by ``=====``) and
    ATX H1 (``# Title``).

    Behavior:
      - If an H1 title exists, it is replaced according to `style`:
          * "preserve": keep the existing style (Setext stays Setext, ATX stays ATX)
          * "setext": force Setext output
          * "atx": force ATX output
      - If no H1 title exists, a new title is inserted at the beginning using:
          * "preserve" -> Setext (default insertion format)
          * "setext" -> Setext
          * "atx" -> ATX

    Notes:
      - Titles inside XML comments are ignored (comments are stripped before detection).
      - Replacement is applied to the first detected H1 only.

    Args:
        text: Markdown text.
        new_title: New title (must be non-empty after stripping).
        style: "preserve" | "setext" | "atx".

    Returns:
        Updated markdown text.

    Raises:
        TypeError: If inputs are not strings.
        ValueError: If `new_title` is blank or `style` is invalid.
    """
    text = require_str(text, "text")
    if not all_str(new_title):
        raise TypeError("new_title must be a string")

    title = new_title.strip()
    if not title:
        raise ValueError("new_title must be non-empty")
    if style not in ("preserve", "setext", "atx"):
        raise ValueError(f"invalid style: {style!r}")

    title_match = first_title_match(text)

    # Decide output style
    if style == "preserve":
        output_style: TitleStyle
        if title_match is not None:
            output_style = title_match[1]
        else:
            output_style = "setext"  # default insertion format
    else:
        output_style = style

    def make_setext(t: str) -> str:
        return f"{t}\n" + ("=" * len(t)) + "\n"

    def make_atx(t: str) -> str:
        return f"# {t}\n"

    if title_match is not None:
        match, _ = title_match
        replacement = make_setext(title) if output_style == "setext" else make_atx(title)
        return text[: match.start()] + replacement + text[match.end() :]

    # No title found: insert at top
    replacement = make_setext(title) if output_style == "setext" else make_atx(title)
    # Add a blank line after the title if content does not already start with newline
    if text and not text.startswith("\n"):
        return replacement + "\n" + text
    return replacement + text
