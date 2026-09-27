"""Compatibility facade for mdtopdf.

Implementations live in _rendering. Public imports remain stable.
"""

from __future__ import annotations

import logging
import shutil
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from . import common, instruction
from ._rendering._files import atomic_copy_file as _atomic_copy_file
from ._rendering._files import commit_staged_file as _commit_staged_file
from ._rendering._files import new_staged_path as _new_staged_path
from ._rendering._shared import ASSET_RE as ASSET_RE
from ._rendering._shared import DEFAULT_HTML_ENCODING as DEFAULT_HTML_ENCODING
from ._rendering._shared import DEFAULT_HTML_EXTENSION as DEFAULT_HTML_EXTENSION
from ._rendering._shared import DEFAULT_LAYOUT as DEFAULT_LAYOUT
from ._rendering._shared import DEFAULT_MD_EXTENSION as DEFAULT_MD_EXTENSION
from ._rendering._shared import DEFAULT_PDF_EXTENSION as DEFAULT_PDF_EXTENSION
from ._rendering._shared import LAYOUT_ASSET_DIRECTORY as LAYOUT_ASSET_DIRECTORY
from ._rendering._shared import LAYOUT_NAME_RE as LAYOUT_NAME_RE
from ._rendering._shared import OVERLAY_OPTION_ALIASES as OVERLAY_OPTION_ALIASES
from ._rendering._shared import PLACEHOLDER_RE as PLACEHOLDER_RE
from ._rendering._shared import TOC_RE as TOC_RE
from ._rendering._shared import MdToHtmlConverter as MdToHtmlConverter
from ._rendering.html import convert_md_to_html as convert_md_to_html
from ._rendering.html import converter_md_to_html_markdown as converter_md_to_html_markdown
from ._rendering.html import converter_md_to_html_mistune as converter_md_to_html_mistune
from ._rendering.html import get_md_to_html_converter as get_md_to_html_converter
from ._rendering.html import mkd as mkd
from ._rendering.layouts import find_wk_html_to_pdf as find_wk_html_to_pdf
from ._rendering.layouts import get_this_filename as _get_this_filename
from ._rendering.pdf_operations import PdfReader as PdfReader
from ._rendering.pdf_operations import PdfWriter as PdfWriter
from ._rendering.pdf_operations import check_odd_pages as check_odd_pages
from ._rendering.pdf_operations import feature_kwargs
from ._rendering.pdf_operations import pdf_features as pdf_features
from ._rendering.pdf_operations import validate_pdf_file as _validate_pdf_file
from .options import PdfFeatures as PdfFeatures
from .pdf_backend import PdfOptions, render_pdf

logger: logging.Logger = logging.getLogger(__name__)


def convert_html_to_pdf(
    filename: common.PathInput,
    filename_ext: str = DEFAULT_HTML_EXTENSION,
    *,
    title: str | None = None,
    options: PdfOptions | None = None,
) -> Path:
    """Render HTML using optional Chromium, committing only a valid PDF.

    Install ``pymdtools[pdf]`` and ``python -m playwright install chromium``.
    Local assets are restricted to the document directory and the optional
    ``PdfOptions.asset_root``. Remote resources and JavaScript default to off.
    """
    from dataclasses import replace

    html_filename = common.check_file(filename, filename_ext)
    configured = options or PdfOptions()
    configured = replace(
        configured, title=title if title is not None else configured.title or html_filename.stem
    )
    pdf_filename = html_filename.with_suffix(DEFAULT_PDF_EXTENSION)
    staged_pdf = _new_staged_path(pdf_filename, suffix=DEFAULT_PDF_EXTENSION)
    try:
        render_pdf(html_filename, staged_pdf, configured)
        _validate_pdf_file(staged_pdf)
        _commit_staged_file(staged_pdf, pdf_filename)
    finally:
        staged_pdf.unlink(missing_ok=True)
    return pdf_filename


def convert_md_to_pdf(
    filename: common.PathInput,
    filename_ext: str = DEFAULT_MD_EXTENSION,
    *,
    options: PdfOptions | None = None,
    features: PdfFeatures | None = None,
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
        options: Chromium rendering options, including timeout and resource policy.
        features: Typed PDF metadata and overlays. Explicit legacy keywords override
            fields with the same name.
        **kwargs: Options forwarded to :func:`pdf_features`.

    Returns:
        Generated PDF path.
    """
    logger.info("Convert md -> pdf %s", filename)
    md_filename = common.check_file(filename, filename_ext)
    md_metadata = instruction.get_vars_from_md_file(md_filename)
    feature_options = feature_kwargs(features, kwargs)
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
            {str(key): str(value) for key, value in requested_metadata_mapping.items()}
        )

    temp_dir = common.make_temp_dir()
    pdf_filename = md_filename.with_suffix(DEFAULT_PDF_EXTENSION)
    try:
        temp_md_filename = Path(temp_dir) / md_filename.name

        logger.info("Copy file to temp")
        shutil.copy2(md_filename, temp_md_filename)
        logger.info("Convert md to html")
        temp_html_filename = convert_md_to_html(
            temp_md_filename,
            converter="mistune",
        )

        title = None
        if "title" in md_metadata:
            title = md_metadata["title"]
        if "page:title" in md_metadata:
            title = md_metadata["page:title"]

        logger.info("Convert html to pdf title=%s", title)
        from dataclasses import replace

        configured = options or PdfOptions()
        if configured.asset_root is None:
            configured = replace(configured, asset_root=str(md_filename.parent))
        temp_pdf_filename = convert_html_to_pdf(temp_html_filename, title=title, options=configured)

        pdf_features(
            temp_pdf_filename,
            filename_ext=DEFAULT_PDF_EXTENSION,
            metadata=combined_metadata,
            **feature_options,
        )
        _validate_pdf_file(temp_pdf_filename)

        logger.info("Copy file from temp")
        _atomic_copy_file(temp_pdf_filename, pdf_filename)
    finally:
        logger.info("Remove the temp dir")
        shutil.rmtree(temp_dir, ignore_errors=True)

    return pdf_filename


def __get_this_filename() -> str:
    """Return this module filename as text for legacy callers."""
    return str(_get_this_filename())


__all__ = [
    "__get_this_filename",
    "ASSET_RE",
    "DEFAULT_HTML_ENCODING",
    "DEFAULT_HTML_EXTENSION",
    "DEFAULT_LAYOUT",
    "DEFAULT_MD_EXTENSION",
    "DEFAULT_PDF_EXTENSION",
    "LAYOUT_ASSET_DIRECTORY",
    "LAYOUT_NAME_RE",
    "MdToHtmlConverter",
    "OVERLAY_OPTION_ALIASES",
    "PLACEHOLDER_RE",
    "PdfReader",
    "PdfWriter",
    "TOC_RE",
    "check_odd_pages",
    "convert_html_to_pdf",
    "convert_md_to_html",
    "convert_md_to_pdf",
    "converter_md_to_html_markdown",
    "converter_md_to_html_mistune",
    "find_wk_html_to_pdf",
    "get_md_to_html_converter",
    "mkd",
    "pdf_features",
]
