#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                    Author: Florent TOURNOIS | License: MIT
# =============================================================================
"""
pymdtools
=========

Utilities for manipulating Markdown files and transforming them into other
representations (HTML, PDF, etc.). The package focuses on practical Markdown
workflows such as normalization/beautification and include-resolution.

This package-level module is designed to be **production-hardened**:

- **Light imports**: importing :mod:`pymdtools` must not pull heavy dependencies.
- **Stable public surface**: only symbols listed in ``__all__`` are public.
- **Lazy loading**: public callables are imported on-demand to reduce import time
  and to keep optional dependencies optional.
- **Actionable errors**: missing submodules / optional dependencies raise
  informative :class:`ImportError`.

Public API
----------
The following functions are exposed at package level:

- :func:`pymdtools.convert_for_stdout`
- :func:`pymdtools.markdown_file_beautifier`
- :func:`pymdtools.convert_md_to_pdf`
- :func:`pymdtools.search_include_refs_to_md_file`

Notes
-----
Lazy loading relies on :pep:`562` (module-level ``__getattr__`` / ``__dir__``),
thus Python >= 3.7 is required.

After the first access, lazily-loaded symbols are cached into the module
namespace (``globals()``) for subsequent direct access.

Examples
--------
Import the package (recommended):

>>> import pymdtools
>>> text = pymdtools.convert_for_stdout("# Title\\n\\nBody")
>>> pymdtools.markdown_file_beautifier("README.md")

Import a specific symbol directly:

>>> from pymdtools import convert_for_stdout
>>> convert_for_stdout("# Title")
"""

from __future__ import annotations

from importlib import import_module
from typing import Final, TYPE_CHECKING

# -----------------------------------------------------------------------------
# Package metadata (must remain side-effect free)
# -----------------------------------------------------------------------------
from .version import __version__, __version_info__, __release_date__
from ._about import __author__, __author_email__, __license__, __status__

__module_name__ = "pymdtools"

# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------

if TYPE_CHECKING:
    from .common import convert_for_stdout
    from .normalize import md_file_beautifier as markdown_file_beautifier
    from .mdtopdf import convert_md_to_pdf
    from .instruction import search_include_refs_to_md_file
    
__all__ = [
    # Lazily-loaded callables
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

# -----------------------------------------------------------------------------
# Lazy resolution table: public_symbol -> (relative_module, attribute_name)
# -----------------------------------------------------------------------------
_LAZY: Final[dict[str, tuple[str, str]]] = {
    "convert_for_stdout": (".common", "convert_for_stdout"),
    "markdown_file_beautifier": (".normalize", "md_file_beautifier"),
    "convert_md_to_pdf": (".mdtopdf", "convert_md_to_pdf"),
    "search_include_refs_to_md_file": (".instruction", "search_include_refs_to_md_file"),
}


# -----------------------------------------------------------------------------
def __getattr__(name: str):
    """
    Lazily resolve public symbols.

    This hook is called only when the attribute is not already present in
    the module namespace. Resolution is strictly limited to the ``_LAZY``
    table to avoid accidentally exposing internal objects.

    Parameters
    ----------
    name : str
        Requested attribute name.

    Returns
    -------
    object
        The resolved symbol (typically a function).

    Raises
    ------
    AttributeError
        If ``name`` is not a supported public symbol.
    ImportError
        If the underlying submodule cannot be imported (e.g. optional
        dependency not installed) or if the attribute is missing from that
        submodule (packaging/refactor mismatch).
    """
    target = _LAZY.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_rel, attr_name = target

    try:
        module = import_module(module_rel, package=__name__)
    except ModuleNotFoundError as exc:
        raise ImportError(
            f"Cannot import {name!r}: failed to import submodule {module_rel!r} "
            f"from package {__name__!r}. This may indicate an optional dependency "
            f"is not installed or the installation is incomplete."
        ) from exc

    try:
        obj = getattr(module, attr_name)
    except AttributeError as exc:
        raise ImportError(
            f"Cannot import {name!r}: attribute {attr_name!r} not found in {module.__name__!r}. "
            f"Check the lazy import table in {__name__!r} and the submodule implementation."
        ) from exc

    # Cache into package namespace for faster subsequent access.
    globals()[name] = obj
    return obj
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def __dir__() -> list[str]:
    """
    Return a curated list of attributes for introspection.

    This improves ``dir(pymdtools)`` output and IDE auto-completion by listing
    public symbols even when they are lazily loaded.
    """
    public = set(__all__)
    dunder = {k for k in globals() if k.startswith("__") and k.endswith("__")}
    return sorted(public | dunder)
# -----------------------------------------------------------------------------


# =============================================================================