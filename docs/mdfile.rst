Markdown File Wrapper
=====================

``pymdtools.mdfile`` provides ``MarkdownContent``, a stateful wrapper for
editable Markdown files. It combines the text-file behavior of
``pymdtools.filetools.FileContent`` with Markdown-specific helpers from
``pymdtools.instruction`` and ``pymdtools.normalize``.

Common Usage
------------

Create a document without changing a source file. This example writes its result
under ``build/``:

.. testcode::

   from pymdtools.mdfile import MarkdownContent

   md = MarkdownContent(
       content="# Draft\n\n<!-- begin-var(project) --><!-- end-var -->\n"
   )
   md["project"] = "pymdtools"
   md.title = "Project guide"
   md.process_tags()
   md.write("build/guide.md")
   assert MarkdownContent("build/guide.md")["project"] == "pymdtools"
   assert not md.save_needed

Persistence and backups
-----------------------

Passing an existing filename reads it immediately unless ``content`` is supplied.
Passing ``content`` starts from that text instead. Edits stay in memory; ``write``
persists the buffer as UTF-8 by default and creates missing parent directories.
``write(new_path)`` updates the object's stored filename after a successful write.

Backups are enabled by default when the destination already exists. They are
dated files next to the destination. Use ``backup=False`` for disposable generated
documents. ``save_needed`` becomes True when content is assigned, even when the
new string is equal to the old one. ``write`` does not skip a save automatically;
check the flag in your application if needed. Successful reads and writes reset it.

Assembly and other helpers
--------------------------

``process_tags()`` runs one pass in this order: file inclusions, variable blocks,
then named reference inclusions. It stores and returns the resulting string.
It is not a recursive template engine: directives introduced by a later stage
are not automatically processed by an earlier stage in the same call.

Pass :class:`pymdtools.options.IncludeOptions` as ``include_options`` to set
search roots, reference depth and raw/boxed file inclusion. The file's parent
directory is an implicit search root. Reference discovery runs only when active
``begin-include`` directives are present. See :doc:`instruction` and :doc:`options`.

``title`` reads or changes the first level-1 heading. Mapping operations
(``md["name"]``, assignment, deletion, ``keys()``, ``values()``, ``items()``)
operate on variable declarations. ``toc`` returns an **HTML fragment** generated
by Python-Markdown's table-of-contents extension; it does not insert a Markdown
table of contents. ``beautify()`` normalizes the in-memory Markdown using the
conservative behavior described in :doc:`normalize`.

Executable examples: ``03_edit_document.py``, ``07_discovery_options.py`` and
``08_titles_and_toc.py`` in the :doc:`workflows` catalogue.

Public API
----------

.. automodule:: pymdtools.mdfile
   :members:
   :undoc-members:
   :show-inheritance:
   :inherited-members:
