#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                    Author: Florent TOURNOIS | License: MIT
# =============================================================================
"""
pymdtools.common.fs
===================

Filesystem & path utilities for ``pymdtools.common``.

This module hosts all utilities that interact with the filesystem or rely on
path semantics (``pathlib.Path``). It is designed as the *I/O layer* of the
``pymdtools.common`` package.

Scope
-----
Included here:

- Path normalization / conversion:
    - ``to_path``: convert any path-like input to ``Path`` with controlled behavior
    - ``_p``: internal shorthand for ``to_path``
    - ``normpath``: normalized absolute path
    - ``with_suffix``: safe suffix replacement
    - ``path_depth``: count path components

- Filesystem checks and creation:
    - ``check_folder``: assert a directory exists
    - ``ensure_folder``: create directory (parents=True, exist_ok=True)
    - ``check_file``: assert a file exists

- Directory tree copy:
    - ``copytree``: incremental directory tree copy
    - ``_copy_file_if_needed``: internal helper for copy decisions

- Backup and binary detection:
    - ``create_backup``: create a ``.bak`` copy (or configurable suffix)
    - ``is_binary_file``: heuristic binary check

- Text encoding detection and file I/O:
    - ``detect_file_encoding``: BOM + chardet-based detection (optional dependency)
    - ``get_file_content``: read text file
    - ``set_file_content``: write text file

- Temporary directories:
    - ``make_temp_dir``: create and return a temp directory

- Traversal / search helpers:
    - ``ApplyResult``: summary dataclass
    - ``apply_to_files``: traverse a file or directory and apply a function
    - ``find_file``: search file from multiple anchors, with upward walk
    - ``get_this_filename``: return the filename of the current module

Dependencies
------------
This module relies on the Python standard library. ``detect_file_encoding`` uses
``chardet`` as an optional dependency and raises ``ImportError`` with an
explicit message if missing.

Compatibility / contract
------------------------
The implementations in this file are intended to be copied *verbatim* from the
historical ``common.py`` module to preserve behavior. Public symbols are
re-exported by ``pymdtools.common`` (the package façade).

"""

from __future__ import annotations

import os
import sys
import shutil
import tempfile
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Callable, Iterable, Optional, Sequence, Set

from .core import PathInput, T
from .time_validate import today_utc


# =============================================================================
# Filesystem & Path utilities
# =============================================================================


# -----------------------------------------------------------------------------
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
            print(backup)
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
    path: PathInput,
    *,
    encoding: str | None = None,
    default_encoding: str = "utf-8",
    min_confidence: float = 0.50,
    sample_size: int = 256 * 1024,
    errors: str = "strict",
    reject_binary: bool = True,
    strip_bom: bool = True,
) -> str:
    """
    Read a text file and return its content, with BOM protection.

    If `encoding` is not provided, the encoding is detected (BOM first,
    then chardet). Optionally rejects binary files and strips leading BOM.

    Parameters
    ----------
    path : str | os.PathLike[str] | Path
        File path.
    encoding : str | None, default=None
        If provided, this encoding is used directly (no detection).
    default_encoding : str, default="utf-8"
        Default encoding used when detection is inconclusive.
    min_confidence : float, default=0.50
        Minimum confidence threshold for chardet when auto-detecting.
    sample_size : int, default=256*1024
        Number of bytes read for encoding detection.
    errors : str, default="strict"
        Error handler for decoding.
    reject_binary : bool, default=True
        If True, raises ValueError when file appears binary.
    strip_bom : bool, default=True
        If True, removes leading Unicode BOM character (U+FEFF)
        from the decoded content.

    Returns
    -------
    str
        File content as text.
    """
    p = check_file(path)

    if reject_binary and is_binary_file(p):
        raise ValueError(f"Binary file detected: {p}")

    enc = encoding
    if enc is None:
        enc = detect_file_encoding(
            p,
            default=default_encoding,
            min_confidence=min_confidence,
            sample_size=sample_size,
        )

    text = p.read_text(encoding=enc, errors=errors)

    if strip_bom and text.startswith("\ufeff"):
        text = text[1:]

    return text
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def set_file_content(
    path: PathInput,
    content: str,
    encoding: str = "utf-8",
    bom: bool = False,
    *,
    atomic: bool = True,
    newline: Optional[str] = "\n",
    create_parents: bool = True,
) -> Path:
    """
    Write text content to a file, optionally adding a UTF-8 BOM.
    """
    # Option A: remove runtime check (preferred with strict typing)
    # If you keep it, prefer TypeError (you already do)
    # if not isinstance(content, str):
    #     raise TypeError("content must be a str")

    p = _p(path)
    if create_parents:
        p.parent.mkdir(parents=True, exist_ok=True)

    target = p.resolve(strict=False)

    enc = "utf-8-sig" if (encoding.lower() == "utf-8" and bom) else encoding

    if not atomic:
        target.write_text(content, encoding=enc, newline=newline)
        return target

    tmp_path: Path | None = None

    try:
        fd, tmp_name = tempfile.mkstemp(
            prefix=f".{target.name}.",
            suffix=".tmp",
            dir=str(target.parent),
        )
        tmp_path = Path(tmp_name)

        # Explicit fd -> text stream
        with os.fdopen(fd, "w", encoding=enc, newline=newline) as f:
            f.write(content)

        tmp_path.replace(target)
        return target

    finally:
        if tmp_path is not None and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def make_temp_dir(
    *,
    prefix: str = "pymdtools_",
    suffix: str = "",
    dir: PathInput | None = None,
) -> Path:
    """
    Create a temporary directory and return its Path.

    Parameters
    ----------
    prefix : str, default="pymdtools_"
        Prefix for the temporary directory name.
    suffix : str, default=""
        Suffix for the temporary directory name.
    dir : str | os.PathLike[str] | Path | None, default=None
        Parent directory in which to create the temp directory.
        If None, the system default temp directory is used.

    Returns
    -------
    Path
        Path to the created temporary directory.

    Notes
    -----
    - The directory is created immediately.
    - Caller is responsible for cleanup (e.g. via shutil.rmtree).
    """
    parent = _p(dir) if dir is not None else None

    tmp = tempfile.mkdtemp(
        prefix=prefix,
        suffix=suffix,
        dir=str(parent) if parent else None,
    )

    return Path(tmp)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class ApplyResult:
    """Result of a batch apply operation."""
    processed: int
    succeeded: int
    failed: int
    skipped: int


