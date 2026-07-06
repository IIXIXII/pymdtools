#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                    Author: Florent TOURNOIS | License: MIT
# =============================================================================
"""
Backward-compatible wrapper for :mod:`pymdtools.markdownify_integration`.

The historical ``pymdtools.markdownify`` module contained a vendored copy of the
third-party ``markdownify`` implementation. The maintained implementation now
lives in the external ``markdownify`` package, and pymdtools exposes it through
``markdownify_integration``.

Import from :mod:`pymdtools.markdownify_integration` in new code. This module is
kept so older imports such as ``from pymdtools.markdownify import markdownify``
continue to work.
"""

from __future__ import annotations

from .markdownify_integration import (
    ATX,
    ATX_CLOSED,
    SETEXT,
    UNDERLINED,
    MarkdownConverter,
    __version__,
    get_backend_name,
    get_backend_version,
    markdownify,
)

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
