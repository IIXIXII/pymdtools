"""Rendering: layouts."""

from __future__ import annotations

import logging
import os
import shutil
import sys
from collections.abc import Mapping
from html import escape
from pathlib import Path, PurePosixPath, PureWindowsPath

from .. import common
from ._files import atomic_copy_file
from ._shared import ASSET_RE, LAYOUT_ASSET_DIRECTORY, LAYOUT_NAME_RE, PLACEHOLDER_RE, TOC_RE

logger: logging.Logger = logging.getLogger(__name__)


def get_this_filename() -> Path:
    """
    Return the module filename, with frozen executable compatibility.

    Returns:
        The executable path when running from a frozen application, otherwise
        this module's path.
    """
    if getattr(sys, "frozen", False):
        return common.normpath(sys.executable)
    return common.normpath(Path(__file__).resolve().parents[1] / "mdtopdf.py")


def get_layout_page(layout: str) -> Path:
    """
    Return the ``page.html`` file for a packaged layout.

    Args:
        layout: Layout folder name under ``pymdtools/layouts``.

    Returns:
        Normalized path to the layout template.

    Raises:
        FileNotFoundError: If the requested layout cannot be found.
    """
    if not LAYOUT_NAME_RE.fullmatch(layout) or layout in {".", ".."}:
        raise ValueError(f"invalid layout name: {layout!r}")

    module_dir = get_this_filename().parent
    return common.find_file(
        "page.html",
        [module_dir, module_dir / "lib" / "pymdtools"],
        [Path("layouts") / layout],
        max_up=1,
    )


def is_windows_reserved_name(name: str) -> bool:
    """Return whether a path component is a reserved Windows device name."""
    stem = name.split(".", 1)[0].rstrip(" ").upper()
    return stem in {"CON", "PRN", "AUX", "NUL"} or (
        len(stem) == 4 and stem[:3] in {"COM", "LPT"} and stem[3] in "123456789"
    )


def validate_asset_name(name: str) -> Path:
    """
    Return a safe relative asset path from a layout placeholder.

    Args:
        name: Asset path as written in ``{{asset '...'}}``.

    Returns:
        Relative asset path.

    Raises:
        ValueError: If ``name`` is empty, absolute, or contains parent traversal.
    """
    cleaned = name.strip()
    windows_path = PureWindowsPath(cleaned)
    portable_path = PurePosixPath(cleaned.replace("\\", "/"))
    if (
        not cleaned
        or cleaned.startswith(("/", "\\"))
        or windows_path.anchor
        or windows_path.drive
        or windows_path.root
        or portable_path.is_absolute()
        or any(
            part in {".", ".."}
            or part.rstrip(" .") != part
            or is_windows_reserved_name(part)
            or any(character in part for character in '<>:"|?*')
            for part in portable_path.parts
        )
    ):
        raise ValueError(f"invalid layout asset path: {name!r}")
    return Path(*portable_path.parts)


def layout_asset_namespace(layout_path: Path) -> Path:
    """Return the portable output namespace for a layout's assets."""
    layout_name = layout_path.name
    if not LAYOUT_NAME_RE.fullmatch(layout_name) or layout_name in {".", ".."}:
        raise ValueError(f"invalid layout name: {layout_name!r}")
    return Path(LAYOUT_ASSET_DIRECTORY) / layout_name


def copy_layout_assets(layout_path: Path, path_dest: Path) -> Path:
    """Copy a complete layout asset tree into an isolated output namespace."""
    layout_root = layout_path.resolve()
    assets_root = common.check_folder(layout_root / "assets").resolve()
    if not assets_root.is_relative_to(layout_root):
        raise ValueError("layout assets resolve outside the layout folder")

    destination_root = common.check_folder(path_dest).resolve()
    namespace = layout_asset_namespace(layout_root)
    namespaced_destination = destination_root / namespace
    resolved_destination = namespaced_destination.resolve(strict=False)
    if not resolved_destination.is_relative_to(destination_root):
        raise ValueError("layout asset destination escapes the output folder")
    if namespaced_destination.is_symlink():
        raise ValueError(f"layout asset namespace must not be a symlink: {namespaced_destination}")
    if namespaced_destination.exists() and not namespaced_destination.is_dir():
        raise FileExistsError(
            f"layout asset namespace is not a directory: {namespaced_destination}"
        )
    namespaced_destination.mkdir(parents=True, exist_ok=True)

    existing_by_case: dict[str, Path] = {}
    for existing in namespaced_destination.rglob("*"):
        if existing.is_symlink():
            raise ValueError(f"layout asset destination contains a symlink: {existing}")
        relative = existing.relative_to(namespaced_destination).as_posix()
        existing_by_case[relative.casefold()] = existing

    source_by_case: dict[str, Path] = {}
    for source in sorted(assets_root.rglob("*")):
        if source.is_dir():
            continue
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"layout asset is not a regular file: {source}")
        resolved_source = source.resolve()
        if not resolved_source.is_relative_to(assets_root):
            raise ValueError(f"layout asset resolves outside its root: {source}")

        relative = validate_asset_name(source.relative_to(assets_root).as_posix())
        relative_key = relative.as_posix().casefold()
        previous_source = source_by_case.get(relative_key)
        if previous_source is not None:
            raise ValueError(
                "layout contains case-insensitive asset collision: "
                f"{previous_source.name!r} and {source.name!r}"
            )
        source_by_case[relative_key] = source

        destination = namespaced_destination / relative
        resolved_file_destination = destination.resolve(strict=False)
        if not resolved_file_destination.is_relative_to(resolved_destination):
            raise ValueError(f"layout asset destination escapes its root: {destination}")

        existing = existing_by_case.get(relative_key)
        if existing is not None:
            existing_relative = existing.relative_to(namespaced_destination).as_posix()
            if existing_relative != relative.as_posix() or not existing.is_file():
                raise FileExistsError(
                    f"layout asset collides on a case-insensitive filesystem: {destination}"
                )
            if existing.read_bytes() != source.read_bytes():
                raise FileExistsError(
                    f"layout asset would overwrite an existing file: {destination}"
                )
            continue

        destination.parent.mkdir(parents=True, exist_ok=True)
        atomic_copy_file(source, destination)
        existing_by_case[relative_key] = destination

    return namespace


def replace_layout_placeholders(
    page_html: str,
    *,
    title: str,
    content: str,
    content_vars: Mapping[str, str],
    layout_path: Path,
    path_dest: Path,
) -> str:
    """
    Replace pymdtools layout placeholders in an HTML template.

    Args:
        page_html: Layout template content.
        title: Markdown title used for ``{{title}}``.
        content: Rendered HTML fragment used for ``{{~> content}}``.
        content_vars: Variables extracted from Markdown comments.
        layout_path: Folder containing the layout's ``page.html``.
        path_dest: Destination folder for generated HTML and copied assets.

    Returns:
        HTML content with placeholders replaced.
    """
    page_html = TOC_RE.sub("", page_html)
    asset_namespace = (
        copy_layout_assets(layout_path, path_dest) if ASSET_RE.search(page_html) else None
    )

    for inst in PLACEHOLDER_RE.findall(page_html):
        logger.debug("instruction %s", inst)
        if inst == "{{title}}":
            page_html = page_html.replace(inst, escape(title, quote=True))
            continue

        if inst == "{{~> content}}":
            page_html = page_html.replace(inst, content)
            continue

        asset_match = ASSET_RE.fullmatch(inst)
        if asset_match:
            asset_rel = validate_asset_name(asset_match.group("name"))
            source_file = common.check_file(layout_path / "assets" / asset_rel)
            assets_root = (layout_path / "assets").resolve()
            if not source_file.resolve().is_relative_to(assets_root):
                raise ValueError(f"layout asset resolves outside its root: {source_file}")
            if asset_namespace is None:
                raise RuntimeError("layout asset namespace was not initialized")
            asset_url = asset_namespace / asset_rel
            page_html = page_html.replace(inst, asset_url.as_posix())
            continue

        var_name = inst[2:-2]
        if var_name in content_vars:
            page_html = page_html.replace(
                inst,
                escape(content_vars[var_name], quote=True),
            )

    return page_html


def find_wk_html_to_pdf() -> Path:
    """
    Locate the platform's ``wkhtmltopdf`` executable.

    Returns:
        Normalized executable path.

    Raises:
        FileNotFoundError: If no executable is found in the known locations.
    """
    logger.info("Search wkhtmltopdf")

    executable = shutil.which("wkhtmltopdf") or shutil.which("wkhtmltopdf.exe")
    if executable:
        return common.check_file(executable)

    module_dir = get_this_filename().parent
    start_points: list[common.PathInput] = [module_dir, module_dir.parent]
    if os.name == "nt":
        for environment_name in ("ProgramFiles", "ProgramFiles(x86)"):
            program_files = os.environ.get(environment_name)
            if program_files:
                start_points.append(Path(program_files) / "wkhtmltopdf")

    relative_paths: list[common.PathInput] = [
        ".",
        "bin",
        "wkhtmltopdf",
        "wkhtmltopdf/bin",
        "software/wkhtmltopdf/bin",
        "software/wkhtmltopdf",
        "software/bin",
        "software",
        "third_party_software/wkhtmltopdf/bin",
        "third_party_software/wkhtmltopdf",
        "third_party_software/bin",
        "third_party_software",
    ]

    executable_names = (
        ("wkhtmltopdf.exe", "wkhtmltopdf")
        if os.name == "nt"
        else ("wkhtmltopdf", "wkhtmltopdf.exe")
    )
    for executable_name in executable_names:
        try:
            return common.find_file(
                executable_name,
                start_points,
                relative_paths,
                max_up=0,
            )
        except FileNotFoundError:
            continue
    raise FileNotFoundError(
        "wkhtmltopdf was not found on PATH or in the supported local install folders"
    )
