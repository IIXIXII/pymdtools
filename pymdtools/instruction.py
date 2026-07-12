#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                    Author: Florent TOURNOIS | License: MIT                   
# =============================================================================
"""
Markdown instruction helpers.

This module implements the comment-based directives used by ``pymdtools`` to
assemble Markdown documents:

- reference blocks, declared with ``begin-ref`` / ``end-ref`` and inserted with
  ``begin-include`` / ``end-include``;
- variable declarations, declared with ``var(NAME)="value"`` and inserted with
  ``begin-var`` / ``end-var``;
- ``include-file`` directives that inline external text files;
- level-1 Markdown title extraction and rewriting.

The functions operate either on text strings or on Markdown files. File-oriented
helpers delegate path validation, encoding detection, backup creation, and
content writes to :mod:`pymdtools.common`.
"""

from __future__ import annotations

# -----------------------------------------------------------------------------
# @package mdtools
# Markdown Tools develops for Florent TOURNOIS
#
# -----------------------------------------------------------------------------
import logging
import os
import re
from pathlib import Path

from typing import (
    Any,
    Final,
    Dict,
    Iterable,
    List,
    Literal,
    Match,
    Mapping,
    Optional,
    Pattern,
    Sequence,
    Union,
)

from . import common
from .mdcommon import markdown_code_ranges, merge_ranges, position_in_ranges

TitleStyle          = Literal["preserve", "setext", "atx"]
IncludeRenderMode   = Literal["box", "raw"]
RegexInput          = Union[str, Pattern[str]]


# -----------------------------------------------------------------------------
# Regular expressions used by this module
#
# Conventions:
# - All patterns are compiled once at import time.
# - Patterns with named groups MUST expose:
#     - group("name") for markers referencing a key/variable/file name
#     - group("string") for var(...) raw string values (without quotes)
# - re.VERBOSE is used for readability when the pattern is non-trivial.
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# 1) Generic XML/HTML comment: <!-- ... -->
#
# Used for: stripping comments from markdown text.
# Notes:
# - DOTALL to match multi-line comments.
# - Non-greedy to stop at the first closing marker.
# -----------------------------------------------------------------------------
_XML_COMMENT_RE: Final[re.Pattern[str]] = re.compile(r"<!--.*?-->", re.DOTALL)


# -----------------------------------------------------------------------------
# 2) Reference blocks: begin-ref(NAME) ... end-ref
#
# Markers:
#   <!-- begin-ref(name) -->
#   ...content...
#   <!-- end-ref -->
#
# Group(s):
#   - name: reference key (letters/digits/_/-)
# -----------------------------------------------------------------------------
_BEGIN_REF_RE: Final[re.Pattern[str]] = re.compile(
    r"<!--\s*begin-ref\(\s*(?P<name>[A-Za-z0-9_-]+)\s*\)\s*-->"
)
_END_REF_RE: Final[re.Pattern[str]] = re.compile(
    r"<!--\s*end-ref\s*-->"
)


# -----------------------------------------------------------------------------
# 3) Include blocks: begin-include(NAME) ... end-include
#
# Markers:
#   <!-- begin-include(name) -->
#   ...content...
#   <!-- end-include -->
#
# Group(s):
#   - name: include key (letters/digits/_/-)
# -----------------------------------------------------------------------------
_BEGIN_INCLUDE_RE: Final[re.Pattern[str]] = re.compile(
    r"""
    <!--\s*
    begin-include
    \(\s*(?P<name>[A-Za-z0-9_-]+)\s*\)
    \s*-->
    """,
    re.VERBOSE,
)
_END_INCLUDE_RE: Final[re.Pattern[str]] = re.compile(
    r"""
    <!--\s*
    end-include
    \s*-->
    """,
    re.VERBOSE,
)


# -----------------------------------------------------------------------------
# 4) Variables: <!-- var(NAME)="value" --> / <!-- var(NAME)='value' -->
#
# Supported NAME:
# - segments separated by '/', to allow namespaces (e.g. "a/b/c")
# - allowed chars per segment: [A-Za-z0-9:_-]
#
# Groups:
# - name  : variable name (possibly "a/b/c")
# - quote : opening quote (single or double)
# - string: raw string content (escapes preserved), without surrounding quotes
#
# Notes:
# - The `string` group accepts escaped characters (\\.) to allow \" or \n etc.
# - The pattern is verbose for maintainability.
# -----------------------------------------------------------------------------
_VAR_RE: Final[re.Pattern[str]] = re.compile(
    r"""
    <!--\s*var\(
        (?P<name>[A-Za-z0-9:_-]+(?:/[A-Za-z0-9:_-]+)*)
    \)\s*=\s*
        (?P<quote>['"])
        (?P<string>(?:\\.|(?!(?P=quote)).)*)
        (?P=quote)
    \s*-->
    """,
    re.VERBOSE,
)


# -----------------------------------------------------------------------------
# 5) Escape helpers for var values
#
# - _ESCAPE_RE captures the escaped character after '\'
# - _ESCAPE_MAP maps supported escapes to their interpreted value
# - _VAR_NAME_RE validates accepted variable names (same grammar as _VAR_RE)
# - _ESCAPE_OUT_MAP maps special chars to their escaped form when writing
# -----------------------------------------------------------------------------
_ESCAPE_RE: Final[re.Pattern[str]] = re.compile(r"\\(.)", re.DOTALL)

_ESCAPE_MAP: Final[dict[str, str]] = {
    "n": "\n",
    "t": "\t",
    "r": "\r",
    "\\": "\\",
    '"': '"',
    "'": "'",
}

_VAR_NAME_RE: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9:_-]+(?:/[A-Za-z0-9:_-]+)*$"
)

_ESCAPE_OUT_MAP: Final[dict[str, str]] = {
    "\\": r"\\",
    "\n": r"\n",
    "\t": r"\t",
    "\r": r"\r",
    '"': r"\"",
}


# -----------------------------------------------------------------------------
# 6) include-file(...) directives
#
# Marker:
#   <!-- include-file(path/to/file.ext) ... -->
#
# Groups:
# - name   : referenced path (relative), optionally starting with ./ or ../
# - content: any content between the filename closing ')' and '-->'
#
# Notes:
# - The module currently supports nested paths (a/b/c.ext).
# - Keep `content` non-greedy to stop at the first "-->".
# -----------------------------------------------------------------------------
_INCLUDE_FILE_RE: Final[re.Pattern[str]] = re.compile(
    r"""
    <!--\s*
    include-file\(
        (?P<name>(?:\.\.?/)?[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)*)
    \)
        (?P<content>[\s\S]*?)
    -->
    """,
    re.VERBOSE,
)


# -----------------------------------------------------------------------------
# 7) Title patterns (Setext H1 / ATX H1)
#
# Used by title extraction and rewriting utilities.
# - Setext:
#       Title
#       =====
# - ATX:
#       # Title
# -----------------------------------------------------------------------------
_SETEXT_H1_RE: Final[re.Pattern[str]] = re.compile(
    r"""(?mx)
    ^[ ]{0,3}(?P<title>[^\r\n]+?)[ \t]*\r?\n
    ^[ ]{0,3}=+[ \t]*\r?\n?
    """
)

_ATX_H1_RE: Final[re.Pattern[str]] = re.compile(
    r"""(?mx)
    ^[ ]{0,3}\#[ \t]+(?P<title>[^\r\n#]*?[^\s#])[ \t]*\#*[ \t]*(?:\r?\n|$)
    """
)


# -----------------------------------------------------------------------------
# 8) begin-var/end-var blocks (replacement blocks)
#
# Markers:
#   <!-- begin-var(name) -->
#   ...content...
#   <!-- end-var -->
#
# Groups:
# - name: var name (same grammar as _VAR_NAME_RE)
# -----------------------------------------------------------------------------
_BEGIN_VAR_RE: Final[re.Pattern[str]] = re.compile(
    r"<!--\s*begin-var\(\s*(?P<name>[A-Za-z0-9:_-]+(?:/[A-Za-z0-9:_-]+)*)\s*\)\s*-->",
)
_END_VAR_RE: Final[re.Pattern[str]] = re.compile(
    r"<!--\s*end-var\s*-->",
)


# -----------------------------------------------------------------------------
def _normalize_read_encoding(encoding: Optional[str]) -> Optional[str]:
    """
    Convert the legacy ``"UNKNOWN"`` sentinel to the current common API.

    ``common.get_file_content`` now uses ``encoding=None`` to request automatic
    encoding detection.
    """
    if encoding is None:
        return None
    if encoding.upper() == "UNKNOWN":
        return None
    return encoding


# -----------------------------------------------------------------------------
def _read_md_text(path: common.PathInput, encoding: Optional[str] = None) -> str:
    """Read text through ``common`` while accepting the legacy encoding sentinel."""
    return common.get_file_content(path, encoding=_normalize_read_encoding(encoding))


# -----------------------------------------------------------------------------
def _create_backup(path: common.PathInput, backup_ext: str) -> Path:
    """Create a backup using the current ``common.create_backup`` signature."""
    return common.create_backup(path, ext=backup_ext, date_prefix=common.today_utc())


# -----------------------------------------------------------------------------
def _require_str(value: object, name: str) -> str:
    """Return ``value`` as ``str`` or raise a stable runtime error."""
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    return value


# -----------------------------------------------------------------------------
def _all_str(*values: object) -> bool:
    """Return whether all values are strings."""
    return all(isinstance(value, str) for value in values)


# -----------------------------------------------------------------------------
def _is_non_empty_str(value: object, *, strip: bool = False) -> bool:
    """Return whether ``value`` is a non-empty string."""
    if not isinstance(value, str):
        return False
    candidate = value.strip() if strip else value
    return bool(candidate)


# -----------------------------------------------------------------------------
def _compile_pattern(pattern: RegexInput) -> Pattern[str]:
    """Return a compiled regex pattern."""
    return re.compile(pattern) if isinstance(pattern, str) else pattern


# -----------------------------------------------------------------------------
def _finditer_outside_ranges(
    pattern: Pattern[str],
    text: str,
    ranges: Sequence[tuple[int, int]],
) -> list[Match[str]]:
    """Return pattern matches whose opening character is not protected."""
    return [
        match
        for match in pattern.finditer(text)
        if not position_in_ranges(match.start(), ranges)
    ]


# -----------------------------------------------------------------------------
def _search_outside_ranges(
    pattern: Pattern[str],
    text: str,
    start: int,
    ranges: Sequence[tuple[int, int]],
) -> Match[str] | None:
    """Return the first match at or after ``start`` outside protected ranges."""
    match = pattern.search(text, start)
    while match is not None and position_in_ranges(match.start(), ranges):
        match = pattern.search(text, max(match.end(), match.start() + 1))
    return match


# -----------------------------------------------------------------------------
def _directive_matches(pattern: Pattern[str], text: str) -> list[Match[str]]:
    """Return directive matches that are outside Markdown code."""
    return _finditer_outside_ranges(pattern, text, markdown_code_ranges(text))


# -----------------------------------------------------------------------------
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
    return _XML_COMMENT_RE.sub("", text)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def _first_title_match(text: str) -> tuple[Match[str], TitleStyle] | None:
    """Return the first real H1 and its source style."""
    protected_ranges = merge_ranges(
        [
            *markdown_code_ranges(text),
            *(match.span() for match in _XML_COMMENT_RE.finditer(text)),
        ]
    )
    candidates: list[tuple[Match[str], TitleStyle]] = []
    candidates.extend(
        (match, "setext")
        for match in _finditer_outside_ranges(
            _SETEXT_H1_RE, text, protected_ranges
        )
    )
    candidates.extend(
        (match, "atx")
        for match in _finditer_outside_ranges(
            _ATX_H1_RE, text, protected_ranges
        )
    )
    return min(candidates, key=lambda item: item[0].start()) if candidates else None


# -----------------------------------------------------------------------------
def get_refs_from_md_text(
        text: str, 
        previous_refs: Optional[Dict[str, str]] = None
        ) -> Dict[str, str]:
    """
    Extract reference blocks from a markdown text.

    Reference blocks are delimited by:
      - <!-- begin-ref(name) -->
      - <!-- end-ref -->

    The function extracts blocks sequentially (not nested). Each `name` must be unique.

    Args:
        text: Input markdown text.
        previous_refs: Optional dict to update (copied to avoid side effects).

    Returns:
        A dict mapping ref names to their raw extracted content.

    Raises:
        ValueError: If a ref name is duplicated or an end marker is missing.
    """
    text = _require_str(text, "text")
    refs: Dict[str, str] = dict(previous_refs) if previous_refs else {}
    code_ranges = markdown_code_ranges(text)

    pos = 0
    while True:
        m_begin = _search_outside_ranges(_BEGIN_REF_RE, text, pos, code_ranges)
        if not m_begin:
            return refs

        key = m_begin.group("name")
        if key in refs:
            raise ValueError(f"duplicate begin-ref({key})")

        after_begin = m_begin.end()
        m_end = _search_outside_ranges(_END_REF_RE, text, after_begin, code_ranges)
        if not m_end:
            raise ValueError(f"begin-ref({key}) without end-ref")

        refs[key] = text[after_begin:m_end.start()]
        pos = m_end.end()
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def get_refs_from_md_file(
    filename: common.PathInput,
    filename_ext: str = ".md",
    previous_refs: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """
    Extract reference blocks from a markdown file.

    The file is validated as an existing file and (optionally) checked for the
    expected extension, then read as text (encoding auto-detected if supported),
    and analyzed by `get_refs_from_md_text`.

    Args:
        filename: Path to the markdown file.
        filename_ext: Expected file extension (including dot), e.g. ".md".
        previous_refs: Optional dict to merge with extracted refs.

    Returns:
        A dict mapping ref names to extracted content.

    Raises:
        RuntimeError / Exception: propagated from `common.check_file`.
        IOError / UnicodeDecodeError: propagated from file reading helpers.
        ValueError: propagated from `get_refs_from_md_text` for malformed refs.
    """
    checked = common.check_file(str(filename), filename_ext)
    text = _read_md_text(checked)
    return get_refs_from_md_text(text, previous_refs=previous_refs)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def get_refs_from_md_directory(
    folder: common.PathInput,
    filename_ext: str = ".md",
    previous_refs: Optional[Dict[str, str]] = None,
    depth: int = -1,
) -> Dict[str, str]:
    """
    Extract refs from markdown files in a directory tree.

    Depth semantics:
        - depth == -1: recurse into all subdirectories (unlimited)
        - depth == 0: only current directory
        - depth > 0 : recurse up to `depth` levels

    Args:
        folder: Root directory to scan.
        filename_ext: File extension to include (e.g. ".md").
        previous_refs: Optional dict to merge with extracted refs (copied).
        depth: Recursion depth.

    Returns:
        A dict mapping ref names to extracted content.
    """
    folder_checked = common.check_folder(str(folder))
    root = Path(folder_checked)

    refs: Dict[str, str] = dict(previous_refs) if previous_refs else {}

    # Current directory files (deterministic)
    md_files = sorted(
        (p for p in root.iterdir() if p.is_file() and p.suffix == filename_ext),
        key=lambda p: p.name,
    )
    for p in md_files:
        refs = get_refs_from_md_file(
            str(p),
            filename_ext=filename_ext,
            previous_refs=refs,
        )

    # Stop recursion
    if depth == 0:
        return refs

    # Subdirectories (deterministic)
    subdirs = sorted((p for p in root.iterdir() if p.is_dir()), key=lambda p: p.name)

    if depth < 0:
        # unlimited
        for d in subdirs:
            refs = get_refs_from_md_directory(
                d,
                filename_ext=filename_ext,   # ✅ propagate correctly
                previous_refs=refs,
                depth=-1,
            )
    else:
        # limited
        next_depth = depth - 1
        for d in subdirs:
            refs = get_refs_from_md_directory(
                d,
                filename_ext=filename_ext,   # ✅ propagate correctly
                previous_refs=refs,
                depth=next_depth,
            )

    return refs
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def get_refs_from_search_folders(
    search_folders: Iterable[common.PathInput],
    *,
    refs: Optional[Dict[str, str]] = None,
    filename_ext: str = ".md",
    depth: int = -1,
) -> Dict[str, str]:
    """
    Extend/collect refs by scanning one or more folders recursively.

    Args:
        search_folders: Folders to scan.
        refs: Existing refs mapping to extend (copied to avoid side effects).
        filename_ext: File extension to scan (e.g. ".md").
        depth: Recursion depth (-1 unlimited, 0 current dir only, >0 limited).

    Returns:
        A dict mapping ref names to extracted content.
    """
    result: Dict[str, str] = dict(refs) if refs else {}

    for folder in search_folders:
        result = get_refs_from_md_directory(
            folder,
            filename_ext=filename_ext,
            previous_refs=result,
            depth=depth,
        )

    return result
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def get_refs_around_md_file(
    filename: common.PathInput,
    filename_ext: str = ".md",
    previous_refs: Optional[Dict[str, str]] = None,
    depth_up: int = 1,
    depth_down: int = -1,
) -> Dict[str, str]:
    """
    Discover refs around a markdown file by scanning parent folders.

    The search root is computed by moving `depth_up` times to the parent directory
    of `filename` (or stopping at filesystem root). Then refs are collected by
    scanning that root directory with `get_refs_from_md_directory`.

    Depth semantics:
        - depth_down == -1: unlimited recursion from the chosen root
        - depth_down == 0: current directory only
        - depth_down > 0 : limited recursion levels

    Note:
        When `depth_up` > 0 and `depth_down` > 0, the effective downward depth
        is increased by the number of levels actually moved up, so that the scan
        still covers the original file directory.

    Args:
        filename: Path to a markdown file (used only to locate directories).
        filename_ext: Extension to scan in directories (e.g. ".md").
        previous_refs: Optional dict to extend.
        depth_up: Number of parent levels to move up (>= 0).
        depth_down: Recursion depth from the computed root (-1 unlimited, >= 0 limited).

    Returns:
        A dict mapping ref names to extracted content.

    Raises:
        ValueError: If `depth_up` < 0 or `depth_down` < -1.
    """
    if depth_up < 0:
        raise ValueError(f"depth_up must be >= 0, got: {depth_up}")
    if depth_down < -1:
        raise ValueError(f"depth_down must be >= -1, got: {depth_down}")

    p = Path(filename).resolve()
    current_dir = p.parent

    moved_up = 0
    while moved_up < depth_up:
        parent = current_dir.parent
        if parent == current_dir:
            break  # filesystem root reached
        current_dir = parent
        moved_up += 1

    effective_depth_down = depth_down
    if depth_down > 0:
        effective_depth_down = depth_down + moved_up

    return get_refs_from_md_directory(
        current_dir,
        filename_ext=filename_ext,
        previous_refs=previous_refs,
        depth=effective_depth_down,
    )
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def refs_in_md_text(text: str) -> List[str]:
    """
    Extract include reference names from markdown text.

    Matches patterns of the form:

        <!-- begin-include(NAME) -->

    where NAME contains only alphanumeric characters, underscores or hyphens.

    Args:
        text: Markdown text to analyze.

    Returns:
        A list of include reference names (strings).
        Example: ["header", "footer"]
    """
    text = _require_str(text, "text")

    return [
        match.group("name")
        for match in _directive_matches(_BEGIN_INCLUDE_RE, text)
    ]
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def include_refs_to_md_text(
    text: str,
    refs_include: Mapping[str, str],
    begin_include_re: RegexInput = _BEGIN_INCLUDE_RE,
    end_include_re: RegexInput = _END_INCLUDE_RE,
    error_if_no_key: bool = True,
) -> str:
    """
    Insert include references into a markdown text.

    Markers:
        <!-- begin-include(NAME) -->
        ...
        <!-- end-include -->

    If NAME exists in `refs_include`, its content is inserted immediately after the
    begin marker, and the original inner content (between markers) is skipped.
    Begin/end markers are preserved in the output.

    If NAME is missing:
        - if `error_if_no_key` is True: raise KeyError
        - else: keep the include block unchanged and continue

    Notes:
        Processing is sequential (not nesting-aware): the first end marker after
        a begin marker is used.

    Args:
        text: Markdown text to process.
        refs_include: Mapping of include names to replacement content.
        begin_include_re: Regex (compiled or string) matching the begin marker and capturing group 'name'.
        end_include_re: Regex (compiled or string) matching the end marker.
        error_if_no_key: Whether to raise if the key is missing.

    Returns:
        The processed markdown text.

    Raises:
        TypeError: If `text` is not a str.
        KeyError: If an include key is missing and `error_if_no_key=True`.
        ValueError: If an end marker is missing.
    """
    text = _require_str(text, "text")
    begin_pattern = _compile_pattern(begin_include_re)
    end_pattern = _compile_pattern(end_include_re)

    code_ranges = markdown_code_ranges(text)
    parts: list[str] = []
    cursor = 0

    while True:
        match_begin = _search_outside_ranges(
            begin_pattern, text, cursor, code_ranges
        )
        if match_begin is None:
            parts.append(text[cursor:])
            return "".join(parts)

        key = match_begin.group("name")
        logging.debug("Find the include key %s", key)
        match_end = _search_outside_ranges(
            end_pattern, text, match_begin.end(), code_ranges
        )
        if match_end is None:
            raise ValueError(f"begin-include({key}) without end-include")

        parts.append(text[cursor:match_begin.end()])
        if key not in refs_include:
            if error_if_no_key:
                raise KeyError(f"begin-include({key}) references an unknown key")
            parts.append(text[match_begin.end():match_end.end()])
        else:
            parts.append(refs_include[key])
            parts.append(text[match_end.start():match_end.end()])
        cursor = match_end.end()
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def include_refs_to_md_file(
    filename: common.PathInput,
    refs: Mapping[str, str],
    *,
    backup_option: bool = True,
    backup_ext: str = ".bak",
    filename_ext: str = ".md",
    begin_include_re: RegexInput = _BEGIN_INCLUDE_RE,
    end_include_re: RegexInput = _END_INCLUDE_RE,
    error_if_no_key: bool = True,
    read_encoding: Optional[str] = None,
    write_encoding: str = "utf-8",
) -> str:
    """
    Apply include references to a markdown file in-place.

    The file is read, include markers are processed via `include_refs_to_md_text`,
    then the file is overwritten with the resulting content.

    Args:
        filename: Markdown file path.
        refs: Mapping of include names to replacement content.
        backup_option: If True, create a backup before overwriting.
        backup_ext: Backup extension (e.g. ".bak").
        filename_ext: Expected extension for `filename`.
        begin_include_re: Regex for begin marker (string or compiled, must capture 'name').
        end_include_re: Regex for end marker (string or compiled).
        error_if_no_key: Raise if an include name is unknown.
        read_encoding: Encoding used for reading. ``None`` triggers auto-detection.
        write_encoding: Encoding used for writing.

    Returns:
        Normalized filename (string).

    Raises:
        ValueError/KeyError: Propagated from include processing.
        RuntimeError/Exception: Propagated from `common.check_file` / IO helpers.
    """
    checked = common.check_file(str(filename), filename_ext)

    text = _read_md_text(checked, read_encoding)

    if backup_option:
        _create_backup(checked, backup_ext)

    new_text = include_refs_to_md_text(
        text,
        refs,
        begin_include_re=begin_include_re,
        end_include_re=end_include_re,
        error_if_no_key=error_if_no_key,
    )

    common.set_file_content(checked, new_text, encoding=write_encoding)
    return str(checked)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
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
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def unescape_var_value(value: str) -> str:
    """
    Interpret backslash escapes inside a var(...) value.

    Supported escapes:
        \\n, \\t, \\r, \\\\, \\\", \\\'

    Unknown escapes keep the escaped character as-is (e.g. "\\x" -> "x").

    Args:
        value: Raw captured value (without surrounding quotes).

    Returns:
        Interpreted value.
    """
    def repl(m: re.Match[str]) -> str:
        ch = m.group(1)
        return _ESCAPE_MAP.get(ch, ch)

    return _ESCAPE_RE.sub(repl, value)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def get_vars_from_md_text(
    text: str, 
    previous_vars: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """
    Extract variable declarations from markdown text and return interpreted values.

    Variables are declared using:
        <!-- var(NAME) = "value" -->
        <!-- var(NAME) = 'value' -->

    Escape sequences inside the quoted value are interpreted (\\n, \\t, \\r, \\\\, \\\", \\\').

    Args:
        text: Markdown text to scan.
        previous_vars: Optional dict to extend (copied to avoid side effects).

    Returns:
        A dict mapping variable names to interpreted string values.

    Raises:
        TypeError: If `text` is not a string.
        ValueError: If a variable name is declared twice.
    """
    text = _require_str(text, "text")

    vars_: Dict[str, str] = dict(previous_vars) if previous_vars else {}

    for m in _directive_matches(_VAR_RE, text):
        key = m.group("name")
        raw_value = m.group("string")
        value = unescape_var_value(raw_value)

        if key in vars_:
            raise ValueError(f"duplicate var({key})")

        vars_[key] = value
    return vars_
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def escape_var_value(value: str) -> str:
    """Escape a value so it can be safely embedded inside <!-- var(...)="..." -->."""
    # order matters: escape backslash first
    out = value.replace("\\", _ESCAPE_OUT_MAP["\\"])
    out = out.replace("\n", _ESCAPE_OUT_MAP["\n"])
    out = out.replace("\t", _ESCAPE_OUT_MAP["\t"])
    out = out.replace("\r", _ESCAPE_OUT_MAP["\r"])
    out = out.replace('"', _ESCAPE_OUT_MAP['"'])
    return out
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
def set_var_to_md_text(text: str, var_name: str, value: str) -> str:
    """
    Set or add a var(...) directive in markdown text.

    If the variable is already present, its declaration is replaced.
    If absent, the declaration is inserted after the existing var(...) block,
    and after any include-file directives that immediately follow.

    Args:
        text: Markdown text.
        var_name: Variable name (allowed: [A-Za-z0-9:_-]+).
        value: Interpreted value (will be escaped for storage).

    Returns:
        Updated markdown text.

    Raises:
        TypeError: If inputs are not strings.
        ValueError: If var_name is invalid.
    """
    text = _require_str(text, "text")
    if not _all_str(var_name, value):
        raise TypeError("var_name and value must be strings")
    if not _VAR_NAME_RE.match(var_name):
        raise ValueError(f"invalid var name: {var_name!r}")

    var_text = f'<!-- var({var_name})="{escape_var_value(value)}" -->'

    var_matches = _directive_matches(_VAR_RE, text)
    matching_vars = [
        match for match in var_matches if match.group("name") == var_name
    ]
    if matching_vars:
        parts: list[str] = []
        cursor = 0
        for match in matching_vars:
            parts.append(text[cursor:match.start()])
            parts.append(var_text)
            cursor = match.end()
        parts.append(text[cursor:])
        return "".join(parts)

    header_matches = [
        *_directive_matches(_VAR_RE, text),
        *_directive_matches(_INCLUDE_FILE_RE, text),
    ]
    insert_at = max((match.end() for match in header_matches), default=0)
    before = text[:insert_at]
    after = text[insert_at:]
    separator_before = "\n" if before else ""
    separator_after = "\n" if not after or after.startswith("\n") else "\n\n"
    return before + separator_before + var_text + separator_after + after
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def del_var_to_md_text(text: str, var_name: str) -> str:
    """
    Remove all var(...) directives with the given name from a markdown text.

    Args:
        text: Markdown text.
        var_name: Variable name to remove.

    Returns:
        Updated markdown text.

    Raises:
        TypeError: If inputs are not strings.
        ValueError: If var_name is invalid.
    """
    text = _require_str(text, "text")
    if not _all_str(var_name):
        raise TypeError("var_name must be a string")
    if not _VAR_NAME_RE.match(var_name):
        raise ValueError(f"invalid var name: {var_name!r}")

    parts: list[str] = []
    cursor = 0
    for match in _directive_matches(_VAR_RE, text):
        if match.group("name") != var_name:
            continue
        parts.append(text[cursor:match.start()])
        cursor = match.end()
    parts.append(text[cursor:])
    return "".join(parts)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def get_title_from_md_text(
    text: str, 
    return_match: bool = False
) -> Union[None, str, Match[str]]:
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
    text = _require_str(text, "text")

    title_match = _first_title_match(text)
    if title_match is None:
        return None
    m, _ = title_match

    if return_match:
        return m

    return m.group("title").strip()
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def set_title_in_md_text(
    text: str, 
    new_title: str, 
    *, 
    style: TitleStyle = "preserve"
) -> str:
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
    text = _require_str(text, "text")
    if not _all_str(new_title):
        raise TypeError("new_title must be a string")

    title = new_title.strip()
    if not title:
        raise ValueError("new_title must be non-empty")
    if style not in ("preserve", "setext", "atx"):
        raise ValueError(f"invalid style: {style!r}")

    title_match = _first_title_match(text)

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
        replacement = (
            make_setext(title) if output_style == "setext" else make_atx(title)
        )
        return text[:match.start()] + replacement + text[match.end():]

    # No title found: insert at top
    replacement = make_setext(title) if output_style == "setext" else make_atx(title)
    # Add a blank line after the title if content does not already start with newline
    if text and not text.startswith("\n"):
        return replacement + "\n" + text
    return replacement + text
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def get_vars_from_md_file(
    filename: common.PathInput,
    *,
    filename_ext: str = ".md",
    previous_vars: Optional[Dict[str, str]] = None,
    encoding: Optional[str] = None,
) -> Dict[str, str]:
    """
    Extract var(...) directives from a markdown file.

    The returned values are interpreted (escapes are processed) as defined by
    `get_vars_from_md_text`.

    Args:
        filename: Path to the markdown file.
        filename_ext: Expected file extension.
        previous_vars: Optional existing mapping to extend.
        encoding: Encoding to use for reading. ``None`` triggers auto-detection.

    Returns:
        A dict mapping variable names to interpreted values.

    Raises:
        RuntimeError/Exception: Propagated from path checks and file reading helpers.
        ValueError: If duplicate var names are found.
    """
    logging.debug("Find vars in the MD file %s", filename)
    checked = common.check_file(str(filename), filename_ext)

    text = _read_md_text(checked, encoding)
    return get_vars_from_md_text(text, previous_vars=previous_vars)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def include_vars_to_md_text(
    text: str,
    vars_include: Mapping[str, str],
    *,
    begin_var_re: RegexInput = _BEGIN_VAR_RE,
    end_var_re: RegexInput = _END_VAR_RE,
    error_if_var_not_found: bool = True,
) -> str:
    """
    Insert variable values into begin-var/end-var blocks in markdown text.

    This is a thin wrapper around :func:`include_refs_to_md_text` configured
    with the variable block markers:

    - ``<!-- begin-var(NAME) -->``
    - ``<!-- end-var -->``

    Args:
        text: Markdown text to process.
        vars_include: Mapping of variable names to replacement content.
        begin_var_re: Regex matching the opening variable marker. It must expose
            a named group ``name``.
        end_var_re: Regex matching the closing variable marker.
        error_if_var_not_found: If True, raise ``KeyError`` when a block refers
            to a missing variable. If False, leave that block unchanged.

    Returns:
        Markdown text with matching variable blocks updated.
    """
    return include_refs_to_md_text(
        text,
        vars_include,
        begin_include_re=begin_var_re,
        end_include_re=end_var_re,
        error_if_no_key=error_if_var_not_found,
    )
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def include_vars_to_md_file(
    filename: common.PathInput,
    vars_include: Mapping[str, str],
    *,
    backup_option: bool = True,
    backup_ext: str = ".bak",
    filename_ext: str = ".md",
    begin_var_re: RegexInput = _BEGIN_VAR_RE,
    end_var_re: RegexInput = _END_VAR_RE,
    error_if_var_not_found: bool = True,
    read_encoding: Optional[str] = None,
    write_encoding: str = "utf-8",
) -> str:
    """
    Apply begin-var/end-var substitutions to a markdown file in-place.

    This is a wrapper around `include_refs_to_md_file`, using the var markers.

    Args:
        filename: Markdown file to process.
        vars_include: Mapping var name -> replacement content.
        backup_option: Whether to create a backup before overwriting.
        backup_ext: Backup extension.
        filename_ext: Expected file extension.
        begin_var_re: Regex for begin-var marker (must capture group 'name').
        end_var_re: Regex for end-var marker.
        error_if_var_not_found: Raise if a referenced var is missing.
        read_encoding: Encoding used to read the file. ``None`` triggers auto-detection.
        write_encoding: Encoding used to write the file.

    Returns:
        Normalized filename (string).
    """
    return include_refs_to_md_file(
        filename,
        vars_include,
        backup_option=backup_option,
        backup_ext=backup_ext,
        filename_ext=filename_ext,
        begin_include_re=begin_var_re,
        end_include_re=end_var_re,
        error_if_no_key=error_if_var_not_found,
        read_encoding=read_encoding,
        write_encoding=write_encoding,
    )
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def get_vars_from_md_directory(
    folder: common.PathInput,
    *,
    filename_ext: str = ".md",
    previous_vars: Optional[Dict[str, str]] = None,
    depth: int = -1,
    encoding: Optional[str] = None,
) -> Dict[str, str]:
    """
    Find var(...) declarations in markdown files in `folder` and (optionally) its subfolders.

    Depth:
      - -1: recurse into all subfolders
      -  0: current folder only
      -  n>0: recurse `n` levels

    Args:
        folder: Directory to scan.
        filename_ext: Markdown file extension to consider.
        previous_vars: Existing mapping to extend.
        depth: Recursion depth.
        encoding: Encoding for reading files. ``None`` triggers auto-detection.

    Returns:
        A dict of var name -> interpreted value.

    Raises:
        RuntimeError: If `folder` is not a directory.
        ValueError: If duplicate var names are found across scanned files.
    """
    logging.debug('Find vars in the folder "%s"', folder)
    folder_str = common.check_folder(str(folder))

    vars_: Dict[str, str] = dict(previous_vars) if previous_vars else {}

    # scan md files in current dir
    for entry in os.listdir(folder_str):
        p = os.path.join(folder_str, entry)
        if os.path.isfile(p) and p.endswith(filename_ext):
            vars_ = get_vars_from_md_file(
                p,
                filename_ext=filename_ext,
                previous_vars=vars_,
                encoding=encoding,
            )

    if depth == 0:
        return vars_

    # recurse into subdirs
    next_depth = depth if depth < 0 else depth - 1
    for entry in os.listdir(folder_str):
        p = os.path.join(folder_str, entry)
        if os.path.isdir(p):
            vars_ = get_vars_from_md_directory(
                p,
                filename_ext=filename_ext,
                previous_vars=vars_,
                depth=next_depth,
                encoding=encoding,
            )

    return vars_
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
def get_vars_around_md_file(
    filename: common.PathInput,
    *,
    filename_ext: str = ".md",
    previous_vars: Optional[Dict[str, str]] = None,
    depth_up: int = 1,
    depth_down: int = -1,
    encoding: Optional[str] = None,
) -> Dict[str, str]:
    """
    Discover var(...) declarations around a markdown file by scanning nearby directories.

    Starting from the directory of `filename`, this function moves up `depth_up` levels
    (stopping at filesystem root), then scans downward with depth `depth_down`.

    Args:
        filename: Markdown file path.
        filename_ext: Extension for markdown files.
        previous_vars: Existing mapping to extend.
        depth_up: Number of parent levels to move up (>= 0).
        depth_down: Downward recursion depth (-1 unlimited, 0 current dir only, >0 limited).
        encoding: Encoding used to read markdown files. ``None`` triggers auto-detection.

    Returns:
        A dict of var name -> interpreted value.

    Raises:
        ValueError: If `depth_up` < 0 or `depth_down` < -1.
        RuntimeError/Exception: Propagated by filesystem helpers.
    """
    if depth_up < 0:
        raise ValueError(f"depth_up must be >= 0, got: {depth_up}")
    if depth_down < -1:
        raise ValueError(f"depth_down must be >= -1, got: {depth_down}")

    filename_str = common.normpath(str(filename))
    logging.debug('Discover vars around the file "%s"', filename_str)

    current_dir = os.path.abspath(os.path.dirname(filename_str))

    # move up
    du = depth_up
    dd = depth_down
    while du > 0:
        new_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
        if new_dir == current_dir:
            break
        current_dir = new_dir
        du -= 1
        if dd > 0:
            dd += 1  # keep total "down scan" horizon roughly stable

    return get_vars_from_md_directory(
        current_dir,
        filename_ext=filename_ext,
        previous_vars=previous_vars,
        depth=dd,
        encoding=encoding,
    )
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
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
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def search_include_vars_to_md_text(
    text: str,
    *,
    error_if_var_not_found: bool = True,
    begin_var_re: RegexInput = _BEGIN_VAR_RE,
    end_var_re: RegexInput = _END_VAR_RE,
) -> str:
    """
    Extract var(...) declarations from `text` and apply begin-var/end-var substitutions.

    Args:
        text: Markdown text.
        error_if_var_not_found: Raise if a referenced var is missing.
        begin_var_re: Regex for begin-var marker (must capture group 'name').
        end_var_re: Regex for end-var marker.

    Returns:
        Updated markdown text.

    Raises:
        KeyError/ValueError: If a referenced var is missing (depending on implementation).
    """
    text_vars = get_vars_from_md_text(text)
    return include_vars_to_md_text(
        text,
        text_vars,
        begin_var_re=begin_var_re,
        end_var_re=end_var_re,
        error_if_var_not_found=error_if_var_not_found,
    )
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def get_file_content_to_include(
    filename: common.PathInput,
    *,
    search_folders: Optional[Iterable[common.PathInput]] = None,
    include_cwd: bool = False,
    relative_paths: Sequence[str] = (".", "referenced_files"),
    nb_up_path: int = 0,
    encoding: Optional[str] = None,
) -> str:
    """
    Retrieve the content of a referenced file to include.

    The function searches `filename` using `common.find_file` starting from:
      - the directory containing this module,
      - optionally the current working directory,
      - and any additional folders provided via `search_folders`.

    Search is performed within `relative_paths` under each start point, and can
    traverse up to `nb_up_path` parent levels.

    Args:
        filename: Referenced filename (typically relative, e.g. "snippet.md").
        search_folders: Additional start points for the search.
        include_cwd: Whether to include the current working directory as a start point.
        relative_paths: Relative subpaths to probe under each start point.
        nb_up_path: Number of parent levels to traverse during the search.
        encoding: Encoding for reading. ``None`` triggers auto-detection.

    Returns:
        File content as text.

    Raises:
        Exception: Propagated if the file cannot be found or read.
    """
    requested = str(filename)
    requested_path = Path(requested)

    if (
        os.path.isabs(requested)
        or requested_path.is_absolute()
        or bool(requested_path.drive)
        or requested.startswith(("/", "\\"))
        or ".." in requested_path.parts
    ):
        raise ValueError(f"invalid referenced filename: {requested!r}")

    module_dir = Path(__file__).resolve().parent
    start_paths: list[Path] = []
    if search_folders:
        start_paths.extend(Path(path).resolve() for path in search_folders)
    if include_cwd:
        start_paths.append(Path.cwd().resolve())
    start_paths.append(module_dir)

    unique_start_paths = list(dict.fromkeys(start_paths))
    start_points = [str(path) for path in unique_start_paths]

    logging.debug(
        "Include-file lookup: filename=%r start_points=%r relative_paths=%r nb_up_path=%d",
        requested, start_points, list(relative_paths), nb_up_path
    )

    found = common.find_file(
        requested,
        start_points,
        list(relative_paths),
        max_up=nb_up_path,
    )

    resolved_found = Path(found).resolve()
    if not any(
        resolved_found == root or resolved_found.is_relative_to(root)
        for root in unique_start_paths
    ):
        raise ValueError(
            f"included file resolves outside the allowed roots: {requested!r}"
        )

    logging.debug("Include-file resolved: %r -> %r", requested, resolved_found)
    return _read_md_text(resolved_found, encoding)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def include_files_to_md_text(
    text: str,
    *,
    include_file_re: RegexInput = _INCLUDE_FILE_RE,
    error_if_no_file: bool = True,
    render_mode: IncludeRenderMode = "box",
    **kwargs: Any,
) -> str:
    """
    Replace include-file directives with the content of referenced files.

    The directive must match `include_file_re` and provide a group 'name'
    containing the referenced filename.

    Args:
        text: Markdown text.
        include_file_re: Regex to match include-file directives (must capture 'name').
        error_if_no_file: If False, keep the directive unchanged when the file is not found/readable.
        render_mode: "box" to wrap content in an ASCII box, "raw" to insert content as-is.
        **kwargs: Forwarded to `get_file_content_to_include` (e.g. search_folders).

    Returns:
        Updated markdown text.
    """
    pattern = _compile_pattern(include_file_re)

    text = _require_str(text, "text")
    code_ranges = markdown_code_ranges(text)
    result_parts: list[str] = []
    pos = 0

    while True:
        m = _search_outside_ranges(pattern, text, pos, code_ranges)
        if not m:
            result_parts.append(text[pos:])
            break

        filename = m.group("name")
        logging.debug("Find include-file(%s)", filename)

        result_parts.append(text[pos:m.start()])

        try:
            file_text = get_file_content_to_include(filename, **kwargs)
        except Exception:
            if error_if_no_file:
                raise
            # keep original directive unchanged
            result_parts.append(text[m.start():m.end()])
            pos = m.end()
            continue

        # Normalize newlines
        file_text = file_text.replace("\r\n", "\n").replace("\r", "\n")

        if render_mode == "raw":
            replacement = file_text
        else:
            # box mode (deterministic)
            left = "| "
            boxed = left + file_text.replace("\n", "\n" + left)
            top = "+" + "-" * 77 + "+"
            replacement = (
                f"<!-- include-file({filename})\n"
                f"{top}\n"
                f"{boxed}\n"
                f"{top} -->"
            )

        result_parts.append(replacement)
        pos = m.end()

    return "".join(result_parts)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def include_files_to_md_file(
    filename: common.PathInput,
    *,
    backup_option: bool = True,
    backup_ext: str = ".bak",
    filename_ext: str = ".md",
    read_encoding: Optional[str] = None,
    write_encoding: str = "utf-8",
    error_if_no_file: bool = True,
    render_mode: IncludeRenderMode = "box",
    **kwargs: Any,
) -> str:
    """
    Apply include-file substitutions to a markdown file in-place.

    Args:
        filename: Markdown file to process.
        backup_option: Create a backup before writing.
        backup_ext: Backup extension.
        filename_ext: Expected markdown extension.
        read_encoding: Encoding to read. ``None`` triggers auto-detection.
        write_encoding: Encoding used to write.
        error_if_no_file: If False, keep unresolved directives unchanged.
        render_mode: Forwarded to include_files_to_md_text (e.g. "box" or "raw").
        **kwargs: Forwarded to get_file_content_to_include (e.g. search_folders).

    Returns:
        Normalized filename.
    """
    logging.debug("Include file to the file %s", filename)
    checked = common.check_file(str(filename), filename_ext)

    text = _read_md_text(checked, read_encoding)

    if backup_option:
        _create_backup(checked, backup_ext)

    configured_search_folders = kwargs.get("search_folders")
    search_folders = (
        [] if configured_search_folders is None else list(configured_search_folders)
    )
    document_folder = Path(checked).resolve().parent
    kwargs["search_folders"] = [
        document_folder,
        *(
            folder
            for folder in search_folders
            if Path(folder).resolve() != document_folder
        ),
    ]
    kwargs.setdefault("include_cwd", False)
    kwargs.setdefault("nb_up_path", 0)

    text = include_files_to_md_text(
        text,
        error_if_no_file=error_if_no_file,
        render_mode=render_mode,
        **kwargs,
    )

    common.set_file_content(checked, text, encoding=write_encoding)
    return str(checked)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def ensure_include_file_in_md_text(
    text: str,
    filename: str,
    *,
    include_file_re: RegexInput = _INCLUDE_FILE_RE,
) -> str:
    """
    Ensure that an `include-file(filename)` directive exists in the markdown text.

    The directive is appended after the last existing include-file directive.
    If no include-file directives exist, it is inserted at the beginning of the text.

    Args:
        text: Markdown text.
        filename: Referenced file name as used in include-file(...).
        include_file_re: Regex matching include-file directives; must capture group 'name'.

    Returns:
        Updated markdown text.
    """
    text = _require_str(text, "text")
    if not _is_non_empty_str(filename, strip=True):
        raise ValueError("filename must be a non-empty string")

    # Normalize newlines (optional but helps determinism)
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    pattern = _compile_pattern(include_file_re)

    # If already present, return as-is
    matches = _directive_matches(pattern, normalized)
    for m in matches:
        if m.group("name") == filename:
            return normalized

    directive = f"<!-- include-file({filename}) -->"

    if not matches:
        # insert at beginning
        if normalized and not normalized.startswith("\n"):
            return directive + "\n\n" + normalized
        return directive + "\n\n" + normalized

    # append after the last include-file directive
    last = matches[-1]
    insert_at = last.end()

    before = normalized[:insert_at]
    after = normalized[insert_at:]

    # ensure spacing
    if not before.endswith("\n"):
        before += "\n"
    if after and not after.startswith("\n"):
        # keep a blank line between directives and content
        insertion = directive + "\n\n"
    else:
        insertion = directive + "\n"

    return before + insertion + after
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def get_include_file_list(
    text: str,
    *,
    include_file_re: RegexInput = _INCLUDE_FILE_RE,
    unique: bool = False,
) -> list[str]:
    """
    Return the list of filenames referenced by include-file(...) directives.

    Args:
        text: Markdown text.
        include_file_re: Regex matching include-file directives; must capture group 'name'.
        unique: If True, remove duplicates while preserving first-seen order.

    Returns:
        A list of referenced filenames, in appearance order.
    """
    pattern = _compile_pattern(include_file_re)

    text = _require_str(text, "text")
    names = [m.group("name") for m in _directive_matches(pattern, text)]

    if not unique:
        return names

    seen: set[str] = set()
    out: list[str] = []
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def del_include_file_to_md_text(
    text: str,
    filename: str,
    *,
    include_file_re: RegexInput = _INCLUDE_FILE_RE,
    first_only: bool = False,
) -> str:
    """
    Remove include-file directives referencing `filename` from markdown text.

    Args:
        text: Markdown text.
        filename: Target referenced filename to remove.
        include_file_re: Regex matching include-file directives; must capture group 'name'.
        first_only: If True, remove only the first matching directive.

    Returns:
        Updated markdown text.
    """
    text = _require_str(text, "text")
    if not _is_non_empty_str(filename):
        raise ValueError("filename must be a non-empty string")

    pattern = _compile_pattern(include_file_re)

    out_parts: list[str] = []
    pos = 0
    removed = False

    for m in _directive_matches(pattern, text):
        name = m.group("name")
        if name == filename and (not first_only or not removed):
            # keep everything before the match, skip the match
            out_parts.append(text[pos:m.start()])
            pos = m.end()
            removed = True
        # else: keep scanning; do not append yet (handled by pos slices)

    out_parts.append(text[pos:])
    return "".join(out_parts)
# -----------------------------------------------------------------------------


# =============================================================================
