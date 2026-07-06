Translation Helpers
===================

``pymdtools.translate`` translates plain text and Markdown with the MyMemory web
API. Markdown translation keeps the document structure while translating text
segments.

Common Usage
------------

Translate plain text:

.. code-block:: python

   from pymdtools.translate import translate_txt

   result = translate_txt("Hello", src="en", dest="fr")

Translate Markdown:

.. code-block:: python

   from pymdtools.translate import translate_md

   translated = translate_md("# Hello", src="en", dest="fr")

Network access is required at runtime because translations are requested from
the MyMemory API.

Public API
----------

.. automodule:: pymdtools.translate
   :members:
   :undoc-members:
   :show-inheritance:
