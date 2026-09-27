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
from collections.abc import Mapping, Sequence
from typing import TypeAlias
from urllib.parse import urlparse, urlsplit, urlunsplit

from . import common
from ._markdown import (
    Document,
    LinkSpan,
    parse_document,
)
from ._markdown import (
    markdown_code_ranges as markdown_code_ranges,
)
from ._markdown import (
    merge_ranges as merge_ranges,
)
from ._markdown import (
    position_in_ranges as position_in_ranges,
)
from ._markdown_syntax import markdown_destination, markdown_title

logger: logging.Logger = logging.getLogger(__name__)


LinkValue: TypeAlias = str | int | None
LinkRecord: TypeAlias = dict[str, LinkValue]
LinkMapping: TypeAlias = Mapping[str, LinkValue]
LinkPair: TypeAlias = tuple[LinkMapping, LinkMapping]


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
def _markdown_title(title: str | None) -> str:
    """Quote a parsed title without turning its quotes into Markdown syntax."""
    return markdown_title(title)


def _reference_definition_text(link: LinkMapping, id_link: str) -> str:
    """Build a reference definition without adding an extra line ending."""
    new_url = _link_string(link, "url")
    title = _optional_link_string(link, "title")
    new_title = _markdown_title(title)
    return f"[{id_link}]: {markdown_destination(new_url)}{new_title}"


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
    for link in parse_document(text).links:
        result.append({"name": link.name, "url": link.url, "title": link.title, "line": link.line})
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
    logger.debug("Search link in the file %s", filename)
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

    The source is parsed once. Renames are sequential: changing A to B and then
    B to C also updates occurrences originally named A to C.

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

    document = parse_document(text_md)
    by_name: dict[str, list[LinkSpan]] = {}
    for occurrence in document.links:
        by_name.setdefault(occurrence.name, []).append(occurrence)
    selected: dict[tuple[int, int], LinkMapping] = {}
    for link in links_to_update:
        name_to_replace = _optional_link_string(link, "name_to_replace")
        if name_to_replace is None:
            name_to_replace = _link_string(link, "name")
        sub_string_link_md("", link)
        occurrences = by_name.pop(name_to_replace, [])
        for occurrence in occurrences:
            selected[occurrence.span] = link
        by_name.setdefault(_link_string(link, "name"), []).extend(occurrences)

    return _render_link_changes(text_md, document, selected)


# -----------------------------------------------------------------------------
def move_base_path_in_md_text(
    text_md: str, mv_base_path: common.PathInput, *, legacy_slug: bool = False
) -> str:
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
    base = (
        common.path_to_url(common.to_path(mv_base_path))
        if legacy_slug
        else common.encode_path_url(common.to_path(mv_base_path))
    ).strip("/")
    links_replace: list[LinkPair] = []

    for link in search_link_in_md_text(text_md):
        url = _link_string(link, "url")
        parsed = urlsplit(url)
        if is_external_link(url) or parsed.netloc or not parsed.path or parsed.path.startswith("/"):
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
    return _rewrite_links(text_md, [(name, None, new_link)])


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
    return _rewrite_links(
        text_md, [(_link_string(old_link, "name"), _link_string(old_link, "url"), new_link)]
    )


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
    return _rewrite_links(
        text_md,
        [(_link_string(old, "name"), _link_string(old, "url"), new) for old, new in links_couple],
    )


def _rewrite_links(text: str, changes: Sequence[tuple[str, str | None, LinkMapping]]) -> str:
    document = parse_document(text)
    selected: dict[tuple[int, int], LinkMapping] = {}
    by_name: dict[str, list[LinkSpan]] = {}
    by_target: dict[tuple[str, str], list[LinkSpan]] = {}
    for occurrence in document.links:
        by_name.setdefault(occurrence.name, []).append(occurrence)
        by_target.setdefault((occurrence.name, occurrence.url), []).append(occurrence)
    for name, url, replacement in changes:
        # Validate eagerly, including when the document has no matching link.
        sub_string_link_md("", replacement)
        matches = by_name.get(name, []) if url is None else by_target.get((name, url), [])
        for occurrence in matches:
            selected[occurrence.span] = replacement
    return _render_link_changes(text, document, selected)


def _render_link_changes(
    text: str, document: Document, selected: Mapping[tuple[int, int], LinkMapping]
) -> str:
    """Render selected occurrences using offsets from one immutable source snapshot."""
    replacements: list[tuple[int, int, str]] = []
    by_reference: dict[str, list[LinkSpan]] = {}
    for occurrence in document.links:
        if occurrence.reference is not None:
            by_reference.setdefault(occurrence.reference.key, []).append(occurrence)
    shared = {
        key
        for key, occurrences in by_reference.items()
        if key not in document.image_references
        and all(
            selected.get(other.span) == selected.get(occurrences[0].span) for other in occurrences
        )
    }
    written_references: set[str] = set()
    for occurrence in document.links:
        replacement = selected.get(occurrence.span)
        if replacement is None:
            continue
        ref = occurrence.reference
        if ref is not None and ref.key in shared:
            # Update a shared definition only when every user gets the same target.
            replacements.append(
                (*occurrence.span, f"[{_link_string(replacement, 'name')}][{ref.label}]")
            )
            if ref.key in written_references:
                continue
            written_references.add(ref.key)
            newline = (
                "\r\n"
                if text[ref.span[0] : ref.span[1]].endswith("\r\n")
                else "\n"
                if text[ref.span[0] : ref.span[1]].endswith("\n")
                else ""
            )
            prefix = text[ref.span[0] : ref.span[1]].split("[", 1)[0]
            replacements.append(
                (
                    *ref.span,
                    prefix + _reference_definition_text(replacement, ref.label) + newline,
                )
            )
        else:
            # Inline a changed occurrence so unrelated references/images keep their URL.
            replacements.append((*occurrence.span, sub_string_link_md("", replacement)))
    return _apply_replacements(text, replacements)


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
    new_title = _markdown_title(title)
    return f"[{name}]({markdown_destination(new_url)}{new_title})"


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
    new_title = _markdown_title(title)
    return f"[{id_link}]: {markdown_destination(new_url)}{new_title}\n"


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
