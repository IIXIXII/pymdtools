#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                    Author: Florent TOURNOIS | License: MIT
# =============================================================================
"""
pymdtools.mdtopdf
=================

Markdown to HTML/PDF conversion helpers.

This module coordinates the conversion pipeline used by pymdtools:

- Markdown text is rendered to HTML with either Python-Markdown or Mistune.
- The HTML fragment is inserted into a packaged layout template.
- ``pdfkit`` and the external ``wkhtmltopdf`` executable render the final PDF.
- Optional PDF post-processing can apply metadata, backgrounds, and watermarks.

The module deliberately keeps external integrations at the edge:

- Markdown rendering is delegated to :mod:`markdown` or
  :mod:`pymdtools.mistune_integration`.
- File and path validation is delegated to :mod:`pymdtools.common`.
- PDF reading/writing prefers maintained ``pypdf`` and supports PyPDF2 3.x as
  a compatibility fallback.
- ``pdfkit`` is imported dynamically because it does not ship type stubs.

The public API is intentionally compatible with the historical module names:
``convert_md_to_html``, ``convert_html_to_pdf``, ``pdf_features`` and
``convert_md_to_pdf`` remain the main entry points.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import copy
from html import escape
from importlib import import_module
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, BinaryIO, cast

import logging
import os
import re
import shutil
import sys
import tempfile
import time
import warnings

from . import common
from . import instruction
from . import mistune_integration as mistune

pdfkit = cast(Any, import_module("pdfkit"))
mkd = cast(Any, import_module("markdown"))
try:
    _pdf_module = import_module("pypdf")
except ModuleNotFoundError:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        _pdf_module = import_module("PyPDF2")
PdfReader = getattr(_pdf_module, "PdfReader")
PdfWriter = getattr(_pdf_module, "PdfWriter")

MdToHtmlConverter = Callable[[str], str]

DEFAULT_LAYOUT = "jasonm23-swiss"
DEFAULT_MD_EXTENSION = ".md"
DEFAULT_HTML_EXTENSION = ".html"
DEFAULT_PDF_EXTENSION = ".pdf"
DEFAULT_HTML_ENCODING = "utf-8"

PLACEHOLDER_RE = re.compile(r"{{.*?}}")
ASSET_RE = re.compile(r"""{{\s*asset\s+['"](?P<name>.*?)['"]\s*}}""")
TOC_RE = re.compile(r"{{\s*~>\s*toc\s*}}")
LAYOUT_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
LAYOUT_ASSET_DIRECTORY = "_pymdtools_assets"
OVERLAY_OPTION_ALIASES: dict[str, str] = {
    "pdf_background": "background",
    "background_pdf": "background",
    "pdf_background_first_page": "background_first_page",
    "background_first_page_pdf": "background_first_page",
    "pdf_watermark": "watermark",
    "watermark_pdf": "watermark",
}


# -----------------------------------------------------------------------------
def _get_this_filename() -> Path:
    """
    Return the module filename, with frozen executable compatibility.

    Returns:
        The executable path when running from a frozen application, otherwise
        this module's path.
    """
    if getattr(sys, "frozen", False):
        return common.normpath(sys.executable)
    return common.normpath(__file__)


# -----------------------------------------------------------------------------
def _new_staged_path(target: Path, *, suffix: str = ".tmp") -> Path:
    """Reserve a temporary sibling path suitable for an atomic replace."""
    target.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, staged_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=suffix,
        dir=target.parent,
    )
    os.close(file_descriptor)
    return Path(staged_name)


# -----------------------------------------------------------------------------
def _commit_staged_file(staged: Path, target: Path) -> None:
    """Atomically replace ``target`` with a fully written sibling file."""
    if target.exists():
        if not target.is_file():
            raise IsADirectoryError(f"destination is not a file: {target}")
        shutil.copymode(target, staged)
    staged.replace(target)


# -----------------------------------------------------------------------------
def _atomic_copy_file(source: Path, target: Path) -> None:
    """Copy a file and expose it at ``target`` only after a complete write."""
    staged = _new_staged_path(target, suffix=target.suffix + ".tmp")
    try:
        shutil.copy2(source, staged)
        _commit_staged_file(staged, target)
    finally:
        staged.unlink(missing_ok=True)


# -----------------------------------------------------------------------------
def _validate_pdf_file(path: Path, *, require_pages: bool = True) -> None:
    """Raise a stable error when ``path`` is not a readable PDF."""
    try:
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError("empty output")
        with path.open("rb") as stream:
            reader = PdfReader(stream)
            page_count = len(reader.pages)
    except Exception as error:
        raise RuntimeError(f"invalid PDF output: {path.name}") from error
    if require_pages and page_count == 0:
        raise ValueError("PDF must contain at least one page")


# -----------------------------------------------------------------------------
def _stage_pdf_writer(writer: Any, target: Path) -> Path:
    """Write and validate a PDF in a temporary sibling of ``target``."""
    staged = _new_staged_path(target, suffix=DEFAULT_PDF_EXTENSION + ".tmp")
    try:
        with staged.open("wb") as stream:
            writer.write(stream)
            stream.flush()
            os.fsync(stream.fileno())
        _validate_pdf_file(staged)
        return staged
    except Exception:
        staged.unlink(missing_ok=True)
        raise


# -----------------------------------------------------------------------------
def _write_pdf_writer_atomic(writer: Any, target: Path) -> None:
    """Write a PDF writer to ``target`` using an atomic sibling replace."""
    staged = _stage_pdf_writer(writer, target)
    try:
        _commit_staged_file(staged, target)
    finally:
        staged.unlink(missing_ok=True)


# -----------------------------------------------------------------------------
def _write_text_atomic(
    target: Path,
    content: str,
    *,
    encoding: str,
) -> None:
    """Write generated HTML atomically while preserving encoding fallback."""
    staged = _new_staged_path(target)
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
        _commit_staged_file(staged, target)
    finally:
        staged.unlink(missing_ok=True)


# -----------------------------------------------------------------------------
def _get_layout_page(layout: str) -> Path:
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

    module_dir = _get_this_filename().parent
    return common.find_file(
        "page.html",
        [module_dir, module_dir / "lib" / "pymdtools"],
        [Path("layouts") / layout],
        max_up=1,
    )


# -----------------------------------------------------------------------------
def _is_windows_reserved_name(name: str) -> bool:
    """Return whether a path component is a reserved Windows device name."""
    stem = name.split(".", 1)[0].rstrip(" ").upper()
    return stem in {"CON", "PRN", "AUX", "NUL"} or (
        len(stem) == 4
        and stem[:3] in {"COM", "LPT"}
        and stem[3] in "123456789"
    )


# -----------------------------------------------------------------------------
def _validate_asset_name(name: str) -> Path:
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
            or _is_windows_reserved_name(part)
            or any(character in part for character in '<>:"|?*')
            for part in portable_path.parts
        )
    ):
        raise ValueError(f"invalid layout asset path: {name!r}")
    return Path(*portable_path.parts)


# -----------------------------------------------------------------------------
def _layout_asset_namespace(layout_path: Path) -> Path:
    """Return the portable output namespace for a layout's assets."""
    layout_name = layout_path.name
    if not LAYOUT_NAME_RE.fullmatch(layout_name) or layout_name in {".", ".."}:
        raise ValueError(f"invalid layout name: {layout_name!r}")
    return Path(LAYOUT_ASSET_DIRECTORY) / layout_name


# -----------------------------------------------------------------------------
def _copy_layout_assets(layout_path: Path, path_dest: Path) -> Path:
    """Copy a complete layout asset tree into an isolated output namespace."""
    layout_root = layout_path.resolve()
    assets_root = common.check_folder(layout_root / "assets").resolve()
    if not assets_root.is_relative_to(layout_root):
        raise ValueError("layout assets resolve outside the layout folder")

    destination_root = common.check_folder(path_dest).resolve()
    namespace = _layout_asset_namespace(layout_root)
    namespaced_destination = destination_root / namespace
    resolved_destination = namespaced_destination.resolve(strict=False)
    if not resolved_destination.is_relative_to(destination_root):
        raise ValueError("layout asset destination escapes the output folder")
    if namespaced_destination.is_symlink():
        raise ValueError(
            f"layout asset namespace must not be a symlink: {namespaced_destination}"
        )
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

        relative = _validate_asset_name(source.relative_to(assets_root).as_posix())
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
            existing_relative = existing.relative_to(
                namespaced_destination
            ).as_posix()
            if existing_relative != relative.as_posix() or not existing.is_file():
                raise FileExistsError(
                    "layout asset collides on a case-insensitive filesystem: "
                    f"{destination}"
                )
            if existing.read_bytes() != source.read_bytes():
                raise FileExistsError(
                    f"layout asset would overwrite an existing file: {destination}"
                )
            continue

        destination.parent.mkdir(parents=True, exist_ok=True)
        _atomic_copy_file(source, destination)
        existing_by_case[relative_key] = destination

    return namespace


