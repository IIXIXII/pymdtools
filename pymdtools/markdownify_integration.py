#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                    Author: Florent TOURNOIS | License: MIT
# =============================================================================
"""
Markdownify integration helpers.

This module is the single integration point between ``pymdtools`` and the
external ``markdownify`` package. It replaces the historical vendored
implementation with a thin compatibility layer over the maintained dependency.

Responsibilities:

- fail early when the installed ``markdownify`` package misses expected API
  symbols;
- re-export the converter class and heading-style constants used by older
  pymdtools callers;
- provide a typed ``markdownify`` helper and backend metadata functions.

Typical usage:

>>> markdownify("<h1>Title</h1>").strip()
'Title\\n====='
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import Any, cast

import markdownify as _markdownify


# -----------------------------------------------------------------------------
def _require_markdownify() -> None:
    """
    Ensure that the external package exposes the expected compatibility API.

    Raises:
        ImportError: If the installed package misses required symbols.
    """
    required = (
        "ATX",
        "ATX_CLOSED",
        "MarkdownConverter",
        "SETEXT",
        "UNDERLINED",
        "markdownify",
    )
    missing = [name for name in required if not hasattr(_markdownify, name)]
    if missing:
        raise ImportError(
            "The installed markdownify package does not expose the expected "
            f"API: missing {', '.join(missing)}."
        )


_require_markdownify()


ATX = _markdownify.ATX
ATX_CLOSED = _markdownify.ATX_CLOSED
UNDERLINED = _markdownify.UNDERLINED
SETEXT = _markdownify.SETEXT
MarkdownConverter = cast(Any, _markdownify.MarkdownConverter)


# -----------------------------------------------------------------------------
def markdownify(html: str, **options: Any) -> str:
    """
    Convert HTML text to Markdown using the external ``markdownify`` package.

    Args:
        html: HTML fragment or document to convert.
        **options: Options forwarded to ``markdownify.markdownify``.

    Returns:
        Converted Markdown text.
    """
    return _markdownify.markdownify(html, **options)


# -----------------------------------------------------------------------------
def get_backend_name() -> str:
    """
    Return the active HTML-to-Markdown backend name.

    Returns:
        Always ``"markdownify"``.
    """
    return "markdownify"


# -----------------------------------------------------------------------------
def get_backend_version() -> str:
    """
    Return the installed markdownify package version.

    Returns:
        Package metadata version when available, otherwise ``"unknown"``.
    """
    raw_version = getattr(_markdownify, "__version__", None)
    if raw_version is not None:
        return str(raw_version)

    try:
        return version("markdownify")
    except PackageNotFoundError:
        return "unknown"


__version__ = get_backend_version()

__all__ = [
    "ATX",
    "ATX_CLOSED",
    "MarkdownConverter",
    "SETEXT",
    "UNDERLINED",
    "__version__",
    "get_backend_name",
    "get_backend_version",
    "markdownify",
]


# =============================================================================
