#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                    Author: Florent TOURNOIS | License: MIT                   
# =============================================================================
""" Markdown Tools package
    ~~~~~~~~~~~~~~~~~~~~~~
    A set of tools to manipulate Markdown files, convert them to PDF, etc."""

from __future__ import annotations

from typing import Callable, Final

# -----------------------------------------------------------------------------
# --- Package metadata (lightweight, no side effects)
# -----------------------------------------------------------------------------
from .version import __version__, __version_info__, __release_date__
from ._about import __author__, __author_email__, __license__, __status__

__all__ = [
    # Public functions (lazy)
    "convert_for_stdout",
    "markdown_file_beautifier",
    "convert_md_to_pdf",
    "search_include_refs_to_md_file",
    # Metadata
    "__version__",
    "__version_info__",
    "__release_date__",
    "__author__",
    "__author_email__",
    "__license__",
    "__status__",
]

__module_name__: Final[str] = "pymdtools"


# -----------------------------------------------------------------------------
# Map public names -> (module, attribute)
# -----------------------------------------------------------------------------
_LAZY: dict[str, tuple[str, str]] = {
    "convert_for_stdout": 
        (".common", "convert_for_stdout"),
    "markdown_file_beautifier": 
        (".normalize", "md_file_beautifier"),
    "convert_md_to_pdf": 
        (".mdtopdf", "convert_md_to_pdf"),
    "search_include_refs_to_md_file": 
        (".instruction", "search_include_refs_to_md_file"),
}


def __getattr__(name: str):
    """Lazy import of public symbols to avoid importing heavy dependencies at import time."""
    try:
        module_name, attr_name = _LAZY[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc

    try:
        module = __import__(f"{__name__}{module_name}", fromlist=[attr_name])
        obj = getattr(module, attr_name)
    except ImportError as exc:
        # Contexte explicite sans perdre la cause
        raise ImportError(f"Cannot import {name!r} from {module_name} (missing optional dependency?)") from exc

    globals()[name] = obj  # cache
    return obj


def __dir__() -> list[str]:
    dunder = {k for k in globals().keys() if k.startswith("__") and k.endswith("__")}
    return sorted(dunder | set(__all__))


# =============================================================================