# -----------------------------------------------------------------------------
def _replace_layout_placeholders(
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
        _copy_layout_assets(layout_path, path_dest)
        if ASSET_RE.search(page_html)
        else None
    )

    for inst in PLACEHOLDER_RE.findall(page_html):
        logging.debug("instruction %s", inst)
        if inst == "{{title}}":
            page_html = page_html.replace(inst, escape(title, quote=True))
            continue

        if inst == "{{~> content}}":
            page_html = page_html.replace(inst, content)
            continue

        asset_match = ASSET_RE.fullmatch(inst)
        if asset_match:
            asset_rel = _validate_asset_name(asset_match.group("name"))
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


# -----------------------------------------------------------------------------
def _read_pdf(path: common.PathInput) -> tuple[Any, BinaryIO]:
    """
    Open a PDF file and return its reader plus the owned file handle.

    Args:
        path: PDF file to open.

    Returns:
        ``(reader, handle)``. The caller must close ``handle``.
    """
    handle = open(path, "rb")
    try:
        return PdfReader(handle), handle
    except Exception:
        handle.close()
        raise


# -----------------------------------------------------------------------------
def check_odd_pages(filename: common.PathInput) -> Path:
    """
    Ensure that a PDF has an even number of pages.

    If the PDF has an odd page count, a backup is created and one blank page is
    appended to the original file.

    Args:
        filename: PDF file to inspect and possibly modify.

    Returns:
        Normalized PDF path.
    """
    pdf_path = common.check_file(filename, expected_ext=DEFAULT_PDF_EXTENSION)

    with pdf_path.open("rb") as input_pdf:
        pdf = PdfReader(input_pdf)
        num_pages = len(pdf.pages)

    if num_pages % 2 == 0:
        return pdf_path

    backup_filename = common.create_backup(pdf_path)
    with open(backup_filename, "rb") as in_pdf:
        pdf_init = PdfReader(in_pdf)
        out_pdf = PdfWriter()
        out_pdf.append_pages_from_reader(pdf_init)
        out_pdf.add_blank_page()
        _write_pdf_writer_atomic(out_pdf, pdf_path)

    return pdf_path


# -----------------------------------------------------------------------------
def converter_md_to_html_markdown(text: str) -> str:
    """
    Convert Markdown text to HTML with Python-Markdown.

    Args:
        text: Markdown text.

    Returns:
        HTML fragment.
    """
    return mkd.markdown(text, output_format="xhtml")


# -----------------------------------------------------------------------------
def converter_md_to_html_mistune(text: str) -> str:
    """
    Convert Markdown text to HTML with Mistune.

    Args:
        text: Markdown text.

    Returns:
        HTML fragment.
    """
    renderer = mistune.ClosingHTMLRenderer()
    markdown = mistune.create_markdown_with_close(renderer=renderer)
    return cast(str, markdown(text))


_MD_TO_HTML_CONVERTERS: dict[str, MdToHtmlConverter] = {
    "markdown": converter_md_to_html_markdown,
    "mistune": converter_md_to_html_mistune,
}


# -----------------------------------------------------------------------------
def get_md_to_html_converter(converter_name: str | None) -> MdToHtmlConverter:
    """
    Return a Markdown-to-HTML converter by name.

    Unknown names fall back to the escaping Mistune converter. The classic
    Python-Markdown converter remains available explicitly as ``"markdown"``
    for trusted input that intentionally contains raw HTML.

    Args:
        converter_name: Converter name, usually ``"markdown"`` or ``"mistune"``.

    Returns:
        Converter function.
    """
    if converter_name not in _MD_TO_HTML_CONVERTERS:
        logging.info("Converter %s does not exist", converter_name)
        logging.info("Converter changed to safe mistune renderer")
        converter_name = "mistune"
    return _MD_TO_HTML_CONVERTERS[converter_name]


# -----------------------------------------------------------------------------
def convert_md_to_html(
    filename: common.PathInput,
    layout: str = DEFAULT_LAYOUT,
    filename_ext: str = DEFAULT_MD_EXTENSION,
    encoding: str = DEFAULT_HTML_ENCODING,
    path_dest: common.PathInput | None = None,
    converter: str | None = None,
) -> Path:
    """
    Convert a Markdown file to an HTML file using a packaged layout.

    Args:
        filename: Markdown file to convert.
        layout: Layout folder name under ``pymdtools/layouts``.
        filename_ext: Expected Markdown extension.
        encoding: Encoding used for the generated HTML file.
        path_dest: Destination folder. Defaults to the Markdown file folder.
        converter: Markdown renderer name. Unknown names fall back to
            the escaping Mistune renderer.

    Returns:
        Generated HTML file path.

    Raises:
        ValueError: If the Markdown file is empty or a layout asset path is
            invalid.
        FileNotFoundError: If the source file, layout, or asset is missing.
    """
    logging.info("Convert md -> html %s", filename)

    md_filename = common.check_file(filename, filename_ext)
    destination = (
        common.check_folder(md_filename.parent)
        if path_dest is None
        else common.check_folder(path_dest)
    )

    content = common.get_file_content(md_filename)
    content_vars = instruction.get_vars_from_md_text(content)
    title = cast(str | None, instruction.get_title_from_md_text(content))
    if title is None:
        title = ""

    if len(content) == 0:
        logging.error("The filename %s seems empty", md_filename)
        raise ValueError(f"The filename {md_filename} seems empty")

    rendered_content = get_md_to_html_converter(converter)(content)

    page_html_filename = _get_layout_page(layout)
    layout_path = common.check_folder(page_html_filename.parent)
    page_html = common.get_file_content(page_html_filename)
    page_html = _replace_layout_placeholders(
        page_html,
        title=title,
        content=rendered_content,
        content_vars=content_vars,
        layout_path=layout_path,
        path_dest=destination,
    )

    html_filename = common.normpath(destination / f"{md_filename.stem}.html")
    logging.info("        -> html %s", html_filename)

    _write_text_atomic(html_filename, page_html, encoding=encoding)

    return html_filename


# -----------------------------------------------------------------------------
def find_wk_html_to_pdf() -> Path:
    """
    Locate the platform's ``wkhtmltopdf`` executable.

    Returns:
        Normalized executable path.

    Raises:
        FileNotFoundError: If no executable is found in the known locations.
    """
    logging.info("Search wkhtmltopdf")

    executable = shutil.which("wkhtmltopdf") or shutil.which("wkhtmltopdf.exe")
    if executable:
        return common.check_file(executable)

    module_dir = _get_this_filename().parent
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


# -----------------------------------------------------------------------------
def convert_html_to_pdf(
    filename: common.PathInput,
    filename_ext: str = DEFAULT_HTML_EXTENSION,
    **kwargs: Any,
) -> Path:
    """
    Convert an HTML file to a PDF file next to it.

    Args:
        filename: HTML file to convert.
        filename_ext: Expected HTML extension.
        **kwargs: Optional options. ``title`` customizes the PDF header text.

    Returns:
        Generated PDF file path.
    """
    logging.info("Convert html -> pdf %s", filename)
    html_filename = common.check_file(filename, filename_ext)

    config = pdfkit.configuration(wkhtmltopdf=find_wk_html_to_pdf())

    title_arg = kwargs.get("title")
    header_text = (
        str(title_arg)
        if title_arg is not None
        else html_filename.stem
    )

    date_print = time.strftime("%d/%m/%Y", time.gmtime())
    options: dict[str, str] = {
        # Permit the generated HTML to load only sibling layout assets rather
        # than enabling unrestricted local-file access.
        "allow": str(html_filename.parent),
        "header-center": header_text,
        "footer-center": "page [page] sur [toPage]",
        "footer-font-size": "8",
        "footer-right": date_print,
        "margin-top": "20mm",
        "margin-bottom": "20mm",
        "footer-spacing": "10",
        "header-spacing": "10",
        "header-font-size": "8",
        "quiet": "",
    }

    pdf_filename = html_filename.with_suffix(DEFAULT_PDF_EXTENSION)
    staged_pdf = _new_staged_path(pdf_filename, suffix=DEFAULT_PDF_EXTENSION)
    try:
        pdfkit.from_file(
            html_filename,
            str(staged_pdf),
            options=options,
            configuration=config,
        )
        _validate_pdf_file(staged_pdf)
        _commit_staged_file(staged_pdf, pdf_filename)
    finally:
        staged_pdf.unlink(missing_ok=True)
    logging.info("Conversion finished for %s", html_filename)

    return pdf_filename


# -----------------------------------------------------------------------------
def _metadata_from_kwargs(
    source_metadata: Mapping[Any, Any],
    requested_metadata: Mapping[Any, Any] | None,
) -> dict[str, str]:
    """
    Build PDF metadata from existing and requested metadata.
    """
    metadata = {
        str(key): str(value)
        for key, value in source_metadata.items()
        if value is not None
    }
    if requested_metadata:
        for key, value in requested_metadata.items():
            normalized = str(key).lstrip("/")
            if not normalized:
                raise ValueError("PDF metadata keys must not be empty")
            metadata[f"/{normalized[0].upper()}{normalized[1:]}"] = str(value)
    return metadata


# -----------------------------------------------------------------------------
def _page_with_background(
    page: Any,
    background: Any,
    writer: Any | None = None,
) -> Any:
    """Return a page with ``background`` below the original page content."""
    if not background.pages:
        raise ValueError("background PDF must contain at least one page")
    if writer is None:
        background_page = copy(background.pages[0])
    else:
        writer.add_page(background.pages[0])
        background_page = writer.pages[-1]
    background_page.merge_page(page)
    return background_page


# -----------------------------------------------------------------------------
def _collect_overlay_pdfs(
    kwargs: Mapping[str, Any],
) -> tuple[dict[str, Any], list[BinaryIO]]:
    """
    Collect background/watermark PDFs from ``pdf_*`` and ``*_pdf`` options.
    """
    unknown_overlay_options = [
        key
        for key in kwargs
        if (key.startswith("pdf_") or key.endswith("_pdf"))
        and key not in OVERLAY_OPTION_ALIASES
    ]
    if unknown_overlay_options:
        raise ValueError(
            f"unsupported PDF overlay option: {unknown_overlay_options[0]!r}"
        )

    pdf_args: dict[str, Any] = {}
    overlay_paths: dict[str, Path] = {}
    handles: list[BinaryIO] = []
    try:
        for option_name, arg_name in OVERLAY_OPTION_ALIASES.items():
            value = kwargs.get(option_name)
            if value is None:
                continue

            local_name = Path(cast(common.PathInput, value))
            base_path = kwargs.get("path")
            if base_path is not None and not local_name.is_absolute():
                local_name = Path(cast(common.PathInput, base_path)) / local_name
            local_path = common.check_file(
                local_name,
                expected_ext=DEFAULT_PDF_EXTENSION,
            ).resolve()

            previous_path = overlay_paths.get(arg_name)
            if previous_path is not None:
                if previous_path != local_path:
                    raise ValueError(
                        f"conflicting aliases for PDF overlay {arg_name!r}"
                    )
                continue

            reader, handle = _read_pdf(local_path)
            if not reader.pages:
                handle.close()
                raise ValueError(
                    f"PDF overlay {option_name!r} must contain at least one page"
                )
            handles.append(handle)
            pdf_args[arg_name] = reader
            overlay_paths[arg_name] = local_path

        return pdf_args, handles
    except Exception:
        for handle in handles:
            handle.close()
        raise


# -----------------------------------------------------------------------------
def pdf_features(
    filename: common.PathInput,
    filename_ext: str = DEFAULT_PDF_EXTENSION,
    **kwargs: Any,
) -> Path:
    """
    Apply PDF metadata, backgrounds, and watermarks in-place.

    Supported overlay arguments:

    - ``pdf_background`` or ``background_pdf``
    - ``pdf_background_first_page`` or ``background_first_page_pdf``
    - ``pdf_watermark`` or ``watermark_pdf``

    Args:
        filename: PDF file to update.
        filename_ext: Expected PDF extension.
        **kwargs: Feature options. ``metadata`` accepts a mapping of metadata
            keys without leading slash.

    Returns:
        Updated PDF file path.
    """
    logging.info("pdf features %s", filename)
    pdf_filename = common.check_file(filename, filename_ext)
    requested_metadata_value = kwargs.get("metadata")
    if requested_metadata_value is not None and not isinstance(
        requested_metadata_value,
        Mapping,
    ):
        raise TypeError("metadata must be a mapping")
    requested_metadata = cast(
        Mapping[Any, Any] | None,
        requested_metadata_value,
    )

    temp_dir = common.make_temp_dir()
    handles: list[BinaryIO] = []
    try:
        temp_pdf_filename = Path(temp_dir) / pdf_filename.name
        shutil.copy2(pdf_filename, temp_pdf_filename)

        pdf_reader, source_handle = _read_pdf(temp_pdf_filename)
        handles.append(source_handle)
        if not pdf_reader.pages:
            raise ValueError("source PDF must contain at least one page")

        metadata = _metadata_from_kwargs(
            pdf_reader.metadata or {},
            requested_metadata,
        )

        pdf_args, overlay_handles = _collect_overlay_pdfs(kwargs)
        handles.extend(overlay_handles)

        pdf_writer = PdfWriter()

        for page_number, page in enumerate(pdf_reader.pages):
            background = None
            if page_number == 0:
                if "background_first_page" in pdf_args:
                    background = pdf_args["background_first_page"]
                elif "background" in pdf_args:
                    background = pdf_args["background"]
            else:
                if "background" in pdf_args:
                    background = pdf_args["background"]

            if background is not None:
                page = _page_with_background(page, background, pdf_writer)
            else:
                pdf_writer.add_page(page)
                page = pdf_writer.pages[-1]

            if "watermark" in pdf_args:
                page.merge_page(pdf_args["watermark"].pages[0])

        pdf_writer.add_metadata(metadata)
        staged_output = _stage_pdf_writer(pdf_writer, pdf_filename)
    finally:
        for handle in handles:
            handle.close()
        shutil.rmtree(temp_dir, ignore_errors=True)

    try:
        _commit_staged_file(staged_output, pdf_filename)
    finally:
        staged_output.unlink(missing_ok=True)

    return pdf_filename


# -----------------------------------------------------------------------------
def convert_md_to_pdf(
    filename: common.PathInput,
    filename_ext: str = DEFAULT_MD_EXTENSION,
    **kwargs: Any,
) -> Path:
    """
    Convert a Markdown file to PDF.

    The conversion is performed in a temporary folder, then the generated PDF is
    copied next to the source Markdown file and post-processed with
    :func:`pdf_features`.

    Args:
        filename: Markdown file to convert.
        filename_ext: Expected Markdown extension.
        **kwargs: Options forwarded to :func:`pdf_features`.

    Returns:
        Generated PDF path.
    """
    logging.info("Convert md -> pdf %s", filename)
    md_filename = common.check_file(filename, filename_ext)
    md_metadata = instruction.get_vars_from_md_file(md_filename)
    feature_options = dict(kwargs)
    requested_metadata = feature_options.pop("metadata", None)
    if requested_metadata is not None and not isinstance(
        requested_metadata,
        Mapping,
    ):
        raise TypeError("metadata must be a mapping")
    combined_metadata = dict(md_metadata)
    if requested_metadata is not None:
        requested_metadata_mapping = cast(Mapping[Any, Any], requested_metadata)
        combined_metadata.update(
            {
                str(key): str(value)
                for key, value in requested_metadata_mapping.items()
            }
        )

    temp_dir = common.make_temp_dir()
    pdf_filename = md_filename.with_suffix(DEFAULT_PDF_EXTENSION)
    try:
        temp_md_filename = Path(temp_dir) / md_filename.name

        logging.info("Copy file to temp")
        shutil.copy2(md_filename, temp_md_filename)
        logging.info("Convert md to html")
        temp_html_filename = convert_md_to_html(
            temp_md_filename,
            converter="mistune",
        )

        title = None
        if "title" in md_metadata:
            title = md_metadata["title"]
        if "page:title" in md_metadata:
            title = md_metadata["page:title"]

        logging.info("Convert html to pdf title=%s", title)
        temp_pdf_filename = convert_html_to_pdf(temp_html_filename, title=title)

        pdf_features(
            temp_pdf_filename,
            filename_ext=DEFAULT_PDF_EXTENSION,
            metadata=combined_metadata,
            **feature_options,
        )
        _validate_pdf_file(temp_pdf_filename)

        logging.info("Copy file from temp")
        _atomic_copy_file(temp_pdf_filename, pdf_filename)
    finally:
        logging.info("Remove the temp dir")
        shutil.rmtree(temp_dir, ignore_errors=True)

    return pdf_filename


# -----------------------------------------------------------------------------
def __get_this_filename() -> str:
    """Return this module filename as text for legacy callers."""
    return str(_get_this_filename())


__all__ = [
    "__get_this_filename",
    "check_odd_pages",
    "convert_html_to_pdf",
    "convert_md_to_html",
    "convert_md_to_pdf",
    "converter_md_to_html_markdown",
    "converter_md_to_html_mistune",
    "find_wk_html_to_pdf",
    "get_md_to_html_converter",
    "pdf_features",
]


# =============================================================================
