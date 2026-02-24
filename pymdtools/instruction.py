#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                    Author: Florent TOURNOIS | License: MIT                   
# =============================================================================

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

TitleStyle          = Literal["preserve", "setext", "atx"]
IncludeRenderMode   = Literal["box", "raw"]

# -----------------------------------------------------------------------------
# re expression used for instruction
# -----------------------------------------------------------------------------
_XML_COMMENT_RE: Final[re.Pattern[str]] = re.compile(r"<!--.*?-->", re.DOTALL)

_BEGIN_REF_RE: Final[re.Pattern[str]] = re.compile(
    r"<!--\s+begin-ref\((?P<name>[a-zA-Z0-9_-]+)\)\s+-->")
_END_REF_RE: Final[re.Pattern[str]] = re.compile(
    r"<!--\s+end-ref\s+-->")

_BEGIN_INCLUDE_RE: Final[re.Pattern[str]] = re.compile(
    r"""
    <!--\s*
    begin-include
    \(\s*
    (?P<name>[a-zA-Z0-9_-]+)
    \s*\)
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

_VAR_RE: Final[re.Pattern[str]] = re.compile(
    r"""
    <!--\s*var\(
        (?P<name>[A-Za-z0-9:_-]+(?:/[A-Za-z0-9:_-]+)*)
    \)\s*=\s*
        (?P<quote>['"])
        (?P<string>(?:\\.|(?!\1).)*)
        \1
    \s*-->
    """,
    re.VERBOSE,
)

_ESCAPE_RE: Final[re.Pattern[str]] = re.compile(r"\\(.)", re.DOTALL)

_ESCAPE_MAP: Final[dict[str, str]] = {
    "n": "\n",
    "t": "\t",
    "r": "\r",
    "\\": "\\",
    '"': '"',
    "'": "'",
}

_VAR_NAME_RE: Final[re.Pattern[str]] = \
    re.compile(r"^[A-Za-z0-9:_-]+(?:/[A-Za-z0-9:_-]+)*$")


_ESCAPE_OUT_MAP: Final[dict[str, str]] = {
    "\\": r"\\",
    "\n": r"\n",
    "\t": r"\t",
    "\r": r"\r",
    '"': r"\"",
}


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


_SETEXT_H1_RE = re.compile(
    r"""(?mx)
    ^[ \t]*(?P<title>[^\r\n]+?)[ \t]*\r?\n
    ^[ \t]*=+[ \t]*\r?\n?
    """
)


_ATX_H1_RE = re.compile(
    r"""(?mx)
    ^[ \t]*\#[ \t]+(?P<title>[^\r\n#]+?)[ \t]*\#*[ \t]*\r?\n?
    """
)


_BEGIN_VAR_RE: Final[re.Pattern[str]] = re.compile(
    r"<!--\s*begin-var\(\s*(?P<name>[A-Za-z0-9:_-]+(?:/[A-Za-z0-9:_-]+)*)\s*\)\s*-->",
)
_END_VAR_RE: Final[re.Pattern[str]] = re.compile(
    r"<!--\s*end-var\s*-->",
)


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

    Raises:
        TypeError: If `text` is not a string.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    return _XML_COMMENT_RE.sub("", text)
# -----------------------------------------------------------------------------


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
        TypeError: If `text` is not a string.
        ValueError: If a ref name is duplicated or an end marker is missing.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    refs: Dict[str, str] = dict(previous_refs) if previous_refs else {}

    pos = 0
    while True:
        m_begin = _BEGIN_REF_RE.search(text, pos)
        if not m_begin:
            return refs

        key = m_begin.group("name")
        if key in refs:
            raise ValueError(f"duplicate begin-ref({key})")

        after_begin = m_begin.end()
        m_end = _END_REF_RE.search(text, after_begin)
        if not m_end:
            raise ValueError(f"begin-ref({key}) without end-ref")

        refs[key] = text[after_begin:m_end.start()]
        pos = m_end.end()
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def get_refs_from_md_file(
    filename: Union[str, Path],
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
    text = common.get_file_content(checked, encoding="UNKNOWN")
    return get_refs_from_md_text(text, previous_refs=previous_refs)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def get_refs_from_md_directory(
    folder: Union[str, Path],
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
    search_folders: Iterable[Union[str, Path]],
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
    filename: Union[str, Path],
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
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    return _BEGIN_INCLUDE_RE.findall(text)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def include_refs_to_md_text(
    text: str,
    refs_include: Mapping[str, str],
    begin_include_re=_BEGIN_INCLUDE_RE,
    end_include_re=_END_INCLUDE_RE,
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
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    # search begin
    match_begin = re.search(begin_include_re, text)
    if not match_begin:
        return text

    key = match_begin.group("name")
    logging.debug("Find the include key %s", key)

    # Find end marker in the remaining text
    last_part = text[match_begin.end(0):]
    match_end = re.search(end_include_re, last_part)
    if not match_end:
        raise ValueError(f"begin-include({key}) without end-include")

    # If key missing
    if key not in refs_include:
        if error_if_no_key:
            raise KeyError(f"begin-include({key}) references an unknown key")

        # Keep this whole include block unchanged (including its original content)
        unchanged_block = last_part[:match_end.end(0)]
        return (
            text[:match_begin.end(0)]
            + unchanged_block
            + include_refs_to_md_text(
                last_part[match_end.end(0):],
                refs_include,
                begin_include_re=begin_include_re,
                end_include_re=end_include_re,
                error_if_no_key=error_if_no_key,
            )
        )

    # Key exists: insert replacement, keep end marker, and skip original inner content
    result = text[:match_begin.end(0)] + refs_include[key]
    result += last_part[match_end.start(0):match_end.end(0)]

    # Continue after end marker
    result += include_refs_to_md_text(
        last_part[match_end.end(0):],
        refs_include,
        begin_include_re=begin_include_re,
        end_include_re=end_include_re,
        error_if_no_key=error_if_no_key,
    )
    return result
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def include_refs_to_md_file(
    filename: Union[str, Path],
    refs: Mapping[str, str],
    *,
    backup_option: bool = True,
    backup_ext: str = ".bak",
    filename_ext: str = ".md",
    begin_include_re: Union[str, Pattern[str]] = _BEGIN_INCLUDE_RE,
    end_include_re: Union[str, Pattern[str]] = _END_INCLUDE_RE,
    error_if_no_key: bool = True,
    read_encoding: str = "UNKNOWN",
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
        read_encoding: Encoding used for reading ("UNKNOWN" may trigger auto-detection in `common`).
        write_encoding: Encoding used for writing.

    Returns:
        Normalized filename (string).

    Raises:
        ValueError/KeyError: Propagated from include processing.
        RuntimeError/Exception: Propagated from `common.check_file` / IO helpers.
    """
    checked = common.check_file(str(filename), filename_ext)

    text = common.get_file_content(checked, encoding=read_encoding)

    if backup_option:
        common.create_backup(checked, backup_ext=backup_ext)

    new_text = include_refs_to_md_text(
        text,
        refs,
        begin_include_re=begin_include_re,
        end_include_re=end_include_re,
        error_if_no_key=error_if_no_key,
    )

    common.set_file_content(checked, new_text, encoding=write_encoding)
    return checked
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def search_include_refs_to_md_file(
    filename: Union[str, Path],
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
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    vars_: Dict[str, str] = dict(previous_vars) if previous_vars else {}

    pos = 0
    while True:
        m = _VAR_RE.search(text, pos)
        if not m:
            return vars_

        key = m.group("name")
        raw_value = m.group("string")
        value = unescape_var_value(raw_value)

        if key in vars_:
            raise ValueError(f"duplicate var({key})")

        vars_[key] = value
        pos = m.end()
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
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not isinstance(var_name, str) or not isinstance(value, str):
        raise TypeError("var_name and value must be strings")
    if not _VAR_NAME_RE.match(var_name):
        raise ValueError(f"invalid var name: {var_name!r}")

    var_text = f'<!-- var({var_name})="{escape_var_value(value)}" -->'

    parts: list[str] = []
    current = text
    var_is_set = False

    # 1) Replace existing var declarations (sequential scan)
    m = _VAR_RE.search(current)
    while m is not None:
        key = m.group("name")
        if key == var_name:
            parts.append(current[:m.start()])
            parts.append(var_text)
            var_is_set = True
        else:
            parts.append(current[:m.end()])

        current = current[m.end():]
        m = _VAR_RE.search(current)

    # 2) Pass-through include-file directives that follow the var header area
    m2 = _INCLUDE_FILE_RE.search(current)
    while m2 is not None:
        parts.append(current[:m2.end()])
        current = current[m2.end():]
        m2 = _INCLUDE_FILE_RE.search(current)

    # 3) Insert if missing
    if not var_is_set:
        if parts:
            parts.append("\n")
        parts.append(var_text)

        # keep a blank line before remaining content (similar to original intent)
        if current and not current.startswith("\n"):
            parts.append("\n\n")
        else:
            parts.append("\n")

    parts.append(current)
    return "".join(parts)
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
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not isinstance(var_name, str):
        raise TypeError("var_name must be a string")
    if not _VAR_NAME_RE.match(var_name):
        raise ValueError(f"invalid var name: {var_name!r}")

    parts: list[str] = []
    current = text

    m = _VAR_RE.search(current)
    while m is not None:
        key = m.group("name")
        if key == var_name:
            # drop the directive
            parts.append(current[:m.start()])
        else:
            # keep the directive
            parts.append(current[:m.end()])

        current = current[m.end():]
        m = _VAR_RE.search(current)

    parts.append(current)
    return "".join(parts)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def get_title_from_md_text(
    text: str, 
    return_match: bool = False
) -> Union[None, str, Match[str]]:
    """
    Extract the first level-1 Markdown title from text.

    Supported syntaxes:
      - Setext H1:
            Title
            =====
      - ATX H1:
            # Title

    Comments of the form <!-- ... --> are stripped before searching.

    Args:
        text: Markdown text.
        return_match: If True, return the `re.Match` object (on the comment-stripped text).

    Returns:
        The title string (stripped), or None if not found.
        If return_match is True, returns the match object instead.

    Raises:
        TypeError: If text is not a string.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    local_text = strip_xml_comment(text)

    m = _SETEXT_H1_RE.search(local_text)
    if not m:
        m = _ATX_H1_RE.search(local_text)
        if not m:
            return None

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

    Supported syntaxes:
      - Setext H1:
            Title
            =====
      - ATX H1:
            # Title

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
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not isinstance(new_title, str):
        raise TypeError("new_title must be a string")

    title = new_title.strip()
    if not title:
        raise ValueError("new_title must be non-empty")
    if style not in ("preserve", "setext", "atx"):
        raise ValueError(f"invalid style: {style!r}")

    # Detect on comment-stripped text (ignore commented titles)
    local_text = strip_xml_comment(text)

    m_setext = _SETEXT_H1_RE.search(local_text)
    m_atx = None if m_setext else _ATX_H1_RE.search(local_text)

    # Decide output style
    if style == "preserve":
        output_style: TitleStyle
        if m_setext:
            output_style = "setext"
        elif m_atx:
            output_style = "atx"
        else:
            output_style = "setext"  # default insertion format
    else:
        output_style = style

    def make_setext(t: str) -> str:
        return f"{t}\n" + ("=" * len(t)) + "\n"

    def make_atx(t: str) -> str:
        return f"# {t}\n"

    # Replace existing title
    if m_setext:
        m2 = _SETEXT_H1_RE.search(text)
        if m2:
            replacement = make_setext(title) if output_style == "setext" else make_atx(title)
            return text[:m2.start()] + replacement + text[m2.end():]

    if m_atx:
        m2 = _ATX_H1_RE.search(text)
        if m2:
            replacement = make_setext(title) if output_style == "setext" else make_atx(title)
            return text[:m2.start()] + replacement + text[m2.end():]

    # No title found: insert at top
    replacement = make_setext(title) if output_style == "setext" else make_atx(title)
    # Add a blank line after the title if content does not already start with newline
    if text and not text.startswith("\n"):
        return replacement + "\n" + text
    return replacement + text
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def get_vars_from_md_file(
    filename: Union[str, Path],
    *,
    filename_ext: str = ".md",
    previous_vars: Optional[Dict[str, str]] = None,
    encoding: str = "UNKNOWN",
) -> Dict[str, str]:
    """
    Extract var(...) directives from a markdown file.

    The returned values are interpreted (escapes are processed) as defined by
    `get_vars_from_md_text`.

    Args:
        filename: Path to the markdown file.
        filename_ext: Expected file extension.
        previous_vars: Optional existing mapping to extend.
        encoding: Encoding to use for reading ("UNKNOWN" may trigger auto-detection).

    Returns:
        A dict mapping variable names to interpreted values.

    Raises:
        RuntimeError/Exception: Propagated from path checks and file reading helpers.
        ValueError: If duplicate var names are found.
    """
    logging.debug("Find vars in the MD file %s", filename)
    checked = common.check_file(str(filename), filename_ext)

    text = common.get_file_content(checked, encoding=encoding)
    return get_vars_from_md_text(text, previous_vars=previous_vars)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def include_vars_to_md_text(
    text: str,
    vars_include: Mapping[str, str],
    *,
    begin_var_re: Union[str, Pattern[str]] = _BEGIN_VAR_RE,
    end_var_re: Union[str, Pattern[str]] = _END_VAR_RE,
    error_if_var_not_found: bool = True,
) -> str:
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
    filename: Union[str, Path],
    vars_include: Mapping[str, str],
    *,
    backup_option: bool = True,
    backup_ext: str = ".bak",
    filename_ext: str = ".md",
    begin_var_re: Union[str, Pattern[str]] = _BEGIN_VAR_RE,
    end_var_re: Union[str, Pattern[str]] = _END_VAR_RE,
    error_if_var_not_found: bool = True,
    read_encoding: str = "UNKNOWN",
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
        read_encoding: Encoding used to read the file ("UNKNOWN" may trigger auto-detection).
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
    folder: Union[str, Path],
    *,
    filename_ext: str = ".md",
    previous_vars: Optional[Dict[str, str]] = None,
    depth: int = -1,
    encoding: str = "UNKNOWN",
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
        encoding: Encoding for reading files ("UNKNOWN" may trigger auto-detection).

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
    filename: Union[str, Path],
    *,
    filename_ext: str = ".md",
    previous_vars: Optional[Dict[str, str]] = None,
    depth_up: int = 1,
    depth_down: int = -1,
    encoding: str = "UNKNOWN",
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
        encoding: Encoding used to read markdown files ("UNKNOWN" may trigger auto-detection).

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
    filename: Union[str, Path],
    *,
    backup_option: bool = True,
    backup_ext: str = ".bak",
    filename_ext: str = ".md",
    depth_up: int = 1,
    depth_down: int = -1,
    encoding: str = "UNKNOWN",
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
    begin_var_re: Union[str, Pattern[str]] = _BEGIN_VAR_RE,
    end_var_re: Union[str, Pattern[str]] = _END_VAR_RE,
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
    filename: Union[str, Path],
    *,
    search_folders: Optional[Iterable[Union[str, Path]]] = None,
    include_cwd: bool = True,
    relative_paths: Sequence[str] = (".", "referenced_files"),
    nb_up_path: int = 1,
    encoding: str = "UNKNOWN",
) -> str:
    """
    Retrieve the content of a referenced file to include.

    The function searches `filename` using `common.search_for_file` starting from:
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
        encoding: Encoding for reading ("UNKNOWN" may trigger auto-detection).

    Returns:
        File content as text.

    Raises:
        Exception: Propagated if the file cannot be found or read.
    """
    requested = str(filename)

    # Optional hardening: forbid path traversal in the requested "filename"
    # (keep it conservative: you can relax if you intentionally support subpaths)
    if os.path.isabs(requested) or ".." in Path(requested).parts:
        raise ValueError(f"invalid referenced filename: {requested!r}")

    module_dir = str(Path(common.get_this_filename()).resolve().parent)

    start_points: list[str] = [module_dir]
    if include_cwd:
        start_points.append(os.getcwd())

    if search_folders:
        start_points.extend(str(Path(p)) for p in search_folders)

    logging.debug(
        "Include-file lookup: filename=%r start_points=%r relative_paths=%r nb_up_path=%d",
        requested, start_points, list(relative_paths), nb_up_path
    )

    found = common.search_for_file(
        requested,
        start_points,
        list(relative_paths),
        nb_up_path=nb_up_path,
    )

    logging.debug("Include-file resolved: %r -> %r", requested, found)
    return common.get_file_content(found, encoding=encoding)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def include_files_to_md_text(
    text: str,
    *,
    include_file_re: Union[str, Pattern[str]] = _INCLUDE_FILE_RE,
    error_if_no_file: bool = True,
    render_mode: IncludeRenderMode = "box",
    **kwargs,
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
    pattern = re.compile(include_file_re) if isinstance(include_file_re, str) else include_file_re

    result_parts: list[str] = []
    pos = 0

    while True:
        m = pattern.search(text, pos)
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
    filename: Union[str, Path],
    *,
    backup_option: bool = True,
    backup_ext: str = ".bak",
    filename_ext: str = ".md",
    read_encoding: str = "UNKNOWN",
    write_encoding: str = "utf-8",
    error_if_no_file: bool = True,
    render_mode: str = "box",
    **kwargs,
) -> str:
    """
    Apply include-file substitutions to a markdown file in-place.

    Args:
        filename: Markdown file to process.
        backup_option: Create a backup before writing.
        backup_ext: Backup extension.
        filename_ext: Expected markdown extension.
        read_encoding: Encoding to read ("UNKNOWN" may trigger auto-detection).
        write_encoding: Encoding used to write.
        error_if_no_file: If False, keep unresolved directives unchanged.
        render_mode: Forwarded to include_files_to_md_text (e.g. "box" or "raw").
        **kwargs: Forwarded to get_file_content_to_include (e.g. search_folders).

    Returns:
        Normalized filename.
    """
    logging.debug("Include file to the file %s", filename)
    checked = common.check_file(str(filename), filename_ext)

    text = common.get_file_content(checked, encoding=read_encoding)

    if backup_option:
        common.create_backup(checked, backup_ext=backup_ext)

    text = include_files_to_md_text(
        text,
        error_if_no_file=error_if_no_file,
        render_mode=render_mode,
        **kwargs,
    )

    common.set_file_content(checked, text, encoding=write_encoding)
    return checked
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def ensure_include_file_in_md_text(
    text: str,
    filename: str,
    *,
    include_file_re: Union[str, Pattern[str]] = _INCLUDE_FILE_RE,
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
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not isinstance(filename, str) or not filename.strip():
        raise ValueError("filename must be a non-empty string")

    # Normalize newlines (optional but helps determinism)
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    pattern = re.compile(include_file_re) if isinstance(include_file_re, str) else include_file_re

    # If already present, return as-is
    for m in pattern.finditer(normalized):
        if m.group("name") == filename:
            return normalized

    directive = f"<!-- include-file({filename}) -->"

    matches = list(pattern.finditer(normalized))
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
    include_file_re: Union[str, Pattern[str]] = _INCLUDE_FILE_RE,
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
    pattern = re.compile(include_file_re) if isinstance(include_file_re, str) else include_file_re

    names = [m.group("name") for m in pattern.finditer(text)]

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
    include_file_re: Union[str, Pattern[str]] = _INCLUDE_FILE_RE,
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
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not isinstance(filename, str) or not filename:
        raise ValueError("filename must be a non-empty string")

    pattern = re.compile(include_file_re) if isinstance(include_file_re, str) else include_file_re

    out_parts: list[str] = []
    pos = 0
    removed = False

    for m in pattern.finditer(text):
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