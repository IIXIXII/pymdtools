#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                    Author: Florent TOURNOIS | License: MIT
# =============================================================================
"""
pymdtools.common.time_validate
==============================

Time and lightweight validation utilities for ``pymdtools.common``.

This module is the home of:
- Small **UTC time helpers** used for deterministic timestamps in logs/outputs.
- Small **validation helpers** used as invariants in calling code.

The functions in this file are reproduced **verbatim** from the historical
``common.py`` implementation (no refactor, no simplification), in order to keep
the exact behavior and output formats stable.

----------------------------------------------------------------------
Included functions
----------------------------------------------------------------------

UTC date/time helpers
~~~~~~~~~~~~~~~~~~~~~

today_utc() -> str
    Return today's date in UTC as the string ``YYYY-MM-DD``.

now_utc_timestamp() -> str
    Return the current UTC timestamp as the string ``YYYY-MM-DD HH:MM:SS`` (UTC).

parse_timestamp(value: str) -> datetime
    Parse a timestamp string into a ``datetime`` using ``python-dateutil``.
    The returned datetime is timezone-aware if the input includes timezone
    information; otherwise it is naive.


----------------------------------------------------------------------
Dependencies
----------------------------------------------------------------------

- Standard library:
    - datetime (UTC utilities)

- Optional third-party dependency:
    - python-dateutil (only used by ``parse_timestamp``)
      Imported lazily inside the function. If missing, an informative
      ``ImportError`` is raised.

----------------------------------------------------------------------
Examples
----------------------------------------------------------------------

    >>> from pymdtools.common import today_utc, now_utc_timestamp, parse_timestamp, check_len
    >>> today_utc()
    '2026-03-01'
    >>> now_utc_timestamp()
    '2026-03-01 21:05:12'
    >>> parse_timestamp("2026-03-01T12:34:56Z")
    datetime.datetime(2026, 3, 1, 12, 34, 56, tzinfo=tzutc())

"""

from __future__ import annotations

from datetime import datetime, timezone


# =============================================================================
# Time & Date utilities
# =============================================================================


# -----------------------------------------------------------------------------
def today_utc() -> str:
    """
    Return today's date in UTC as 'YYYY-MM-DD'.
    """
    return datetime.now(timezone.utc).date().isoformat()
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def now_utc_timestamp() -> str:
    """
    Return current UTC timestamp as 'YYYY-MM-DD HH:MM:SS' (UTC).
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def parse_timestamp(value: str) -> datetime:
    """
    Parse a timestamp string into a datetime.

    This function uses python-dateutil for flexible parsing.

    Args:
        value: Timestamp string.

    Returns:
        A datetime instance (timezone-aware if the input contains timezone
        information, otherwise naive).

    Raises:
        ValueError: If the timestamp cannot be parsed.
        ImportError: If python-dateutil is not installed.
    """
    try:
        from dateutil.parser import parse
    except ImportError as ex:
        raise ImportError("python-dateutil is required for parse_timestamp()") from ex

    return parse(value)
# -----------------------------------------------------------------------------


# =============================================================================