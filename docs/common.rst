Common Utilities
================

``pymdtools.common`` is the shared utility layer used by the rest of
``pymdtools``. It exposes one stable facade for path handling, filesystem
operations, text helpers, UTC date/time helpers, and small validation utilities.

Prefer importing public helpers from ``pymdtools.common`` instead of importing
from implementation modules such as ``pymdtools.common.fs`` or
``pymdtools.common.text``.

Common Usage
------------

Read and write text files with encoding detection:

.. code-block:: python

   from pymdtools.common import get_file_content, set_file_content

   content = get_file_content("README.md")
   set_file_content("build/output.txt", content)

Create a backup next to an existing file:

.. code-block:: python

   from pymdtools.common import create_backup

   backup_path = create_backup("report.md")

Copy a directory tree incrementally:

.. code-block:: python

   from pymdtools.common import copytree

   copytree("templates", "build/templates")

Create safe text identifiers and paths:

.. code-block:: python

   from pymdtools.common import get_valid_filename, path_to_url, slugify

   filename = get_valid_filename("CON: bad/name.md")
   slug = slugify("My Markdown Title")
   url_path = path_to_url("Docs/My Page.md")

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
- ``limit_str``

Time helpers
~~~~~~~~~~~~

- ``today_utc``
- ``now_utc_timestamp``
- ``parse_timestamp``

Validation helpers
~~~~~~~~~~~~~~~~~~

- ``check_len``

Public API
----------

.. automodule:: pymdtools.common
   :members:
   :undoc-members:
   :show-inheritance:
