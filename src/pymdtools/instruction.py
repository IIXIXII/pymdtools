"""Compatibility facade for instruction.

Implementations live in _directives. Public imports remain stable.
"""

from __future__ import annotations

import logging
from typing import (
    Optional,
)

from . import common
from ._directives._shared import IncludeRenderMode as IncludeRenderMode
from ._directives._shared import RegexInput as RegexInput
from ._directives._shared import TitleStyle as TitleStyle
from ._directives.discovery import get_refs_around_md_file as get_refs_around_md_file
from ._directives.discovery import get_refs_from_md_directory as get_refs_from_md_directory
from ._directives.discovery import get_refs_from_search_folders as get_refs_from_search_folders
from ._directives.discovery import get_vars_around_md_file as get_vars_around_md_file
from ._directives.discovery import get_vars_from_md_directory as get_vars_from_md_directory
from ._directives.headings import get_title_from_md_text as get_title_from_md_text
from ._directives.headings import set_title_in_md_text as set_title_in_md_text
from ._directives.headings import strip_xml_comment as strip_xml_comment
from ._directives.includes import del_include_file_to_md_text as del_include_file_to_md_text
from ._directives.includes import ensure_include_file_in_md_text as ensure_include_file_in_md_text
from ._directives.includes import get_file_content_to_include as get_file_content_to_include
from ._directives.includes import get_include_file_list as get_include_file_list
from ._directives.includes import include_files_to_md_file as include_files_to_md_file
from ._directives.includes import include_files_to_md_text as include_files_to_md_text
from ._directives.references import get_refs_from_md_file as get_refs_from_md_file
from ._directives.references import get_refs_from_md_text as get_refs_from_md_text
from ._directives.references import include_refs_to_md_file as include_refs_to_md_file
from ._directives.references import include_refs_to_md_text as include_refs_to_md_text
from ._directives.references import refs_in_md_text as refs_in_md_text
from ._directives.variables import del_var_to_md_text as del_var_to_md_text
from ._directives.variables import escape_var_value as escape_var_value
from ._directives.variables import get_vars_from_md_file as get_vars_from_md_file
from ._directives.variables import get_vars_from_md_text as get_vars_from_md_text
from ._directives.variables import include_vars_to_md_file as include_vars_to_md_file
from ._directives.variables import include_vars_to_md_text as include_vars_to_md_text
from ._directives.variables import search_include_vars_to_md_text as search_include_vars_to_md_text
from ._directives.variables import set_var_to_md_text as set_var_to_md_text
from ._directives.variables import unescape_var_value as unescape_var_value

logger: logging.Logger = logging.getLogger(__name__)


def search_include_refs_to_md_file(
    filename: common.PathInput,
    *,
    backup_option: bool = True,
    backup_ext: str = ".bak",
    filename_ext: str = ".md",
    depth_up: int = 1,
    depth_down: int = -1,
) -> str:
    """
    Discover refs around a markdown file and apply include substitutions in-place.

    This is a convenience function:
      1) Collect refs by scanning folders around `filename` (see `get_refs_around_md_file`)
      2) Apply includes into `filename` (see `include_refs_to_md_file`)

    Args:
        filename: Markdown file to process.
        backup_option: Whether to create a backup before overwriting.
        backup_ext: Backup extension (e.g. ".bak").
        filename_ext: Expected extension for `filename`.
        depth_up: Number of parent directory levels to move up for the search root (>= 0).
        depth_down: Depth for scanning downward (-1 unlimited, 0 current dir only, >0 limited).

    Returns:
        Normalized filename (string).

    Raises:
        ValueError: If `depth_up` < 0 or `depth_down` < -1.
        KeyError/ValueError: Propagated from include resolution if refs are missing/malformed.
        RuntimeError/Exception: Propagated from filesystem helpers.
    """
    if depth_up < 0:
        raise ValueError(f"depth_up must be >= 0, got: {depth_up}")
    if depth_down < -1:
        raise ValueError(f"depth_down must be >= -1, got: {depth_down}")

    refs = get_refs_around_md_file(
        filename,
        filename_ext=filename_ext,
        depth_up=depth_up,
        depth_down=depth_down,
    )
    return include_refs_to_md_file(
        filename,
        refs,
        backup_option=backup_option,
        backup_ext=backup_ext,
        filename_ext=filename_ext,
    )


def search_include_vars_to_md_file(
    filename: common.PathInput,
    *,
    backup_option: bool = True,
    backup_ext: str = ".bak",
    filename_ext: str = ".md",
    depth_up: int = 1,
    depth_down: int = -1,
    encoding: Optional[str] = None,
) -> str:
    """
    Search vars around `filename` and apply begin-var/end-var substitutions in-place.
    """
    vars_ = get_vars_around_md_file(
        filename,
        filename_ext=filename_ext,
        depth_up=depth_up,
        depth_down=depth_down,
        encoding=encoding,
    )
    return include_vars_to_md_file(
        filename,
        vars_,
        backup_option=backup_option,
        backup_ext=backup_ext,
        filename_ext=filename_ext,
    )


__all__ = [
    "IncludeRenderMode",
    "RegexInput",
    "TitleStyle",
    "del_include_file_to_md_text",
    "del_var_to_md_text",
    "ensure_include_file_in_md_text",
    "escape_var_value",
    "get_file_content_to_include",
    "get_include_file_list",
    "get_refs_around_md_file",
    "get_refs_from_md_directory",
    "get_refs_from_md_file",
    "get_refs_from_md_text",
    "get_refs_from_search_folders",
    "get_title_from_md_text",
    "get_vars_around_md_file",
    "get_vars_from_md_directory",
    "get_vars_from_md_file",
    "get_vars_from_md_text",
    "include_files_to_md_file",
    "include_files_to_md_text",
    "include_refs_to_md_file",
    "include_refs_to_md_text",
    "include_vars_to_md_file",
    "include_vars_to_md_text",
    "refs_in_md_text",
    "search_include_refs_to_md_file",
    "search_include_vars_to_md_file",
    "search_include_vars_to_md_text",
    "set_title_in_md_text",
    "set_var_to_md_text",
    "strip_xml_comment",
    "unescape_var_value",
]
