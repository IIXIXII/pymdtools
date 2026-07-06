#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                    Author: Florent TOURNOIS | License: MIT
# =============================================================================
"""
Markdown normalization helpers.

This module provides the small public surface used by pymdtools to make Markdown
content consistent:

- :func:`md_beautifier` normalizes an in-memory Markdown string;
- :func:`md_file_beautifier` applies the same transformation to a Markdown file.

Normalization is implemented as a Markdown-to-Markdown rendering pass through
the Mistune 3 integration layer. File-oriented work delegates path validation,
backup creation, encoding-aware reads, and writes to :mod:`pymdtools.common`.

Examples:
    Normalize a string:

    >>> md_beautifier("# Title\\n\\nBody\\n\\n")
    '# Title\\n\\nBody'

    Normalize a file in place:

    >>> md_file_beautifier("README.md", backup_option=True)
    '...README.md'
"""

from __future__ import annotations

import logging
from pathlib import Path

from . import common
from . import mistune_integration as mistune


# -----------------------------------------------------------------------------
def md_beautifier(text: object) -> str:
    """
    Normalize Markdown text.

    The input is parsed by Mistune and rendered back to Markdown with
    :class:`pymdtools.mistune_integration.MdRenderer`. The result is stripped of
    leading and trailing whitespace, matching the historical behavior of this
    function.

    This helper is intentionally small: it does not resolve include directives,
    variables, or file references. Those transformations live in
    :mod:`pymdtools.instruction`.

    Args:
        text: Markdown text to normalize.

    Returns:
        Normalized Markdown text.

    Raises:
        TypeError: If ``text`` is not a string.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    logging.debug("Beautify markdown content")

    renderer = mistune.MdRenderer()
    markdown = mistune.create_markdown_with_close(renderer=renderer)
    return str(markdown(text)).strip()


# -----------------------------------------------------------------------------
def md_file_beautifier(
    filename: common.PathInput,
    backup_option: bool = True,
    filename_ext: str = ".md",
    *,
    backup_ext: str = ".bak",
    read_encoding: str | None = None,
    write_encoding: str = "utf-8",
) -> str:
    """
    Normalize a Markdown file in place.

    The file is validated, read, optionally backed up, normalized with
    :func:`md_beautifier`, and written back with the requested encoding.

    Backups are created before writing and use :func:`pymdtools.common.create_backup`.
    The file is written through :func:`pymdtools.common.set_file_content`, so the
    write path follows the common module's atomic-write behavior.

    Args:
        filename: Markdown file to normalize.
        backup_option: Whether to create a backup before overwriting the file.
        filename_ext: Expected Markdown extension, including the leading dot.
        backup_ext: Backup extension used when ``backup_option`` is true.
        read_encoding: Encoding used to read the file. ``None`` triggers
            automatic detection in :mod:`pymdtools.common`.
        write_encoding: Encoding used to write the normalized file.

    Returns:
        Normalized absolute filename as a string.

    Raises:
        FileNotFoundError: If ``filename`` does not exist.
        IsADirectoryError: If ``filename`` is not a regular file.
        ValueError: If the file extension is unexpected or the file is empty.
        OSError: Propagated from filesystem helpers.
    """
    logging.debug("Beautify markdown file %s", filename)

    checked: Path = common.check_file(filename, filename_ext)
    text = common.get_file_content(checked, encoding=read_encoding)
    if not text:
        raise ValueError(f"The filename {checked} seems empty")

    if backup_option:
        common.create_backup(checked, ext=backup_ext)

    normalized = md_beautifier(text)
    common.set_file_content(checked, normalized, encoding=write_encoding)
    return str(checked)


# =============================================================================
