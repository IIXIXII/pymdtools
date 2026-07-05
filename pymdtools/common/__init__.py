#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                    Author: Florent TOURNOIS | License: MIT
# =============================================================================
"""
Shared utility layer for the pymdtools package.

This submodule provides a stable, public façade that aggregates
low-level helpers used across the project. The internal implementation
is split into several focused modules (core, fs, text, datetime_utils),
but consumers should import public helpers from this facade:

.. code-block:: python

    from pymdtools.common import slugify, get_file_content

The public API exposed here is considered stable. Internal submodules
are implementation details and may evolve without notice.

----------------------------------------------------------------------
Design principles
----------------------------------------------------------------------

- Clear separation of concerns:
    * core          : typing aliases, decorators, utility classes
    * fs            : filesystem and path operations
    * text          : string and filename transformations
    * datetime_utils : UTC date/time helpers

- Minimal dependencies:
    Optional third-party dependencies (e.g. chardet, dateutil,
    unidecode) are imported lazily in the functions that require them.

- Explicit API surface:
    The ``__all__`` variable defines the official public contract.

----------------------------------------------------------------------
Typing utilities
----------------------------------------------------------------------

T, F, P, R, T_sized
    Generic type variables used across the project.

PathInput
    Alias for ``str | os.PathLike[str] | pathlib.Path``.

----------------------------------------------------------------------
Core utilities
----------------------------------------------------------------------

handle_exception
    Decorator for enriching raised exceptions with contextual metadata.

static
    Decorator for attaching static-like attributes to a function.

Constant
    Descriptor for read-only instance-level constant values.

----------------------------------------------------------------------
Filesystem and path utilities
----------------------------------------------------------------------

Path helpers:
    to_path, normpath, with_suffix, path_depth

Filesystem checks:
    check_folder, ensure_folder, check_file

File operations:
    copytree, create_backup, make_temp_dir

Traversal:
    apply_to_files, ApplyResult, find_file

Introspection:
    get_this_filename

Binary detection:
    is_binary_file

Text file IO:
    detect_file_encoding
    get_file_content
    set_file_content

----------------------------------------------------------------------
Text utilities
----------------------------------------------------------------------

convert_for_stdout
    Safe conversion for stdout output.

to_ascii
    Unicode to ASCII transliteration (if unidecode is installed).

slugify
    URL-friendly slug generation.

get_valid_filename
    Sanitized filename generator.

get_flat_filename
    Flattened path string suitable for filenames.

path_to_url
    Convert filesystem path to POSIX-style URL path.

limit_str
    Truncate a string by whole separator-delimited tokens.

----------------------------------------------------------------------
Time and validation utilities
----------------------------------------------------------------------

today_utc
    Current UTC date as ``YYYY-MM-DD``.

now_utc_timestamp
    Current UTC timestamp as ``YYYY-MM-DD HH:MM:SS``.

parse_timestamp
    Flexible timestamp parsing (requires python-dateutil).

check_len
    Length validation helper.

----------------------------------------------------------------------
Usage example
----------------------------------------------------------------------

.. code-block:: python

    from pymdtools.common import slugify, get_file_content

    slug = slugify("My Title")
    content = get_file_content("README.md")
"""

# ---------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------

from .core import (
    T,
    F,
    P,
    R,
    T_sized,
    PathInput,
    handle_exception,
    static,
    Constant,
    check_len,
)

# ---------------------------------------------------------------------
# Filesystem
# ---------------------------------------------------------------------

from .fs import (
    to_path,
    normpath,
    with_suffix,
    path_depth,
    check_folder,
    ensure_folder,
    check_file,
    copytree,
    create_backup,
    make_temp_dir,
    apply_to_files,
    ApplyResult,
    find_file,
    get_this_filename,
    is_binary_file,
    detect_file_encoding,
    get_file_content,
    set_file_content,
)

# ---------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------

from .text import (
    convert_for_stdout,
    to_ascii,
    slugify,
    get_valid_filename,
    get_flat_filename,
    path_to_url,
    limit_str,
)

# ---------------------------------------------------------------------
# Time and validation
# ---------------------------------------------------------------------

from .datetime_utils import (
    today_utc,
    now_utc_timestamp,
    parse_timestamp,
)

# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------

__all__ = [
    # Typing
    "T",
    "F",
    "P",
    "R",
    "T_sized",
    "PathInput",

    # Core
    "handle_exception",
    "static",
    "Constant",
    "check_len",

    # Filesystem / path
    "to_path",
    "normpath",
    "with_suffix",
    "path_depth",
    "check_folder",
    "ensure_folder",
    "check_file",
    "copytree",
    "create_backup",
    "make_temp_dir",
    "apply_to_files",
    "ApplyResult",
    "find_file",
    "get_this_filename",
    "is_binary_file",
    "detect_file_encoding",
    "get_file_content",
    "set_file_content",

    # Text
    "convert_for_stdout",
    "to_ascii",
    "slugify",
    "get_valid_filename",
    "get_flat_filename",
    "path_to_url",
    "limit_str",

    # Time / validation
    "today_utc",
    "now_utc_timestamp",
    "parse_timestamp",
]


# =============================================================================
