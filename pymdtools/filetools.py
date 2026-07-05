#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                    Author: Florent TOURNOIS | License: MIT                   
# =============================================================================

# -----------------------------------------------------------------------------
# standard object to wrap file and access easily to the filename
# -----------------------------------------------------------------------------
"""
pymdtools.filetools
===================

High-level helpers for working with template files and text file content.

This module builds on :mod:`pymdtools.common` instead of reimplementing low-level
filesystem behavior. It provides:

- ``get_template_file``: read a file from a local ``template/`` directory.
- ``get_template_files_in_folder``: list direct files under a template subfolder.
- ``FileName``: keep and edit a normalized file path by path/name/suffix.
- ``FileContent``: keep a file path together with an editable text buffer.

The module is intentionally text-oriented. Binary detection, encoding detection,
atomic writes, backups, and path validation are delegated to ``pymdtools.common``.
"""

from pathlib import Path
from typing import Optional, List

from . import common


# -----------------------------------------------------------------------------
def _relative_template_path(path: common.PathInput, *, name: str) -> Path:
    """
    Normalize and validate a path relative to the local ``template`` folder.
    """
    if isinstance(path, str):
        if not path.strip():
            raise ValueError(f"{name} must be a non-empty string")
        rel = Path(path)
    else:
        if not str(path).strip():
            raise ValueError(f"{name} must be a non-empty path")
        rel = Path(path)

    if rel.is_absolute():
        raise ValueError(f"{name} must be a relative path, got absolute: {rel!s}")

    if any(part == ".." for part in rel.parts):
        raise ValueError(f"{name} must not contain '..' path traversal, got: {rel!s}")

    return rel
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def _template_base(start_folder: common.PathInput | None = None) -> Path:
    """
    Return the base directory used to locate the local ``template`` folder.
    """
    if start_folder is None:
        return common.get_this_filename().parent

    base = common.to_path(start_folder)
    if base.exists():
        if base.is_file():
            base = base.parent
    elif base.suffix:
        base = base.parent

    return base.resolve(strict=False)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def get_template_file(
    filename: common.PathInput, 
    start_folder: common.PathInput | None = None,
) -> str:
    """
    Load and return the content of a template file located under 
    a ``template/`` directory.

    The lookup root is ``<base>/template``. When ``start_folder`` is provided,
    ``base`` is that folder, or the parent folder when ``start_folder`` points
    to a file. When it is omitted, ``base`` is derived from
    ``common.get_this_filename()``.

    ``filename`` must be relative to the template directory. Absolute paths,
    parent traversal with ``..``, and resolved paths escaping the template
    directory are rejected.

    Args:
        filename: Template filename or relative path inside ``template/``.
        start_folder: Optional folder or file used to locate ``template/``.

    Returns:
        The template file content.

    Raises:
        ValueError: If ``filename`` is empty, absolute, or escapes the template
            directory.
        FileNotFoundError: If the template directory or file does not exist.
        NotADirectoryError: If the template path is not a directory.
        OSError: Propagated from the underlying file read operation.
    """
    rel = _relative_template_path(filename, name="filename")
    template_dir = common.check_folder(_template_base(start_folder) / "template")
    candidate = (template_dir / rel).resolve(strict=False)

    try:
        candidate.relative_to(template_dir)
    except ValueError as ex:
        raise ValueError(f"template path escapes template directory: {rel!s}") from ex

    # --- read content ---
    common.check_file(candidate)
    return common.get_file_content(candidate)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def get_template_files_in_folder(folder: common.PathInput) -> List[str]:
    """
    List template files contained in `template/<folder>`.

    Args:
        folder: Subfolder name under the local `template/` directory.

    Returns:
        A list of relative template paths (POSIX-style), e.g. ["emails/a.html"].
        The result is sorted for determinism.

    Raises:
        ValueError: If ``folder`` is empty, absolute, or attempts path traversal.
        FileNotFoundError: If the template folder does not exist.
        NotADirectoryError: If the resolved template folder is not a directory.
    """
    rel = _relative_template_path(folder, name="folder")
    template_dir = common.check_folder(_template_base() / "template")
    local_template_folder = common.check_folder(template_dir / rel)

    files: List[str] = []
    for p in sorted(local_template_folder.iterdir(), key=lambda x: x.name):
        if p.is_file():
            files.append((rel / p.name).as_posix())

    return files
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def _validate_text_content(value: object | None) -> Optional[str]:
    """
    Return validated text content.

    The public setter is typed as ``Optional[str]`` for static callers, but this
    guard still protects runtime assignments that bypass type checking.
    """
    if value is not None and not isinstance(value, str):
        raise TypeError("content must be a str or None")
    return value
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
class FileName:
    """
    Utility object to manipulate a file path.

    ``FileName`` keeps a normalized ``Path`` internally while preserving the
    historical public interface based on strings. It is useful when code needs
    to keep one file reference and update only one part of it:

    - ``full_filename``: complete path, returned as ``str | None``.
    - ``filename``: basename with suffix, for example ``"report.md"``.
    - ``filename_path``: parent directory, returned as ``str | None``.
    - ``filename_ext``: suffix, including the leading dot, for example ``".md"``.

    Assigning to these properties updates the stored path:

    - setting ``full_filename`` accepts any ``common.PathInput``;
    - setting ``filename`` sanitizes the basename with
      ``common.get_valid_filename``;
    - setting ``filename_path`` moves the stored file reference to another
      directory;
    - setting ``filename_ext`` replaces the suffix and requires a leading dot.

    The object does not create, move, or rename files on disk. It only updates
    the path value it stores. Use ``is_file()`` and ``is_dir()`` to inspect the
    current filesystem state.
    """

    def __init__(self, filename: common.PathInput | None = None):
        self._path: Path | None = None
        if filename is not None:
            self.full_filename = filename

    @property
    def full_filename(self) -> Optional[str]:
        """Return the complete normalized filename as a string, or ``None``."""
        if self._path is None:
            return None
        return str(self._path)

    @full_filename.setter
    def full_filename(self, value: common.PathInput | None) -> None:
        """Set the complete filename from any ``common.PathInput`` value."""
        if value is None:
            self._path = None
            return
        self._path = common.normpath(value)

    @property
    def filename(self) -> Optional[str]:
        """Return the basename, including suffix, or ``None``."""
        if self._path is None:
            return None
        return self._path.name

    @filename.setter
    def filename(self, value: Optional[str]) -> None:
        """Replace the basename while preserving the current parent directory."""
        if value is None:
            self._path = None
            return

        safe_name = common.get_valid_filename(value)

        if self._path is None:
            self._path = common.normpath(safe_name)
        else:
            self._path = common.normpath(self._path.with_name(safe_name))

    @property
    def filename_path(self) -> Optional[str]:
        """Return the parent directory as a string, or ``None``."""
        if self._path is None:
            return None
        return str(self._path.parent)

    @filename_path.setter
    def filename_path(self, value: common.PathInput | None) -> None:
        """Move the stored file reference to another parent directory."""
        if value is None:
            raise ValueError("filename_path cannot be None")
        if self._path is None:
            raise ValueError("cannot set filename_path when full_filename is None")

        base = common.normpath(value)
        self._path = common.normpath(base / self._path.name)

    @property
    def filename_ext(self) -> Optional[str]:
        """Return the file suffix, including the leading dot, or ``None``."""
        if self._path is None:
            return None
        return self._path.suffix

    @filename_ext.setter
    def filename_ext(self, value: Optional[str]) -> None:
        """Replace the suffix of the stored filename."""
        if value is None or value == "":
            raise ValueError("filename_ext cannot be empty")
        if not value.startswith("."):
            raise ValueError(f"filename_ext must start with '.', got: {value!r}")
        if self._path is None:
            raise ValueError("cannot set filename_ext when full_filename is None")

        self._path = common.normpath(self._path.with_suffix(value))

    def is_file(self) -> bool:
        """Return ``True`` when the stored path currently exists as a file."""
        return self._path is not None and self._path.is_file()

    def is_dir(self) -> bool:
        """Return ``True`` when the stored path currently exists as a directory."""
        return self._path is not None and self._path.is_dir()

    def __repr__(self) -> str:
        return f"FileName({self.full_filename!r})"

    def __str__(self) -> str:
        if self._path is None:
            return "path=<None>\nfilename=<None>\nfile extension=<None>\n"

        lines = [
            f"          path={str(self._path.parent)}",
            f"      filename={self._path.name}",
            f"file extension={self._path.suffix}",
        ]
        if self._path.is_dir():
            lines.append("It is a directory")
        elif self._path.is_file():
            lines.append("The file exists")
        else:
            lines.append("The file or the directory does not exist")
        return "\n".join(lines) + "\n"
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
class FileContent(FileName):
    """
    File wrapper that stores text content and reads/writes it from disk.

    ``FileContent`` extends ``FileName`` with an in-memory text buffer:

    - if instantiated with an existing filename and ``content is None``, the
      file is read immediately;
    - setting ``content`` marks the object as needing a save;
    - ``read()`` reloads content from disk and clears ``save_needed``;
    - ``write()`` writes the current content to disk and clears ``save_needed``;
    - if ``backup`` is true, ``write()`` creates a numbered backup before
      overwriting an existing file.

    ``content`` may be ``None`` to represent an empty/unloaded buffer, but
    ``write()`` requires actual text. Assigning any non-string, non-``None``
    value raises ``TypeError``.
    """

    def __init__(
        self,
        filename: common.PathInput | None = None,
        content: Optional[str] = None,
        *,
        backup: bool = True,
        encoding: str | None = None,
    ) -> None:
        super().__init__(filename=filename)

        self._content: Optional[str] = None
        self._backup: bool = bool(backup)
        self._save_needed: bool = False

        if self.is_file() and content is None:
            self.read(encoding=encoding)
            self._save_needed = False

        if content is not None:
            self.content = content  # sets save_needed

    @property
    def content(self) -> Optional[str]:
        """Return the in-memory text content, or ``None`` if unloaded."""
        return self._content

    @content.setter
    def content(self, value: Optional[str]) -> None:
        """Set the in-memory text content and mark the file as needing a save."""
        self._content = _validate_text_content(value)
        self._save_needed = True

    @property
    def backup(self) -> bool:
        """Return whether writes create a backup before overwriting a file."""
        return self._backup

    @backup.setter
    def backup(self, value: bool) -> None:
        """Enable or disable backup creation for future writes."""
        self._backup = bool(value)

    @property
    def save_needed(self) -> bool:
        """Return whether the in-memory content should be written to disk."""
        return self._save_needed

    @save_needed.setter
    def save_needed(self, value: bool) -> None:
        """Manually set the dirty flag for the in-memory content."""
        self._save_needed = bool(value)

    def read(self, filename: common.PathInput | None = None, *, encoding: str | None = None) -> None:
        """
        Read text content from disk into memory.

        If ``filename`` is provided, it replaces the current stored path before
        reading. ``encoding=None`` delegates encoding detection to
        ``common.get_file_content``.
        """
        if filename is not None:
            self.full_filename = filename

        if self._path is None:
            raise ValueError("cannot read content without a filename")

        self._content = common.get_file_content(self._path, encoding=encoding)
        self._save_needed = False

    def write(
        self,
        filename: common.PathInput | None = None,
        *,
        encoding: str = "utf-8",
        backup_ext: str = ".bak",
    ) -> None:
        """
        Write the in-memory text content to disk.

        If ``filename`` is provided, it replaces the current stored path before
        writing. When backups are enabled and the target file already exists,
        a backup is created before writing the new content.
        """
        if filename is not None:
            self.full_filename = filename

        if self._path is None:
            raise ValueError("cannot write content without a filename")

        if self._content is None:
            raise ValueError("cannot write: content is None")

        if self.backup and self._path.is_file():
            common.create_backup(self._path, ext=backup_ext)

        common.set_file_content(self._path, self._content, encoding=encoding)
        self._save_needed = False

    def __repr__(self) -> str:
        return f"FileContent(filename={self.full_filename!r}, content_len={None if self._content is None else len(self._content)})"

    def __str__(self) -> str:
        base = super().__str__()
        base += f"backup option={self.backup}\n"
        base += f"save needed={self._save_needed}\n"
        if self._content is None:
            base += "Content is None\n"
        else:
            base += f"Content char number={len(self._content):6d}\n"
        return base
# -----------------------------------------------------------------------------

# =============================================================================
