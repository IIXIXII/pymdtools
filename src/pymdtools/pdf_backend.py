"""Public Chromium renderer and compatibility worker entrypoint."""

from ._rendering.pdf_backend import PdfOptions as PdfOptions
from ._rendering.pdf_backend import PdfRenderError as PdfRenderError
from ._rendering.pdf_backend import local_resource as local_resource
from ._rendering.pdf_backend import main
from ._rendering.pdf_backend import render_pdf as render_pdf

__all__ = ["PdfOptions", "PdfRenderError", "local_resource", "render_pdf"]

if __name__ == "__main__":
    main()
