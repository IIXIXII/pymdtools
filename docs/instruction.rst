Markdown Instructions
=====================

``pymdtools.instruction`` contains the comment-based directives used to assemble
Markdown documents from reusable fragments, variables, titles, and external
files.

Directive Families
------------------

Reference blocks
~~~~~~~~~~~~~~~~

Reference blocks define reusable content:

.. code-block:: markdown

   <!-- begin-ref(header) -->
   # Shared Header
   <!-- end-ref -->

They can be inserted into include blocks:

.. code-block:: markdown

   <!-- begin-include(header) -->
   <!-- end-include -->

Variable directives
~~~~~~~~~~~~~~~~~~~

Variables are stored as one-line declarations and inserted into variable blocks:

.. code-block:: markdown

   <!-- var(project/name)="pymdtools" -->

   <!-- begin-var(project/name) -->
   <!-- end-var -->

File includes
~~~~~~~~~~~~~

External text files can be resolved and inserted with ``include-file``:

.. code-block:: markdown

   <!-- include-file(example.md) -->

The directive accepts a plain filename. Supply the containing directory through
``search_folders``, for example ``search_folders=["snippets"]``. Paths with
directory separators or parent traversal are rejected by the file lookup helper.

``MarkdownContent`` adds the source document's parent directory. Include-file
lookup probes explicit roots before falling back to packaged resources, using
``relative_paths`` under each root. Keep search roots deliberate when processing
documents that contain local inclusions. Directive-looking text inside fenced
or inline code, including code nested in lists or quotes, stays literal.

The default ``render_mode="box"`` wraps the included text in an ASCII box inside
an HTML comment. Use ``"raw"`` for a visible Markdown fragment. File inclusion
replaces the directive itself, so rerunning it does not reload that file once
the marker has gone. Keep an unprocessed source template when you need to rebuild.
Named ``begin-include`` blocks retain their markers and can be refreshed.

Title helpers
~~~~~~~~~~~~~

The module can read and update the first level-1 Markdown title, preserving or
forcing Setext / ATX style.

Common Usage
------------

Insert a local snippet with an explicit lookup folder:

.. testcode::

   from pathlib import Path

   from pymdtools.instruction import include_files_to_md_text

   snippets = Path("snippets")
   snippets.mkdir(exist_ok=True)
   (snippets / "intro.md").write_text("Welcome to the guide.\n", encoding="utf-8")
   updated = include_files_to_md_text(
       "# Guide\n\n<!-- include-file(intro.md) -->\n",
       search_folders=[snippets],
       render_mode="raw",
   )
   assert "Welcome to the guide." in updated

Replace variables in an in-memory string:

.. testcode::

   from pymdtools.instruction import search_include_vars_to_md_text

   markdown_text = (
       '<!-- var(project/name)="pymdtools" -->\n'
       '<!-- begin-var(project/name) --><!-- end-var -->\n'
   )
   updated = search_include_vars_to_md_text(markdown_text)
   assert "<!-- begin-var(project/name) -->pymdtools<!-- end-var -->" in updated

Fill named reference blocks without scanning the filesystem:

.. testcode::

   from pymdtools.instruction import get_refs_from_md_text, include_refs_to_md_text

   refs = get_refs_from_md_text(
       "<!-- begin-ref(support) -->Contact the documentation team.<!-- end-ref -->"
   )
   source = "<!-- begin-include(support) --><!-- end-include -->"
   assembled = include_refs_to_md_text(source, refs)
   assert "Contact the documentation team." in assembled
   assert include_refs_to_md_text(assembled, refs) == assembled

Discovery rules
---------------

For file-backed processing, prefer ``MarkdownContent`` with explicit
``IncludeOptions``. It scans the document directory and additional roots with
``refs_depth=0`` by default. The standalone ``get_refs_from_md_directory`` and
``get_refs_from_search_folders`` helpers default to unlimited depth; pass
``depth=0`` when only direct children should be read. The around-file helper
has separate ``depth_up`` and ``depth_down`` parameters.

Reference discovery excludes common generated directories and skips symlinks.
Exclusions apply to reference scans, not include-file lookup. Duplicate named
references raise an error, including when overlapping roots scan the same file.
Use unique names and non-overlapping roots. Named reference blocks are distinct
from ordinary Markdown link definitions such as ``[guide]: guide.md``.

See :doc:`options` for all defaults and :doc:`mdfile` for processing order.
Examples 04–07 in :doc:`workflows` demonstrate each directive family.

Public API
----------

.. automodule:: pymdtools.instruction
   :members:
   :imported-members:
   :undoc-members:
   :show-inheritance:
