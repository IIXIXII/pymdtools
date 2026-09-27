"""Common/ Filesystem: copying."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable, Iterable, Optional, Set

from ..core import PathInput
from .paths import as_path


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
    ValueError
        If *dst* is *src*, is contained in *src*, or a followed directory
        symlink introduces a traversal cycle.
    FileExistsError
        If source and destination entries have incompatible types, or copying
        a symbolic link would replace an existing entry.
    OSError
        For underlying filesystem errors.
    """
    src_p = as_path(src)
    dst_p = as_path(dst)

    if not src_p.exists():
        raise FileNotFoundError(f"Source folder does not exist: {src_p}")
    if not src_p.is_dir():
        raise NotADirectoryError(f"Source is not a directory: {src_p}")

    def _resolved(path: Path, *, role: str) -> Path:
        try:
            return path.resolve(strict=False)
        except RuntimeError as ex:
            raise ValueError(f"Directory cycle detected while resolving {role}: {path}") from ex

    def _validate_destination(source_dir: Path, destination_dir: Path) -> Path:
        source_resolved = _resolved(source_dir, role="source")
        destination_resolved = _resolved(destination_dir, role="destination")
        # Validate both a possible link target and the physical location where
        # a destination entry would be created.
        destination_location = (
            _resolved(destination_dir.parent, role="destination parent") / destination_dir.name
        )
        for candidate in (destination_resolved, destination_location):
            if candidate == source_resolved or candidate.is_relative_to(source_resolved):
                raise ValueError(
                    "Destination directory must not be the source directory or one of "
                    f"its descendants: source={source_dir}, destination={destination_dir}"
                )
        return source_resolved

    def _ensure_destination_directory(path: Path) -> None:
        if path.is_symlink() or (path.exists() and not path.is_dir()):
            raise FileExistsError(f"Cannot copy a directory over a non-directory entry: {path}")
        path.mkdir(parents=True, exist_ok=True)

    active_directories: Set[tuple[int, int, Path]] = set()

    def _copy_directory(source_dir: Path, destination_dir: Path) -> None:
        source_resolved = _validate_destination(source_dir, destination_dir)

        source_stat = source_dir.stat()
        identity = (source_stat.st_dev, source_stat.st_ino, source_resolved)
        if identity in active_directories:
            raise ValueError(f"Directory cycle detected while copying: {source_dir}")

        active_directories.add(identity)
        try:
            _ensure_destination_directory(destination_dir)

            names = [entry.name for entry in source_dir.iterdir()]
            ignored: Set[str] = set(ignore(str(source_dir), names)) if ignore else set()

            for name in names:
                if name in ignored:
                    continue

                source = source_dir / name
                destination = destination_dir / name

                if source.is_symlink():
                    if symlinks:
                        target_is_directory = source.is_dir()
                        if destination.exists() or destination.is_symlink():
                            raise FileExistsError(
                                f"Cannot copy a symbolic link over an existing entry: {destination}"
                            )
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        destination.symlink_to(
                            source.readlink(),
                            target_is_directory=target_is_directory,
                        )
                    elif source.is_dir():
                        _copy_directory(source, destination)
                    else:
                        copy_file_if_needed(source, destination)
                    continue

                if source.is_dir():
                    _copy_directory(source, destination)
                else:
                    copy_file_if_needed(source, destination)
        finally:
            active_directories.remove(identity)

    _copy_directory(src_p, dst_p)

    return dst_p


def copy_file_if_needed(source: PathInput, destination: PathInput) -> Path:
    src = as_path(source)
    dst = as_path(destination)

    dst.parent.mkdir(parents=True, exist_ok=True)

    if dst.is_symlink() or dst.is_dir():
        raise FileExistsError(f"Cannot copy a file over a directory or symbolic link: {dst}")

    if not dst.exists():
        shutil.copy2(src, dst)
        return dst

    s = src.stat()
    d = dst.stat()

    if s.st_size != d.st_size or s.st_mtime > d.st_mtime:
        shutil.copy2(src, dst)

    return dst
