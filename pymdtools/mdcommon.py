#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                    Author: Florent TOURNOIS | License: MIT
# =============================================================================
"""
Markdown link management helpers.

``pymdtools.mdcommon`` provides tools to inspect and rewrite links inside
Markdown documents. It is designed for workflows that modify a set of Markdown
files together, for example after moving documentation folders, renaming pages,
or replacing obsolete link targets.

Links are represented as dictionaries with keys such as ``name``, ``url``,
``title``, ``line``, ``id_link`` and ``name_to_replace``. This small data model
is easy to serialize, compare, transform, and feed back into rewrite functions.

The helpers operate on Markdown text and avoid mutating caller-provided link
dictionaries. File-oriented helpers delegate path validation and text loading to
:mod:`pymdtools.common`.
"""

from __future__ import annotations

import json
import logging
import posixpath
import re
from collections.abc import Mapping, Sequence
from typing import Final, TypeAlias
from urllib.parse import urlparse, urlsplit, urlunsplit

from . import common

LinkValue: TypeAlias = str | int | None
LinkRecord: TypeAlias = dict[str, LinkValue]
LinkMapping: TypeAlias = Mapping[str, LinkValue]
LinkPair: TypeAlias = tuple[LinkMapping, LinkMapping]


# -----------------------------------------------------------------------------
# Regular expressions used by this module
#
# Conventions:
# - All patterns are compiled once at import time.
# - Link extraction patterns expose named groups matching the link data model:
#     - group("name") for the visible link label
#     - group("url") for the destination URL/path
#     - group("title") for the optional Markdown title
#     - group("id_link") for reference-style link identifiers
# - The full inline link expression is captured by an outer group so callers can
#   replace the complete Markdown token when needed.
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# 1) Inline Markdown links: [label](url "title")
#
# Matched examples:
#   [label](target.md)
#   [label](target.md "Optional title")
#
# Groups:
# - name : visible label between square brackets
# - url  : destination between parentheses, excluding nested parentheses
# - title: optional title surrounded by double quotes
#
# Notes:
# - The title group accepts multi-line content for compatibility with legacy
#   behavior.
# - The URL group intentionally does not support nested parentheses.
# -----------------------------------------------------------------------------
_INLINE_LINK_RE: Final[re.Pattern[str]] = re.compile(
    r"""(?<![!\]])(\[(?P<name>[^\]]*)]\s*"""
    r"""\(\s*(?P<url>[^()]+?)\s*(?:\"(?P<title>[\s\S]*?)\")?\))"""
)


# -----------------------------------------------------------------------------
# 2) Reference-style link names: [label][id]
#
# Matched examples:
#   [label][ref-id]
#   [label][]
#
# Groups:
# - name   : visible label between the first square brackets
# - id_link: reference identifier between the second square brackets
#
# Notes:
# - URL resolution is completed by _REF_URL_RE.
# -----------------------------------------------------------------------------
_REF_NAME_RE: Final[re.Pattern[str]] = re.compile(
    r"""(?<![!\]])\[(?P<name>.*?)\]\s*?\[(?P<id_link>.*?)\]"""
)


# -----------------------------------------------------------------------------
# 3) Reference-style link definitions: [id]: url "title"
#
# Matched examples:
#   [ref-id]: target.md
#   [ref-id]: target.md "Optional title"
#
# Groups:
# - id_link: reference identifier
# - url    : destination URL/path
# - title  : optional title surrounded by double quotes
# -----------------------------------------------------------------------------
_REF_URL_RE: Final[re.Pattern[str]] = re.compile(
    r"""^[ \t]{0,3}\[(?P<id_link>[^\]\r\n]*?)\]:[ \t]*"""
    r"""(?P<url>\S+?)(?:[ \t]+\"(?P<title>[^\"\r\n]*)\")?"""
    r"""[ \t]*(?:\r?\n|$)""",
    re.MULTILINE,
)


# -----------------------------------------------------------------------------
def _require_string(value: object, *, key: str) -> str:
    """
    Return a required string value from a link field.

    Args:
        value: Candidate value to validate.
        key: Link field name used in the error message.

    Returns:
        ``value`` typed as ``str``.

    Raises:
        TypeError: If ``value`` is not a string.
    """
    if not isinstance(value, str):
        raise TypeError(f"link[{key!r}] must be a string")
    return value


# -----------------------------------------------------------------------------
def _link_value(link: LinkMapping, key: str) -> LinkValue:
    """
    Return a raw value from a link mapping.

    Args:
        link: Link mapping to inspect.
        key: Field name to read.

    Returns:
        The field value, or ``None`` if the field is missing.
    """
    return link.get(key)


# -----------------------------------------------------------------------------
def _link_string(link: LinkMapping, key: str) -> str:
    """
    Return a required string field from a link mapping.

    Args:
        link: Link mapping to inspect.
        key: Field name to read.

    Returns:
        The field value as a string.

    Raises:
        TypeError: If the field is missing or is not a string.
    """
    return _require_string(_link_value(link, key), key=key)


# -----------------------------------------------------------------------------
def _optional_link_string(link: LinkMapping, key: str) -> str | None:
    """
    Return an optional string field from a link mapping.

    Args:
        link: Link mapping to inspect.
        key: Field name to read.

    Returns:
        The field value as a string, or ``None`` when the field is missing.

    Raises:
        TypeError: If the field exists but is not a string.
    """
    value = _link_value(link, key)
    if value is None:
        return None
    return _require_string(value, key=key)


# -----------------------------------------------------------------------------
def _copy_link(link: LinkMapping) -> LinkRecord:
    """
    Return a mutable copy of a link mapping.

    Args:
        link: Source link mapping.

    Returns:
        A new mutable dictionary with the same values.
    """
    return dict(link)


# -----------------------------------------------------------------------------
def _line_number(text: str, index: int) -> int:
    """
    Return the one-based line number for a character index.

    Args:
        text: Source text.
        index: Character offset inside ``text``.

    Returns:
        The one-based line number containing ``index``.
    """
    return text[:index].count("\n") + 1


# -----------------------------------------------------------------------------
def merge_ranges(ranges: Sequence[tuple[int, int]]) -> list[tuple[int, int]]:
    """Return sorted, overlapping character ranges as disjoint ranges."""
    merged: list[tuple[int, int]] = []
    for start, end in sorted(ranges):
        if start >= end:
            continue
        if merged and start <= merged[-1][1]:
            previous_start, previous_end = merged[-1]
            merged[-1] = (previous_start, max(previous_end, end))
        else:
            merged.append((start, end))
    return merged


# -----------------------------------------------------------------------------
def markdown_code_ranges(text: str) -> list[tuple[int, int]]:
    """Locate fenced, indented, and inline Markdown code regions."""
    ranges: list[tuple[int, int]] = []
    fenced_ranges: list[tuple[int, int]] = []
    offset = 0
    fence_start: int | None = None
    fence_char = ""
    fence_length = 0

    for line in text.splitlines(keepends=True):
        if fence_start is None:
            opener = re.match(r" {0,3}(`{3,}|~{3,})(.*?)(?:\r?\n)?$", line)
            if opener and not (
                opener.group(1).startswith("`") and "`" in opener.group(2)
            ):
                fence_start = offset
                fence_char = opener.group(1)[0]
                fence_length = len(opener.group(1))
        else:
            closer = re.match(
                rf" {{0,3}}{re.escape(fence_char)}{{{fence_length},}}[ \t]*(?:\r?\n)?$",
                line,
            )
            if closer:
                fenced_ranges.append((fence_start, offset + len(line)))
                fence_start = None
                fence_char = ""
                fence_length = 0
        offset += len(line)

    if fence_start is not None:
        fenced_ranges.append((fence_start, len(text)))

    # Conservatively treat every Markdown-indented line as code. Blank lines
    # between adjacent indented lines remain part of the same block, which
    # prevents directives embedded in examples from being executed.
    indented_ranges = [
        match.span()
        for match in re.finditer(
            r"(?m)^(?: {4}|\t)[^\r\n]*(?:\r?\n|$)"
            r"(?:^[ \t]*(?:\r?\n|$)|^(?: {4}|\t)[^\r\n]*(?:\r?\n|$))*",
            text,
        )
    ]
    block_ranges = merge_ranges([*fenced_ranges, *indented_ranges])
    ranges.extend(block_ranges)

    def in_block_range(index: int) -> tuple[int, int] | None:
        for start, end in block_ranges:
            if start <= index < end:
                return start, end
            if index < start:
                break
        return None

    index = 0
    while index < len(text):
        code_block = in_block_range(index)
        if code_block is not None:
            index = code_block[1]
            continue
        escape_start = index
        while escape_start > 0 and text[escape_start - 1] == "\\":
            escape_start -= 1
        is_escaped = (index - escape_start) % 2 == 1
        if text[index] != "`" or is_escaped:
            index += 1
            continue

        opener_end = index + 1
        while opener_end < len(text) and text[opener_end] == "`":
            opener_end += 1
        delimiter_length = opener_end - index
        search_at = opener_end
        closing_end: int | None = None
        while search_at < len(text):
            next_tick = text.find("`", search_at)
            if next_tick < 0:
                break
            code_block = in_block_range(next_tick)
            if code_block is not None:
                search_at = code_block[1]
                continue
            run_end = next_tick + 1
            while run_end < len(text) and text[run_end] == "`":
                run_end += 1
            if run_end - next_tick == delimiter_length:
                closing_end = run_end
                break
            search_at = run_end

        if closing_end is None:
            index = opener_end
            continue
        ranges.append((index, closing_end))
        index = closing_end

    return merge_ranges(ranges)


# -----------------------------------------------------------------------------
def position_in_ranges(index: int, ranges: Sequence[tuple[int, int]]) -> bool:
    """Return whether ``index`` belongs to one of the sorted ranges."""
    for start, end in ranges:
        if index < start:
            return False
        if index < end:
            return True
    return False


# -----------------------------------------------------------------------------
def _matches_outside_code(pattern: re.Pattern[str], text: str) -> list[re.Match[str]]:
    """Return regex matches whose opening character is not Markdown code."""
    ranges = markdown_code_ranges(text)
    return [
        match
        for match in pattern.finditer(text)
        if not position_in_ranges(match.start(), ranges)
    ]


# -----------------------------------------------------------------------------
def _apply_replacements(
    text: str,
    replacements: Sequence[tuple[int, int, str]],
) -> str:
    """Apply non-overlapping replacements expressed with source offsets."""
    if not replacements:
        return text

    parts: list[str] = []
    cursor = 0
    for start, end, replacement in sorted(replacements, key=lambda item: item[0]):
        if start < cursor:
            continue
        parts.append(text[cursor:start])
        parts.append(replacement)
        cursor = end
    parts.append(text[cursor:])
    return "".join(parts)


# -----------------------------------------------------------------------------
def _reference_definition_text(link: LinkMapping, id_link: str) -> str:
    """Build a reference definition without adding an extra line ending."""
    new_url = _link_string(link, "url")
    title = _optional_link_string(link, "title")
    new_title = f' "{title}"' if title is not None else ""
    return f"[{id_link}]: {new_url}{new_title}"


# -----------------------------------------------------------------------------
def is_external_link(url: str) -> bool:
    """
    Return whether ``url`` is an external link.

    ``http`` and ``https`` URLs require both a scheme and a network location.
    Other schemes, such as ``mailto``, are considered external when their scheme
    is present. Invalid URLs return ``False``.

    Args:
        url: URL or Markdown link target to classify.

    Returns:
        ``True`` when the target is considered external, otherwise ``False``.
    """
    try:
        result = urlparse(url)
    except ValueError:
        return False

    if result.scheme in ("http", "https"):
        return bool(result.scheme and result.netloc)
    return bool(result.scheme)


# -----------------------------------------------------------------------------
def get_domain_name(url: str) -> str:
    """
    Return the domain part of an external URL.

    Non-external URLs are returned unchanged. ``mailto`` URLs return their path,
    which is the email address.

    Args:
        url: URL or Markdown link target to inspect.

    Returns:
        Domain name for external HTTP(S) URLs, email address for ``mailto`` URLs,
        or the original value for local links.
    """
    if not is_external_link(url):
        return url

    parsed = urlparse(url)
    if parsed.scheme == "mailto":
        return parsed.path
    return parsed.netloc


# -----------------------------------------------------------------------------
class Link(dict[str, LinkValue]):
    """
    Dictionary-compatible link object.

    The class stores the same fields returned by link extraction helpers while
    exposing convenience properties for ``name``, ``label``, ``url`` and
    ``title``. Assigning ``None`` removes the underlying key.
    """

    @property
    def name(self) -> str | None:
        """Return the link label, stored under the ``name`` key."""
        value = self.get("name")
        return value if isinstance(value, str) else None

    @name.setter
    def name(self, value: str | None) -> None:
        """Set or remove the link label."""
        if value is None:
            self.pop("name", None)
        else:
            self["name"] = value

    @property
    def label(self) -> str | None:
        """Alias for :attr:`name`."""
        return self.name

    @label.setter
    def label(self, value: str | None) -> None:
        """Set or remove the link label."""
        self.name = value

    @property
    def url(self) -> str | None:
        """Return the link target URL."""
        value = self.get("url")
        return value if isinstance(value, str) else None

    @url.setter
    def url(self, value: str | None) -> None:
        """Set or remove the link target URL."""
        if value is None:
            self.pop("url", None)
        else:
            self["url"] = value

    @property
    def title(self) -> str | None:
        """Return the optional link title."""
        value = self.get("title")
        return value if isinstance(value, str) else None

    @title.setter
    def title(self, value: str | None) -> None:
        """Set or remove the optional link title."""
        if value is None:
            self.pop("title", None)
        else:
            self["title"] = value

    def __str__(self) -> str:
        """Return a human-readable representation of the link."""
        return f"Link name='{self.name}' title='{self.title}'\n      url={self.url}\n"


# -----------------------------------------------------------------------------
def search_link_in_md_text(
    text: str,
    previous_links: Sequence[LinkMapping] | None = None,
) -> list[LinkRecord]:
    """
    Extract Markdown links from text.

    Both inline links, such as ``[label](target "title")``, and reference links,
    such as ``[label][id]`` plus ``[id]: target "title"``, are returned. The
    returned records contain ``name``, ``url``, ``title`` and ``line``.

    ``previous_links`` is copied before new entries are appended.

    Args:
        text: Markdown text to inspect.
        previous_links: Optional existing links to prepend to the result.

    Returns:
        A list of link records in discovery order. Each extracted record contains
        ``name``, ``url``, ``title`` and ``line`` when available.
    """
    result = [_copy_link(link) for link in previous_links] if previous_links else []

    for match in _matches_outside_code(_INLINE_LINK_RE, text):
        result.append(
            {
                "name": match.group("name"),
                "url": match.group("url"),
                "title": match.group("title"),
                "line": _line_number(text, match.start()),
            }
        )

    links_by_ref: dict[str, LinkRecord] = {}
    for match in _matches_outside_code(_REF_NAME_RE, text):
        links_by_ref[match.group("id_link")] = {
            "name": match.group("name"),
            "url": None,
        }

    for match in _matches_outside_code(_REF_URL_RE, text):
        id_link = match.group("id_link")
        ref_link = links_by_ref.get(id_link)
        if ref_link is None:
            continue
        ref_link["url"] = match.group("url")
        ref_link["title"] = match.group("title")
        ref_link["line"] = _line_number(text, match.start())
        result.append(ref_link)

    return result


# -----------------------------------------------------------------------------
def search_link_in_md_text_json(text_md: str) -> str:
    """
    Return links found in Markdown text as formatted JSON.

    Args:
        text_md: Markdown text to inspect.

    Returns:
        A deterministic, pretty-printed JSON string describing extracted links.
    """
    links = search_link_in_md_text(text_md)
    return json.dumps(links, sort_keys=True, indent=2)


# -----------------------------------------------------------------------------
def search_link_in_md_file(
    filename: common.PathInput,
    filename_ext: str = ".md",
    encoding: str | None = "utf-8",
    previous_links: Sequence[LinkMapping] | None = None,
) -> list[LinkRecord]:
    """
    Extract Markdown links from a file.

    The file is validated with :func:`pymdtools.common.check_file` before being
    read with :func:`pymdtools.common.get_file_content`.

    Args:
        filename: Markdown file to inspect.
        filename_ext: Expected file extension, including the leading dot.
        encoding: Encoding used to read the file. ``None`` triggers automatic
            detection in :mod:`pymdtools.common`.
        previous_links: Optional existing links to prepend to the result.

    Returns:
        A list of link records extracted from the file.

    Raises:
        RuntimeError: Propagated from file validation helpers.
        OSError: Propagated from file reading helpers.
    """
    logging.debug("Search link in the file %s", filename)
    checked = common.check_file(filename, filename_ext)
    text = common.get_file_content(checked, encoding=encoding)
    return search_link_in_md_text(text, previous_links=previous_links)


# -----------------------------------------------------------------------------
def update_links_in_md_text(
    text_md: str,
    links: LinkMapping | Sequence[LinkMapping],
) -> str:
    """
    Replace one or more links in Markdown text.

    A single link mapping or a sequence of link mappings is accepted. When
    ``name_to_replace`` is provided, it is used as the search key and ``name`` is
    used as the replacement label.

    Args:
        text_md: Markdown text to update.
        links: One link mapping or a sequence of mappings describing the new
            link values.

    Returns:
        Updated Markdown text.

    Raises:
        TypeError: If required link fields are missing or are not strings.
    """
    links_to_update = [links] if isinstance(links, Mapping) else links

    result = text_md
    for link in links_to_update:
        name_to_replace = _optional_link_string(link, "name_to_replace")
        if name_to_replace is None:
            name_to_replace = _link_string(link, "name")
        result = update_link_in_md_text(result, name_to_replace, link)

    return result


# -----------------------------------------------------------------------------
def move_base_path_in_md_text(text_md: str, mv_base_path: common.PathInput) -> str:
    """
    Prefix relative Markdown links with ``mv_base_path``.

    External URLs are left unchanged. The generated Markdown URLs use POSIX
    separators, even on Windows.

    Args:
        text_md: Markdown text to update.
        mv_base_path: Base path to prepend to relative link targets.

    Returns:
        Updated Markdown text.

    Raises:
        TypeError: If extracted link records do not contain string URLs.
    """
    base = common.path_to_url(common.to_path(mv_base_path)).strip("/")
    links_replace: list[LinkPair] = []

    for link in search_link_in_md_text(text_md):
        url = _link_string(link, "url")
        parsed = urlsplit(url)
        if (
            is_external_link(url)
            or parsed.netloc
            or not parsed.path
            or parsed.path.startswith("/")
        ):
            continue

        new_link = _copy_link(link)
        joined = (
            posixpath.normpath(posixpath.join(base, parsed.path))
            if base
            else posixpath.normpath(parsed.path)
        )
        new_link["url"] = urlunsplit(("", "", joined, parsed.query, parsed.fragment))
        links_replace.append((link, new_link))

    return update_links_from_old_link(text_md, links_replace)


# -----------------------------------------------------------------------------
def update_link_in_md_text(text_md: str, name: str, new_link: LinkMapping) -> str:
    """
    Replace links identified by their visible label.

    Inline links and reference-style links are both supported. ``new_link`` is
    copied internally, so the caller-provided mapping is not modified.

    Args:
        text_md: Markdown text to update.
        name: Existing visible link label to replace.
        new_link: Mapping containing at least ``name`` and ``url``. ``title`` is
            optional.

    Returns:
        Updated Markdown text.

    Raises:
        TypeError: If required fields in ``new_link`` are missing or are not
            strings.
    """
    link = _copy_link(new_link)
    replacement_inline = sub_string_link_md("", link)
    replacement_name = _link_string(link, "name")
    replacements: list[tuple[int, int, str]] = []

    for match in _matches_outside_code(_INLINE_LINK_RE, text_md):
        if match.group("name") == name:
            replacements.append((*match.span(), replacement_inline))

    reference_ids: set[str] = set()
    for match in _matches_outside_code(_REF_NAME_RE, text_md):
        if match.group("name") != name:
            continue
        id_link = match.group("id_link")
        reference_ids.add(id_link)
        replacements.append(
            (*match.span(), f"[{replacement_name}][{id_link}]")
        )

    for match in _matches_outside_code(_REF_URL_RE, text_md):
        id_link = match.group("id_link")
        if id_link not in reference_ids:
            continue
        newline = (
            "\r\n"
            if match.group().endswith("\r\n")
            else "\n"
            if match.group().endswith("\n")
            else ""
        )
        replacements.append(
            (*match.span(), _reference_definition_text(link, id_link) + newline)
        )

    return _apply_replacements(text_md, replacements)


# -----------------------------------------------------------------------------
def update_link_from_old_link(
    text_md: str,
    old_link: LinkMapping,
    new_link: LinkMapping,
) -> str:
    """
    Replace a link identified by its previous label and URL.

    This is stricter than :func:`update_link_in_md_text`: both the old label and
    old URL must match before an inline link is replaced.

    Args:
        text_md: Markdown text to update.
        old_link: Mapping describing the existing link. Requires ``name`` and
            ``url``.
        new_link: Mapping describing the replacement link.

    Returns:
        Updated Markdown text.

    Raises:
        TypeError: If required fields are missing or are not strings.
    """
    name = _link_string(old_link, "name")
    url = _link_string(old_link, "url")
    link = _copy_link(new_link)
    replacement_inline = sub_string_link_md("", link)
    replacement_name = _link_string(link, "name")
    replacements: list[tuple[int, int, str]] = []

    for match in _matches_outside_code(_INLINE_LINK_RE, text_md):
        if match.group("name") == name and match.group("url") == url:
            replacements.append((*match.span(), replacement_inline))

    matching_reference_ids = {
        match.group("id_link")
        for match in _matches_outside_code(_REF_URL_RE, text_md)
        if match.group("url") == url
    }

    referenced_ids: set[str] = set()
    for match in _matches_outside_code(_REF_NAME_RE, text_md):
        id_link = match.group("id_link")
        if match.group("name") != name or id_link not in matching_reference_ids:
            continue
        referenced_ids.add(id_link)
        replacements.append(
            (*match.span(), f"[{replacement_name}][{id_link}]")
        )

    for match in _matches_outside_code(_REF_URL_RE, text_md):
        id_link = match.group("id_link")
        if id_link not in referenced_ids or match.group("url") != url:
            continue
        newline = (
            "\r\n"
            if match.group().endswith("\r\n")
            else "\n"
            if match.group().endswith("\n")
            else ""
        )
        replacements.append(
            (*match.span(), _reference_definition_text(link, id_link) + newline)
        )

    return _apply_replacements(text_md, replacements)


# -----------------------------------------------------------------------------
def update_links_from_old_link(text_md: str, links_couple: Sequence[LinkPair]) -> str:
    """
    Apply several ``(old_link, new_link)`` replacements to Markdown text.

    Args:
        text_md: Markdown text to update.
        links_couple: Sequence of ``(old_link, new_link)`` pairs.

    Returns:
        Updated Markdown text after all replacements have been applied in order.

    Raises:
        TypeError: If any replacement mapping misses required string fields.
    """
    result = text_md
    for old_link, new_link in links_couple:
        result = update_link_from_old_link(result, old_link, new_link)
    return result


# -----------------------------------------------------------------------------
def sub_string_link_md(unused_dummy: object, link: LinkMapping) -> str:
    """
    Build an inline Markdown link string from a link mapping.

    Args:
        unused_dummy: Kept for compatibility with ``re.sub`` callbacks.
        link: Mapping containing ``name``, ``url`` and optional ``title``.

    Returns:
        Markdown inline link string.

    Raises:
        TypeError: If required fields are missing or are not strings.
    """
    name = _link_string(link, "name")
    new_url = _link_string(link, "url")
    title = _optional_link_string(link, "title")
    new_title = f' "{title}"' if title is not None else ""
    return f"[{name}]({new_url}{new_title})"


# -----------------------------------------------------------------------------
def sub_string_link_by_ref_md(unused_dummy: object, link: LinkMapping) -> str:
    """
    Build a Markdown reference definition from a link mapping.

    Args:
        unused_dummy: Kept for compatibility with ``re.sub`` callbacks.
        link: Mapping containing ``url``, optional ``id_link`` and optional
            ``title``.

    Returns:
        Markdown reference definition line.

    Raises:
        TypeError: If required fields are missing or are not strings.
    """
    id_link = _optional_link_string(link, "id_link") or ""
    new_url = _link_string(link, "url")
    title = _optional_link_string(link, "title")
    new_title = f' "{title}"' if title is not None else ""
    return f"[{id_link}]: {new_url}{new_title}\n"


# -----------------------------------------------------------------------------
def sub_string_name_by_ref_md(unused_dummy: object, link: LinkMapping) -> str:
    """
    Build the visible part of a Markdown reference-style link.

    Args:
        unused_dummy: Kept for compatibility with ``re.sub`` callbacks.
        link: Mapping containing ``name`` and ``id_link``.

    Returns:
        Markdown reference-style link label.

    Raises:
        TypeError: If required fields are missing or are not strings.
    """
    return f"[{_link_string(link, 'name')}][{_link_string(link, 'id_link')}]"


# =============================================================================
