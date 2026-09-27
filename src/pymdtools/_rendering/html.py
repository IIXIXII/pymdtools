"""Rendering: html."""

from __future__ import annotations

import logging
from importlib import import_module
from pathlib import Path
from typing import Any, cast

from .. import common, instruction
from .. import mistune_integration as mistune
from ._files import write_text_atomic
from ._shared import DEFAULT_HTML_ENCODING, DEFAULT_LAYOUT, DEFAULT_MD_EXTENSION, MdToHtmlConverter
from .layouts import get_layout_page, replace_layout_placeholders

logger: logging.Logger = logging.getLogger(__name__)

mkd: Any = import_module("markdown")


def converter_md_to_html_markdown(text: str) -> str:
    """
    Convert Markdown text to HTML with Python-Markdown.

    Args:
        text: Markdown text.

    Returns:
        HTML fragment.
    """
    return mkd.markdown(text, output_format="xhtml")


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


MD_TO_HTML_CONVERTERS: dict[str, MdToHtmlConverter] = {
    "markdown": converter_md_to_html_markdown,
    "mistune": converter_md_to_html_mistune,
}


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
    if converter_name not in MD_TO_HTML_CONVERTERS:
        logger.info("Converter %s does not exist", converter_name)
        logger.info("Converter changed to safe mistune renderer")
        converter_name = "mistune"
    return MD_TO_HTML_CONVERTERS[converter_name]


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
    logger.info("Convert md -> html %s", filename)

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
        logger.error("The filename %s seems empty", md_filename)
        raise ValueError(f"The filename {md_filename} seems empty")

    rendered_content = get_md_to_html_converter(converter)(content)

    page_html_filename = get_layout_page(layout)
    layout_path = common.check_folder(page_html_filename.parent)
    page_html = common.get_file_content(page_html_filename)
    page_html = replace_layout_placeholders(
        page_html,
        title=title,
        content=rendered_content,
        content_vars=content_vars,
        layout_path=layout_path,
        path_dest=destination,
    )

    html_filename = common.normpath(destination / f"{md_filename.stem}.html")
    logger.info("        -> html %s", html_filename)

    write_text_atomic(html_filename, page_html, encoding=encoding)

    return html_filename
