Markdown Normalization
======================

``pymdtools.normalize`` provides helpers to normalize Markdown strings and
Markdown files. It uses the Mistune integration layer to parse Markdown and
render it back to a consistent Markdown representation.

Common Usage
------------

Normalize an in-memory string:

.. testcode::

   from pymdtools.normalize import md_beautifier

   text = md_beautifier("# Title\n\nBody\n")
   assert md_beautifier(text) == text

Normalize a Markdown file in place:

.. testcode::

   from pathlib import Path

   from pymdtools.normalize import md_file_beautifier

   source = Path("guide.md")
   source.write_text("Title\n=====\n\nBody\n", encoding="utf-8")
   md_file_beautifier(source, backup_option=True)
   assert list(source.parent.glob("guide.md.*.bak"))

Preservation contract
---------------------

Mistune produces a candidate and a CommonMark renderer compares it with the
source. If rendered HTML changes, or normalizing the candidate again would
change it, the original text is returned unchanged. Normalization can therefore
leave unusual formatting intact. It does not process variable or include
directives, check links, or guarantee support for extensions from every
Markdown dialect.

``md_file_beautifier`` changes the source file, writes UTF-8 by default and can
create a dated backup. Pass ``read_encoding`` for a known input encoding and
``write_encoding`` for a different output encoding. It returns the normalized
absolute filename as a string; ``md_beautifier`` returns Markdown text.
The package-level ``markdown_file_beautifier`` is a compatibility shortcut.

Examples 01 and 02 in :doc:`workflows` show the input, output and backup files.

Public API
----------

.. automodule:: pymdtools.normalize
   :members:
   :undoc-members:
   :show-inheritance:
