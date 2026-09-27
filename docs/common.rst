Common Utilities
================

``pymdtools.common`` is the shared utility layer used by the rest of
``pymdtools``. It exposes one stable facade for path handling, filesystem
operations, text helpers, UTC date/time helpers, and small validation utilities.

Prefer importing public helpers from ``pymdtools.common``. Existing imports from
``pymdtools.common.fs`` and ``pymdtools.common.text`` remain compatible; underscore
modules such as ``common._filesystem`` are implementation details.

Common Usage
------------

Read and write text files with encoding detection:

.. testcode::

   from pymdtools.common import get_file_content, set_file_content

   set_file_content("build/input.txt", "A text with accents: café.\n")
   content = get_file_content("build/input.txt", encoding="utf-8")
   set_file_content("build/output.txt", content)
   assert get_file_content("build/output.txt", encoding="utf-8") == content

Create a backup next to an existing file:

.. testcode::

   from pymdtools.common import create_backup

   backup_path = create_backup("build/output.txt")
   assert get_file_content(backup_path, encoding="utf-8") == content

Copy a directory tree incrementally:

.. code-block:: python

   from pymdtools.common import copytree

   copytree("templates", "build/templates")

Create new identifiers, or encode the actual spelling of an existing path:

.. testcode::

   from pymdtools.common import encode_path_url, get_valid_filename, path_to_url, slugify

   filename = get_valid_filename("CON: bad/name.md")
   slug = slugify("My Markdown Title")
   slug_path = path_to_url("Docs/My Page.md")
   url_path = encode_path_url("Docs/My Page.md")
   assert url_path == "Docs/My%20Page.md"

``slugify`` and ``path_to_url`` create normalized names; they do not rename
existing files. Use ``encode_path_url`` for links to paths whose case and Unicode
spelling must remain intact.

Reads detect encoding when none is supplied. Detection is heuristic, especially
for short strings; specify the encoding when it is known, as in this example.
``set_file_content`` writes UTF-8, creates parents and uses atomic replacement
by default. It does not create a dated backup; call ``create_backup`` explicitly
or use :class:`pymdtools.filetools.FileContent`.

Enrich exceptions with contextual information:

.. code-block:: python

   from pymdtools.common import handle_exception

   @handle_exception("Unable to convert markdown file", filename="File")
   def convert(filename: str) -> None:
       raise ValueError("invalid input")

Helpers By Family
-----------------

Core helpers
~~~~~~~~~~~~

- ``handle_exception``: enrich exceptions raised by decorated functions.
- ``static``: attach static attributes to a function.
- ``Constant``: expose read-only descriptor values.

Filesystem and path helpers
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``to_path``, ``normpath``, ``with_suffix``, ``path_depth``
- ``check_folder``, ``ensure_folder``, ``check_file``
- ``copytree``, ``create_backup``, ``make_temp_dir``
- ``apply_to_files``, ``ApplyResult``, ``find_file``
- ``get_this_filename``
- ``is_binary_file``
- ``detect_file_encoding``, ``get_file_content``, ``set_file_content``

Text helpers
~~~~~~~~~~~~

- ``convert_for_stdout``
- ``to_ascii``
- ``slugify``
- ``get_valid_filename``
- ``get_flat_filename``
- ``path_to_url``
- ``encode_path_url``
- ``limit_str``

Time helpers
~~~~~~~~~~~~

- ``today_utc``
- ``now_utc_timestamp``
- ``parse_timestamp``

Validation helpers
~~~~~~~~~~~~~~~~~~

- ``check_len``

For directory processing, ``apply_to_files`` can report individual failures
through ``ApplyResult``. Example 16 in :doc:`workflows` demonstrates collection
of a failed operation while processing other files, and example 17 compares
encoding and path helpers.

Public API
----------

.. automodule:: pymdtools.common
   :members:
   :imported-members:
   :undoc-members:
   :show-inheritance:
