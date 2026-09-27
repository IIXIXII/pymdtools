"""CommonMark parsing with source positions shared by document transformations.

Only this adapter depends on markdown-it's rule API. Offsets always refer to the
original input, including CRLF and container prefixes. Reference definitions
immediately following a paragraph remain supported for historical documents.
"""

from __future__ import annotations

import re
from bisect import bisect_right
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, cast

from markdown_it import MarkdownIt
from markdown_it.common.utils import normalizeReference
from markdown_it.rules_inline import backtick, link
from markdown_it.rules_inline.state_inline import StateInline
from markdown_it.token import Token

Span = tuple[int, int]


def merge_ranges(ranges: Sequence[Span]) -> list[Span]:
    """Merge overlapping or adjacent intervals."""
    result: list[Span] = []
    for start, end in sorted(ranges):
        if start >= end:
            continue
        if result and start <= result[-1][1]:
            result[-1] = (result[-1][0], max(end, result[-1][1]))
        else:
            result.append((start, end))
    return result


def position_in_ranges(index: int, ranges: Sequence[Span]) -> bool:
    """Find a position in sorted, disjoint intervals in logarithmic time."""
    at = bisect_right(ranges, (index, float("inf"))) - 1
    return at >= 0 and index < ranges[at][1]


def _track(
    rule: Callable[[StateInline, bool], bool], kind: str
) -> Callable[[StateInline, bool], bool]:
    def tracked(state: StateInline, silent: bool) -> bool:
        start, count = state.pos, len(state.tokens)
        matched = rule(state, silent)
        if matched and not silent:
            for token in state.tokens[count:]:
                if token.type == kind and "source_span" not in token.meta:
                    token.meta["source_span"] = (start, state.pos)
                    if kind == "link_open":
                        label_end = state.md.helpers.parseLinkLabel(state, start, True)
                        token.meta["source_name"] = state.src[start + 1 : label_end]
                    break
        return matched

    return tracked


def parser() -> MarkdownIt:
    """Create an independent parser; mutable parse state is never shared."""
    md = MarkdownIt("commonmark", {"store_labels": True, "inline_definitions": True})
    md.inline.ruler.at("backticks", _track(backtick, "code_inline"))
    md.inline.ruler.at("link", _track(link, "link_open"))
    return md


@dataclass(frozen=True)
class Reference:
    key: str
    label: str
    url: str
    title: str | None
    span: Span
    line: int


@dataclass(frozen=True)
class LinkSpan:
    name: str
    url: str
    title: str | None
    span: Span
    line: int
    reference: Reference | None = None


@dataclass
class Document:
    code_ranges: list[Span] = field(default_factory=lambda: [])
    links: list[LinkSpan] = field(default_factory=lambda: [])
    references: dict[str, Reference] = field(default_factory=lambda: {})
    image_references: set[str] = field(default_factory=lambda: set())


def _normalized_source(text: str) -> tuple[str, list[int]]:
    chars: list[str] = []
    offsets: list[int] = []
    for match in re.finditer(r"\r\n?|[^\r]", text):
        chars.append("\n" if match[0].startswith("\r") else match[0].replace("\0", "\ufffd"))
        offsets.append(match.start())
    offsets.append(len(text))
    return "".join(chars), offsets


def _inline_offsets(token: Token, lines: list[str], starts: list[int]) -> list[int]:
    """Align inline content with source lines after list/quote prefixes."""
    assert token.map is not None
    result: list[int] = []
    line_no = token.map[0]
    for part in token.content.split("\n"):
        while line_no < token.map[1]:
            at = lines[line_no].find(part)
            if at >= 0:
                result.extend(range(starts[line_no] + at, starts[line_no] + at + len(part)))
                result.append(starts[line_no] + len(lines[line_no].rstrip("\n")))
                line_no += 1
                break
            line_no += 1
        else:
            # Tabs expanded by the block parser cannot always be mapped back.
            # Fail closed: the caller protects this block from source edits.
            return []
    return result


