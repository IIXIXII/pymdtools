Markdown File Wrapper
=====================

``pymdtools.mdfile`` provides ``MarkdownContent``, a stateful wrapper for
editable Markdown files. It combines the text-file behavior of
``pymdtools.filetools.FileContent`` with Markdown-specific helpers from
``pymdtools.instruction`` and ``pymdtools.normalize``.

Common Usage
------------

Edit variables and titles in a Markdown document:

.. code-block:: python

   from pymdtools.mdfile import MarkdownContent

   md = MarkdownContent("README.md")
   md["project"] = "pymdtools"
   md.title = "Project README"
   md.process_tags()
   md.write()

Use ``process_tags`` when include files, include refs, and variables must be
resolved back into the in-memory content before writing.

Public API
----------

.. automodule:: pymdtools.mdfile
   :members:
   :undoc-members:
   :show-inheritance:
