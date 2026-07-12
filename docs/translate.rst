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

Translation text is sent to a third-party service. Do not submit secrets or
regulated content without an appropriate data policy. Network failures keep the
original text by default; ``on_error="raise"`` is available when a failed
translation must stop the workflow.

Public API
----------

.. automodule:: pymdtools.translate
   :members:
   :undoc-members:
   :show-inheritance:
