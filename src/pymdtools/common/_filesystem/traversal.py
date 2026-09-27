"""Common/ Filesystem: traversal."""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path, PureWindowsPath
from typing import Callable, Iterable, Sequence, Set

from ..core import PathInput, T
from .paths import as_path, require_str


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
        from the root directory. Example: ``("**/*.md", "*.md")`` is NOT
        supported by fnmatch; use simple patterns like ``("*.md",)`` when
        non-recursive. For recursive matching, patterns are applied to the POSIX
        relative path string.
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
    if on_error not in {"raise", "collect"}:
        raise ValueError(f"on_error must be either 'raise' or 'collect', got: {on_error!r}")

    root_p = as_path(root)

    # Normalize expected extensions (lowercase, leading dot)
    exts: tuple[str, ...] | None
    if expected_ext is None:
        exts = None
    else:
        raw = (expected_ext,) if isinstance(expected_ext, str) else expected_ext
        exts = tuple(e.lower() if e.startswith(".") else f".{e.lower()}" for e in raw)

    def _match(rel_posix: str) -> bool:
        if include_globs and not any(fnmatchcase(rel_posix, pat) for pat in include_globs):
            return False
        if exclude_globs and any(fnmatchcase(rel_posix, pat) for pat in exclude_globs):
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

        seen_directories: Set[tuple[int, int, Path]] = set()

        def _walk(directory: Path) -> Iterable[Path]:
            directory_stat = directory.stat()
            identity = (
                directory_stat.st_dev,
                directory_stat.st_ino,
                directory.resolve(strict=False),
            )
            if identity in seen_directories:
                return
            seen_directories.add(identity)

            for p in sorted(directory.iterdir(), key=lambda item: item.name):
                if p.is_dir():
                    if recursive and (follow_symlinks or not p.is_symlink()):
                        yield from _walk(p)
                    continue

                if p.is_file():
                    yield p

        yield from _walk(base)

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
    - `relative_paths` MUST be confined relative paths: absolute, rooted,
      drive-relative, and parent-traversing forms are rejected.
    - Resolved candidates must remain below the anchor selected for that
      iteration, including when links are involved.
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
        - If `filename` is empty or contains a path.
        - If `max_up < 0`.
        - If any item in `relative_paths` is rooted or contains `..`.
        - If a resolved candidate escapes its current anchor.
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
    filename = require_str(filename, name="filename")
    if not filename.strip():
        raise ValueError("filename must be a non-empty string")
    if max_up < 0:
        raise ValueError(f"max_up must be >= 0, got: {max_up}")

    filename_path = PureWindowsPath(filename)
    if filename_path.anchor or len(filename_path.parts) != 1 or filename_path.name in {".", ".."}:
        raise ValueError(f"filename must be a plain filename, got: {filename!r}")

    # Validate relative_paths early and normalize them to Path
    rel_paths: list[Path] = []
    for rel in relative_paths:
        rel_p = as_path(rel)
        windows_rel = PureWindowsPath(str(rel_p))
        if windows_rel.anchor:
            raise ValueError(f"relative_paths must be relative, got: {rel_p}")
        if ".." in windows_rel.parts:
            raise ValueError(f"relative_paths must not contain '..', got: {rel_p}")
        rel_paths.append(rel_p)

    tested: list[Path] = []

    for start in start_points:
        base = as_path(start)

        # We do not require base to exist; we simply build candidates.
        for up in range(0, max_up + 1):
            anchor = base
            for _ in range(up):
                anchor = anchor.parent

            for rel_p in rel_paths:
                resolved_anchor = anchor.resolve(strict=False)
                candidate = (resolved_anchor / rel_p / filename).resolve(strict=False)
                if not candidate.is_relative_to(resolved_anchor):
                    raise ValueError(f"Resolved search path escapes its anchor: {anchor / rel_p}")
                tested.append(candidate)
                if candidate.is_file():
                    return candidate

    raise FileNotFoundError(
        f"File not found: {filename!r}. Tested {len(tested)} paths: {[str(p) for p in tested]}"
    )
