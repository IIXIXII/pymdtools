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

Repository map
--------------

.. list-table:: Supporting files
   :header-rows: 1

   * - Location
     - Purpose
   * - ``pyproject.toml``, ``uv.lock``
     - Package metadata, extras, tool configuration and locked development resolution.
   * - ``requirements*.txt``
     - Compatibility entry points that install the project and selected extras.
   * - ``examples/``
     - Executable public-API workflows, local fixtures and a batch runner.
   * - ``docs/``
     - Sphinx/MyST guides, generated API reference and offline documentation examples.
   * - ``scripts/``
     - Release validation, archive checks, benchmarks and license-notice maintenance.
   * - ``.github/workflows/``
     - Tests, quality checks, compatibility, security analysis and publication.
   * - ``src/pymdtools/layouts/``
     - HTML templates, local assets and exported notices for each layout.
   * - ``LICENSES-*.md``, ``THIRD_PARTY_LICENSES/``
     - Reviewed licensing inventories and component notices.

The README is a project overview. Task-specific contracts belong in the user
guides, and signatures/docstrings come from the installed package via autodoc.
The contribution guide, changelog, example catalogue and license pages are
included from their repository sources rather than maintained as duplicate text.

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
The Sphinx doctest builder executes marked offline snippets in temporary working
directories. The full example runner additionally exercises the scenarios in
``examples/``. See :doc:`contributing` for local commands and CI responsibilities.
