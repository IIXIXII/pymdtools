Markdown Link Management
========================

``pymdtools.mdcommon`` provides utilities for inspecting and rewriting links
inside Markdown documents. It is meant for workflows that update a set of
Markdown files together: collecting link targets, moving relative paths,
renaming labels, replacing obsolete targets, or normalizing references after a
documentation tree has been reorganized.

The module works on Markdown text and leaves file discovery, encoding, backups,
and writes to higher-level helpers such as ``pymdtools.common`` and
``pymdtools.filetools``. This keeps link transformations easy to test before the
updated content is written back to disk.

Supported Links
---------------

The parser handles the two Markdown link forms used by the project:

- inline links, such as ``[label](target "title")``;
- reference-style links, such as ``[label][id]`` with a matching
  ``[id]: target "title"`` definition.

External links are detected separately so that bulk path updates can skip URLs
such as ``https://example.org`` or ``mailto:contact@example.org``.

Link Records
------------

Links are exchanged as small dictionaries. This representation makes it simple
to serialize, compare, transform, and feed discovered links back into rewrite
functions.

Common keys are:

- ``name`` stores the visible link label;
- ``url`` stores the link target;
- ``title`` stores the optional Markdown title;
- ``line`` stores the one-based line number for discovered links;
- ``id_link`` is used for reference-style links;
- ``name_to_replace`` can be provided when replacing a label with another one.

Common Usage
------------

Extract links from Markdown text:

.. code-block:: python

   from pymdtools.mdcommon import search_link_in_md_text

   links = search_link_in_md_text('[Docs](docs/index.md "Documentation")')

Replace one link by label:

.. code-block:: python

   from pymdtools.mdcommon import update_links_in_md_text

   updated = update_links_in_md_text(
       "[old](old.md)",
       {"name_to_replace": "old", "name": "new", "url": "new.md"},
   )

Move relative link targets under a new base path while leaving external links
unchanged:

.. code-block:: python

   from pymdtools.mdcommon import move_base_path_in_md_text

   updated = move_base_path_in_md_text("[Guide](guide.md)", "docs")

Apply a transformation to a Markdown tree:

.. code-block:: python

   from pathlib import Path

   from pymdtools.common import get_file_content, set_file_content
   from pymdtools.mdcommon import move_base_path_in_md_text

   for md_file in Path("docs").rglob("*.md"):
       original = get_file_content(md_file)
       updated = move_base_path_in_md_text(original, "archive")
       if updated != original:
           set_file_content(md_file, updated)

Choosing A Rewrite Function
---------------------------

Use ``update_link_in_md_text`` when the visible label is the stable identifier.
Use ``update_link_from_old_link`` when both the previous label and previous
target must match before replacing a link. Use ``update_links_from_old_link``
to apply several old/new replacements in sequence.

Use ``move_base_path_in_md_text`` for documentation moves where every relative
target in one Markdown document needs to be prefixed with the same base path.

Public API
----------

.. automodule:: pymdtools.mdcommon
   :members:
   :undoc-members:
   :show-inheritance:
