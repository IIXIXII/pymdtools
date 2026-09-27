Troubleshooting and migration
=============================

Import fails after cloning or moving the package
------------------------------------------------

The importable code lives under ``src/pymdtools``. Install the checkout before
running scripts, tests or Sphinx::

   uv sync --locked --extra dev --extra docs --extra pdf
   uv run --no-sync python -c "import pymdtools; print(pymdtools.__file__)"

Use ``python -m pip install -e .`` instead if you manage your own environment.
In VS Code, select that environment with **Python: Select Interpreter**. A
previously selected interpreter can override the workspace's default setting.

Sphinx or an optional module is missing
---------------------------------------

Install the appropriate extra into the interpreter that runs the command.
``uv run --no-sync`` deliberately does not install missing dependencies. Run the
sync command above first, or use the pip-only documentation instructions in
:doc:`getting_started`. Installing with one Python and running another leaves
their dependencies separate.

PDF rendering reports a missing browser or library
--------------------------------------------------

The ``pdf`` extra installs Python packages, not Chromium. In the development
environment::

   uv run --no-sync playwright install chromium

On Linux, add ``--with-deps`` for system libraries. Reinstall the browser after
updating Playwright if it requests a different browser build. If you configure
``PLAYWRIGHT_BROWSERS_PATH``, use the same value for installation and rendering.
See :doc:`mdtopdf` for the installation commands without uv.

An image, font or stylesheet is missing from the PDF
----------------------------------------------------

Remote resources are blocked by default. Put assets under the HTML directory
or the permitted ``PdfOptions.asset_root`` and use relative URLs. Markdown
conversion permits the source document directory by default. Absolute
``file://`` URLs and paths escaping the permitted roots are not supported.
Local files are served to the browser through an internal virtual URL.

Use ``allow_network=True`` only when the document is intended to fetch remote
resources. JavaScript remains disabled, so scripts cannot create document
content during rendering. For a layout comparison, run example 14 and inspect
the HTML pages with their adjacent asset trees.

The PDF timeout is reached
--------------------------

Increase ``PdfOptions(timeout=60)`` for a document that needs more rendering
time. The limit covers Chromium startup and rendering in its worker process.
It does not cover all preprocessing or PDF overlay work. A failed conversion
preserves an existing destination PDF. Reduce large assets or split the document
if a longer timeout is not sufficient.

An inclusion is missing or invisible
------------------------------------

Use ``include-file(introduction.md)``, not a path containing ``/`` or ``\\``.
Provide the folder through ``IncludeOptions(search_folders=("snippets",))``.
The default ``render_mode="box"`` places the included text inside an HTML
comment; use ``"raw"`` for a visible Markdown fragment.

For ``begin-include(name)`` blocks, declare a matching ``begin-ref(name)`` in a
Markdown file under the reference search roots. ``MarkdownContent`` scans
each root only by default. Increase ``refs_depth`` for nested folders. Keep
reference names unique and avoid scanning the same folder through overlapping
roots. File lookup and reference discovery are different operations; increasing
``refs_depth`` does not enable paths inside ``include-file`` directives.

Call ``process_tags()`` before exporting HTML or PDF, then ``write()`` to save
the processed buffer. Conversion functions read the file on disk and do not
assemble directives automatically. See :doc:`instruction` and :doc:`options`.

Text edits appear to do nothing
-------------------------------

``MarkdownContent`` and ``FileContent`` edit memory until ``write()`` is called.
The ``save_needed`` flag records assignments; it is not a content comparison.
For normalization, unchanged output can be intentional: candidates are rejected
if they alter CommonMark rendering or are not stable on a second pass.

Translation returns the source text
-----------------------------------

The default ``on_error="keep_original"`` preserves text when transport or
paragraph-marker validation fails. Use ``on_error="raise"`` to diagnose the
failure and enable logging in your application. A ``TranslationClient`` retries
selected transient errors, but a provider rejection or invalid marker response
can still stop translation. The default source/destination is French to English;
set both explicitly for other directions. See :doc:`translate`.

A single test fails the coverage threshold
------------------------------------------

The normal test command enforces 100% coverage across the package. For a selected
test, keep coverage reporting but lower that threshold for the local run::

   uv run --no-sync pytest tests/mdfile --cov-fail-under=0

Run the full suite before submitting a change. The opt-in real-browser test has
a separate invocation documented in :doc:`contributing`.

Updating an older integration
-----------------------------

- Reinstall editable checkouts after the move to ``src/``; public module imports
  are unchanged. Imports from underscore-prefixed implementation modules are
  not part of the compatibility contract.
- Replace wkhtmltopdf/pdfkit installation with the PDF extra and Chromium.
  The existing conversion functions remain; ``find_wk_html_to_pdf`` is only a
  legacy lookup helper. Review fonts and pagination when migrating.
- Pass ``IncludeOptions(refs_depth=-1)`` when a high-level document workflow
  needs recursive reference discovery. Lower-level discovery helpers retain
  their own defaults.
- Link rebasing preserves directory spelling. Use ``legacy_slug=True`` only
  when you need the old slug-based behavior. ``common.path_to_url`` still creates
  slugs; ``common.encode_path_url`` encodes existing names.
- Replace unsupported include or PDF keywords with the documented options;
  unknown names now raise errors. See :doc:`options` and :doc:`changelog`.
