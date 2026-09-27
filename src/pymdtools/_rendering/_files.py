"""Rendering: files."""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
from pathlib import Path

logger: logging.Logger = logging.getLogger(__name__)


def new_staged_path(target: Path, *, suffix: str = ".tmp") -> Path:
    """Reserve a temporary sibling path suitable for an atomic replace."""
    target.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, staged_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=suffix,
        dir=target.parent,
    )
    os.close(file_descriptor)
    return Path(staged_name)


def commit_staged_file(staged: Path, target: Path) -> None:
    """Atomically replace ``target`` with a fully written sibling file."""
    if target.exists():
        if not target.is_file():
            raise IsADirectoryError(f"destination is not a file: {target}")
        shutil.copymode(target, staged)
    staged.replace(target)


def atomic_copy_file(source: Path, target: Path) -> None:
    """Copy a file and expose it at ``target`` only after a complete write."""
    staged = new_staged_path(target, suffix=target.suffix + ".tmp")
    try:
        shutil.copy2(source, staged)
        commit_staged_file(staged, target)
    finally:
        staged.unlink(missing_ok=True)


def write_text_atomic(
    target: Path,
    content: str,
    *,
    encoding: str,
) -> None:
    """Write generated HTML atomically while preserving encoding fallback."""
    staged = new_staged_path(target)
    try:
        with staged.open(
            "w",
            encoding=encoding,
            errors="xmlcharrefreplace",
            newline="\n",
        ) as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        commit_staged_file(staged, target)
    finally:
        staged.unlink(missing_ok=True)
