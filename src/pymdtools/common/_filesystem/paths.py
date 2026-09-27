"""Common/ Filesystem: paths."""

from __future__ import annotations

from pathlib import Path

from ..core import PathInput


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
    - Most library-level functions should call ``p = to_path(path)`` without
      ``resolve=True``.
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


def as_path(p: PathInput) -> Path:
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


def require_str(value: object, *, name: str) -> str:
    """Return *value* as text, with a clear runtime error for dynamic callers."""
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a str")
    return value


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


def check_file(path: PathInput, expected_ext: str | tuple[str, ...] | None = None) -> Path:
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

    p = as_path(path)

    # Normalize suffix format
    if not suffix.startswith("."):
        suffix = f".{suffix}"

    return p.with_suffix(suffix)


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
    p = as_path(path)

    # Ignore file name if it has a suffix
    if p.suffix:
        p = p.parent

    # Remove anchor (e.g. "/" or "C:\\")
    if p.anchor:
        parts = p.parts[1:]
    else:
        parts = p.parts

    return len(parts)
