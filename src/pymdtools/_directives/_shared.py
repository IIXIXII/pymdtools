"""Directives: shared."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import (
    Final,
    Literal,
    Match,
    Optional,
    Pattern,
    Sequence,
    Union,
)

from .. import common
from ..mdcommon import markdown_code_ranges, position_in_ranges

logger: logging.Logger = logging.getLogger(__name__)


TitleStyle = Literal["preserve", "setext", "atx"]

IncludeRenderMode = Literal["box", "raw"]

RegexInput = Union[str, Pattern[str]]

XML_COMMENT_RE: Final[re.Pattern[str]] = re.compile(r"<!--.*?-->", re.DOTALL)

BEGIN_REF_RE: Final[re.Pattern[str]] = re.compile(
    r"<!--\s*begin-ref\(\s*(?P<name>[A-Za-z0-9_-]+)\s*\)\s*-->"
)

END_REF_RE: Final[re.Pattern[str]] = re.compile(r"<!--\s*end-ref\s*-->")

BEGIN_INCLUDE_RE: Final[re.Pattern[str]] = re.compile(
    r"""
    <!--\s*
    begin-include
    \(\s*(?P<name>[A-Za-z0-9_-]+)\s*\)
    \s*-->
    """,
    re.VERBOSE,
)

END_INCLUDE_RE: Final[re.Pattern[str]] = re.compile(
    r"""
    <!--\s*
    end-include
    \s*-->
    """,
    re.VERBOSE,
)

VAR_RE: Final[re.Pattern[str]] = re.compile(
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

ESCAPE_RE: Final[re.Pattern[str]] = re.compile(r"\\(.)", re.DOTALL)

ESCAPE_MAP: Final[dict[str, str]] = {
    "n": "\n",
    "t": "\t",
    "r": "\r",
    "\\": "\\",
    '"': '"',
    "'": "'",
}

VAR_NAME_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9:_-]+(?:/[A-Za-z0-9:_-]+)*$")

ESCAPE_OUT_MAP: Final[dict[str, str]] = {
    "\\": r"\\",
    "\n": r"\n",
    "\t": r"\t",
    "\r": r"\r",
    '"': r"\"",
}

INCLUDE_FILE_RE: Final[re.Pattern[str]] = re.compile(
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

SETEXT_H1_RE: Final[re.Pattern[str]] = re.compile(
    r"""(?mx)
    ^[ ]{0,3}(?P<title>[^\r\n]+?)[ \t]*\r?\n
    ^[ ]{0,3}=+[ \t]*\r?\n?
    """
)

ATX_H1_RE: Final[re.Pattern[str]] = re.compile(
    r"""(?mx)
    ^[ ]{0,3}\#[ \t]+(?P<title>[^\r\n#]*?[^\s#])[ \t]*\#*[ \t]*(?:\r?\n|$)
    """
)

BEGIN_VAR_RE: Final[re.Pattern[str]] = re.compile(
    r"<!--\s*begin-var\(\s*(?P<name>[A-Za-z0-9:_-]+(?:/[A-Za-z0-9:_-]+)*)\s*\)\s*-->",
)

END_VAR_RE: Final[re.Pattern[str]] = re.compile(
    r"<!--\s*end-var\s*-->",
)


def normalize_read_encoding(encoding: Optional[str]) -> Optional[str]:
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


def read_md_text(path: common.PathInput, encoding: Optional[str] = None) -> str:
    """Read text through ``common`` while accepting the legacy encoding sentinel."""
    return common.get_file_content(path, encoding=normalize_read_encoding(encoding))


def create_backup(path: common.PathInput, backup_ext: str) -> Path:
    """Create a backup using the current ``common.create_backup`` signature."""
    return common.create_backup(path, ext=backup_ext, date_prefix=common.today_utc())


def require_str(value: object, name: str) -> str:
    """Return ``value`` as ``str`` or raise a stable runtime error."""
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    return value


def all_str(*values: object) -> bool:
    """Return whether all values are strings."""
    return all(isinstance(value, str) for value in values)


def is_non_empty_str(value: object, *, strip: bool = False) -> bool:
    """Return whether ``value`` is a non-empty string."""
    if not isinstance(value, str):
        return False
    candidate = value.strip() if strip else value
    return bool(candidate)


def compile_pattern(pattern: RegexInput) -> Pattern[str]:
    """Return a compiled regex pattern."""
    return re.compile(pattern) if isinstance(pattern, str) else pattern


def finditer_outside_ranges(
    pattern: Pattern[str],
    text: str,
    ranges: Sequence[tuple[int, int]],
) -> list[Match[str]]:
    """Return pattern matches whose opening character is not protected."""
    return [
        match for match in pattern.finditer(text) if not position_in_ranges(match.start(), ranges)
    ]


def search_outside_ranges(
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


def directive_matches(pattern: Pattern[str], text: str) -> list[Match[str]]:
    """Return directive matches that are outside Markdown code."""
    return finditer_outside_ranges(pattern, text, markdown_code_ranges(text))
