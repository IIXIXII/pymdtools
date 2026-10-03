Options reference
=================

Use ``IncludeOptions`` for document assembly, ``PdfOptions`` for the browser
renderer and ``PdfFeatures`` for PDF post-processing. These frozen dataclasses
make configuration explicit; create a new instance to change their fields.
The translation client has its own settings described in :doc:`translate`.

Document assembly
-----------------

Pass ``include_options=IncludeOptions(...)`` to
:class:`pymdtools.mdfile.MarkdownContent`. Lower-level functions in
:mod:`pymdtools.instruction` take individual keyword arguments instead.

.. list-table:: IncludeOptions defaults
   :header-rows: 1
   :widths: 22 22 56

   * - Field
     - Default
     - Meaning
   * - ``search_folders``
     - ``()``
     - Additional roots for file lookup and named reference discovery.
   * - ``refs_depth``
     - ``0``
     - Reference scan depth for each root: 0 for the root, 1 for one nested
       level, -1 for unlimited recursion. Does not control include-file lookup.
   * - ``exclude_dirs``
     - ``DEFAULT_EXCLUDED_DIRECTORIES``
     - Directory names or root-relative patterns skipped by reference scans.
       An empty tuple disables exclusions; symlinks remain skipped.
   * - ``relative_paths``
     - ``(".", "referenced_files")``
     - Subdirectories probed under each include-file lookup root.
   * - ``include_cwd``
     - ``False``
     - Add the process working directory to include-file lookup.
   * - ``nb_up_path``
     - ``0``
     - Additional parent levels to probe and permit for include files. The default
       ``0`` confines lookup to the configured roots; increase it only for trusted
       directory trees.
   * - ``encoding``
     - ``None``
     - Included-file encoding; None enables detection. This is separate from
       the ``MarkdownContent(encoding=...)`` source-file setting.
   * - ``render_mode``
     - ``"box"``
     - Box included text inside an HTML comment, or use ``"raw"`` to insert
       visible Markdown.
   * - ``error_if_no_file``
     - ``True``
     - Propagate include-file lookup/read errors. False leaves that directive
       unchanged; it does not change missing-variable or missing-ref handling.

A file-backed document adds its parent directory. Include-file lookup also
falls back to packaged resources; explicit folders do not disable that fallback.
The filename in the directive must contain no directory separators. Keep
``include_cwd=False`` and ``nb_up_path=0`` unless a broader lookup is intended.
See :doc:`instruction` for the difference between files and named references.

.. testcode::

   from pymdtools.mdfile import MarkdownContent
   from pymdtools.options import IncludeOptions

   policy = IncludeOptions(search_folders=("snippets",), refs_depth=1, render_mode="raw")
   document = MarkdownContent(content="# Draft\n", include_options=policy)
   assert document.title == "Draft"

Supported legacy constructor keywords override the corresponding typed fields.
Unknown keywords raise ``TypeError``. Avoid overlapping reference roots:
discovering the same reference twice can raise a duplicate-name error.

.. automodule:: pymdtools.options
   :members: IncludeOptions, DEFAULT_EXCLUDED_DIRECTORIES
   :undoc-members:

Browser rendering
-----------------

Pass ``options=PdfOptions(...)`` to ``convert_md_to_pdf`` or
``convert_html_to_pdf``. The type is imported from ``pymdtools.pdf_backend``.

.. list-table:: PdfOptions defaults
   :header-rows: 1
   :widths: 22 22 56

   * - Field
     - Default
     - Meaning
   * - ``timeout``
     - ``30.0``
     - Positive, finite seconds for the Chromium worker, including startup.
       Markdown conversion and separate pypdf operations are outside this limit.
   * - ``page_format``
     - ``"A4"``
     - One of A3, A4, A5, Letter, Legal or Tabloid.
   * - ``title``
     - ``""``
     - Rendering title fallback. An explicit HTML conversion title overrides it;
       Markdown title variables and final PDF metadata can also take precedence.
   * - ``allow_network``
     - ``False``
     - Permit HTTP(S) resources when True. JavaScript remains disabled.
   * - ``asset_root``
     - ``None``
     - Extra local root, as a string path. Markdown conversion uses its source
       directory when this is omitted; HTML conversion permits its own directory.

.. autoclass:: pymdtools.pdf_backend.PdfOptions
   :members:

PDF post-processing
-------------------

Pass ``features=PdfFeatures(...)`` to ``convert_md_to_pdf`` or ``pdf_features``.
The HTML conversion entry point does not accept ``features``: render first,
then call ``pdf_features`` on its result.

.. list-table:: PdfFeatures fields (all default to None)
   :header-rows: 1
   :widths: 30 70

   * - Field
     - Meaning
   * - ``metadata``
     - Mapping such as ``{"title": "Guide", "author": "Example team"}``.
       Keys are normalized to PDF names; use conventional lowercase keys.
   * - ``background_pdf``
     - First page of a PDF placed beneath each page's content.
   * - ``background_first_page_pdf``
     - Alternative background for the document's first page only.
   * - ``watermark_pdf``
     - First page of a PDF placed over each page's content.
   * - ``path``
     - Base directory for relative overlay filenames. With None, they resolve
       from the process working directory.

Overlays should match the target page size; they are not automatically scaled.
The first-page background overrides the general background on that page.
Explicit legacy keywords override fields with the same name; conflicting
overlay aliases raise ``ValueError``. Unknown feature keywords also raise
``ValueError``. ``check_odd_pages`` is a separate operation, not a feature flag;
see :doc:`mdtopdf` for operation order and backups.

.. autoclass:: pymdtools.options.PdfFeatures
   :members:
