Markdownify Integration
=======================

``pymdtools.markdownify_integration`` is the thin wrapper around the external
``markdownify`` package. It replaces the old vendored implementation with a
single compatibility point and re-exports the symbols historically used by
pymdtools callers.

Common Usage
------------

Convert HTML to Markdown:

.. code-block:: python

   from pymdtools.markdownify_integration import markdownify

   markdown = markdownify("<h1>Title</h1>")

Backend helpers expose the active backend name and version for diagnostics.

Public API
----------

.. automodule:: pymdtools.markdownify_integration
   :members:
   :undoc-members:
   :show-inheritance:
