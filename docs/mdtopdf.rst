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

Generate HTML
-------------

``convert_md_to_html`` reads a Markdown file and returns the generated HTML
``Path``. By default it writes beside the source; ``path_dest`` selects an
existing output directory. Process and save directives first if needed.

.. testcode::

   from pathlib import Path

   from pymdtools.mdtopdf import convert_md_to_html

   output = Path("build")
   output.mkdir(exist_ok=True)
   source = output / "guide.md"
   source.write_text("# Guide\n\nA small **document**.\n", encoding="utf-8")
   html_path = convert_md_to_html(source, layout="github")
   assert html_path.name == "guide.html"
   assert "<strong>document</strong>" in html_path.read_text(encoding="utf-8")

The default converter is Mistune with raw HTML escaped. Select
``converter="markdown"`` for Python-Markdown when trusted documents intentionally
contain raw HTML. This selection is an HTML rendering choice, not a general
sanitizer for arbitrary content or link schemes. Conversion does not execute
``process_tags`` or check whether document links exist.

Layouts and assets
------------------

The 17 bundled layout names are:

* ``github``, ``bootstrap3``;
* ``jasonm23-dark``, ``jasonm23-foghorn``, ``jasonm23-markdown``, ``jasonm23-swiss``;
* ``markedapp-byword``;
* ``mixu-book``, ``mixu-bootstrap``, ``mixu-bootstrap-2col``, ``mixu-gray``,
  ``mixu-page``, ``mixu-radar``;
* ``roryg-ghostwriter``;
* ``thomasf-solarizedcssdark``, ``thomasf-solarizedcsslight``, ``witex``.

``jasonm23-swiss`` is the default. Assets are copied under
``_pymdtools_assets/<layout>/`` next to the generated page, including
``LICENSES.txt``. Share that tree with the HTML. Some historical themes have
unresolved permissions, recorded in :doc:`LICENSES-3rd-party`; review the
selected theme's notices before redistributing its assets. Example 14 creates
a gallery of three layouts without altering packaged resources.

Generate PDF
------------

After installing PDF support, continue with the Markdown file created above:

.. code-block:: python

   from pymdtools.mdtopdf import convert_md_to_pdf
   from pymdtools.options import PdfFeatures
   from pymdtools.pdf_backend import PdfOptions

   pdf_path = convert_md_to_pdf(
       "build/guide.md",
       options=PdfOptions(page_format="Letter", timeout=60),
       features=PdfFeatures(metadata={"title": "Guide", "author": "Example team"}),
   )

The result is ``build/guide.pdf``. Markdown conversion uses the default
``jasonm23-swiss`` layout and the Mistune converter in a temporary directory.
To choose another layout, render it to HTML first, then pass that HTML path to
``convert_html_to_pdf(html_path, options=...)``. This also provides a way to
prepare custom HTML and print CSS. HTML conversion writes a PDF beside its input.

``convert_md_to_pdf`` reads Markdown variable declarations as PDF metadata;
explicit ``PdfFeatures.metadata`` values override matching declaration keys.
Use the metadata ``title`` field when you need to set the final PDF title.
HTML-to-PDF accepts an explicit ``title=...`` but no ``features`` parameter;
call ``pdf_features`` separately to add metadata or overlays.

Resource policy
---------------

Chromium runs headlessly with JavaScript disabled. Network access is blocked
unless ``PdfOptions(allow_network=True)`` is explicitly supplied. Local assets
are restricted to the generated HTML directory and the optional source asset
root. A worker process bounds browser startup and rendering to 30 seconds by
default; Markdown preprocessing and pypdf post-processing are outside this limit.
The output is validated before atomically replacing an existing PDF.

Use ``PdfOptions(timeout=60, page_format="Letter")`` to customize rendering.
``find_wk_html_to_pdf`` remains a legacy lookup helper but is never used by the
conversion pipeline. Page breaks and fonts can differ from the old renderer.

Post-process existing PDFs
--------------------------

The following operations require pypdf from the PDF extra, but do not launch a
browser. Supply existing PDF files for the overlays:

.. code-block:: python

   from pymdtools.mdtopdf import check_odd_pages, pdf_features
   from pymdtools.options import PdfFeatures

   check_odd_pages("build/guide.pdf")
   pdf_features(
       "build/guide.pdf",
       features=PdfFeatures(
           path="stationery",
           background_pdf="background.pdf",
           watermark_pdf="draft.pdf",
           metadata={"title": "Guide", "author": "Example team"},
       ),
   )

``check_odd_pages`` leaves an even page count unchanged. For an odd count, it
backs up the file and appends a blank page. This rewrite does not preserve all
metadata; apply final metadata afterwards. ``pdf_features`` edits in place
without creating a dated backup, using validated temporary output before
replacement. Create a backup explicitly if you need the pre-overlay document.

Only the first page of each overlay PDF is used. Backgrounds go below content;
watermarks go above it. Use overlays with compatible page dimensions. Every page,
including a blank page added for balancing, receives the general overlays.
``background_first_page_pdf`` can customize the first page separately.

Examples 23–25 in :doc:`workflows` create and check real PDFs, including local
assets and generated stationery. See :doc:`options` for the full field reference
and :doc:`troubleshooting` for missing browser/assets and timeout errors.

Public API
----------

.. automodule:: pymdtools.mdtopdf
   :members:
   :imported-members:
   :undoc-members:

.. automodule:: pymdtools.pdf_backend
   :members: PdfRenderError, render_pdf
   :imported-members:
