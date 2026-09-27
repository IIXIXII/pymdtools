"""Typed options for document discovery, inclusions and PDF post-processing."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from .common.core import PathInput

DEFAULT_EXCLUDED_DIRECTORIES = (
    ".git",
    ".venv",
    ".tox",
    ".nox",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "build",
    "dist",
    "_build",
)


@dataclass(frozen=True)
class IncludeOptions:
    """Include and discovery policy; depth zero scans each configured root only.

    ``refs_depth=-1`` explicitly enables unlimited recursion. Exclusions match
    directory names or paths relative to each search root. Symlinks are skipped.
    """

    search_folders: tuple[PathInput, ...] = ()
    refs_depth: int = 0
    exclude_dirs: tuple[str, ...] = DEFAULT_EXCLUDED_DIRECTORIES
    relative_paths: tuple[str, ...] = (".", "referenced_files")
    include_cwd: bool = False
    nb_up_path: int = 0
    encoding: str | None = None
    render_mode: Literal["box", "raw"] = "box"
    error_if_no_file: bool = True

    def __post_init__(self) -> None:
        if self.refs_depth < -1:
            raise ValueError("refs_depth must be -1 or non-negative")
        if self.nb_up_path < 0:
            raise ValueError("nb_up_path must be non-negative")
        if self.render_mode not in {"box", "raw"}:
            raise ValueError("render_mode must be box or raw")


@dataclass(frozen=True)
class PdfFeatures:
    """PDF metadata and overlays, resolved relative to ``path`` when provided."""

    metadata: Mapping[str, str] | None = None
    background_pdf: PathInput | None = None
    background_first_page_pdf: PathInput | None = None
    watermark_pdf: PathInput | None = None
    path: PathInput | None = None
