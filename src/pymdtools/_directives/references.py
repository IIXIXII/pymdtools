"""Directives: references."""

from __future__ import annotations

import logging
from typing import (
    Dict,
    List,
    Mapping,
    Optional,
)

from .. import common
from ..mdcommon import markdown_code_ranges
from ._shared import (
    BEGIN_INCLUDE_RE,
    BEGIN_REF_RE,
    END_INCLUDE_RE,
    END_REF_RE,
    RegexInput,
    compile_pattern,
    create_backup,
    directive_matches,
    read_md_text,
    require_str,
    search_outside_ranges,
)

logger: logging.Logger = logging.getLogger(__name__)


def get_refs_from_md_text(
    text: str, previous_refs: Optional[Dict[str, str]] = None
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
    text = require_str(text, "text")
    refs: Dict[str, str] = dict(previous_refs) if previous_refs else {}
    code_ranges = markdown_code_ranges(text)

    pos = 0
    while True:
        m_begin = search_outside_ranges(BEGIN_REF_RE, text, pos, code_ranges)
        if not m_begin:
            return refs

        key = m_begin.group("name")
        if key in refs:
            raise ValueError(f"duplicate begin-ref({key})")

        after_begin = m_begin.end()
        m_end = search_outside_ranges(END_REF_RE, text, after_begin, code_ranges)
        if not m_end:
            raise ValueError(f"begin-ref({key}) without end-ref")

        refs[key] = text[after_begin : m_end.start()]
        pos = m_end.end()


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
    text = read_md_text(checked)
    return get_refs_from_md_text(text, previous_refs=previous_refs)


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
    text = require_str(text, "text")

    return [match.group("name") for match in directive_matches(BEGIN_INCLUDE_RE, text)]


def include_refs_to_md_text(
    text: str,
    refs_include: Mapping[str, str],
    begin_include_re: RegexInput = BEGIN_INCLUDE_RE,
    end_include_re: RegexInput = END_INCLUDE_RE,
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
    text = require_str(text, "text")
    begin_pattern = compile_pattern(begin_include_re)
    end_pattern = compile_pattern(end_include_re)

    code_ranges = markdown_code_ranges(text)
    parts: list[str] = []
    cursor = 0

    while True:
        match_begin = search_outside_ranges(begin_pattern, text, cursor, code_ranges)
        if match_begin is None:
            parts.append(text[cursor:])
            return "".join(parts)

        key = match_begin.group("name")
        logger.debug("Find the include key %s", key)
        match_end = search_outside_ranges(end_pattern, text, match_begin.end(), code_ranges)
        if match_end is None:
            raise ValueError(f"begin-include({key}) without end-include")

        parts.append(text[cursor : match_begin.end()])
        if key not in refs_include:
            if error_if_no_key:
                raise KeyError(f"begin-include({key}) references an unknown key")
            parts.append(text[match_begin.end() : match_end.end()])
        else:
            parts.append(refs_include[key])
            parts.append(text[match_end.start() : match_end.end()])
        cursor = match_end.end()


def include_refs_to_md_file(
    filename: common.PathInput,
    refs: Mapping[str, str],
    *,
    backup_option: bool = True,
    backup_ext: str = ".bak",
    filename_ext: str = ".md",
    begin_include_re: RegexInput = BEGIN_INCLUDE_RE,
    end_include_re: RegexInput = END_INCLUDE_RE,
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

    text = read_md_text(checked, read_encoding)

    if backup_option:
        create_backup(checked, backup_ext)

    new_text = include_refs_to_md_text(
        text,
        refs,
        begin_include_re=begin_include_re,
        end_include_re=end_include_re,
        error_if_no_key=error_if_no_key,
    )

    common.set_file_content(checked, new_text, encoding=write_encoding)
    return str(checked)
