Markdown Normalization
======================

``pymdtools.normalize`` provides helpers to normalize Markdown strings and
Markdown files. It uses the Mistune integration layer to parse Markdown and
render it back to a consistent Markdown representation.

Common Usage
------------

Normalize an in-memory string:

.. code-block:: python

   from pymdtools.normalize import md_beautifier

   text = md_beautifier("# Title\n\nBody\n")

Normalize a Markdown file in place:

.. code-block:: python

   from pymdtools.normalize import md_file_beautifier

   md_file_beautifier("README.md", backup_option=True)

Public API
----------

.. automodule:: pymdtools.normalize
   :members:
   :undoc-members:
   :show-inheritance:
