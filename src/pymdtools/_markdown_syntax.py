"""Serialize parsed Markdown destinations and titles without changing their value."""

from html import escape
from urllib.parse import quote


def markdown_destination(url: str) -> str:
    """Protect delimiters, whitespace and entities in a parsed link destination."""
    encoded = escape(quote(url, safe="/:?#[]@!$&'()*+,;=%~"), quote=False)
    return f"<{encoded}>" if not encoded or "(" in encoded or ")" in encoded else encoded


def markdown_title(title: str | None) -> str:
    """Quote a parsed title, retaining literal backslashes, quotes and entities."""
    if title is None:
        return ""
    escaped = escape(title, quote=False).replace("\\", "\\\\").replace('"', '\\"')
    return f' "{escaped}"'
