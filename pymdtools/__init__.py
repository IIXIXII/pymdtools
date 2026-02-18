#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                    Author: Florent TOURNOIS | License: MIT                   
# =============================================================================
""" Markdown Tools package
    ~~~~~~~~~~~~~~~~~~~~~~
    A set of tools to manipulate Markdown files, convert them to PDF, etc."""

from __future__ import annotations


# -----------------------------------------------------------------------------
# Package metadata (lightweight, no side effects)
# -----------------------------------------------------------------------------
from .version import __version_info__, __release_date__
from ._about import (
    __author__,
    __author_email__,
    __license__,
    __status__,
)


__version__ = ".".join(str(c) for c in __version_info__)
__module_name__ = "pymdtools"


# -----------------------------------------------------------------------------
# Public API (lazy-loaded)
# -----------------------------------------------------------------------------
__all__ = [
    "convert_for_stdout",
    "markdown_file_beautifier",
    "convert_md_to_pdf",
    "search_include_refs_to_md_file",
    "__version__",
]


def __getattr__(name: str):
    """
    Lazy import of public symbols to avoid importing heavy dependencies
    (dateutil, pdfkit, etc.) at package import time.
    """
    if name == "convert_for_stdout":
        from .common import convert_for_stdout
        return convert_for_stdout

    if name == "markdown_file_beautifier":
        from .normalize import md_file_beautifier as markdown_file_beautifier
        return markdown_file_beautifier

    if name == "convert_md_to_pdf":
        from .mdtopdf import convert_md_to_pdf
        return convert_md_to_pdf

    if name == "search_include_refs_to_md_file":
        from .instruction import search_include_refs_to_md_file
        return search_include_refs_to_md_file

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# =============================================================================