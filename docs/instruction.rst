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

   <!-- include-file(snippets/example.md) -->

Referenced paths are intentionally constrained to relative paths without parent
traversal.

For file-backed operations, explicitly configure trusted search folders. The
resolver confines results to those roots and ``MarkdownContent`` automatically
adds the source document's parent directory. Directive-looking text inside
fenced or inline code is treated as an example, not as an instruction.

Title helpers
~~~~~~~~~~~~~

The module can read and update the first level-1 Markdown title, preserving or
forcing Setext / ATX style.

Common Usage
------------

Collect refs around a Markdown file and apply include blocks in-place:

.. code-block:: python

   from pymdtools.instruction import search_include_refs_to_md_file

   search_include_refs_to_md_file("docs/page.md", backup_option=True)

Replace variables in an in-memory string:

.. code-block:: python

   from pymdtools.instruction import search_include_vars_to_md_text

   updated = search_include_vars_to_md_text(markdown_text)

Public API
----------

.. automodule:: pymdtools.instruction
   :members:
   :undoc-members:
   :show-inheritance:
