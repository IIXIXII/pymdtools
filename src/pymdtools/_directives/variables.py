"""Directives: variables."""

from __future__ import annotations

import logging
import re
from typing import (
    Dict,
    Mapping,
    Optional,
)

from .. import common
from ._shared import (
    BEGIN_VAR_RE,
    END_VAR_RE,
    ESCAPE_MAP,
    ESCAPE_OUT_MAP,
    ESCAPE_RE,
    INCLUDE_FILE_RE,
    VAR_NAME_RE,
    VAR_RE,
    RegexInput,
    all_str,
    directive_matches,
    read_md_text,
    require_str,
)
from .references import include_refs_to_md_file, include_refs_to_md_text

logger: logging.Logger = logging.getLogger(__name__)


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
        return ESCAPE_MAP.get(ch, ch)

    return ESCAPE_RE.sub(repl, value)


def get_vars_from_md_text(
    text: str, previous_vars: Optional[Dict[str, str]] = None
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
    text = require_str(text, "text")

    vars_: Dict[str, str] = dict(previous_vars) if previous_vars else {}

    for m in directive_matches(VAR_RE, text):
        key = m.group("name")
        raw_value = m.group("string")
        value = unescape_var_value(raw_value)

        if key in vars_:
            raise ValueError(f"duplicate var({key})")

        vars_[key] = value
    return vars_


def escape_var_value(value: str) -> str:
    """Escape a value so it can be safely embedded inside <!-- var(...)="..." -->."""
    # order matters: escape backslash first
    out = value.replace("\\", ESCAPE_OUT_MAP["\\"])
    out = out.replace("\n", ESCAPE_OUT_MAP["\n"])
    out = out.replace("\t", ESCAPE_OUT_MAP["\t"])
    out = out.replace("\r", ESCAPE_OUT_MAP["\r"])
    out = out.replace('"', ESCAPE_OUT_MAP['"'])
    return out


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
    text = require_str(text, "text")
    if not all_str(var_name, value):
        raise TypeError("var_name and value must be strings")
    if not VAR_NAME_RE.match(var_name):
        raise ValueError(f"invalid var name: {var_name!r}")

    var_text = f'<!-- var({var_name})="{escape_var_value(value)}" -->'

    var_matches = directive_matches(VAR_RE, text)
    matching_vars = [match for match in var_matches if match.group("name") == var_name]
    if matching_vars:
        parts: list[str] = []
        cursor = 0
        for match in matching_vars:
            parts.append(text[cursor : match.start()])
            parts.append(var_text)
            cursor = match.end()
        parts.append(text[cursor:])
        return "".join(parts)

    header_matches = [
        *directive_matches(VAR_RE, text),
        *directive_matches(INCLUDE_FILE_RE, text),
    ]
    insert_at = max((match.end() for match in header_matches), default=0)
    before = text[:insert_at]
    after = text[insert_at:]
    separator_before = "\n" if before else ""
    separator_after = "\n" if not after or after.startswith("\n") else "\n\n"
    return before + separator_before + var_text + separator_after + after


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
    text = require_str(text, "text")
    if not all_str(var_name):
        raise TypeError("var_name must be a string")
    if not VAR_NAME_RE.match(var_name):
        raise ValueError(f"invalid var name: {var_name!r}")

    parts: list[str] = []
    cursor = 0
    for match in directive_matches(VAR_RE, text):
        if match.group("name") != var_name:
            continue
        parts.append(text[cursor : match.start()])
        cursor = match.end()
    parts.append(text[cursor:])
    return "".join(parts)


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
    logger.debug("Find vars in the MD file %s", filename)
    checked = common.check_file(str(filename), filename_ext)

    text = read_md_text(checked, encoding)
    return get_vars_from_md_text(text, previous_vars=previous_vars)


def include_vars_to_md_text(
    text: str,
    vars_include: Mapping[str, str],
    *,
    begin_var_re: RegexInput = BEGIN_VAR_RE,
    end_var_re: RegexInput = END_VAR_RE,
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


def include_vars_to_md_file(
    filename: common.PathInput,
    vars_include: Mapping[str, str],
    *,
    backup_option: bool = True,
    backup_ext: str = ".bak",
    filename_ext: str = ".md",
    begin_var_re: RegexInput = BEGIN_VAR_RE,
    end_var_re: RegexInput = END_VAR_RE,
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


def search_include_vars_to_md_text(
    text: str,
    *,
    error_if_var_not_found: bool = True,
    begin_var_re: RegexInput = BEGIN_VAR_RE,
    end_var_re: RegexInput = END_VAR_RE,
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
