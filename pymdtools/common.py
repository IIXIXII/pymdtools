#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                    Author: Florent TOURNOIS | License: MIT                   
# =============================================================================
"""
pymdtools.common
================

This module provides a consolidated collection of low-level utility functions
used throughout pymdtools. For simplicity and readability, all utilities are
kept in a single file, but are explicitly structured into clearly delimited
sections reflecting their functional domain.

The module is intentionally free of backward-compatibility wrappers: the public
API corresponds exactly to the functions and classes defined below.

Design principles
-----------------
- Explicit and predictable behavior: each function has a single, well-defined
  responsibility.
- Preference for standard library primitives (`pathlib`, `datetime`, `tempfile`)
  over custom implementations.
- No implicit global state and no mandatory logging inside utility functions.
- Use of standard Python exception types whenever possible.
- Optional third-party dependencies are imported locally to keep module import
  lightweight and robust.

Structure of the module
-----------------------

Core helpers (exceptions, decorators, lightweight utilities)
-------------------------------------------------------------
Utilities that do not belong to a specific functional domain but are reused
across the codebase.

- `handle_exception` : exception handling helper/decorator.
- `Constant` : lightweight constant holder / descriptor.
- `static` : decorator to attach static attributes to functions.

Filesystem & Path utilities
----------------------------
Helpers related to filesystem access, path manipulation, file traversal,
and file I/O.

- Path normalization and validation:
    - `normpath`
    - `check_folder`
    - `ensure_folder`
    - `check_file`
    - `path_depth`
- Filename and suffix handling:
    - `with_suffix`
- Directory tree operations:
    - `copytree`
- Backup and file-type detection:
    - `create_backup`
    - `is_binary_file`
- Encoding detection and text file I/O:
    - `detect_file_encoding`
    - `get_file_content`
    - `set_file_content`
- Temporary directories:
    - `make_temp_dir`
- File traversal and search:
    - `apply_to_files`
    - `find_file`
    - `get_this_filename`

Text & Encoding utilities
-------------------------
Helpers for string normalization, naming, and encoding-safe transformations.

- Output encoding adaptation:
    - `convert_for_stdout`
- Unicode and naming helpers:
    - `to_ascii`
    - `slugify`
    - `get_valid_filename`
    - `get_flat_filename`
- URL-safe path generation:
    - `path_to_url`
- Controlled string truncation:
    - `limit_str`

Time & Date utilities
---------------------
Helpers for generating and parsing timestamps, standardized on UTC.

- Date and timestamp generation:
    - `today_utc`
    - `now_utc_timestamp`
- Timestamp parsing:
    - `parse_timestamp`

Validation helpers
------------------
Small invariant checks used to enforce assumptions in calling code.

- `check_len`

Optional dependencies
---------------------
The module relies primarily on the Python standard library. Some functions use
optional third-party dependencies, imported locally:

- `python-dateutil` for flexible timestamp parsing (`parse_timestamp`).
- `chardet` for text encoding detection (`detect_file_encoding`).
- `Unidecode` for Unicode transliteration (`to_ascii`).

If these dependencies are not installed, the corresponding functions raise
`ImportError` with an explicit message.

Usage
-----
Functions from this module are intended to be imported and used directly:

    from pymdtools.common import (
        get_file_content,
        set_file_content,
        slugify,
        get_valid_filename,
        find_file,
    )

This module acts as a low-level utility layer and does not implement
application-level logging or user interaction.
"""


from __future__ import annotations

# Standard library
import codecs
import functools
import logging
import os
from os import PathLike
import re
import shutil
import sys
import tempfile
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path
from typing import (
    Any, Callable, Generic, Iterable, List, Optional, Sequence, 
    Set, TypeVar, Union, Sized, 
)
from urllib.parse import quote


# =============================================================================
# Core helpers (exceptions, decorators, lightweight utilities)
# =============================================================================


# -----------------------------------------------------------------------------
PathInput = Union[str, PathLike[str], Path]
def to_path(
    p: PathInput,
    *,
    expand_user: bool = True,
    resolve: bool = False,
    strict: bool = False,
) -> Path:
    """
    Convert a path-like input to a pathlib.Path instance.

    This helper standardizes path handling across the module.
    It guarantees that all internal path manipulations operate
    on `pathlib.Path` objects.

    Parameters
    ----------
    p : str | os.PathLike[str] | Path
        Input path. Can be:
        - A string path
        - Any os.PathLike object
        - A pathlib.Path instance

    expand_user : bool, default=True
        If True, expands '~' to the user home directory using
        Path.expanduser().

    resolve : bool, default=False
        If True, resolves the path using Path.resolve().

        This will:
        - Normalize the path (remove '..', '.')
        - Follow symbolic links (unless strict=False and target missing)

    strict : bool, default=False
        Only used if resolve=True.

        - If True, raises FileNotFoundError if the path does not exist.
        - If False, resolves as much as possible without requiring existence.

    Returns
    -------
    Path
        A pathlib.Path object.

    Notes
    -----
    - This function does NOT implicitly resolve paths unless `resolve=True`.
      This avoids surprising behavior with symlinks or non-existing paths.
    - Most library-level functions should call:
          p = to_path(path)
      without resolve=True.
    - Use resolve=True only when canonicalization is explicitly required.

    Examples
    --------
    >>> to_path("~/.config")
    PosixPath('/home/user/.config')

    >>> to_path("file.txt", resolve=True)
    PosixPath('/current/dir/file.txt')

    >>> to_path("missing.txt", resolve=True, strict=True)
    FileNotFoundError
    """
    if isinstance(p, Path):
        path = p
    else:
        path = Path(p)

    if expand_user:
        path = path.expanduser()

    if resolve:
        path = path.resolve(strict=strict)

    return path
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def _p(p: PathInput) -> Path:
    """
    Internal shorthand for `to_path`.

    This helper ensures that all path manipulations inside the module
    operate on `pathlib.Path` objects.

    It applies the module defaults:
    - expand_user=True
    - resolve=False
    - strict=False

    Parameters
    ----------
    p : str | os.PathLike[str] | Path
        Input path.

    Returns
    -------
    Path
        A pathlib.Path instance.
    """
    return to_path(p)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def handle_exception(action_desc: str, **kwargs_print_name: str) -> Callable:
    """
    Decorator used to enrich exceptions with contextual information.

    This decorator catches any exception raised by the decorated function,
    enriches the error message with a functional description and selected
    keyword arguments, then re-raises a new exception while preserving the
    original traceback using exception chaining.

    The original exception is accessible through the ``__cause__`` attribute.

    Args:
        action_desc: Human-readable description of the action being performed
            (e.g. "Error while processing markdown file").
        **kwargs_print_name: Mapping between keyword argument names of the
            decorated function and their display labels to include in the
            error message.
            Example: filename="File", output_dir="Output directory".

    Returns:
        A decorator wrapping the target function.

    Raises:
        RuntimeError: Raised when the decorated function fails. The original
        exception is attached as the cause.

    Example:
        >>> @handle_exception(
        ...     "Error while converting file",
        ...     filename="File",
        ...     output="Output directory"
        ... )
        ... def convert(filename: str, output: str):
        ...     raise ValueError("Invalid format")
        ...
        >>> convert("doc.md", "/tmp")
        RuntimeError: Invalid format
        Error while converting file (convert)
        File : doc.md
        Output directory : /tmp
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as ex:
                lines = [f"{action_desc} ({func.__name__})"]
                for key, label in kwargs_print_name.items():
                    if key in kwargs:
                        lines.append(f"{label} : {kwargs[key]}")
                message = "\n".join(lines)
                raise RuntimeError(f"{ex}\n{message}") from ex

        return wrapper

    return decorator
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
T = TypeVar("T")
class Constant(Generic[T]):
    """
    Descriptor representing an immutable constant value.

    This class is intended to be used as a *class attribute* and provides
    read-only access to a fixed value through both the class and its instances.

    The constant value cannot be modified or deleted **via an instance**.
    Any attempt to assign or delete the attribute on an instance will raise
    a `ValueError`.

    Note:
        Assignment at the *class level* (e.g. ``MyClass.CONST = ...``) is not
        prevented. This is a limitation of Python descriptors and is considered
        acceptable by design. Preventing class-level reassignment would require
        a metaclass or custom `__setattr__` logic on the owning class.

    Example:
        class Config:
            VERSION = Constant("1.0")
            DEBUG = Constant(False)

        Config.VERSION        # "1.0"
        Config().VERSION      # "1.0"

        Config().VERSION = "2.0"
        # ValueError: You can't change a constant value

        Config.VERSION = "2.0"
        # Allowed: the descriptor is replaced at the class level
    """

    def __init__(self, value: Optional[T] = None):
        self._value = value

    def __get__(self, instance: Any, owner: Any) -> Optional[T]:
        return self._value

    def __set__(self, instance: Any, value: Any) -> None:
        raise ValueError("You can't change a constant value")
    
    def __delete__(self, instance: Any) -> None:
        raise ValueError("Cannot delete a constant value")

    @property
    def value(self) -> Optional[T]:
        """Return the constant value."""
        return self._value
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
F = TypeVar("F", bound=Callable[..., Any])
def static(**attributes: Any) -> Callable[[F], F]:
    """
    Attach static attributes to a function.

    This decorator sets attributes on the decorated function object. It is
    typically used to emulate "static variables" inside a function, i.e. to
    keep state across calls without using globals.

    Args:
        **attributes: Attribute names and their initial values to attach to the
            function.

    Returns:
        A decorator that returns the same function with attributes set.

    Example:
        >>> @static(counter=0)
        ... def f():
        ...     f.counter += 1
        ...     return f.counter
        ...
        >>> f()
        1
        >>> f()
        2
    """
    def decorator(func: F) -> F:
        for key, value in attributes.items():
            setattr(func, key, value)
        return func

    return decorator
# -----------------------------------------------------------------------------


# =============================================================================
# Filesystem & Path utilities
# =============================================================================


# -----------------------------------------------------------------------------
def normpath(path: PathInput) -> Path:
    """
    Return a normalized absolute Path.

    This function:
    - Converts the input to a pathlib.Path
    - Expands '~'
    - Resolves '.' and '..'
    - Returns an absolute path

    It does NOT require the path to exist.

    Parameters
    ----------
    path : str | os.PathLike[str] | Path
        Input path.

    Returns
    -------
    Path
        A normalized absolute Path object.
    """
    return to_path(path, resolve=True, strict=False)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def check_folder(path: PathInput) -> Path:
    """
    Validate that `path` exists and is a directory.

    Parameters
    ----------
    path : str | os.PathLike[str] | Path
        Input directory path.

    Returns
    -------
    Path
        Normalized absolute directory path.

    Raises
    ------
    FileNotFoundError
        If the path does not exist.
    NotADirectoryError
        If the path exists but is not a directory.
    """
    p = normpath(path)

    if not p.exists():
        raise FileNotFoundError(f"Folder does not exist: {p}")

    if not p.is_dir():
        raise NotADirectoryError(f"Not a folder: {p}")

    return p
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def ensure_folder(path: PathInput) -> Path:
    """
    Ensure that a directory exists.

    If the directory does not exist, it is created (including parents).
    If it already exists, nothing is done.

    Parameters
    ----------
    path : str | os.PathLike[str] | Path
        Target directory path.

    Returns
    -------
    Path
        Normalized absolute directory path.

    Raises
    ------
    NotADirectoryError
        If the path exists but is not a directory.
    OSError
        If directory creation fails.
    """
    p = normpath(path)

    if p.exists():
        if not p.is_dir():
            raise NotADirectoryError(f"Path exists but is not a directory: {p}")
        return p

    p.mkdir(parents=True, exist_ok=True)
    return p
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def check_file(
    path: PathInput, 
    expected_ext: str | tuple[str, ...] | None = None
) -> Path:
    """
    Validate that `path` exists and is a regular file, 
    optionally enforcing an extension.

    Parameters
    ----------
    path : str | os.PathLike[str] | Path
        Input file path.
    expected_ext : str | tuple[str, ...] | None, default=None
        Expected file extension(s). Examples:
        - ".md"
        - "md"
        - (".md", ".markdown")
        If None, no extension check is performed.

    Returns
    -------
    Path
        Normalized absolute file path.

    Raises
    ------
    FileNotFoundError
        If the path does not exist.
    IsADirectoryError
        If the path exists but is not a regular file.
    ValueError
        If `expected_ext` is provided and 
        the file extension does not match.
    """
    p = normpath(path)

    if not p.exists():
        raise FileNotFoundError(f"File does not exist: {p}")

    if not p.is_file():
        raise IsADirectoryError(f"Not a regular file: {p}")

    if expected_ext is not None:
        exts = (expected_ext,) if isinstance(expected_ext, str) else expected_ext
        normalized = tuple(e.lower() if e.startswith(".") else f".{e.lower()}" for e in exts)
        if p.suffix.lower() not in normalized:
            raise ValueError(
                f"Unexpected file extension for {p}: got {p.suffix!r}, expected one of {normalized}"
            )

    return p
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def with_suffix(path: PathInput, suffix: str) -> Path:
    """
    Return a new Path with a modified file suffix.

    Parameters
    ----------
    path : str | os.PathLike[str] | Path
        Input file path.
    suffix : str
        New file extension (with or without leading dot).
        Examples:
        - ".html"
        - "html"

    Returns
    -------
    Path
        Path with updated suffix.

    Raises
    ------
    ValueError
        If suffix is empty or invalid.
    """
    if not suffix:
        raise ValueError("Suffix must not be empty.")

    p = _p(path)

    # Normalize suffix format
    if not suffix.startswith("."):
        suffix = f".{suffix}"

    return p.with_suffix(suffix)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def path_depth(path: PathInput) -> int:
    """
    Return the depth of a filesystem path.

    The depth is defined as the number of directory components.
    If the path appears to reference a file (has a suffix),
    the last component is ignored.

    This function does not access the filesystem.

    Parameters
    ----------
    path : str | os.PathLike[str] | Path
        Filesystem path (absolute or relative).

    Returns
    -------
    int
        Number of directory levels in the path.
    """
    p = _p(path)

    # Ignore file name if it has a suffix
    if p.suffix:
        p = p.parent

    # Remove anchor (e.g. "/" or "C:\\")
    if p.anchor:
        parts = p.parts[1:]
    else:
        parts = p.parts

    return len(parts)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def copytree(
    src: PathInput,
    dst: PathInput,
    *,
    symlinks: bool = False,
    ignore: Optional[Callable[[str, list[str]], Iterable[str]]] = None,
) -> Path:
    """
    Copy a directory tree from *src* to *dst* (incremental, dirs_exist_ok=True).

    - Creates destination directories as needed
    - Recursively copies files
    - Supports an ``ignore`` callable compatible with shutil.copytree
    - Optionally preserves symlinks when ``symlinks=True``
    - Copies a file only if destination missing, sizes differ, or source is newer

    Parameters
    ----------
    src : str | os.PathLike[str] | Path
        Source directory path.
    dst : str | os.PathLike[str] | Path
        Destination directory path (created if missing).
    symlinks : bool, default=False
        If True, copy symlinks as symlinks. If False, follow symlinks and copy
        target content.
    ignore : callable | None, default=None
        Callable with signature ``ignore(dirpath, names) -> iterable`` returning
        the names to ignore in *dirpath* (same contract as shutil.copytree).

    Returns
    -------
    Path
        Destination directory path.

    Raises
    ------
    FileNotFoundError
        If *src* does not exist.
    NotADirectoryError
        If *src* is not a directory.
    OSError
        For underlying filesystem errors.
    """
    src_p = _p(src)
    dst_p = _p(dst)

    if not src_p.exists():
        raise FileNotFoundError(f"Source folder does not exist: {src_p}")
    if not src_p.is_dir():
        raise NotADirectoryError(f"Source is not a directory: {src_p}")

    dst_p.mkdir(parents=True, exist_ok=True)

    names = [p.name for p in src_p.iterdir()]
    ignored: Set[str] = set(ignore(str(src_p), names)) if ignore else set()

    for name in names:
        if name in ignored:
            continue

        source = src_p / name
        destin = dst_p / name

        # Symlink handling
        if source.is_symlink():
            if symlinks:
                # Copy link itself
                if destin.exists() or destin.is_symlink():
                    if destin.is_dir() and not destin.is_symlink():
                        shutil.rmtree(destin)
                    else:
                        destin.unlink()

                link_target = source.readlink()
                destin.symlink_to(link_target)
            else:
                # Follow link: copy target content (may recurse into target dir)
                if source.is_dir():
                    copytree(source, destin, symlinks=symlinks, ignore=ignore)
                else:
                    _copy_file_if_needed(source, destin)
            continue

        if source.is_dir():
            copytree(source, destin, symlinks=symlinks, ignore=ignore)
        else:
            _copy_file_if_needed(source, destin)

    return dst_p

def _copy_file_if_needed(source: PathInput, destination: PathInput) -> Path:
    src = _p(source)
    dst = _p(destination)

    dst.parent.mkdir(parents=True, exist_ok=True)

    if not dst.exists():
        shutil.copy2(src, dst)
        return dst

    s = src.stat()
    d = dst.stat()

    if s.st_size != d.st_size or s.st_mtime > d.st_mtime:
        shutil.copy2(src, dst)

    return dst
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def create_backup(
    file_path: PathInput,
    *,
    ext: str = ".bak",
    max_tries: int = 100,
    date_prefix: str | None = None,
) -> Path:
    """
    Create a backup copy of a file next to it.

    The backup name is built as:
        <original_name>.<YYYY-MM-DD>-<N><ext>

    Example:
        report.md -> report.md.2026-02-27-1.bak

    Parameters
    ----------
    file_path : str | os.PathLike[str] | Path
        Source file to back up.
    ext : str, default=".bak"
        Backup extension (with or without leading dot).
    max_tries : int, default=100
        Maximum number of candidate names to try before failing.
    date_prefix : str | None, default=None
        Optional override for the date prefix (format not enforced).
        If None, uses today_utc() from your module.

    Returns
    -------
    Path
        Path to the created backup file.

    Raises
    ------
    FileNotFoundError
        If the source file does not exist.
    IsADirectoryError
        If the source path is not a regular file.
    ValueError
        If ext is empty or max_tries is not positive.
    FileExistsError
        If no available backup filename is found within max_tries.
    """
    src = check_file(file_path)  # uses normpath + existence/type checks

    if not ext:
        raise ValueError("ext must not be empty")
    if max_tries <= 0:
        raise ValueError("max_tries must be > 0")

    # Normalize ext format
    if not ext.startswith("."):
        ext = f".{ext}"

    # Date prefix: keep your existing convention
    prefix = date_prefix if date_prefix is not None else today_utc()  # e.g. "2026-02-27"

    # Compose candidates in the same folder
    # Keep the original full name (including suffix) to preserve semantics
    base = src.name  # e.g. "report.md"
    folder = src.parent

    for i in range(1, max_tries + 1):
        backup = folder / f"{base}.{prefix}-{i:03d}{ext}"
        if not backup.exists():
            shutil.copy2(src, backup)
            return backup

    raise FileExistsError(
        f"Unable to find available backup filename for {src} after {max_tries} tries "
        f"(ext={ext!r}, prefix={prefix!r})."
    )
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def get_this_filename() -> Path:
    """
    Return the absolute path of the current program/module.

    - If running as a frozen executable (e.g., PyInstaller), returns sys.executable.
    - Otherwise returns the current module file path (__file__).
    - In interactive contexts where __file__ is unavailable, falls back to sys.argv[0],
      then to the current working directory.

    Returns:
        Absolute Path.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()

    module_file = globals().get("__file__")
    if module_file:
        return Path(module_file).resolve()

    argv0 = sys.argv[0] if sys.argv else ""
    if argv0:
        p = Path(argv0)
        # argv0 may be relative; resolve() will anchor to cwd
        return p.resolve()

    return Path.cwd().resolve()
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def is_binary_file(path: PathInput, *, sample_size: int = 8192) -> bool:
    """
    Determine whether a file appears to be binary.

    A file is considered text if:
    - It starts with a known Unicode BOM
    - It does not contain null bytes
    - It can be decoded as UTF-8

    Parameters
    ----------
    path : str | os.PathLike[str] | Path
        File path.
    sample_size : int, default=8192
        Number of bytes to read for detection.

    Returns
    -------
    bool
        True if the file appears binary, False otherwise.
    """
    p = check_file(path)

    with p.open("rb") as f:
        chunk = f.read(sample_size)

    if not chunk:
        # Empty file → text
        return False

    # Known BOMs (UTF text encodings)
    BOMS = (
        b"\xef\xbb\xbf",      # UTF-8 BOM
        b"\xff\xfe",          # UTF-16 LE
        b"\xfe\xff",          # UTF-16 BE
        b"\xff\xfe\x00\x00",  # UTF-32 LE
        b"\x00\x00\xfe\xff",  # UTF-32 BE
    )

    if any(chunk.startswith(bom) for bom in BOMS):
        return False

    # Null byte strongly indicates binary
    if b"\x00" in chunk:
        return True

    # Try UTF-8 decode
    try:
        chunk.decode("utf-8")
        return False
    except UnicodeDecodeError:
        return True
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def detect_file_encoding(
    path: PathInput,
    *,
    default: str = "utf-8",
    min_confidence: float = 0.50,
    sample_size: int = 256 * 1024,
    prefer_utf8_sig: bool = True,
) -> str:
    """
    Detect the text encoding of a file using chardet, with BOM handling.

    The function reads up to `sample_size` bytes. If a known Unicode BOM is
    present, it returns the corresponding encoding immediately. Otherwise it
    delegates to chardet and returns the detected encoding if the confidence is
    >= `min_confidence`. If detection is inconclusive, it returns `default`.

    Parameters
    ----------
    path : str | os.PathLike[str] | Path
        File path to inspect.
    default : str, default="utf-8"
        Encoding returned when detection fails or confidence is too low.
    min_confidence : float, default=0.50
        Minimum confidence threshold (0.0..1.0).
    sample_size : int, default=262144
        Number of bytes read from the file (default: 256 KB).
    prefer_utf8_sig : bool, default=True
        If True, returns "utf-8-sig" when a UTF-8 BOM is present; otherwise "utf-8".

    Returns
    -------
    str
        A normalized encoding name (lowercase), or `default` if detection is
        inconclusive.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    IsADirectoryError
        If the path is not a file.
    ValueError
        If `min_confidence` is outside [0.0, 1.0] or sample_size <= 0.
    ImportError
        If chardet is not installed.
    OSError
        For underlying I/O errors.
    """
    if not (0.0 <= min_confidence <= 1.0):
        raise ValueError(f"min_confidence must be within [0.0, 1.0], got: {min_confidence}")
    if sample_size <= 0:
        raise ValueError(f"sample_size must be > 0, got: {sample_size}")

    p = check_file(path)

    with p.open("rb") as f:
        data = f.read(sample_size)

    if not data:
        return default.lower()

    # BOM detection (check longer BOMs first)
    if data.startswith(b"\xff\xfe\x00\x00"):
        return "utf-32-le"
    if data.startswith(b"\x00\x00\xfe\xff"):
        return "utf-32-be"
    if data.startswith(b"\xff\xfe"):
        return "utf-16-le"
    if data.startswith(b"\xfe\xff"):
        return "utf-16-be"
    if data.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig" if prefer_utf8_sig else "utf-8"

    try:
        import chardet
    except ImportError as ex:
        raise ImportError("chardet is required to detect file encodings") from ex

    result = chardet.detect(data)
    enc: Optional[str] = result.get("encoding")
    conf = float(result.get("confidence") or 0.0)

    if not enc or conf < min_confidence:
        return default.lower()

    return enc.lower()
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def get_file_content(
    path: Union[str, Path],
    encoding: str = "utf-8",
    *,
    default_encoding: str = "utf-8",
    min_confidence: float = 0.50,
) -> str:
    """
    Read a text file and return its content, removing a leading BOM if present.

    Args:
        path: File path.
        encoding: Encoding to use. If "UNKNOWN" (case-insensitive), the encoding
            is detected using `detect_file_encoding`.
        default_encoding: Fallback encoding when detection is inconclusive.
        min_confidence: Confidence threshold used for detection.

    Returns:
        File content as str, without a leading BOM.

    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path is not a file.
        UnicodeDecodeError: If decoding fails.
        OSError: For underlying I/O errors.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(path))
    if not p.is_file():
        raise IsADirectoryError(str(path))

    local_encoding = encoding
    if local_encoding.upper() == "UNKNOWN":
        local_encoding = detect_file_encoding(
            p,
            default=default_encoding,
            min_confidence=min_confidence,
        )

    # UTF-8 BOM: use utf-8-sig to transparently drop BOM on read
    read_encoding = "utf-8-sig" if local_encoding.lower() == "utf-8" else local_encoding

    content = p.read_text(encoding=read_encoding)

    # Defensive: remove BOM char if still present (rare mismatch cases)
    if content.startswith("\ufeff"):
        content = content[1:]

    return content
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def set_file_content(
    path: Union[str, Path],
    content: str,
    encoding: str = "utf-8",
    bom: bool = True,
    *,
    atomic: bool = True,
    newline: Optional[str] = "\n",
    create_parents: bool = True,
) -> str:
    """
    Write text content to a file, optionally adding a UTF-8 BOM.

    Args:
        path: Target file path.
        content: Text content to write.
        encoding: Target encoding (default: "utf-8").
        bom: If True and encoding is UTF-8, write a UTF-8 BOM.
        atomic: If True, write atomically (tmp file + replace).
        newline: Newline sequence used when writing (default: "\\n"). Use None
            to preserve content as-is.
        create_parents: If True, create parent directories.

    Returns:
        Absolute normalized path of the written file.

    Raises:
        ValueError: If content is not a str.
        OSError: For underlying filesystem errors.
    """
    if not isinstance(content, str):
        raise ValueError("content must be a str")

    p = Path(path)
    if create_parents:
        p.parent.mkdir(parents=True, exist_ok=True)

    write_encoding = "utf-8-sig" if (encoding.lower() == "utf-8" and bom) else encoding
    target = p.resolve()

    if not atomic:
        target.write_text(content, encoding=write_encoding, newline=newline)
        return str(target)

    tmp = target.with_name(target.name + ".tmp")
    try:
        tmp.write_text(content, encoding=write_encoding, newline=newline)
        os.replace(str(tmp), str(target))
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass

    return str(target)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def make_temp_dir(prefix: str = "pymdtools_", dir: Optional[Union[str, Path]] = None) -> str:
    """
    Create a new empty temporary directory and return its absolute path.

    Args:
        prefix: Prefix for the temporary directory name.
        dir: Base directory where the temp directory is created. If None, uses
            the system temp directory.

    Returns:
        Absolute path to the created temporary directory.

    Raises:
        OSError: For underlying filesystem errors.
    """
    base_dir = str(Path(dir).resolve()) if dir is not None else None
    tmp = tempfile.mkdtemp(prefix=prefix, dir=base_dir)
    return str(Path(tmp).resolve())
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def apply_to_files(
    folder: Union[str, Path],
    process: Callable[[str], None],
    *,
    ext: str = ".md",
    recursive: bool = True,
    case_sensitive: bool = False,
    sort: bool = True,
) -> int:
    """
    Apply a function to each file in a folder matching an extension.

    Args:
        folder: Folder to scan.
        process: Callback invoked for each matching file. It receives the file path as str.
        ext: File extension to match (e.g. ".md").
        recursive: If True, scan subfolders.
        case_sensitive: If False, match extension case-insensitively.
        sort: If True, process files in a stable sorted order (useful for tests).

    Returns:
        Number of processed files.

    Raises:
        FileNotFoundError: If folder does not exist.
        NotADirectoryError: If folder is not a directory.
        ValueError: If ext is invalid.
    """
    if not ext.startswith("."):
        raise ValueError(f"ext must start with '.', got: {ext!r}")

    base = Path(folder)
    if not base.exists():
        raise FileNotFoundError(str(folder))
    if not base.is_dir():
        raise NotADirectoryError(str(folder))

    matcher = (ext if case_sensitive else ext.lower())
    pattern_iter = base.rglob("*") if recursive else base.glob("*")

    files = [p for p in pattern_iter if p.is_file()]
    if sort:
        files.sort(key=lambda p: str(p))

    count = 0
    for p in files:
        suffix = p.suffix if case_sensitive else p.suffix.lower()
        if suffix == matcher:
            process(str(p))
            count += 1

    return count
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def find_file(
    filename: str,
    start_points: Sequence[Union[str, Path]],
    relative_paths: Sequence[Union[str, Path]],
    *,
    max_up: int = 4,
) -> str:
    """
    Find a file by searching from multiple start points, optionally walking up parent directories.

    Search order:
        for start in start_points:
            for up in range(0, max_up + 1):
                for rel in relative_paths:
                    candidate = (start / (".." * up) / rel / filename)

    Args:
        filename: Target filename (no path).
        start_points: Absolute or relative paths used as search anchors.
        relative_paths: Relative paths to try under each anchor.
        max_up: Maximum number of parent levels to walk up (inclusive).

    Returns:
        Absolute normalized path of the first file found.

    Raises:
        ValueError: If max_up < 0 or filename is empty.
        FileNotFoundError: If no matching file is found. The exception message
            includes the tested candidate paths.
    """
    if not filename or not isinstance(filename, str):
        raise ValueError("filename must be a non-empty string")
    if max_up < 0:
        raise ValueError(f"max_up must be >= 0, got: {max_up}")

    tested: List[str] = []

    for start in start_points:
        base = Path(start)

        # We do not require base to exist; we simply build candidates.
        for up in range(0, max_up + 1):
            anchor = base
            for _ in range(up):
                anchor = anchor.parent

            for rel in relative_paths:
                candidate = (anchor / Path(rel) / filename).resolve()
                tested.append(str(candidate))
                if candidate.is_file():
                    return str(candidate)

    # No file found
    raise FileNotFoundError(
        f"File not found: {filename!r}. Tested {len(tested)} paths: {tested}"
    )
# -----------------------------------------------------------------------------


# =============================================================================
# Text & Encoding utilities
# =============================================================================


# -----------------------------------------------------------------------------
def convert_for_stdout(
    text: str,
    coding_in: str = "utf-8",
    coding_out: Optional[str] = None,
    *,
    encode_errors: str = "replace",
    decode_errors: str = "ignore",
) -> str:
    """
    Convert a text string for console output.

    The function performs a round-trip conversion:
    ``text (str) -> bytes (coding_in) -> str (coding_out)``.
    This is mainly useful to adapt text to the terminal encoding.

    If ``coding_out`` is not provided, the function uses ``sys.stdout.encoding``
    when available and falls back to UTF-8.

    Args:
        text: Input text (Python str).
        coding_in: Encoding used to encode the string to bytes.
        coding_out: Target encoding used to decode bytes back to str.
            If None, uses stdout encoding or UTF-8.
        encode_errors: Error handler for encoding (default: "replace").
        decode_errors: Error handler for decoding (default: "ignore").

    Returns:
        Converted text suitable for console output.
    """
    if coding_out is None:
        coding_out = (getattr(sys.stdout, "encoding", None) or "utf-8")

    data = text.encode(coding_in, errors=encode_errors)
    return data.decode(coding_out, errors=decode_errors)
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
        ValueError: If value is not a string.
        ImportError: If the Unidecode package is not installed.
    """
    if not isinstance(value, str):
        raise ValueError("value must be a str")

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
    if not isinstance(filename, str):
        raise ValueError("filename must be a str")

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
    if not isinstance(filename, str):
        raise ValueError("filename must be a str")

    # Step 1: ASCII transliteration
    text = to_ascii(filename)

    # Step 2: slug-like normalization, but keep underscores instead of hyphens
    text = slugify(text, allow_unicode=False).replace("-", replacement)

    # Step 3: final Windows-safe validation
    return get_valid_filename(text, replacement=replacement)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def path_to_url(path: Union[str, Path], *, remove_accent: bool = True) -> str:
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
    if not isinstance(value, str):
        raise ValueError("value must be a str")

    try:
        from dateutil.parser import parse
    except ImportError as ex:
        raise ImportError("python-dateutil is required for parse_timestamp()") from ex

    return parse(value)
# -----------------------------------------------------------------------------


# =============================================================================
# Validation helpers
# =============================================================================


# -----------------------------------------------------------------------------
T_sized = TypeVar("T_sized", bound=Sized)
def check_len(obj: T_sized, expected: int = 1, *, name: str = "object") -> T_sized:
    """
    Ensure that an object has the expected length.

    Args:
        obj: Any object supporting len().
        expected: Expected length (must be >= 0).
        name: Logical name used in error messages.

    Returns:
        The input object (for fluent-style usage).

    Raises:
        ValueError: If the object's length does not match `expected`,
            or if `expected` is negative.
        TypeError: If `obj` does not support len().
    """
    if expected < 0:
        raise ValueError(f"expected length must be >= 0, got: {expected}")

    try:
        actual = len(obj)
    except TypeError as ex:
        raise TypeError(f"{name} does not support len()") from ex

    if actual != expected:
        raise ValueError(f"{name} must have length {expected}, got {actual}")

    return obj
# -----------------------------------------------------------------------------


# =============================================================================