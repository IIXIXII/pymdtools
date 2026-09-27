"""Directives: discovery."""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator, Sequence
from fnmatch import fnmatchcase
from pathlib import Path
from typing import (
    Dict,
    Iterable,
    Optional,
)

from .. import common
from ..options import DEFAULT_EXCLUDED_DIRECTORIES
from .references import get_refs_from_md_file
from .variables import get_vars_from_md_file

logger: logging.Logger = logging.getLogger(__name__)


def get_refs_from_md_directory(
    folder: common.PathInput,
    filename_ext: str = ".md",
    previous_refs: Optional[Dict[str, str]] = None,
    depth: int = -1,
    *,
    exclude_dirs: Sequence[str] = DEFAULT_EXCLUDED_DIRECTORIES,
) -> Dict[str, str]:
    """
    Extract refs from markdown files in a directory tree.

    Depth semantics:
        - depth == -1: recurse into all subdirectories (unlimited)
        - depth == 0: only current directory
        - depth > 0 : recurse up to `depth` levels

    Args:
        folder: Root directory to scan.
        filename_ext: File extension to include (e.g. ".md").
        previous_refs: Optional dict to merge with extracted refs (copied).
        depth: Recursion depth.

    Returns:
        A dict mapping ref names to extracted content.
    """
    refs = dict(previous_refs) if previous_refs else {}
    for path in iter_markdown_files(folder, filename_ext, depth, exclude_dirs):
        refs = get_refs_from_md_file(path, filename_ext=filename_ext, previous_refs=refs)
    return refs


def get_refs_from_search_folders(
    search_folders: Iterable[common.PathInput],
    *,
    refs: Optional[Dict[str, str]] = None,
    filename_ext: str = ".md",
    depth: int = -1,
    exclude_dirs: Sequence[str] = DEFAULT_EXCLUDED_DIRECTORIES,
) -> Dict[str, str]:
    """
    Extend/collect refs by scanning one or more folders recursively.

    Args:
        search_folders: Folders to scan.
        refs: Existing refs mapping to extend (copied to avoid side effects).
        filename_ext: File extension to scan (e.g. ".md").
        depth: Recursion depth (-1 unlimited, 0 current dir only, >0 limited).

    Returns:
        A dict mapping ref names to extracted content.
    """
    result: Dict[str, str] = dict(refs) if refs else {}

    for folder in search_folders:
        result = get_refs_from_md_directory(
            folder,
            filename_ext=filename_ext,
            previous_refs=result,
            depth=depth,
            exclude_dirs=exclude_dirs,
        )

    return result


def get_refs_around_md_file(
    filename: common.PathInput,
    filename_ext: str = ".md",
    previous_refs: Optional[Dict[str, str]] = None,
    depth_up: int = 1,
    depth_down: int = -1,
    *,
    exclude_dirs: Sequence[str] = DEFAULT_EXCLUDED_DIRECTORIES,
) -> Dict[str, str]:
    """
    Discover refs around a markdown file by scanning parent folders.

    The search root is computed by moving `depth_up` times to the parent directory
    of `filename` (or stopping at filesystem root). Then refs are collected by
    scanning that root directory with `get_refs_from_md_directory`.

    Depth semantics:
        - depth_down == -1: unlimited recursion from the chosen root
        - depth_down == 0: current directory only
        - depth_down > 0 : limited recursion levels

    Note:
        When `depth_up` > 0 and `depth_down` > 0, the effective downward depth
        is increased by the number of levels actually moved up, so that the scan
        still covers the original file directory.

    Args:
        filename: Path to a markdown file (used only to locate directories).
        filename_ext: Extension to scan in directories (e.g. ".md").
        previous_refs: Optional dict to extend.
        depth_up: Number of parent levels to move up (>= 0).
        depth_down: Recursion depth from the computed root (-1 unlimited, >= 0 limited).

    Returns:
        A dict mapping ref names to extracted content.

    Raises:
        ValueError: If `depth_up` < 0 or `depth_down` < -1.
    """
    if depth_up < 0:
        raise ValueError(f"depth_up must be >= 0, got: {depth_up}")
    if depth_down < -1:
        raise ValueError(f"depth_down must be >= -1, got: {depth_down}")

    p = Path(filename).resolve()
    current_dir = p.parent

    moved_up = 0
    while moved_up < depth_up:
        parent = current_dir.parent
        if parent == current_dir:
            break  # filesystem root reached
        current_dir = parent
        moved_up += 1

    effective_depth_down = depth_down
    if depth_down > 0:
        effective_depth_down = depth_down + moved_up

    return get_refs_from_md_directory(
        current_dir,
        filename_ext=filename_ext,
        previous_refs=previous_refs,
        depth=effective_depth_down,
        exclude_dirs=exclude_dirs,
    )


def get_vars_from_md_directory(
    folder: common.PathInput,
    *,
    filename_ext: str = ".md",
    previous_vars: Optional[Dict[str, str]] = None,
    depth: int = -1,
    encoding: Optional[str] = None,
    exclude_dirs: Sequence[str] = DEFAULT_EXCLUDED_DIRECTORIES,
) -> Dict[str, str]:
    """
    Find var(...) declarations in markdown files in `folder` and (optionally) its subfolders.

    Depth:
      - -1: recurse into all subfolders
      -  0: current folder only
      -  n>0: recurse `n` levels

    Args:
        folder: Directory to scan.
        filename_ext: Markdown file extension to consider.
        previous_vars: Existing mapping to extend.
        depth: Recursion depth.
        encoding: Encoding for reading files. ``None`` triggers auto-detection.

    Returns:
        A dict of var name -> interpreted value.

    Raises:
        RuntimeError: If `folder` is not a directory.
        ValueError: If duplicate var names are found across scanned files.
    """
    vars_ = dict(previous_vars) if previous_vars else {}
    for path in iter_markdown_files(folder, filename_ext, depth, exclude_dirs):
        vars_ = get_vars_from_md_file(
            path, filename_ext=filename_ext, previous_vars=vars_, encoding=encoding
        )
    return vars_


def get_vars_around_md_file(
    filename: common.PathInput,
    *,
    filename_ext: str = ".md",
    previous_vars: Optional[Dict[str, str]] = None,
    depth_up: int = 1,
    depth_down: int = -1,
    encoding: Optional[str] = None,
    exclude_dirs: Sequence[str] = DEFAULT_EXCLUDED_DIRECTORIES,
) -> Dict[str, str]:
    """
    Discover var(...) declarations around a markdown file by scanning nearby directories.

    Starting from the directory of `filename`, this function moves up `depth_up` levels
    (stopping at filesystem root), then scans downward with depth `depth_down`.

    Args:
        filename: Markdown file path.
        filename_ext: Extension for markdown files.
        previous_vars: Existing mapping to extend.
        depth_up: Number of parent levels to move up (>= 0).
        depth_down: Downward recursion depth (-1 unlimited, 0 current dir only, >0 limited).
        encoding: Encoding used to read markdown files. ``None`` triggers auto-detection.

    Returns:
        A dict of var name -> interpreted value.

    Raises:
        ValueError: If `depth_up` < 0 or `depth_down` < -1.
        RuntimeError/Exception: Propagated by filesystem helpers.
    """
    if depth_up < 0:
        raise ValueError(f"depth_up must be >= 0, got: {depth_up}")
    if depth_down < -1:
        raise ValueError(f"depth_down must be >= -1, got: {depth_down}")

    filename_str = common.normpath(str(filename))
    logger.debug('Discover vars around the file "%s"', filename_str)

    current_dir = os.path.abspath(os.path.dirname(filename_str))

    # move up
    du = depth_up
    dd = depth_down
    while du > 0:
        new_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
        if new_dir == current_dir:
            break
        current_dir = new_dir
        du -= 1
        if dd > 0:
            dd += 1  # keep total "down scan" horizon roughly stable

    return get_vars_from_md_directory(
        current_dir,
        filename_ext=filename_ext,
        previous_vars=previous_vars,
        depth=dd,
        exclude_dirs=exclude_dirs,
        encoding=encoding,
    )


def iter_markdown_files(
    folder: common.PathInput,
    filename_ext: str,
    depth: int,
    exclude_dirs: Sequence[str],
) -> Iterator[Path]:
    """Walk deterministically, pruning excluded directories and cyclic/external paths."""
    if depth < -1:
        raise ValueError("depth must be -1 or non-negative")
    root = common.check_folder(folder).resolve()
    pending = [(root, depth)]
    visited: set[Path] = set()
    while pending:
        directory, remaining = pending.pop()
        resolved = directory.resolve()
        if resolved in visited or not resolved.is_relative_to(root):
            continue
        visited.add(resolved)
        children: list[Path] = []
        for entry in sorted(directory.iterdir(), key=lambda path: path.name):
            if entry.is_symlink() or not entry.resolve().is_relative_to(root):
                continue
            if entry.is_file() and entry.suffix == filename_ext:
                yield entry
            elif entry.is_dir() and remaining != 0:
                relative = entry.relative_to(root).as_posix()
                if not any(
                    fnmatchcase(entry.name, pattern) or fnmatchcase(relative, pattern)
                    for pattern in exclude_dirs
                ):
                    children.append(entry)
        next_depth = remaining - 1 if remaining > 0 else remaining
        pending.extend((child, next_depth) for child in reversed(children))
