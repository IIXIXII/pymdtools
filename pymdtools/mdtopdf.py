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
- PDF reading/writing uses the modern PyPDF2 3.x API.
- ``pdfkit`` is imported dynamically because it does not ship type stubs.

The public API is intentionally compatible with the historical module names:
``convert_md_to_html``, ``convert_html_to_pdf``, ``pdf_features`` and
``convert_md_to_pdf`` remain the main entry points.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from importlib import import_module
from pathlib import Path
from typing import Any, BinaryIO, cast

import logging
import re
import shutil
import sys
import time

import markdown as mkd
from PyPDF2 import PdfReader, PdfWriter

from . import common
from . import instruction
from . import mistune_integration as mistune

pdfkit = cast(Any, import_module("pdfkit"))

MdToHtmlConverter = Callable[[str], str]

DEFAULT_LAYOUT = "jasonm23-swiss"
DEFAULT_MD_EXTENSION = ".md"
DEFAULT_HTML_EXTENSION = ".html"
DEFAULT_PDF_EXTENSION = ".pdf"
DEFAULT_HTML_ENCODING = "utf-8"

PLACEHOLDER_RE = re.compile(r"{{.*?}}")
ASSET_RE = re.compile(r"""{{\s*asset\s+['"](?P<name>.*?)['"]\s*}}""")


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
    module_dir = _get_this_filename().parent
    return common.find_file(
        "page.html",
        [module_dir, module_dir / "lib" / "pymdtools"],
        [Path("layouts") / layout],
        max_up=1,
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
    cleaned = name.strip().lstrip("/\\")
    rel = Path(cleaned)
    if not cleaned or rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"invalid layout asset path: {name!r}")
    return rel


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
    for inst in PLACEHOLDER_RE.findall(page_html):
        logging.debug("instruction %s", inst)
        if inst == "{{title}}":
            page_html = page_html.replace(inst, title)
            continue

        if inst == "{{~> content}}":
            page_html = page_html.replace(inst, content)
            continue

        asset_match = ASSET_RE.fullmatch(inst)
        if asset_match:
            asset_rel = _validate_asset_name(asset_match.group("name"))
            src_file = common.check_file(layout_path / "assets" / asset_rel)
            dst_file = common.normpath(path_dest / asset_rel)
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src_file, dst_file)
            page_html = page_html.replace(inst, asset_rel.as_posix())
            continue

        var_name = inst[2:-2]
        if var_name in content_vars:
            page_html = page_html.replace(inst, content_vars[var_name])

    return page_html


# -----------------------------------------------------------------------------
def _read_pdf(path: common.PathInput) -> tuple[PdfReader, BinaryIO]:
    """
    Open a PDF file and return its reader plus the owned file handle.

    Args:
        path: PDF file to open.

    Returns:
        ``(reader, handle)``. The caller must close ``handle``.
    """
    handle = open(path, "rb")
    return PdfReader(handle), handle


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

        with pdf_path.open("wb") as out_stream:
            cast(Any, out_pdf).write(out_stream)

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

    Unknown names fall back to the classic Python-Markdown converter for
    backward compatibility.

    Args:
        converter_name: Converter name, usually ``"markdown"`` or ``"mistune"``.

    Returns:
        Converter function.
    """
    if converter_name not in _MD_TO_HTML_CONVERTERS:
        logging.info("Converter %s does not exist", converter_name)
        logging.info("Converter changed to classic markdown")
        converter_name = "markdown"
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
            ``"markdown"``.

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

    with html_filename.open(
        "w",
        encoding=encoding,
        errors="xmlcharrefreplace",
    ) as output_file:
        output_file.write(page_html)

    return html_filename


# -----------------------------------------------------------------------------
def find_wk_html_to_pdf() -> Path:
    """
    Locate the ``wkhtmltopdf.exe`` executable.

    Returns:
        Normalized path to ``wkhtmltopdf.exe``.

    Raises:
        FileNotFoundError: If no executable is found in the known locations.
    """
    logging.info("Search wkhtmltopdf")

    start_points: list[common.PathInput] = [
        r"C:\Program Files\wkhtmltopdf",
        ".",
        __get_this_filename(),
        r"D:\Program Files\wkhtmltopdf",
    ]

    relative_paths: list[common.PathInput] = [
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

    return common.find_file(
        "wkhtmltopdf.exe",
        start_points,
        relative_paths,
        max_up=4,
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
    pdfkit.from_file(
        html_filename,
        str(pdf_filename),
        options=options,
        configuration=config,
    )
    logging.info("Conversion finished for %s", html_filename)

    return pdf_filename


# -----------------------------------------------------------------------------
def _metadata_from_kwargs(
    source_metadata: Mapping[Any, Any],
    requested_metadata: Mapping[str, str] | None,
) -> dict[str, str]:
    """
    Build PyPDF2 metadata from existing and requested metadata.
    """
    metadata = {str(key): "" for key in source_metadata}
    if requested_metadata:
        for key, value in requested_metadata.items():
            metadata[f"/{key[0].upper()}{key[1:]}"] = value
    return metadata


# -----------------------------------------------------------------------------
def _collect_overlay_pdfs(
    kwargs: Mapping[str, Any],
) -> tuple[dict[str, PdfReader], list[BinaryIO]]:
    """
    Collect background/watermark PDFs from ``pdf_*`` and ``*_pdf`` options.
    """
    pdf_args: dict[str, PdfReader] = {}
    handles: list[BinaryIO] = []

    for key, value in kwargs.items():
        if key.startswith("pdf_"):
            arg_name = key[4:]
        elif key.endswith("_pdf"):
            arg_name = key[:-4]
        else:
            continue

        local_name = value
        if "path" in kwargs:
            local_name = Path(cast(common.PathInput, kwargs["path"])) / str(local_name)
        local_path = common.check_file(cast(common.PathInput, local_name))
        reader, handle = _read_pdf(local_path)
        handles.append(handle)
        pdf_args[arg_name] = reader

    return pdf_args, handles


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

    temp_dir = common.make_temp_dir()
    handles: list[BinaryIO] = []
    try:
        temp_pdf_filename = Path(temp_dir) / pdf_filename.name
        shutil.copy(pdf_filename, temp_pdf_filename)

        pdf_reader, source_handle = _read_pdf(temp_pdf_filename)
        handles.append(source_handle)

        requested_metadata = cast(
            Mapping[str, str] | None,
            kwargs.get("metadata"),
        )
        metadata = _metadata_from_kwargs(
            pdf_reader.metadata or {},
            requested_metadata,
        )

        pdf_args, overlay_handles = _collect_overlay_pdfs(kwargs)
        handles.extend(overlay_handles)

        pdf_writer = PdfWriter()

        for page_number, page in enumerate(pdf_reader.pages):
            if page_number == 0:
                if "background_first_page" in pdf_args:
                    page.merge_page(pdf_args["background_first_page"].pages[0])
                elif "background" in pdf_args:
                    page.merge_page(pdf_args["background"].pages[0])
            else:
                if "background" in pdf_args:
                    page.merge_page(pdf_args["background"].pages[0])

            if "watermark" in pdf_args:
                page.merge_page(pdf_args["watermark"].pages[0])

            pdf_writer.add_page(page)

        pdf_writer.add_metadata(metadata)

        with pdf_filename.open("wb") as file_out:
            cast(Any, pdf_writer).write(file_out)
    finally:
        for handle in handles:
            handle.close()
        shutil.rmtree(temp_dir, ignore_errors=True)

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

    temp_dir = common.make_temp_dir()
    try:
        temp_md_filename = Path(temp_dir) / md_filename.name

        logging.info("Copy file to temp")
        shutil.copy(md_filename, temp_md_filename)
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

        logging.info("Copy file from temp")
        pdf_filename = md_filename.with_suffix(DEFAULT_PDF_EXTENSION)
        shutil.copy(temp_pdf_filename, pdf_filename)
    finally:
        logging.info("Remove the temp dir")
        shutil.rmtree(temp_dir, ignore_errors=True)

    pdf_features(
        pdf_filename,
        filename_ext=DEFAULT_PDF_EXTENSION,
        metadata=md_metadata,
        **kwargs,
    )

    return pdf_filename


# -----------------------------------------------------------------------------
def __get_this_filename() -> str:
    """
    Return this module filename as a string for legacy callers.

    Prefer :func:`_get_this_filename` inside this module.
    """
    return str(_get_this_filename())


__all__ = [
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