def apply_to_files(
    root: PathInput,
    func: Callable[[Path], T],
    *,
    recursive: bool = True,
    include_globs: Sequence[str] = ("*",),
    exclude_globs: Sequence[str] = (),
    expected_ext: str | tuple[str, ...] | None = None,
    follow_symlinks: bool = False,
    on_error: str = "raise",  # "raise" | "collect"
) -> tuple[list[T], ApplyResult, list[tuple[Path, Exception]]]:
    """
    Apply a function to files under a path (file or directory).

    Parameters
    ----------
    root : str | os.PathLike[str] | Path
        A file path or a directory path.
    func : Callable[[Path], T]
        Function applied to each selected file. Receives a Path and returns T.
    recursive : bool, default=True
        If root is a directory, walk recursively if True, else only direct children.
    include_globs : Sequence[str], default=("*",)
        Filename patterns to include (fnmatch patterns), applied to relative paths
        from the root directory. Example: ("**/*.md", "*.md") is NOT supported by fnmatch;
        use simple patterns like ("*.md",) when non-recursive. For recursive matching,
        patterns are applied to the POSIX relative path string.
    exclude_globs : Sequence[str], default=()
        Patterns to exclude (same matching rules as include_globs).
    expected_ext : str | tuple[str, ...] | None, default=None
        Restrict to file extensions. Accepts ".md", "md", or tuple of them.
        If None, no extension filter is applied.
    follow_symlinks : bool, default=False
        If True, symlinked directories may be traversed. Use with care (cycles).
    on_error : {"raise","collect"}, default="raise"
        - "raise": stop at first error
        - "collect": continue and return errors list

    Returns
    -------
    (results, summary, errors) : (list[T], ApplyResult, list[(Path, Exception)])
        results: return values from func for each successful file
        summary: counts
        errors: list of (file, exception) when on_error="collect"

    Notes
    -----
    - This function does not perform I/O by itself except directory traversal.
    - `func` is responsible for reading/writing file contents.
    """
    root_p = _p(root)

    # Normalize expected extensions (lowercase, leading dot)
    exts: tuple[str, ...] | None
    if expected_ext is None:
        exts = None
    else:
        raw = (expected_ext,) if isinstance(expected_ext, str) else expected_ext
        exts = tuple(e.lower() if e.startswith(".") else f".{e.lower()}" for e in raw)

    def _match(rel_posix: str) -> bool:
        if include_globs and not any(fnmatch(rel_posix, pat) for pat in include_globs):
            return False
        if exclude_globs and any(fnmatch(rel_posix, pat) for pat in exclude_globs):
            return False
        return True

    def _iter_files(base: Path) -> Iterable[Path]:
        if base.is_file():
            yield base
            return

        if not base.exists():
            raise FileNotFoundError(f"Path does not exist: {base}")
        if not base.is_dir():
            raise NotADirectoryError(f"Not a directory: {base}")

        if recursive:
            it = base.rglob("*")
        else:
            it = base.glob("*")

        for p in it:
            # Skip directories
            if p.is_dir():
                # Optionally skip symlinked dirs (rglob/glob will still enumerate)
                if p.is_symlink() and not follow_symlinks:
                    continue
                continue

            # Skip non-files (specials)
            if not p.is_file():
                continue

            yield p

    results: list[T] = []
    errors: list[tuple[Path, Exception]] = []

    processed = succeeded = failed = skipped = 0

    base_dir = root_p if root_p.is_dir() else root_p.parent

    for f in _iter_files(root_p):
        processed += 1

        # Extension filter
        if exts is not None and f.suffix.lower() not in exts:
            skipped += 1
            continue

        # Pattern filters (relative path, POSIX form for stable matching)
        try:
            rel = f.relative_to(base_dir).as_posix()
        except ValueError:
            # Defensive: if relative_to fails, fall back to name
            rel = f.name

        if not _match(rel):
            skipped += 1
            continue

        try:
            results.append(func(f))
            succeeded += 1
        except Exception as exc:
            failed += 1
            if on_error == "raise":
                raise
            errors.append((f, exc))

    summary = ApplyResult(
        processed=processed,
        succeeded=succeeded,
        failed=failed,
        skipped=skipped,
    )
    return results, summary, errors
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def find_file(
    filename: str,
    start_points: Sequence[PathInput],
    relative_paths: Sequence[PathInput],
    *,
    max_up: int = 4,
) -> Path:
    """
    Find a file by searching from multiple start points, optionally walking up parent directories.

    The function searches for the *first* matching file according to a deterministic order.

    Search order
    ------------
    For each `start` in `start_points` (in the given order):
        - Let `base = start`
        - For each `up` from 0 to `max_up` (inclusive):
            - Let `anchor = base` moved up `up` times (anchor = anchor.parent repeated)
            - For each `rel` in `relative_paths` (in the given order):
                - Test candidate: anchor / rel / filename

    Notes
    -----
    - `start_points` are used as anchors; they are *not* required to exist.
    - `relative_paths` MUST be relative paths (no absolute paths allowed). This is enforced
      to prevent accidental bypassing of the `anchor` with an absolute path.
    - The returned path is normalized as an absolute path via `resolve(strict=False)`.
    - The function only returns when `candidate.is_file()` is True.

    Parameters
    ----------
    filename : str
        Target filename (no path). Must be a non-empty string.
        Example: "config.yml".
    start_points : Sequence[str | os.PathLike[str] | Path]
        Absolute or relative paths used as search anchors.
        Examples:
        - Path.cwd()
        - "/some/project/subdir"
        - "relative/subdir"
    relative_paths : Sequence[str | os.PathLike[str] | Path]
        Relative paths to try under each anchor. Each element must be relative.
        Examples:
        - "."
        - "docs"
        - Path("configs") / "environments"
    max_up : int, default=4
        Maximum number of parent levels to walk up from each start point (inclusive).
        `max_up=0` searches only under the start point itself.

    Returns
    -------
    Path
        Absolute normalized path of the first file found.

    Raises
    ------
    ValueError
        - If `filename` is empty.
        - If `max_up < 0`.
        - If any item in `relative_paths` is absolute.
    FileNotFoundError
        If no matching file is found. The exception message includes the tested paths.

    Examples
    --------
    Search for "config.yml" starting from the current directory and a secondary start point,
    trying ".", "configs", and walking up to 2 parent levels:

    >>> find_file(
    ...     "config.yml",
    ...     start_points=[Path.cwd(), "other/start"],
    ...     relative_paths=[".", "configs"],
    ...     max_up=2,
    ... )

    The effective candidates include (in order):
      - <cwd> / "." / "config.yml"
      - <cwd> / "configs" / "config.yml"
      - <cwd.parent> / "." / "config.yml"
      - <cwd.parent> / "configs" / "config.yml"
      - <cwd.parent.parent> / "." / "config.yml"
      - <cwd.parent.parent> / "configs" / "config.yml"
      - then the same pattern for "other/start".
    """
    if not filename:
        raise ValueError("filename must be a non-empty string")
    if max_up < 0:
        raise ValueError(f"max_up must be >= 0, got: {max_up}")

    # Validate relative_paths early and normalize them to Path
    rel_paths: list[Path] = []
    for rel in relative_paths:
        rel_p = _p(rel)
        if rel_p.is_absolute():
            raise ValueError(f"relative_paths must be relative, got: {rel_p}")
        rel_paths.append(rel_p)

    tested: list[Path] = []

    for start in start_points:
        base = _p(start)

        # We do not require base to exist; we simply build candidates.
        for up in range(0, max_up + 1):
            anchor = base
            for _ in range(up):
                anchor = anchor.parent

            for rel_p in rel_paths:
                candidate = (anchor / rel_p / filename).resolve(strict=False)
                tested.append(candidate)
                if candidate.is_file():
                    return candidate

    raise FileNotFoundError(
        f"File not found: {filename!r}. Tested {len(tested)} paths: {[str(p) for p in tested]}"
    )
# -----------------------------------------------------------------------------


# =============================================================================