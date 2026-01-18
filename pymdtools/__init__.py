#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
#
# Copyright (c) 2018 Florent TOURNOIS
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# -----------------------------------------------------------------------------
""" Markdown Tools developed for Gucihet Entreprises """

from __future__ import annotations

# ---------------------------------------------------------------------------
# Package metadata (lightweight, no side effects)
# ---------------------------------------------------------------------------
from .version import __version_info__, __release_date__
from ._about import (
    __author__,
    __author_email__,
    __license__,
    __status__,
)

__version__ = ".".join(str(c) for c in __version_info__)
__module_name__ = "pymdtools"

# ---------------------------------------------------------------------------
# Public API (lazy-loaded)
# ---------------------------------------------------------------------------
__all__ = [
    "print_conv",
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
    if name == "print_conv":
        from .common import print_conv
        return print_conv

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
