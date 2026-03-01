#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                    Author: Florent TOURNOIS | License: MIT
# =============================================================================
"""
pymdtools.common.text
=====================

Text utilities for ``pymdtools.common``.

This module contains *pure* text transformation helpers originally implemented
in the historical ``common.py`` file. The implementations below are preserved
**verbatim** (no behavior changes, no simplification) to ensure backward
compatibility.

Scope
-----
Included here:

- ``convert_for_stdout``:
    Encode/decode round-trip to adapt a Unicode string to a stream encoding.

- ``to_ascii``:
    Unicode → ASCII transliteration using the third-party ``Unidecode`` package.
    (The dependency is required; an informative ``ImportError`` is raised if
    missing.)

- ``slugify``:
    Convert an arbitrary value to a URL- and filename-safe slug:
    normalization, optional Unicode preservation, stripping invalid characters,
    collapse whitespace/hyphens, lowercase.

- Windows-safe filename helpers:
    - ``get_valid_filename``: sanitize an input filename for Windows
      (invalid characters, control chars, trailing dots/spaces, reserved names).
    - ``get_flat_filename``: ASCII transliteration + slug-like normalization
      and final Windows-safe validation.

- ``path_to_url``:
    Convert a filesystem path to a URL-safe path:
    normalize separators, lowercase, whitespace to hyphen, optional accent
    removal, percent-encode.

- ``limit_str``:
    Truncate a string by keeping whole tokens separated by a given separator
    without exceeding a maximum length.

Public API
----------
Symbols are re-exported by ``pymdtools.common`` (package façade). This module is
an implementation unit, but its exported functions are considered part of the
public contract through the façade.

Dependencies
------------
- Standard library only, except:
  - ``to_ascii`` requires ``Unidecode`` at runtime.

Notes
-----
- The code is intentionally *not refactored* here (including stylistic choices),
  to preserve behavior exactly as in ``common.py``.
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Optional, TextIO
from urllib.parse import quote


# =============================================================================
# Text & Encoding utilities
# =============================================================================


# -----------------------------------------------------------------------------
def convert_for_stdout(
    text: str,
    *,
    stream: TextIO = sys.stdout,
    fallback_encoding: str = "utf-8",
    errors: str = "replace",
) -> str:
    """
    Adapt a Unicode string to the encoding of the given text stream.

    Parameters
    ----------
    text : str
        Input Unicode string.
    stream : TextIO, default=sys.stdout
        Target output stream. Its `.encoding` attribute is used when available.
    fallback_encoding : str, default="utf-8"
        Encoding used if the stream has no encoding.
    errors : str, default="replace"
        Error handler used for the encode/decode round-trip.

    Returns
    -------
    str
        Text safe to print to the given stream.
    """
    enc: Optional[str] = getattr(stream, "encoding", None)
    encoding = enc or fallback_encoding

    try:
        return text.encode(encoding, errors=errors).decode(encoding, errors=errors)
    except LookupError:
        return text.encode(fallback_encoding, errors="replace").decode(fallback_encoding)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def to_ascii(value: str) -> str:
    """
    Transliterate a Unicode string to an ASCII approximation.

    This function uses the third-party package `Unidecode` to convert
    non-ASCII characters to an ASCII representation.

    Args:
        value: Input Unicode string.

    Returns:
        An ASCII transliteration of the input string.

    Raises:
        ImportError: If the Unidecode package is not installed.
    """
    try:
        from unidecode import unidecode
    except ImportError as exc:
        raise ImportError("Unidecode is required for to_ascii()") from exc

    return unidecode(value)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def slugify(value: Any, *, allow_unicode: bool = False) -> str:
    """
    Convert a string to a URL- and filename-safe slug.

    The function:
    - converts the input to string,
    - optionally normalizes Unicode characters,
    - removes characters that are not alphanumeric, underscores, spaces or hyphens,
    - converts spaces and repeated hyphens to single hyphens,
    - lowercases the result.

    Args:
        value: Input value to slugify.
        allow_unicode: If True, keep Unicode characters.
            If False, transliterate to ASCII.

    Returns:
        A slugified string (lowercase, hyphen-separated).
    """
    text = str(value)

    if allow_unicode:
        # Normalize Unicode (canonical composition)
        text = unicodedata.normalize("NFKC", text)
    else:
        # Normalize + transliterate to ASCII
        text = unicodedata.normalize("NFKD", text)
        text = to_ascii(text)

    # Remove invalid characters (keep alphanumerics, underscore, space, hyphen)
    text = re.sub(r"[^\w\s-]", "", text)

    # Normalize whitespace / hyphens, lowercase
    text = re.sub(r"[-\s]+", "-", text).strip("-").lower()

    return text
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# Windows reserved filenames (case-insensitive)
_WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}

def get_valid_filename(
    filename: str,
    *,
    replacement: str = "_",
    strip: bool = True,
) -> str:
    """
    Return a filename safe for Windows filesystems.

    This function:
    - replaces invalid Windows filename characters,
    - trims leading/trailing whitespace,
    - removes trailing dots and spaces,
    - avoids Windows reserved names.

    Args:
        filename: Input filename (not a full path).
        replacement: Character used to replace invalid characters.
        strip: Whether to strip leading/trailing whitespace.

    Returns:
        A Windows-safe filename.

    Raises:
        ValueError: If filename is empty after sanitization.
    """
    name = filename

    if strip:
        name = name.strip()

    # Replace invalid Windows characters
    name = re.sub(r'[\\/*?:"<>|]', replacement, name)

    # Remove control characters (0x00–0x1F)
    name = re.sub(r"[\x00-\x1F]", replacement, name)

    # Remove trailing dots and spaces (invalid on Windows)
    name = name.rstrip(" .")

    if not name:
        raise ValueError("filename is empty after sanitization")

    # Handle reserved device names (Windows)
    stem, dot, suffix = name.partition(".")
    if stem.upper() in _WINDOWS_RESERVED_NAMES:
        stem = f"{stem}{replacement}"
        name = stem + (dot + suffix if dot else "")

    return name
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def get_flat_filename(filename: str, *, replacement: str = "_") -> str:
    """
    Return a flattened, Windows-safe filename.

    This function:
    - transliterates Unicode characters to ASCII,
    - removes punctuation and special characters,
    - replaces spaces and separators with a single replacement character,
    - ensures the result is a valid Windows filename.

    Args:
        filename: Input filename (without path).
        replacement: Character used to replace separators (default: "_").

    Returns:
        A flattened, Windows-safe filename.

    Raises:
        ValueError: If filename is empty after sanitization.
    """
    # Step 1: ASCII transliteration
    text = to_ascii(filename)

    # Step 2: slug-like normalization, but keep underscores instead of hyphens
    text = slugify(text, allow_unicode=False).replace("-", replacement)

    # Step 3: final Windows-safe validation
    return get_valid_filename(text, replacement=replacement)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def path_to_url(path: str | Path, *, remove_accent: bool = True) -> str:
    """
    Convert a filesystem path to a URL-safe path.

    The function:
    - normalizes path separators,
    - lowercases the path,
    - replaces whitespace with hyphens,
    - optionally transliterates Unicode characters to ASCII,
    - percent-encodes characters for safe use in URLs.

    Args:
        path: Input path (string or Path).
        remove_accent: If True, transliterate Unicode characters to ASCII.

    Returns:
        A URL-safe path string.
    """
    # Convert to POSIX-style path (forward slashes)
    p = Path(path)
    text = p.as_posix()

    # Normalize case
    text = text.lower()

    # Replace whitespace by hyphen
    text = re.sub(r"\s+", "-", text)

    # Optional transliteration
    if remove_accent:
        text = to_ascii(text)

    # Percent-encode (keep '/' as path separator)
    text = quote(text, safe="/")

    # Cleanup accidental "/-" or "-/" sequences
    text = text.replace("/-", "/").replace("-/", "/")

    return text
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
def limit_str(value: str, limit: int, sep: str, min_last_word: int = 2) -> str:
    """
    Limit a string by keeping whole tokens separated by `sep`, without exceeding `limit`.

    The string is split on `sep`. Tokens are appended in order, re-joined with `sep`,
    as long as the resulting string length does not exceed `limit`.

    Args:
        value: Input text.
        limit: Maximum length of the returned string (must be >= 0).
        sep: Token separator used to split and re-join.
        min_last_word: Minimum token length to be considered meaningful (>= 0).
            Tokens shorter than this value are ignored unless already included as
            part of the kept prefix.

    Returns:
        A shortened string not exceeding `limit`.

    Raises:
        ValueError: If `limit` < 0, `min_last_word` < 0, or `sep` is empty.
    """
    if limit < 0:
        raise ValueError(f"limit must be >= 0, got: {limit}")
    if min_last_word < 0:
        raise ValueError(f"min_last_word must be >= 0, got: {min_last_word}")
    if not sep:
        raise ValueError("sep must be a non-empty string")

    if not value or limit == 0:
        return ""

    tokens = value.split(sep)
    kept: list[str] = []

    for token in tokens:
        if token == "":
            # avoid growing output with empty tokens (e.g. consecutive seps)
            continue
        if len(token) < min_last_word:
            continue

        candidate = token if not kept else f"{sep.join(kept)}{sep}{token}"
        if len(candidate) <= limit:
            kept.append(token)
        else:
            break

    return sep.join(kept)
# -----------------------------------------------------------------------------


# =============================================================================