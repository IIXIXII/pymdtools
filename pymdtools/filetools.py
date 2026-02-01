#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                    Author: Florent TOURNOIS | License: MIT                   
# =============================================================================

# -----------------------------------------------------------------------------
# standard object to wrap file and access easily to the filename
# -----------------------------------------------------------------------------

import logging
import sys
import os
import os.path
from pathlib import Path
from typing import Optional, Union, List
from dataclasses import dataclass

from . import common

# -----------------------------------------------------------------------------
def _get_this_filename() -> str:
    """
    Return the filename of the current module or executable.

    If the application is running in a frozen environment (e.g. PyInstaller),
    the path to the executable is returned. Otherwise, the path to this module
    file is returned.

    Returns:
        Absolute path to the current module file or executable.
    """
    if getattr(sys, "frozen", False):
        return str(Path(sys.executable).resolve())

    return str(Path(__file__).resolve())
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def get_template_file(filename: str, start_folder: Optional[Union[str, Path]] = None) -> str:
    """
    Read a template file from a `template/` folder.

    The template folder is resolved as:
    - `<start_folder>/template` if `start_folder` is provided,
    - otherwise `<module_folder>/template`.

    Args:
        filename: Template filename to read (relative to the template folder).
        start_folder: Base folder used to locate the `template/` directory.

    Returns:
        The template file content as a string.

    Raises:
        ValueError: If `filename` is empty.
        RuntimeError: If the template folder does not exist or is not a directory.
        Exception/IOError: Propagated from file reading helpers.
    """
    if not isinstance(filename, str) or not filename.strip():
        raise ValueError("filename must be a non-empty string")

    if start_folder is None:
        base = Path(_get_this_filename()).resolve().parent
    else:
        base = Path(start_folder)

    template_dir = common.ensure_folder(str(base / "template"))
    return common.get_file_content(str(Path(template_dir) / filename))
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def get_template_files_in_folder(folder: str) -> List[str]:
    """
    List template files contained in `template/<folder>`.

    Args:
        folder: Subfolder name under the local `template/` directory.

    Returns:
        A list of relative template paths (POSIX-style), e.g. ["emails/a.html"].
        The result is sorted for determinism.

    Raises:
        RuntimeError: If the template folder does not exist or is not a directory.
    """
    template_dir = Path(_get_this_filename()).resolve().parent / "template" / folder
    local_template_folder = Path(common.check_folder(str(template_dir)))

    files: List[str] = []
    for p in sorted(local_template_folder.iterdir(), key=lambda x: x.name):
        if p.is_file():
            files.append((Path(folder) / p.name).as_posix())

    return files
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
@dataclass
class FileName:
    """
    Utility object to manipulate a file path.

    The object stores a normalized path string (via `common.normpath`) and exposes
    convenient properties to update the filename, directory and suffix.
    """
    _full: Optional[str] = None

    def __init__(self, filename: Optional[Union[str, Path]] = None):
        self._full = None
        if filename is not None:
            self.full_filename = filename

    @property
    def full_filename(self) -> Optional[str]:
        return self._full

    @full_filename.setter
    def full_filename(self, value: Optional[Union[str, Path]]) -> None:
        if value is None:
            self._full = None
            return
        self._full = common.normpath(str(value))

    @property
    def filename(self) -> Optional[str]:
        if self._full is None:
            return None
        return Path(self._full).name

    @filename.setter
    def filename(self, value: Optional[str]) -> None:
        if value is None:
            self._full = None
            return

        safe_name = common.get_valid_filename(value)

        if self._full is None:
            self._full = common.normpath(safe_name)
        else:
            p = Path(self._full)
            self._full = common.normpath(str(p.with_name(safe_name)))

    @property
    def filename_path(self) -> Optional[str]:
        if self._full is None:
            return None
        return str(Path(self._full).parent)

    @filename_path.setter
    def filename_path(self, value: Union[str, Path]) -> None:
        if value is None:
            raise ValueError("filename_path cannot be None")
        if self._full is None:
            raise ValueError("cannot set filename_path when full_filename is None")

        base = Path(common.normpath(str(value)))
        self._full = common.normpath(str(base / Path(self._full).name))

    @property
    def filename_ext(self) -> Optional[str]:
        if self._full is None:
            return None
        return Path(self._full).suffix

    @filename_ext.setter
    def filename_ext(self, value: str) -> None:
        if value is None or value == "":
            raise ValueError("filename_ext cannot be empty")
        if not value.startswith("."):
            raise ValueError(f"filename_ext must start with '.', got: {value!r}")
        if self._full is None:
            raise ValueError("cannot set filename_ext when full_filename is None")

        p = Path(self._full)
        self._full = common.normpath(str(p.with_suffix(value)))

    def is_file(self) -> bool:
        return self._full is not None and Path(self._full).is_file()

    def is_dir(self) -> bool:
        return self._full is not None and Path(self._full).is_dir()

    def __repr__(self) -> str:
        return f"FileName({self._full!r})"

    def __str__(self) -> str:
        if self._full is None:
            return "path=<None>\nfilename=<None>\nfile extension=<None>\n"

        p = Path(self._full)
        lines = [
            f"          path={str(p.parent)}",
            f"      filename={p.name}",
            f"file extension={p.suffix}",
        ]
        if p.is_dir():
            lines.append("It is a directory")
        elif p.is_file():
            lines.append("The file exists")
        else:
            lines.append("The file or the directory does not exist")
        return "\n".join(lines) + "\n"
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------

class FileContent(FileName):
    """
    File wrapper that holds text content and supports read/write with optional backups.

    - If instantiated with an existing filename and `content is None`, the file is read.
    - If `backup=True`, `write()` creates a numbered backup when overwriting an existing file.
    - `save_needed` tracks whether in-memory content differs from the last read/write.
    """

    def __init__(
        self,
        filename: Optional[Union[str, Path]] = None,
        content: Optional[str] = None,
        *,
        backup: bool = True,
        encoding: str = "utf-8",
    ) -> None:
        super().__init__(filename=filename)

        self._content: Optional[str] = None
        self._backup: bool = bool(backup)
        self._save_needed: bool = False

        if self.is_file() and content is None:
            self._content = common.get_file_content(self.full_filename, encoding=encoding)
            self._save_needed = False

        if content is not None:
            self.content = content  # sets save_needed

    @property
    def content(self) -> Optional[str]:
        return self._content

    @content.setter
    def content(self, value: Optional[str]) -> None:
        self._content = value
        self._save_needed = True

    @property
    def backup(self) -> bool:
        return self._backup

    @backup.setter
    def backup(self, value: bool) -> None:
        self._backup = bool(value)

    @property
    def save_needed(self) -> bool:
        return self._save_needed

    @save_needed.setter
    def save_needed(self, value: bool) -> None:
        self._save_needed = bool(value)

    def read(self, filename: Optional[Union[str, Path]] = None, *, encoding: str = "utf-8") -> None:
        if filename is not None:
            self.full_filename = filename

        if self.full_filename is None:
            raise ValueError("cannot read content without a filename")

        self._content = common.get_file_content(self.full_filename, encoding=encoding)
        self._save_needed = False

    def write(
        self,
        filename: Optional[Union[str, Path]] = None,
        *,
        encoding: str = "utf-8",
        backup_ext: str = ".bak",
    ) -> None:
        if filename is not None:
            self.full_filename = filename

        if self.full_filename is None:
            raise ValueError("cannot write content without a filename")

        if self._content is None:
            raise ValueError("cannot write: content is None")

        if self.backup and Path(self.full_filename).is_file():
            common.create_backup(self.full_filename, backup_ext=backup_ext)

        common.set_file_content(self.full_filename, self._content, encoding=encoding)
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
