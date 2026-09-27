"""Compatibility facade for common.fs.

Implementations live in common._filesystem. Public imports remain stable.
"""

from __future__ import annotations

import sys
from pathlib import Path

from ._filesystem.copying import copytree as copytree
from ._filesystem.paths import check_file as check_file
from ._filesystem.paths import check_folder as check_folder
from ._filesystem.paths import ensure_folder as ensure_folder
from ._filesystem.paths import normpath as normpath
from ._filesystem.paths import path_depth as path_depth
from ._filesystem.paths import to_path as to_path
from ._filesystem.paths import with_suffix as with_suffix
from ._filesystem.text_io import create_backup as create_backup
from ._filesystem.text_io import detect_file_encoding as detect_file_encoding
from ._filesystem.text_io import get_file_content as get_file_content
from ._filesystem.text_io import is_binary_file as is_binary_file
from ._filesystem.text_io import make_temp_dir as make_temp_dir
from ._filesystem.text_io import set_file_content as set_file_content
from ._filesystem.traversal import ApplyResult as ApplyResult
from ._filesystem.traversal import apply_to_files as apply_to_files
from ._filesystem.traversal import find_file as find_file


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


__all__ = [
    "ApplyResult",
    "apply_to_files",
    "check_file",
    "check_folder",
    "copytree",
    "create_backup",
    "detect_file_encoding",
    "ensure_folder",
    "find_file",
    "get_file_content",
    "get_this_filename",
    "is_binary_file",
    "make_temp_dir",
    "normpath",
    "path_depth",
    "set_file_content",
    "to_path",
    "with_suffix",
]