def parse_document(text: str) -> Document:
    """Read code spans, links and definitions without reconstructing Markdown."""
    source, original = _normalized_source(text)
    # CommonMark recognizes LF, not Unicode line separators.
    parts = source.split("\n")
    lines = [line + "\n" for line in parts[:-1]] + [parts[-1]]
    starts = [0]
    for line_text in lines:
        starts.append(starts[-1] + len(line_text))
    md = parser()
    env: dict[str, Any] = {}
    tokens = md.parse(source, env)
    document = Document()

    def block_span(token: Token) -> Span:
        assert token.map is not None
        return original[starts[token.map[0]]], original[starts[token.map[1]]]

    inline_blocks: list[tuple[Token, list[int]]] = []
    for token in tokens:
        if token.type in ("fence", "code_block"):
            document.code_ranges.append(block_span(token))
        elif token.type == "inline" and token.map is not None:
            offsets = _inline_offsets(token, lines, starts)
            if not offsets:
                document.code_ranges.append(block_span(token))
                continue
            inline_blocks.append((token, offsets))
            # Exclude definitions inside multiline inline code before applying
            # the historical adjacent-definition extension below.
            for child in token.children or []:
                if child.type == "code_inline":
                    begin, end = cast(Span, child.meta["source_span"])
                    document.code_ranges.append(
                        (original[offsets[begin]], original[offsets[end - 1] + 1])
                    )

    # Preserve the historical conservative treatment of indented examples.
    document.code_ranges.extend(
        (original[m.start()], original[m.end()])
        for m in re.finditer(r"(?m)^(?: {4}|\t)[^\n]*(?:\n|$)", source)
    )
    document.code_ranges = merge_ranges(document.code_ranges)

    # CommonMark definitions, plus the documented adjacent-definition extension.
    definitions = [token for token in tokens if token.type == "definition"]
    for match in re.finditer(r"(?m)^ {0,3}\[[^\]\n]+\]:[^\n]*(?:\n|$)", source):
        if position_in_ranges(original[match.start()], document.code_ranges):
            continue
        parsed = md.parse(match[0], {})
        if parsed and parsed[0].type == "definition":
            token = parsed[0]
            line_no = bisect_right(starts, match.start()) - 1
            token.map = [line_no, line_no + 1]
            definitions.append(token)
    for token in sorted(definitions, key=lambda t: (t.map or [0])[0]):
        assert token.map is not None
        label = str(token.meta["label"])
        key = normalizeReference(label)
        document.references.setdefault(
            key,
            Reference(
                key,
                label,
                str(token.meta["url"]),
                str(token.meta["title"]) or None,
                block_span(token),
                token.map[0] + 1,
            ),
        )
    env["references"] = {
        key: {"href": ref.url, "title": ref.title or "", "map": [ref.line - 1, ref.line]}
        for key, ref in document.references.items()
    }
    definition_ranges = merge_ranges([ref.span for ref in document.references.values()])

    for token, offsets in inline_blocks:
        children: list[Token] = []
        md.inline.parse(token.content, md, env, children)
        for child in children:
            if child.type == "image" and "label" in child.meta:
                document.image_references.add(str(child.meta["label"]))
            raw_span = child.meta.get("source_span")
            if raw_span is None:
                continue
            begin, end = cast(Span, raw_span)
            span = (original[offsets[begin]], original[offsets[end - 1] + 1])
            if child.type == "code_inline":
                document.code_ranges.append(span)
            elif child.type == "link_open" and not position_in_ranges(span[0], definition_ranges):
                ref = document.references.get(str(child.meta.get("label", "")))
                document.links.append(
                    LinkSpan(
                        str(child.meta["source_name"]),
                        str(child.attrGet("href") or ""),
                        cast(str | None, child.attrGet("title")),
                        span,
                        ref.line if ref else bisect_right(starts, offsets[begin]),
                        ref,
                    )
                )
    document.code_ranges = merge_ranges(document.code_ranges)
    document.links = [
        link
        for link in document.links
        if not position_in_ranges(link.span[0], document.code_ranges)
    ]
    return document


def markdown_code_ranges(text: str) -> list[Span]:
    """Locate fenced, indented and inline code, including nested containers."""
    return parse_document(text).code_ranges
