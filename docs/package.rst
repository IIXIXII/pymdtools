Package API
===========

``pymdtools`` exposes a small package-level API with lazy imports. Importing the
package itself stays lightweight; heavier integrations such as PDF conversion
are only imported when the corresponding public symbol is accessed.

Public Shortcuts
----------------

- ``convert_for_stdout``: normalize text for console output.
- ``markdown_file_beautifier``: normalize a Markdown file in place.
- ``convert_md_to_pdf``: convert Markdown to PDF through the HTML/PDF pipeline.
- ``search_include_refs_to_md_file``: resolve Markdown include references.

For new workflows, import from the task-specific modules documented in this
manual, for example ``pymdtools.mdfile.MarkdownContent``. The package root does
not re-export every helper. Inspect ``pymdtools.__version__`` for the installed
version. Optional PDF dependencies are loaded when PDF functionality is used;
importing the conversion facade does not install or start Chromium.

Public API
----------

.. automodule:: pymdtools
   :members:
   :imported-members:
   :undoc-members:
   :show-inheritance:
