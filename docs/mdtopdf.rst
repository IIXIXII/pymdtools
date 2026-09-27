Markdown, HTML and PDF conversion
=================================

Markdown is rendered into packaged HTML layouts. Optional Playwright/Chromium
creates PDFs; pypdf handles metadata, page balancing, backgrounds and watermarks.

Installation
------------

Install the PDF extra and browser::

   python -m pip install "pymdtools[pdf]"
   python -m playwright install chromium

On Linux, add ``--with-deps`` to the browser installation command.
Markdown and HTML operations do not require the PDF extra.

Resource policy
---------------

Chromium runs headlessly with JavaScript disabled. Network access is blocked
unless ``PdfOptions(allow_network=True)`` is explicitly supplied. Local assets
are restricted to the generated HTML directory and the optional source asset
root. A worker process bounds the entire conversion to 30 seconds by default.
The output is validated before atomically replacing an existing PDF.

Use ``PdfOptions(timeout=60, page_format="Letter")`` to customize rendering.
``find_wk_html_to_pdf`` remains a legacy lookup helper but is never used by the
conversion pipeline. Page breaks and fonts can differ from the old renderer.

Public API
----------

.. automodule:: pymdtools.mdtopdf
   :members:
   :imported-members:
   :undoc-members:

.. automodule:: pymdtools.pdf_backend
   :members: PdfOptions, PdfRenderError
