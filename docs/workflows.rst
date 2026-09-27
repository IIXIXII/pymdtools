Practical workflows
===================

Example catalogue
-----------------

The ``examples/`` directory contains 25 focused scripts plus the complete
workflow below. The :doc:`catalogue with expected outputs <examples>`
groups the examples by their numbered progression: normalization and editing,
variables and inclusions, links, HTML conversion, file utilities, offline
translation, custom rendering, report assembly and PDF publishing.

From a checkout or source archive, install the package as described in
:doc:`getting_started`. Then list the examples or execute the 23 scenarios
that need only core dependencies::

   uv run --no-sync python examples/run_all.py --list
   uv run --no-sync python examples/run_all.py

Scripts use local fixtures or create their own sample data, and write to a dedicated
``examples/output/<example>`` directory. Pass ``--output`` to select a different
output location. The fixtures are left unchanged; generated files can be replaced
on subsequent runs. Translation uses injected offline transports.

For example, build a report from JSON, variables and shared sections::

   uv run --no-sync python examples/22_report_pipeline.py

Open ``examples/output/22_report_pipeline/report.html`` with its adjacent assets.
After installing the PDF extra, run the three PDF examples::

   uv run --no-sync playwright install --with-deps --only-shell chromium
   uv run --no-sync python examples/run_all.py --only-pdf

Use ``--pdf`` instead of ``--only-pdf`` to run all 26 scenarios. PDF examples
demonstrate metadata, local SVGs, CSS page breaks, even page counts and overlays.

Complete workflow
-----------------

After installing the development environment, run the complete offline example:

.. code-block:: console

   uv run --no-sync python examples/workflows.py --output examples/output/workflows

It assembles a document from a reusable fragment, rebases its links, normalizes
the result, generates HTML and demonstrates translation with an injected local
transport. Run it in a dedicated output directory: it creates example files.
The example makes no translation requests to an external service.

Add ``--pdf`` after installing Chromium to exercise the PDF pipeline too:

.. code-block:: console

   uv run --no-sync playwright install chromium
   uv run --no-sync python examples/workflows.py --output examples/output/workflows --pdf

.. literalinclude:: ../examples/workflows.py
   :language: python
   :start-at: def offline_translation
   :end-before: if __name__

Discovery and compatibility
---------------------------

``MarkdownContent`` accepts ``include_options=IncludeOptions(...)``. Reference
discovery only runs when the document contains an active ``begin-include``
directive. The default depth is zero for the document directory and additional
search roots; use ``refs_depth=1`` for one subdirectory level or ``-1`` for
unlimited recursion. Common generated directories are excluded by default.
``exclude_dirs=()`` disables directory exclusions; symbolic links remain skipped.

Legacy include keyword arguments remain supported and override typed options.
Unknown keywords raise ``TypeError``. ``convert_md_to_pdf`` and ``pdf_features``
accept ``features=PdfFeatures(...)``; existing metadata and overlay keywords remain
available, with explicit keywords taking precedence over fields of the same
name. Conflicting overlay aliases still raise an error.

``update_links_in_md_text`` retains sequential renaming: an ``A`` to ``B`` change
followed by a ``B`` to ``C`` change produces ``C``. Parsing occurs once and edits
are applied to the original source positions. This preserves surrounding source
text and reference users that were not selected for replacement.

See :doc:`options` for the typed settings and :doc:`mdcommon` for the distinction
between label-based batches and old/new pair matching.
