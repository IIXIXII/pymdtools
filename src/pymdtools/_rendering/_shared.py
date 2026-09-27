"""Rendering: shared."""

from __future__ import annotations

import logging
import re
from collections.abc import Callable

logger: logging.Logger = logging.getLogger(__name__)


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
