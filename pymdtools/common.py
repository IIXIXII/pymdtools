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
import re
import shutil
import sys
import tempfile
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path
from typing import (
    Any, Callable, Generic, Iterable, List, Optional, Sequence, 
    Set, TypeVar, Union, Sized
)
from urllib.parse import quote


# =============================================================================
# Core helpers (exceptions, decorators, lightweight utilities)
# =============================================================================


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
def normpath(path: str) -> str:
    """
    Return an absolute, normalized filesystem path.

    Resolves ".", ".." and returns an absolute path without checking
    for existence.
    """
    return str(Path(path).resolve())
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def check_folder(path: str) -> str:
    """
    Validate that a path exists and is a directory.

    Args:
        path: Path to validate.

    Returns:
        The normalized absolute path of the directory.

    Raises:
        NotADirectoryError: If the path exists but is not a directory.
        FileNotFoundError: If the path does not exist.
    """
    p = Path(path)

    if not p.exists():
        raise FileNotFoundError(path)

    if not p.is_dir():
        raise NotADirectoryError(path)

    return str(p.resolve())
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def ensure_folder(path: str) -> str:
    """
    Ensure that a directory exists and return its normalized absolute path.

    If the directory does not exist, it is created (including parents).
    If the path exists and is not a directory, an exception is raised.

    Args:
        path: Directory path to create or validate.

    Returns:
        The normalized absolute path of the directory.

    Raises:
        NotADirectoryError: If the path exists but is not a directory.
        OSError: If the directory cannot be created due to filesystem errors.
    """
    p = Path(path)

    if p.exists() and not p.is_dir():
        raise NotADirectoryError(path)

    p.mkdir(parents=True, exist_ok=True)
    return str(p.resolve())
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def check_file(path: str, expected_ext: Optional[str] = None) -> str:
    """
    Validate that a path exists and is a file, optionally checking its extension.

    Args:
        path: File path to validate.
        expected_ext: Expected file extension (e.g. ".md"). If provided, the file
            extension must match exactly (case-insensitive).

    Returns:
        Normalized absolute file path.

    Raises:
        FileNotFoundError: If the path does not exist.
        IsADirectoryError: If the path exists but is a directory.
        ValueError: If the extension does not match `expected_ext`.
    """
    p = Path(path)

    if not p.exists():
        raise FileNotFoundError(path)

    if not p.is_file():
        # could be a directory or other special node
        raise IsADirectoryError(path)

    if expected_ext is not None:
        if not expected_ext.startswith("."):
            raise ValueError(f"expected_ext must start with '.', got: {expected_ext!r}")

        actual_ext = p.suffix
        if actual_ext.lower() != expected_ext.lower():
            raise ValueError(
                f"Unexpected file extension for {str(p)!r}: "
                f"got {actual_ext!r}, expected {expected_ext!r}"
            )

    return str(p.resolve())
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def with_suffix(path: Union[str, Path], suffix: str) -> str:
    """
    Return a filename with a new suffix (extension).

    Args:
        path: Input filename or path.
        suffix: New suffix including the leading dot (e.g. ".md").

    Returns:
        Filename with the new suffix.

    Raises:
        ValueError: If suffix does not start with a dot.
    """
    if not suffix.startswith("."):
        raise ValueError(f"suffix must start with '.', got: {suffix!r}")

    p = Path(path)
    return str(p.with_suffix(suffix))
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def path_depth(path: str) -> int:
    """
    Return the depth of a filesystem path.

    The depth is defined as the number of directory components in the path.
    If the path points to a file, the file name is ignored.

    Args:
        path: Filesystem path (absolute or relative).

    Returns:
        Number of directory levels in the path.
    """
    p = Path(path)

    # If it looks like a file (has a suffix), ignore the last part
    if p.suffix:
        p = p.parent

    # Remove root/anchor and count parts
    parts = [part for part in p.parts if part not in (p.root, p.anchor)]
    return len(parts)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def copytree(
    src: str,
    dst: str,
    symlinks: bool = False,
    ignore: Optional[Callable[[str, list[str]], Iterable[str]]] = None,
) -> None:
    """
    Copy a directory tree from *src* to *dst*.

    This function behaves like a simplified, incremental version of
    ``shutil.copytree`` with ``dirs_exist_ok=True``:
    - creates destination directories as needed,
    - recursively copies files,
    - supports an ``ignore`` callable compatible with ``shutil.copytree``,
    - optionally preserves symlinks (copy the link itself) when ``symlinks=True``,
    - copies a file only if the destination file does not exist, or if the
      source file is newer (mtime), or if sizes differ.

    Args:
        src: Source directory path.
        dst: Destination directory path (created if missing).
        symlinks: If True, copy symlinks as symlinks. If False, copy the
            content of the linked file/directory.
        ignore: Callable with signature ``ignore(dirpath, names) -> iterable``
            returning the names to ignore in *dirpath*. Same contract as
            ``shutil.copytree``.

    Raises:
        FileNotFoundError: If *src* does not exist.
        NotADirectoryError: If *src* is not a directory.
        OSError: For underlying filesystem errors.
    """
    if not os.path.exists(src):
        raise FileNotFoundError(src)
    if not os.path.isdir(src):
        raise NotADirectoryError(src)

    os.makedirs(dst, exist_ok=True)

    names = os.listdir(src)
    ignored: Set[str] = set(ignore(src, names)) if ignore else set()

    for name in names:
        if name in ignored:
            continue

        source = os.path.join(src, name)
        destin = os.path.join(dst, name)

        # Symlink handling
        if os.path.islink(source):
            if symlinks:
                # Copy link itself
                if os.path.lexists(destin):
                    os.remove(destin)
                link_target = os.readlink(source)
                logging.info("Copy symlink %s -> %s", source, destin)
                os.symlink(link_target, destin)
            else:
                # Follow link: copy target content
                if os.path.isdir(source):
                    copytree(source, destin, symlinks=symlinks, ignore=ignore)
                else:
                    _copy_file_if_needed(source, destin)
            continue

        if os.path.isdir(source):
            copytree(source, destin, symlinks=symlinks, ignore=ignore)
        else:
            _copy_file_if_needed(source, destin)

def _copy_file_if_needed(source: str, destin: str) -> None:
    """Copy file preserving metadata if destination is missing or outdated."""
    if not os.path.exists(destin):
        logging.info("Copy file %s -> %s", source, destin)
        shutil.copy2(source, destin)
        return

    src_stat = os.stat(source)
    dst_stat = os.stat(destin)

    # Copy if size differs or if source is newer (mtime strictly greater)
    if src_stat.st_size != dst_stat.st_size or src_stat.st_mtime > dst_stat.st_mtime:
        logging.info("Copy file %s -> %s", source, destin)
        shutil.copy2(source, destin)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def create_backup(path: str, backup_ext: str = ".bak", *, max_tries: int = 100) -> str:
    """
    Create a dated backup copy of a file in the same directory.

    The backup file name follows the pattern:
        <original>.<YYYY-MM-DD>-NNN<backup_ext>

    Example:
        "/tmp/a.txt" -> "/tmp/a.txt.2026-01-31-000.bak"

    Args:
        path: Path to the source file.
        backup_ext: Backup extension (default: ".bak").
        max_tries: Maximum number of candidate names to try (default: 100).

    Returns:
        The absolute path of the created backup file.

    Raises:
        FileNotFoundError: If the source path does not exist.
        IsADirectoryError: If the source path is not a file.
        ValueError: If backup_ext is invalid or max_tries is not positive.
        RuntimeError: If no available backup name can be found.
        OSError: For underlying filesystem errors (copy, permissions, etc.).
    """
    if max_tries <= 0:
        raise ValueError(f"max_tries must be > 0, got: {max_tries}")
    if not backup_ext.startswith("."):
        raise ValueError(f"backup_ext must start with '.', got: {backup_ext!r}")

    src = Path(path)

    if not src.exists():
        raise FileNotFoundError(path)
    if not src.is_file():
        raise IsADirectoryError(path)

    src_abs = src.resolve()
    today = date.today().isoformat()  # "YYYY-MM-DD"

    # Candidate names: <filename>.<date>-NNN<ext>
    for i in range(max_tries):
        candidate = Path(f"{src_abs}.{today}-{i:03d}{backup_ext}")
        if not candidate.exists():
            # copy2 preserves metadata; change to copyfile if you explicitly do not want that
            shutil.copy2(src_abs, candidate)
            return str(candidate.resolve())

    raise RuntimeError(f"Cannot find an available backup filename for {str(src_abs)!r}")
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def get_this_filename() -> str:
    """
    Return the absolute path of the current program/module.

    - If running as a frozen executable (e.g., PyInstaller), returns sys.executable.
    - Otherwise returns the current module file path (__file__).
    - In interactive contexts where __file__ is unavailable, falls back to sys.argv[0],
      then to the current working directory.

    Returns:
        Absolute path as a string.
    """
    if getattr(sys, "frozen", False):
        return str(Path(sys.executable).resolve())

    module_file = globals().get("__file__")
    if module_file:
        return str(Path(module_file).resolve())

    argv0 = sys.argv[0] if sys.argv else ""
    if argv0:
        p = Path(argv0)
        # argv0 may be relative; resolve() will anchor to cwd
        return str(p.resolve())

    return str(Path.cwd().resolve())
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
#: BOMs indicating a text file, even if it contains null bytes.
_TEXT_BOMS = (
    codecs.BOM_UTF8,
    codecs.BOM_UTF16_BE,
    codecs.BOM_UTF16_LE,
    codecs.BOM_UTF32_BE,
    codecs.BOM_UTF32_LE,
)

