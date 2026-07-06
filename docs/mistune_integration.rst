Mistune Integration
===================

``pymdtools.mistune_integration`` is the compatibility layer between pymdtools
and the external ``mistune`` package. It targets Mistune 3 and provides
renderers that preserve pymdtools' historical ``close()`` hook.

Common Usage
------------

Create a Markdown parser with close-hook support:

.. code-block:: python

   from pymdtools.mistune_integration import create_markdown_with_close

   markdown = create_markdown_with_close(renderer="html")
   html = markdown("# Title")

Use ``MdRenderer`` when Markdown should be normalized back to Markdown.

Public API
----------

The module also re-exports selected Mistune classes and helpers for backward
compatibility. The generated API below focuses on pymdtools' own compatibility
objects.

.. automodule:: pymdtools.mistune_integration
   :members: ClosingHTMLRenderer, ClosingMarkdownRenderer, MdRenderer, create_markdown_with_close, get_backend_name, get_backend_version
   :undoc-members:
   :show-inheritance:
