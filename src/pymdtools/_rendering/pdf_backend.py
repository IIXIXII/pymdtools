"""Optional Chromium PDF rendering with bounded execution and local resources.

Install ``pymdtools[pdf]`` and run ``python -m playwright install chromium``.
The browser is created in a worker process, so callers may use any event loop.
"""

from __future__ import annotations

import json
import math
import mimetypes
import subprocess
import sys
from dataclasses import asdict, dataclass
from html import escape
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import quote, unquote, urlsplit

if TYPE_CHECKING:
    from playwright.sync_api import Route


class PdfRenderError(RuntimeError):
    """The renderer could not produce a PDF within its resource policy."""


@dataclass(frozen=True)
class PdfOptions:
    """PDF rendering options; JavaScript and remote resources are disabled.

    ``timeout`` bounds the complete worker lifetime in seconds. ``asset_root``
    optionally permits source document assets in addition to generated layouts.
    ``allow_network`` explicitly permits HTTP(S) resources in trusted documents.
    """

    timeout: float = 30.0
    page_format: str = "A4"
    title: str = ""
    allow_network: bool = False
    asset_root: str | None = None

    def __post_init__(self) -> None:
        if not math.isfinite(self.timeout) or self.timeout <= 0:
            raise ValueError("timeout must be finite and greater than zero")
        if self.page_format not in {"A3", "A4", "A5", "Letter", "Legal", "Tabloid"}:
            raise ValueError("unsupported page_format")


def local_resource(url: str, roots: tuple[Path, ...]) -> Path | None:
    """Resolve a browser URL to a file strictly inside one permitted root."""
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != "pymdtools.invalid":
        return None
    relative = unquote(parsed.path).lstrip("/")
    if "\\" in relative or ":" in relative:
        return None
    for root in roots:
        candidate = (root / relative).resolve()
        if candidate.is_relative_to(root.resolve()) and candidate.is_file():
            return candidate
    return None


def render_pdf(source: Path, destination: Path, options: PdfOptions) -> None:
    """Render in a separate process; timeouts preserve the caller's target."""
    request = json.dumps(
        {
            "source": str(source.resolve()),
            "destination": str(destination.resolve()),
            "options": asdict(options),
        }
    )
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pymdtools.pdf_backend"],
            input=request,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=options.timeout,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
    except subprocess.TimeoutExpired as exc:
        raise PdfRenderError(f"PDF conversion exceeded {options.timeout:g} seconds") from exc
    if result.returncode:
        raise PdfRenderError(result.stderr.strip() or "Chromium PDF conversion failed")


def render_in_process(source: Path, destination: Path, options: PdfOptions) -> None:
    """Worker implementation, also exercised directly by integration tests."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise PdfRenderError(
            "Install pymdtools[pdf], then run: python -m playwright install chromium"
        ) from exc

    roots = (source.parent.resolve(),)
    if options.asset_root:
        roots += (Path(options.asset_root).resolve(),)

    def serve(route: Route) -> None:
        path = local_resource(route.request.url, roots)
        if path is not None:
            route.fulfill(
                body=path.read_bytes(),
                content_type=mimetypes.guess_type(path.name)[0] or "application/octet-stream",
            )
        elif (
            options.allow_network
            and urlsplit(route.request.url).scheme in {"http", "https"}
            and urlsplit(route.request.url).netloc != "pymdtools.invalid"
        ):
            route.continue_()
        else:
            route.abort()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            context = browser.new_context(java_script_enabled=False, service_workers="block")
            context.route("**/*", serve)
            page = context.new_page()
            page.goto(
                "https://pymdtools.invalid/" + quote(source.name),
                wait_until="networkidle",
                timeout=options.timeout * 1000,
            )
            page.pdf(
                path=str(destination),
                format=options.page_format,
                print_background=True,
                display_header_footer=True,
                margin={"top": "20mm", "bottom": "20mm", "left": "12mm", "right": "12mm"},
                header_template=f'<div style="font-size:8px;width:100%;text-align:center">{escape(options.title)}</div>',
                footer_template='<div style="font-size:8px;width:100%;text-align:center"><span class="pageNumber"></span> / <span class="totalPages"></span></div>',
            )
        finally:
            browser.close()


def main() -> None:
    request = json.load(sys.stdin)
    render_in_process(
        Path(request["source"]), Path(request["destination"]), PdfOptions(**request["options"])
    )


if __name__ == "__main__":
    main()