def is_binary_file(path: Union[str, Path], *, sample_size: int = 8192) -> bool:
    """
    Determine whether a file should be considered binary.

    A file is considered binary if it contains at least one null byte (0x00)
    in its initial bytes and does not start with a known text BOM.

    Args:
        path: Path to the file to inspect.
        sample_size: Number of bytes to read from the start of the file
            (default: 8192).

    Returns:
        True if the file is considered binary, False otherwise.

    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path is a directory.
        OSError: For underlying I/O errors.
    """
    p = Path(path)

    if not p.exists():
        raise FileNotFoundError(path)
    if not p.is_file():
        raise IsADirectoryError(path)

    with p.open("rb") as f:
        initial_bytes = f.read(sample_size)

    if not initial_bytes:
        # Empty file → considered text
        return False

    # If file starts with a known text BOM, treat as text
    for bom in _TEXT_BOMS:
        if initial_bytes.startswith(bom):
            return False

    # Heuristic: presence of null byte indicates binary
    return b"\x00" in initial_bytes
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def detect_file_encoding(
    path: Union[str, Path],
    *,
    default: str = "utf-8",
    min_confidence: float = 0.50,
    sample_size: int = 256 * 1024,
) -> str:
    """
    Detect the text encoding of a file using chardet.

    The function reads up to `sample_size` bytes and returns the detected
    encoding if the confidence is >= `min_confidence`. Otherwise, it returns
    `default`.

    Args:
        path: File path to inspect.
        default: Encoding returned when detection fails or confidence is too low.
        min_confidence: Minimum confidence threshold (0.0..1.0).
        sample_size: Number of bytes read from the file (default: 256 KB).

    Returns:
        A normalized encoding name (lowercase), or `default` if detection is
        inconclusive.

    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path is not a file.
        ValueError: If `min_confidence` is outside [0.0, 1.0] or sample_size <= 0.
        ImportError: If chardet is not installed.
        OSError: For underlying I/O errors.
    """
    if not (0.0 <= min_confidence <= 1.0):
        raise ValueError(f"min_confidence must be within [0.0, 1.0], got: {min_confidence}")
    if sample_size <= 0:
        raise ValueError(f"sample_size must be > 0, got: {sample_size}")

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(path))
    if not p.is_file():
        raise IsADirectoryError(str(path))

    try:
        import chardet
    except ImportError as ex:
        raise ImportError("chardet is required to detect file encodings") from ex

    data = p.read_bytes()[:sample_size]
    if not data:
        return default.lower()

    result = chardet.detect(data)
    enc: Optional[str] = result.get("encoding")
    conf: float = float(result.get("confidence") or 0.0)

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