Project architecture
====================

The importable package lives in ``src/pymdtools``. Install it with
``uv sync --locked --extra dev --extra docs --extra pdf`` before running scripts
or tests. The source layout makes local scripts use the installed package.

Public imports remain stable: ``instruction``, ``mdcommon``, ``mdfile``,
``mdtopdf``, ``translate``, ``translation_client``, ``pdf_backend`` and
``common.fs`` retain their existing entry points. The underscore packages below
are implementation details and may change independently of that API.

.. list-table:: Ownership
   :header-rows: 1

   * - Location
     - Responsibility
   * - ``_markdown.py``, ``_markdown_syntax.py``
     - CommonMark source positions and safe destination/title serialization
   * - ``_directives/``
     - Variables, reference blocks, inclusions, headings and filesystem discovery
   * - ``_rendering/``
     - HTML conversion, layout resources, Chromium worker and PDF operations
   * - ``_translation/``
     - MyMemory transport, reusable client and protected paragraph blocks
   * - ``common/_filesystem/``
     - Paths, text I/O, copying and traversal
   * - ``options.py``
     - Typed inclusion policy and PDF post-processing options
   * - ``mdfile.py``, ``mdtopdf.py``
     - Document workflow orchestration and public compatibility exports

The translation client depends on the provider transport, never on the
high-level ``translate`` module. Filesystem discovery is kept separate from
text transformations. PDF dependencies load only when PDF functionality is used.

Validation
----------

``tests/fixtures/markdown`` is a shared corpus used to check inspection,
rewriting, normalization and offline translation. Add regression documents
there when changing Markdown semantics. Unit tests continue to cover failure
handling and filesystem behavior. Mocks target the module owning an
implementation; functional tests use the public imports.

``scripts/benchmark_markdown.py`` measures parsing and batched link updates.
``scripts/check_distribution.py`` validates archives and exercises the installed
wheel outside the checkout. The PDF integration test runs Chromium explicitly.
