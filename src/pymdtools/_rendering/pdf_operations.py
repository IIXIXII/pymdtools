"""Rendering: pdf operations."""

from __future__ import annotations

import logging
import os
import shutil
from collections.abc import Mapping
from copy import copy
from dataclasses import fields
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO, cast

from .. import common
from ..options import PdfFeatures

if TYPE_CHECKING:
    from pypdf import PdfReader as Reader
    from pypdf import PdfWriter as Writer

from ._files import commit_staged_file, new_staged_path
from ._shared import DEFAULT_PDF_EXTENSION, OVERLAY_OPTION_ALIASES

logger: logging.Logger = logging.getLogger(__name__)


def PdfReader(stream: BinaryIO) -> Reader:
    """Lazily construct a reader from the optional PDF extra."""
    try:
        from pypdf import PdfReader as Reader
    except ImportError as exc:
        raise ImportError("PDF operations require: pip install pymdtools[pdf]") from exc
    return Reader(stream)


def PdfWriter() -> Writer:
    """Lazily construct a writer from the optional PDF extra."""
    try:
        from pypdf import PdfWriter as Writer
    except ImportError as exc:
        raise ImportError("PDF operations require: pip install pymdtools[pdf]") from exc
    return Writer()


def validate_pdf_file(path: Path, *, require_pages: bool = True) -> None:
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


def stage_pdf_writer(writer: Any, target: Path) -> Path:
    """Write and validate a PDF in a temporary sibling of ``target``."""
    staged = new_staged_path(target, suffix=DEFAULT_PDF_EXTENSION + ".tmp")
    try:
        with staged.open("wb") as stream:
            writer.write(stream)
            stream.flush()
            os.fsync(stream.fileno())
        validate_pdf_file(staged)
        return staged
    except Exception:
        staged.unlink(missing_ok=True)
        raise


def write_pdf_writer_atomic(writer: Any, target: Path) -> None:
    """Write a PDF writer to ``target`` using an atomic sibling replace."""
    staged = stage_pdf_writer(writer, target)
    try:
        commit_staged_file(staged, target)
    finally:
        staged.unlink(missing_ok=True)


def read_pdf(path: common.PathInput) -> tuple[Any, BinaryIO]:
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
        write_pdf_writer_atomic(out_pdf, pdf_path)

    return pdf_path


def metadata_from_kwargs(
    source_metadata: Mapping[Any, Any],
    requested_metadata: Mapping[Any, Any] | None,
) -> dict[str, str]:
    """
    Build PDF metadata from existing and requested metadata.
    """
    metadata = {str(key): str(value) for key, value in source_metadata.items() if value is not None}
    if requested_metadata:
        for key, value in requested_metadata.items():
            normalized = str(key).lstrip("/")
            if not normalized:
                raise ValueError("PDF metadata keys must not be empty")
            metadata[f"/{normalized[0].upper()}{normalized[1:]}"] = str(value)
    return metadata


def page_with_background(
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


def collect_overlay_pdfs(
    kwargs: Mapping[str, Any],
) -> tuple[dict[str, Any], list[BinaryIO]]:
    """
    Collect background/watermark PDFs from ``pdf_*`` and ``*_pdf`` options.
    """
    unknown_overlay_options = [
        key
        for key in kwargs
        if (key.startswith("pdf_") or key.endswith("_pdf")) and key not in OVERLAY_OPTION_ALIASES
    ]
    if unknown_overlay_options:
        raise ValueError(f"unsupported PDF overlay option: {unknown_overlay_options[0]!r}")

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
                    raise ValueError(f"conflicting aliases for PDF overlay {arg_name!r}")
                continue

            reader, handle = read_pdf(local_path)
            if not reader.pages:
                handle.close()
                raise ValueError(f"PDF overlay {option_name!r} must contain at least one page")
            handles.append(handle)
            pdf_args[arg_name] = reader
            overlay_paths[arg_name] = local_path

        return pdf_args, handles
    except Exception:
        for handle in handles:
            handle.close()
        raise


def feature_kwargs(features: PdfFeatures | None, legacy: Mapping[str, Any]) -> dict[str, Any]:
    """Merge typed options and legacy aliases, rejecting misspelled option names."""
    unknown = legacy.keys() - (OVERLAY_OPTION_ALIASES.keys() | {"metadata", "path"})
    if unknown:
        raise ValueError(f"unsupported PDF feature option: {sorted(unknown)[0]!r}")
    result = {
        field.name: getattr(features, field.name)
        for field in fields(PdfFeatures)
        if features is not None and getattr(features, field.name) is not None
    }
    result.update(legacy)
    return result


def pdf_features(
    filename: common.PathInput,
    filename_ext: str = DEFAULT_PDF_EXTENSION,
    *,
    features: PdfFeatures | None = None,
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
        features: Typed metadata and overlay settings. Explicit keyword arguments
            override fields with the same name; unknown option names are rejected.
        **kwargs: Feature options. ``metadata`` accepts a mapping of metadata
            keys without leading slash.

    Returns:
        Updated PDF file path.
    """
    kwargs = feature_kwargs(features, kwargs)
    logger.info("pdf features %s", filename)
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

        pdf_reader, source_handle = read_pdf(temp_pdf_filename)
        handles.append(source_handle)
        if not pdf_reader.pages:
            raise ValueError("source PDF must contain at least one page")

        metadata = metadata_from_kwargs(
            pdf_reader.metadata or {},
            requested_metadata,
        )

        pdf_args, overlay_handles = collect_overlay_pdfs(kwargs)
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
                page = page_with_background(page, background, pdf_writer)
            else:
                pdf_writer.add_page(page)
                page = pdf_writer.pages[-1]

            if "watermark" in pdf_args:
                page.merge_page(pdf_args["watermark"].pages[0])

        pdf_writer.add_metadata(metadata)
        staged_output = stage_pdf_writer(pdf_writer, pdf_filename)
    finally:
        for handle in handles:
            handle.close()
        shutil.rmtree(temp_dir, ignore_errors=True)

    try:
        commit_staged_file(staged_output, pdf_filename)
    finally:
        staged_output.unlink(missing_ok=True)

    return pdf_filename
