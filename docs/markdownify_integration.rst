Markdownify Integration
=======================

``pymdtools.markdownify_integration`` is the thin wrapper around the external
``markdownify`` package. It replaces the old vendored implementation with a
single compatibility point and re-exports the symbols historically used by
pymdtools callers.

Common Usage
------------

Convert HTML to Markdown:

.. testcode::

   from pymdtools.markdownify_integration import markdownify

   markdown = markdownify("<h1>Title</h1><p>A <strong>short</strong> guide.</p>", heading_style="ATX")
   assert "# Title" in markdown
   assert "**short**" in markdown

Backend helpers expose the active backend name and version for diagnostics.
Options are forwarded to the installed external ``markdownify`` package; select
``heading_style="ATX"`` or a list ``bullets`` style explicitly when your output
depends on that choice. The wrapper converts supplied HTML text: it does not
fetch a URL or reproduce a browser's layout. See example 12 in :doc:`workflows`.

Public API
----------

.. automodule:: pymdtools.markdownify_integration
   :members:
   :undoc-members:
   :show-inheritance:
