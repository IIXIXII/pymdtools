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

Reusable clients and paragraph context
--------------------------------------

Pass a ``TranslationClient`` to enable a bounded in-memory cache and up to two
retries after transient HTTP or connection errors. Cache entries belong to that
client and include the language pair and credentials; there is no global cache
or disk persistence. Use ``cache_size=0`` to disable retention or
``client.clear_cache()`` to discard retained data. Each attempt uses ``timeout``;
the total duration can include several attempts and bounded exponential waits.
Clients are intended for sequential use.

.. code-block:: python

   from pymdtools.translate import TranslationClient, translate_md

   client = TranslationClient(cache_size=128, max_retries=2)
   result = translate_md(
       "Un **texte** avec un [lien](page.md).",
       client=client,
       segmentation="paragraph",
   )
   client.clear_cache()

``segmentation="paragraph"`` sends the visible text of each short paragraph,
heading or list item in one request. Formatting, link destinations and code
remain local and are represented by protected markers. The response must retain
every marker in its original order. If it does not, the original text is kept;
``on_error="empty"`` removes that block's text and ``on_error="raise"`` raises
``TranslationStructureError``. Text returned by the provider is escaped before
being inserted into Markdown. Blocks exceeding the provider's 500-byte limit
use token segmentation. The default remains ``segmentation="token"``.

Marker preservation depends on the provider, so paragraph grouping is opt-in.
Its structural guarantees are tested offline; translation quality must be
assessed with representative documents and the chosen provider.

For offline tests or another provider, inject a callable as
``TranslationClient(transport=my_transport)``. It receives ``text``, ``src`` and
``dest`` plus keyword arguments ``email``, ``api_key`` and ``timeout``, and returns
a translated string or raises an exception. Exceptions raised with
``on_error="raise"`` remain the caller's responsibility, including closing any
HTTP error response that it consumes.

Public API
----------

.. automodule:: pymdtools.translate
   :members:
   :imported-members:
   :undoc-members:
   :show-inheritance:
