#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                    Author: Florent TOURNOIS | License: MIT
# =============================================================================
"""
Mistune 3 integration helpers.

This module is the single integration point between ``pymdtools`` and the
external ``mistune`` package. It deliberately targets the modern Mistune API and
does not fall back to the old vendored implementation.

Responsibilities:

- fail early when the installed ``mistune`` package is older than version 3;
- re-export the Mistune objects used by the rest of the package;
- provide renderers that preserve pymdtools' historical ``close()`` hook;
- expose a small helper to create Markdown parsers using those renderers.

The ``close()`` hook is intentionally opt-in: when a renderer defines a callable
``close`` method, its returned text is appended after Mistune has rendered all
tokens. Renderers without ``close`` behave exactly like their Mistune base class.

Typical usage:

>>> markdown = create_markdown_with_close(renderer="html")
>>> markdown("# Title")
'<h1>Title</h1>\\n'

Custom renderers can add final content by defining ``close``:

>>> class Renderer(MdRenderer):
...     def close(self) -> str:
...         return "\\n<!-- closed -->"
>>> markdown = create_markdown_with_close(renderer=Renderer())
>>> markdown("# Title").endswith("<!-- closed -->")
True
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

import mistune
from mistune import HTMLRenderer, Markdown, create_markdown, escape, html
from mistune.core import BaseRenderer, BlockState
from mistune.renderers.markdown import MarkdownRenderer


# -----------------------------------------------------------------------------
def _version_tuple(version: str) -> tuple[int, ...]:
    """
    Convert a version string to a comparable tuple.

    Args:
        version: Version string such as ``"3.2.1"``.

    Returns:
        Tuple containing the leading numeric components.
    """
    parts: list[int] = []
    for raw_part in version.split("."):
        digits = ""
        for char in raw_part:
            if not char.isdigit():
                break
            digits += char
        if digits == "":
            break
        parts.append(int(digits))
    return tuple(parts)


# -----------------------------------------------------------------------------
def _require_mistune3() -> None:
    """
    Ensure that the imported Mistune package exposes the modern API.

    Raises:
        ImportError: If Mistune is older than version 3 or misses required
            modern API entry points.
    """
    version = str(getattr(mistune, "__version__", "0"))
    if _version_tuple(version) < (3,):
        raise ImportError(
            "pymdtools now requires mistune>=3.0. "
            f"The installed mistune version is {version!r}."
        )

    required = ("Markdown", "HTMLRenderer", "create_markdown", "html", "escape")
    missing = [name for name in required if not hasattr(mistune, name)]
    if missing:
        raise ImportError(
            "The installed mistune package does not expose the expected "
            f"Mistune 3 API: missing {', '.join(missing)}."
        )


_require_mistune3()


# -----------------------------------------------------------------------------
def _append_close_output(renderer: BaseRenderer, rendered: str) -> str:
    """
    Append the optional ``close()`` hook output to rendered text.

    Args:
        renderer: Renderer that may define a callable ``close`` method.
        rendered: Text already produced by Mistune.

    Returns:
        ``rendered`` unchanged when the renderer has no close hook, otherwise
        ``rendered`` followed by ``renderer.close()``.
    """
    close = getattr(renderer, "close", None)
    if callable(close):
        close_hook = cast(Callable[[], str], close)
        return rendered + close_hook()
    return rendered


# -----------------------------------------------------------------------------
class ClosingHTMLRenderer(HTMLRenderer):
    """
    HTML renderer with pymdtools' ``close()`` hook support.

    Subclass this renderer and define ``close(self) -> str`` to append final HTML
    after normal Markdown rendering.

    This class is intended for Markdown-to-HTML conversion paths such as
    :func:`pymdtools.mdtopdf.converter_md_to_html_mistune`.
    """

    def __call__(self, tokens: Any, state: BlockState) -> str:
        """Render tokens to HTML and append optional close output."""
        rendered = HTMLRenderer.__call__(self, tokens, state)
        return _append_close_output(self, rendered)


# -----------------------------------------------------------------------------
class ClosingMarkdownRenderer(MarkdownRenderer):
    """
    Markdown renderer with pymdtools' ``close()`` hook support.

    Subclass this renderer and define ``close(self) -> str`` to append final
    Markdown after normal rendering.

    This is the base class for Markdown-to-Markdown workflows, for example
    normalization and translation helpers that preserve Markdown structure.
    """

    def __call__(self, tokens: Any, state: BlockState) -> str:
        """Render tokens to Markdown and append optional close output."""
        rendered = MarkdownRenderer.__call__(self, tokens, state)
        return _append_close_output(self, rendered)


# -----------------------------------------------------------------------------
class MdRenderer(ClosingMarkdownRenderer):
    """
    Render Mistune tokens back to Markdown for pymdtools workflows.

    The base implementation comes from Mistune 3's ``MarkdownRenderer``. Custom
    pymdtools renderers can subclass this class and optionally define
    ``close(self) -> str`` to append final closing content after rendering.

    ``MdRenderer`` exists as the stable pymdtools-facing name for Markdown output
    renderers. It keeps callers independent from Mistune's internal renderer
    module layout.
    """


# -----------------------------------------------------------------------------
def create_markdown_with_close(renderer: Any = "html", **kwargs: Any) -> Any:
    """
    Create a Mistune Markdown parser with ``close()`` support for renderers.

    Args:
        renderer: Mistune renderer name or renderer instance. ``"html"`` and
            ``"markdown"`` are replaced by the pymdtools closing-aware renderers.
        **kwargs: Forwarded to :func:`mistune.create_markdown`.

    Returns:
        A configured Mistune Markdown parser.
    """
    if renderer == "html":
        renderer = ClosingHTMLRenderer()
    elif renderer == "markdown":
        renderer = ClosingMarkdownRenderer()
    return create_markdown(renderer=renderer, **kwargs)


# -----------------------------------------------------------------------------
def get_backend_name() -> str:
    """
    Return the active Markdown backend name.

    Returns:
        Always ``"mistune"``.
    """
    return "mistune"


# -----------------------------------------------------------------------------
def get_backend_version() -> str:
    """
    Return the installed Mistune version string.

    Returns:
        Mistune ``__version__`` when available, otherwise ``"unknown"``.
    """
    return str(getattr(mistune, "__version__", "unknown"))


__version__ = get_backend_version()

__all__ = [
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
]


# =============================================================================
