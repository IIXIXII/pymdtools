Practical workflows
===================

After installing the development environment, run the complete offline example:

.. code-block:: console

   uv run --no-sync python examples/workflows.py --output examples/output

It assembles a document from a reusable fragment, rebases its links, normalizes
the result, generates HTML and demonstrates translation with an injected local
transport. Run it in a dedicated output directory: it creates example files.
The example makes no translation requests to an external service.

Add ``--pdf`` after installing Chromium to exercise the PDF pipeline too:

.. code-block:: console

   uv run --no-sync playwright install chromium
   uv run --no-sync python examples/workflows.py --output examples/output --pdf

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
Unknown keywords raise ``TypeError``. PDF entry points accept
``features=PdfFeatures(...)``; existing metadata and overlay keywords remain
available, with explicit keywords taking precedence over fields of the same
name. Conflicting overlay aliases still raise an error.

Batch link replacements retain sequential renaming: an ``A`` to ``B`` change
followed by a ``B`` to ``C`` change produces ``C``. Parsing occurs once and edits
are applied to the original source positions. This preserves surrounding source
text and reference users that were not selected for replacement.
